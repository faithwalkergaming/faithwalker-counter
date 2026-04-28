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

CACHE_TIME = 310
OFFLINE_THRESHOLD = 17 * 60  # 17 minutes
LOCK = threading.Lock()


# -----------------------
# FETCH FUNCTION
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
# UPDATE CACHE
# -----------------------
def update_cache():
    global CACHE

    total = fetch_total()
    now = time.time()

    with LOCK:

        # API failed → keep last value
        if total is None:
            print("[WARN] API failed, keeping last value")
            return False

        # update only raw value
        CACHE["value"] = str(total)
        CACHE["last_success_time"] = now

        print("[UPDATE]", total)

    return True


# -----------------------
# INITIAL FETCH
# -----------------------
def initial_fetch():
    print("[INIT] Starting fetch...")

    for _ in range(10):
        if update_cache():
            print("[INIT] Success")
            return
        time.sleep(2)

    print("[INIT] Failed initial fetch")


# -----------------------
# BACKGROUND LOOP
# -----------------------
def background_loop():
    while True:
        update_cache()
        time.sleep(CACHE_TIME)


# -----------------------
# API ROUTE (OFFLINE SAFE)
# -----------------------
@app.route("/")
def total_players():
    with LOCK:

        now = time.time()
        time_since_success = now - CACHE["last_success_time"]

        # OFFLINE MODE
        if time_since_success > OFFLINE_THRESHOLD:
            return jsonify({"value": "OFFLINE"})

        return jsonify({"value": CACHE["value"]})


# START SYSTEM
initial_fetch()
threading.Thread(target=background_loop, daemon=True).start()
