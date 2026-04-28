from flask import Flask, jsonify
import requests
import time
import threading

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {
    "timestamp": 0,
    "data": {"value": "0"},
    "last_count": None,
    "last_valid_count": 0,
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
# UPDATE CACHE (with decay + offline logic)
# -----------------------
def update_cache():
    global CACHE

    total = fetch_total()
    now = time.time()

    with LOCK:

        # -----------------------
        # API FAILED
        # -----------------------
        if total is None:
            print("[WARN] API failed, keeping last value")
            return False

        # mark successful fetch time
        CACHE["last_success_time"] = now

        last = CACHE["last_count"]

        # -----------------------
        # DECAY LOGIC (smooth trend)
        # -----------------------
        if last is None:
            delta = 0
            trend = "➖"

        else:
            delta = total - last

            # decay smoothing: ignore tiny fluctuations (-1 to +1)
            if -1 <= delta <= 1:
                trend = "➖"
                delta = 0
            elif delta > 1:
                trend = "▲"
            else:
                trend = "▼"

        # -----------------------
        # FORMAT OUTPUT
        # -----------------------
        if total == 0:
            formatted = "0"
        else:
            formatted = f"{total} {trend} ({delta:+d})"

        CACHE["data"] = {"value": formatted}
        CACHE["last_count"] = total
        CACHE["last_valid_count"] = total
        CACHE["timestamp"] = now

        print(f"[UPDATE] {formatted}")

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

        # -----------------------
        # OFFLINE MODE
        # -----------------------
        if time_since_success > OFFLINE_THRESHOLD:
            return jsonify({"value": "OFFLINE"})

        return jsonify(CACHE["data"])


# START SYSTEM
initial_fetch()
threading.Thread(target=background_loop, daemon=True).start()
