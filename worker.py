import json
import os
import signal

from confluent_kafka import Consumer
from opentelemetry import metrics
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor

import telemetry

env = os.environ.get("APP_ENV", "local")
topic = f"calc.events.{env}"

tracer_provider = telemetry.setup("calc-worker")
meter = metrics.get_meter("calc-worker")
processed = meter.create_counter(
    "calc.events.processed", description="Events handled by the worker"
)

consumer = Consumer(
    {
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP"],
        "group.id": f"calc-worker-{env}",
        "auto.offset.reset": "earliest",
    }
)
if tracer_provider is not None:
    consumer = ConfluentKafkaInstrumentor().instrument_consumer(
        consumer, tracer_provider=tracer_provider
    )
consumer.subscribe([topic])

running = True


def stop(*_):
    global running
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

count = 0
print(f"worker started: topic={topic}", flush=True)
try:
    while running:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"consumer error: {msg.error()}", flush=True)
            continue
        event = json.loads(msg.value().decode("utf-8"))
        count += 1
        processed.add(1, {"op": event["op"]})
        print(
            f"#{count} {event['a']} {event['op']} {event['b']} = {event['result']}"
            f" (env {event['env']}, build {event['build']})",
            flush=True,
        )
finally:
    consumer.close()