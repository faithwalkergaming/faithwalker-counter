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


# -----------------------
# FETCH TOTAL PLAYERS
# -----------------------
def fetch_total():
    try:
        r = requests.get(API_URL, timeout=5)
        r.raise_for_status()
        servers = r.json().get("servers", [])

        return sum(
            int(s.get("playerAmount", 0))
            for s in servers
            if int(s.get("playerAmount", 0)) > 0
        )
    except Exception as e:
        print("[ERROR] Fetch failed:", e)
        return None


# -----------------------
# UPDATE CACHE (310s loop)
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


# -----------------------
# BACKGROUND LOOP
# -----------------------
def background_loop():
    while True:
        update_cache()
        time.sleep(310)


threading.Thread(target=background_loop, daemon=True).start()


# -----------------------
# TIME FORMATTER
# -----------------------
def format_age(seconds):
    minutes = int(seconds / 60)

    if minutes < 60:
        return f"{minutes}m ago"
    else:
        hours = minutes // 60
        return "1h+ ago"


# -----------------------
# API ROUTE
# -----------------------
@app.route("/")
def total_players():
    with LOCK:

        now = time.time()
        age_seconds = now - CACHE["last_success_time"]

        age_text = format_age(age_seconds)

        return jsonify({
            "value": f"{CACHE['value']} ({age_text})"
        })
