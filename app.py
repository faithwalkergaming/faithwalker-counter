from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faith&limit=50"

CACHE = {
    "value": None,
    "last_update": 0
}

CACHE_TIME = 330  # seconds


# -----------------------
# FETCH TOTAL PLAYERS
# -----------------------
def fetch_total():

    for attempt in range(3):

        try:
            print(f"Fetching API (attempt {attempt + 1})")

            r = requests.get(API_URL, timeout=15)

            print("STATUS:", r.status_code)

            r.raise_for_status()

            data = r.json()

            servers = data.get("servers", [])

            print("SERVERS FOUND:", len(servers))

            # If API returns empty, treat as failure (do NOT overwrite cache)
            if not servers:
                raise Exception("Empty server list returned")

            total = 0

            for s in servers:
                try:
                    total += int(s.get("playerAmount", 0))
                except Exception as e:
                    print("PARSE ERROR:", e)

            print("TOTAL PLAYERS:", total)

            return total

        except Exception as e:
            print("FETCH ERROR:", e)
            time.sleep(2)

    raise Exception("API failed after retries")


# -----------------------
# CACHE HANDLING
# -----------------------
def get_cached_value():

    now = time.time()

    if (
        CACHE["value"] is None or
        now - CACHE["last_update"] > CACHE_TIME
    ):

        try:
            new_value = fetch_total()

            # only update cache if fetch succeeded
            CACHE["value"] = new_value
            CACHE["last_update"] = now

            print("CACHE UPDATED:", CACHE)

        except Exception as e:
            print("CACHE UPDATE ERROR:", e)
            # keep last good value (do nothing)

    return CACHE["value"]


# -----------------------
# MAIN ENDPOINT (DISCORD SAFE)
# -----------------------
@app.route("/")
def total_players():

    value = get_cached_value()

    # IMPORTANT: always return an integer for Discord compatibility
    if value is None:
        value = 0

    return jsonify({"value": int(value)})


# -----------------------
# HEALTH CHECK
# -----------------------
@app.route("/health")
def health():
    return jsonify({"status": "online"})


# -----------------------
# DEBUG (optional)
# -----------------------
@app.route("/debug")
def debug():

    try:
        r = requests.get(API_URL, timeout=15)
        return jsonify({
            "status_code": r.status_code,
            "response": r.json()
        })
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run()
