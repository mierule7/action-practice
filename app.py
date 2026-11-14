import json
import os
import time

from confluent_kafka import KafkaException, Producer
from flask import Flask, jsonify, render_template_string, request
from logtide_sdk import ClientOptions, LogTideClient
from logtide_sdk.middleware import LogTideFlaskMiddleware
from opentelemetry import metrics, propagate, trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import SpanKind

import calc
import telemetry

app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "local")
BUILD_ID = os.environ.get("BUILD_ID", "local")
TOPIC = f"calc.events.{APP_ENV}"

tracer_provider = telemetry.setup("calc-app")
tracer = trace.get_tracer("calc-app")
meter = metrics.get_meter("calc-app")
operations = meter.create_counter(
    "calc.operations", description="Calculations requested"
)

if tracer_provider is not None:
    FlaskInstrumentor().instrument_app(app, excluded_urls="health")

client = None
producer = None

if os.environ.get("LOGTIDE_API_KEY"):
    client = LogTideClient(
        ClientOptions(
            api_url=os.environ["LOGTIDE_API_URL"],
            api_key=os.environ["LOGTIDE_API_KEY"],
            global_metadata={"env": APP_ENV, "build": BUILD_ID},
        )
    )
    LogTideFlaskMiddleware(
        app,
        client=client,
        service_name="calc-app",
        log_requests=True,
        log_responses=True,
        skip_paths=["/health"],
    )

if os.environ.get("KAFKA_BOOTSTRAP"):
    producer = Producer(
        {
            "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP"],
            "message.timeout.ms": 5000,
        }
    )


def on_delivery(err, msg):
    if err is not None:
        app.logger.warning("Kafka delivery failed: %s", err)


def publish_event(op, a, b, result):
    """Send one event to Kafka. A broker problem must never break a calculation."""
    if producer is None:
        return
    event = {
        "env": APP_ENV,
        "build": BUILD_ID,
        "op": op,
        "a": a,
        "b": b,
        "result": result,
        "ts": time.time(),
    }
    with tracer.start_as_current_span(
        f"{TOPIC} publish", kind=SpanKind.PRODUCER
    ) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination.name", TOPIC)
        headers = {}
        propagate.inject(headers)
        try:
            producer.produce(
                TOPIC,
                json.dumps(event).encode("utf-8"),
                headers=headers or None,
                callback=on_delivery,
            )
            producer.poll(0)
        except (BufferError, KafkaException) as err:
            span.record_exception(err)
            app.logger.warning("Kafka publish failed: %s", err)


OPS = {
    "add": calc.add,
    "subtract": calc.subtract,
    "multiply": calc.multiply,
    "divide": calc.divide,
}

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Calculator - {{ env }}</title>
  <style>
    body { font-family: sans-serif; max-width: 420px; margin: 0 auto; }
    .banner { padding: 12px; color: #fff; text-align: center; font-weight: bold;
              background: {{ color }}; }
    .box { padding: 20px; }
    input, select, button { font-size: 16px; padding: 8px; margin: 4px 0; width: 100%;
                            box-sizing: border-box; }
    #result { font-size: 22px; margin-top: 16px; }
  </style>
</head>
<body>
  <div class="banner">{{ env|upper }} &middot; Build {{ build }}</div>
  <div class="box">
    <h2>Calculator v2</h2>
    <input id="a" type="number" step="any" placeholder="First number">
    <select id="op">
      <option value="add">+ Add</option>
      <option value="subtract">- Subtract</option>
      <option value="multiply">&times; Multiply</option>
      <option value="divide">&divide; Divide</option>
    </select>
    <input id="b" type="number" step="any" placeholder="Second number">
    <button onclick="calc()">Calculate</button>
    <div id="result"></div>
  </div>
  <script>
    async function calc() {
      const a = document.getElementById("a").value;
      const b = document.getElementById("b").value;
      const op = document.getElementById("op").value;
      const res = await fetch(`/api/calc?a=${a}&b=${b}&op=${op}`);
      const data = await res.json();
      document.getElementById("result").textContent =
        res.ok ? "Result: " + data.result : "Error: " + data.error;
    }
  </script>
</body>
</html>
"""

COLORS = {"dev": "#1976d2", "uat": "#f57c00", "prod": "#c62828"}


@app.get("/")
def index():
    return render_template_string(
        PAGE,
        env=APP_ENV,
        color=COLORS.get(APP_ENV, "#555"),
        build=BUILD_ID,
    )


@app.get("/api/calc")
def api_calc():
    op = request.args.get("op", "")
    try:
        a = float(request.args["a"])
        b = float(request.args["b"])
        if op not in OPS:
            raise ValueError("Unknown operation")
        result = OPS[op](a, b)
    except (KeyError, ValueError) as err:
        operations.add(1, {"op": op or "unknown", "outcome": "bad_request"})
        if client:
            client.warn(
                "calc-app",
                "Bad calculation request",
                {"op": op, "error": str(err) or "Enter two numbers"},
            )
        return jsonify(error=str(err) or "Enter two numbers"), 400
    operations.add(1, {"op": op, "outcome": "ok"})
    publish_event(op, a, b, result)
    return jsonify(result=result)


@app.get("/health")
def health():
    return jsonify(status="ok", env=APP_ENV, build=BUILD_ID)


if __name__ == "__main__":
    app.run(port=8000)