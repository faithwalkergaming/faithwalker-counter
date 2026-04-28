from flask import Flask, jsonify
import requests
import time
import threading

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {
    "value": "0",
    "last_success_time": time.time()
}

LOCK = threading.Lock()

CACHE_TIME = 310


# -----------------------
# FETCH TOTAL PLAYERS (FINAL FIX)
# -----------------------
def fetch_total():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()

        servers = data.get("servers") or []

        total = 0

        for s in servers:
            players = s.get("playerAmount", 0)

            try:
                players = int(players)
            except:
                continue

            # count ALL valid positive players
            if players > 0:
                total += players

        return total

    except Exception as e:
        print("[ERROR] Fetch failed:", e)
        return None


# -----------------------
# UPDATE CACHE
# -----------------------
def update_cache():
    global CACHE

    total = fetch_total()

    if total is None:
        return False

    with LOCK:
        CACHE["value"] = str(total)
        CACHE["last_success_time"] = time.time()
        print("[UPDATE]", total)

    return True


def background_loop():
    while True:
        update_cache()
        time.sleep(CACHE_TIME)


threading.Thread(target=background_loop, daemon=True).start()


# -----------------------
# TIME FORMATTER
# -----------------------
def format_age(seconds):
    minutes = int(seconds / 60)
    return f"{minutes}m ago" if minutes < 60 else "1h+ ago"


# -----------------------
# API ENDPOINT
# -----------------------
@app.route("/")
def total_players():
    with LOCK:
        now = time.time()
        age_seconds = now - CACHE["last_success_time"]
        age_minutes = int(age_seconds / 60)

        value = CACHE["value"]

        if age_minutes >= 17:
            return jsonify({
                "value": f"{value} ({format_age(age_seconds)})"
            })

        return jsonify({"value": value})
