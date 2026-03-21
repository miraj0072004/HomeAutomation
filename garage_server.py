from flask import Flask, jsonify, request
import RPi.GPIO as GPIO
import time

app = Flask(__name__)

RELAY_PIN = 17
COOLDOWN_SECONDS = 180
SECRET_TOKEN = "myGarage_92kL_secure"  # change this

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)

last_trigger_time = 0.0


def pulse_relay():
    GPIO.output(RELAY_PIN, GPIO.LOW)
    time.sleep(1)
    GPIO.output(RELAY_PIN, GPIO.HIGH)


@app.route("/trigger")
def trigger():
    global last_trigger_time

    token = request.args.get("token")

    # Check token
    if token != SECRET_TOKEN:
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

    # Cooldown check
    if elapsed < COOLDOWN_SECONDS:
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
    app.run(host="0.0.0.0", port=5000)
