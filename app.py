from flask import Flask, jsonify
import requests
import time
import threading

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {
    "value": "0 ➖ (+0)",
    "last_count": None,
    "last_success": time.time()
}

LOCK = threading.Lock()
CACHE_TIME = 310


# -----------------------
# FETCH FUNCTION (SAFE)
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
    except:
        return None


# -----------------------
# BACKGROUND UPDATER
# -----------------------
def updater():
    global CACHE

    while True:
        total = fetch_total()

        if total is not None:
            with LOCK:
                last = CACHE["last_count"]

                if last is None:
                    delta = 0
                    trend = "➖"
                else:
                    delta = total - last

                    if delta > 0:
                        trend = "▲"
                    elif delta < 0:
                        trend = "▼"
                    else:
                        trend = "➖"

                formatted = f"{total} {trend} ({delta:+d})"

                CACHE["value"] = formatted
                CACHE["last_count"] = total
                CACHE["last_success"] = time.time()

                print("[UPDATE]", formatted)

        time.sleep(CACHE_TIME)


# start background thread
threading.Thread(target=updater, daemon=True).start()


# -----------------------
# API ROUTE (INSTANT ONLY)
# -----------------------
@app.route("/")
def total_players():
    with LOCK:
        return jsonify({"value": CACHE["value"]})
