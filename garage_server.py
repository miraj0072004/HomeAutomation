from flask import Flask, jsonify, request
import os
import RPi.GPIO as GPIO
import time
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

RELAY_PIN = 17
COOLDOWN_SECONDS = 10
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")

if not SECRET_TOKEN:
    raise RuntimeError("SECRET_TOKEN environment variable is not set")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

last_trigger_time = 0.0


def pulse_relay():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    time.sleep(1)
    GPIO.output(RELAY_PIN, GPIO.HIGH)


@app.route("/trigger")
def trigger():
    global last_trigger_time

    token = request.args.get("token")

    if token != SECRET_TOKEN:
        app.logger.warning("Unauthorized trigger attempt")
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "unauthorized",
                }
            ),
            403,
        )

    now = time.time()
    elapsed = now - last_trigger_time

    if elapsed < COOLDOWN_SECONDS:
        app.logger.info("Trigger blocked by cooldown")
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "cooldown active",
                    "seconds_remaining": round(COOLDOWN_SECONDS - elapsed, 1),
                }
            ),
            429,
        )

    pulse_relay()
    last_trigger_time = now
    app.logger.info("Garage triggered successfully")

    return jsonify(
        {
            "ok": True,
            "message": "garage triggered",
        }
    )


@app.route("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)