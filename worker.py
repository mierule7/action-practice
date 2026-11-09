import json
import os
import signal

from confluent_kafka import Consumer

env = os.environ.get("APP_ENV", "local")
topic = f"calc.events.{env}"

consumer = Consumer(
    {
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP"],
        "group.id": f"calc-worker-{env}",
        "auto.offset.reset": "earliest",
    }
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
        print(
            f"#{count} {event['a']} {event['op']} {event['b']} = {event['result']}"
            f" (env {event['env']}, build {event['build']})",
            flush=True,
        )
finally:
    consumer.close()