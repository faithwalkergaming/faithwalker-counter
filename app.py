from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {
    "value": 0,
    "last_update": 0
}

CACHE_TIME = 310  # seconds


# -----------------------
# FETCH TOTAL PLAYERS
# -----------------------
def fetch_total():
    r = requests.get(API_URL, timeout=10)
    data = r.json()

    servers = data.get("servers", [])

    total = 0

    for s in servers:
        try:
            total += int(s.get("playerAmount", 0))
        except:
            continue

    return total


# -----------------------
# UPDATE CACHE IF NEEDED
# -----------------------
def get_cached_value():
    now = time.time()

    # refresh every 310 seconds
    if now - CACHE["last_update"] > CACHE_TIME:
        try:
            CACHE["value"] = fetch_total()
            CACHE["last_update"] = now
        except:
            # if API fails, keep last good value
            pass

    return CACHE["value"]


# -----------------------
# ROUTE
# -----------------------
@app.route("/")
def total_players():
    value = get_cached_value()
    return jsonify({"value": value})
