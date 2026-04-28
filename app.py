from flask import Flask, jsonify
import requests
import time
import threading

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"

CACHE = {
    "timestamp": 0,
    "data": {"count": 0, "trend": "➖"},
    "last_count": None
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
    if total is None:
        return False

    with LOCK:
        last = CACHE["last_count"]

        if last is None:
            trend = "➖"
        elif total > last:
            trend = "▲"
        elif total < last:
            trend = "▼"
        else:
            trend = "➖"

        CACHE["data"] = {
            "count": total,
            "trend": trend
        }

        CACHE["last_count"] = total
        CACHE["timestamp"] = time.time()

        print(f"[UPDATE] {total} {trend}")

    return True


# -----------------------
# STARTUP RETRY LOOP
# -----------------------
def initial_fetch():
    print("[INIT] Fetching initial data...")

    for _ in range(10):  # try up to 10 times
        success = update_cache()
        if success:
            print("[INIT] Success")
            return
        time.sleep(2)

    print("[INIT] Failed to fetch initial data after retries")


# -----------------------
# BACKGROUND LOOP
# -----------------------
def background_loop():
    while True:
        update_cache()
        time.sleep(CACHE_TIME)


# 🔥 Run initial fetch with retries
initial_fetch()

# Start background updates
threading.Thread(target=background_loop, daemon=True).start()


# -----------------------
# API ROUTE
# -----------------------
@app.route("/")
def total_players():
    with LOCK:
        return jsonify(CACHE["data"])
