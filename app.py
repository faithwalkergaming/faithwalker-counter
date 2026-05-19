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

            # Prevent wiping cache with empty API results
            if len(servers) == 0:
                raise Exception("No servers returned from API")

            total = 0

            for s in servers:

                try:

                    player_count = int(s.get("playerAmount", 0))

                    print("PLAYER COUNT:", player_count)

                    total += player_count

                except Exception as e:

                    print("PARSE ERROR:", e)

            print("TOTAL PLAYERS:", total)

            return total

        except Exception as e:

            print("FETCH ERROR:", e)

            time.sleep(2)

    raise Exception("API failed after 3 retries")


# -----------------------
# UPDATE CACHE IF NEEDED
# -----------------------
def get_cached_value():

    now = time.time()

    if (
        CACHE["value"] is None or
        now - CACHE["last_update"] > CACHE_TIME
    ):

        try:

            new_value = fetch_total()

            # Only overwrite cache on successful valid fetch
            CACHE["value"] = new_value
            CACHE["last_update"] = now

            print("CACHE UPDATED:", CACHE)

        except Exception as e:

            print("CACHE UPDATE ERROR:", e)

            # Keep last known good value
            pass

    return CACHE["value"]


# -----------------------
# MAIN ROUTE
# -----------------------
@app.route("/")
def total_players():

    value = get_cached_value()

    # Startup state if API unavailable
    if value is None:
        return jsonify({"value": "updating"})

    return jsonify({"value": value})


# -----------------------
# HEALTHCHECK
# -----------------------
@app.route("/health")
def health():

    return jsonify({
        "status": "online"
    })


# -----------------------
# CACHE DEBUG ROUTE
# -----------------------
@app.route("/cache")
def cache():

    return jsonify(CACHE)


# -----------------------
# DEBUG ROUTE
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

        return jsonify({
            "error": str(e)
        })


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    app.run()
