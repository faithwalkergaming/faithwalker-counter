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
    "last_valid_count": 0
}

CACHE_TIME = 310
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

    with LOCK:

        # ❌ API FAILED → DO NOTHING (keep last value)
        if total is None:
            print("[WARN] Using last known value:", CACHE["last_valid_count"])
            return False

        last = CACHE["last_count"]

        # Determine trend + delta
        if last is None:
            trend = "➖"
            delta = 0
        else:
            delta = total - last

            if delta > 0:
                trend = "▲"
            elif delta < 0:
                trend = "▼"
            else:
                trend = "➖"

        # Build output
        if total == 0:
            formatted = "0"
        else:
            formatted = f"{total} {trend} ({delta:+d})"

        # Save state
        CACHE["data"] = {"value": formatted}
        CACHE["last_count"] = total
        CACHE["last_valid_count"] = total
        CACHE["timestamp"] = time.time()

        print(f"[UPDATE] {formatted}")

    return True


# -----------------------
# INITIAL FETCH (safe startup)
# -----------------------
def initial_fetch():
    print("[INIT] Fetching initial data...")

    for _ in range(10):
        if update_cache():
            print("[INIT] Success")
            return
        time.sleep(2)

    print("[INIT] Using fallback state")


# -----------------------
# BACKGROUND LOOP
# -----------------------
def background_loop():
    while True:
        update_cache()
        time.sleep(CACHE_TIME)


# Start system
initial_fetch()
threading.Thread(target=background_loop, daemon=True).start()


# -----------------------
# API ROUTE
# -----------------------
@app.route("/")
def total_players():
    with LOCK:
        return jsonify(CACHE["data"])
