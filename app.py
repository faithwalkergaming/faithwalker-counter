from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {
    "timestamp": 0,
    "data": {"count": 0}
}

CACHE_TIME = 310  # seconds


def fetch_total():
    r = requests.get(API_URL, timeout=10)
    data = r.json().get("servers", [])

    total = sum(
        int(s.get("playerAmount", 0))
        for s in data
        if int(s.get("playerAmount", 0)) > 0
    )

    return total


@app.route("/")
def total_players():
    now = time.time()

    # use cache if still valid
    if now - CACHE["timestamp"] < CACHE_TIME:
        return jsonify(CACHE["data"])

    # refresh cache
    try:
        total = fetch_total()
        CACHE["data"] = {"count": total}
        CACHE["timestamp"] = now

    except Exception as e:
        print("Error:", e)
        CACHE["data"] = {"count": 0}

    return jsonify(CACHE["data"])
