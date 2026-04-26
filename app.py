from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {"timestamp": 0, "data": {"count": 0}}
CACHE_TIME = 310


def safe_fetch():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()

        servers = data.get("servers", [])

        total = sum(
            int(s.get("playerAmount", 0))
            for s in servers
            if int(s.get("playerAmount", 0)) > 0
        )

        return total

    except Exception as e:
        print("Fetch error:", e)
        return None


@app.route("/")
def total_players():
    now = time.time()

    # use cache if valid
    if now - CACHE["timestamp"] < CACHE_TIME:
        return jsonify(CACHE["data"])

    total = safe_fetch()

    # only update if successful
    if total is not None:
        CACHE["data"] = {"count": total}
        CACHE["timestamp"] = now

    # ALWAYS return valid JSON
    return jsonify(CACHE["data"])
