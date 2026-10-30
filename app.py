import os

from flask import Flask, jsonify, render_template_string, request

import calc

app = Flask(__name__)

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
    <h2>Calculator</h2>
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
    env = os.environ.get("APP_ENV", "local")
    return render_template_string(
        PAGE,
        env=env,
        color=COLORS.get(env, "#555"),
        build=os.environ.get("BUILD_ID", "local"),
    )


@app.get("/api/calc")
def api_calc():
    op = request.args.get("op", "")
    try:
        a = float(request.args["a"])
        b = float(request.args["b"])
        if op not in OPS:
            raise ValueError("Unknown operation")
        return jsonify(result=OPS[op](a, b))
    except (KeyError, ValueError) as err:
        return jsonify(error=str(err) or "Enter two numbers"), 400


@app.get("/health")
def health():
    return jsonify(status="ok", env=os.environ.get("APP_ENV", "local"),
                   build=os.environ.get("BUILD_ID", "local"))


if __name__ == "__main__":
    app.run(port=8000)