from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faith&limit=50"

CACHE = {
    "value": None,
    "last_update": 0
}

CACHE_TIME = 310  # seconds


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

            total = 0

            for s in servers:

                print("SERVER:", s)

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

            # only overwrite cache on success
            CACHE["value"] = new_value
            CACHE["last_update"] = now

            print("CACHE UPDATED:", CACHE)

        except Exception as e:

            print("CACHE UPDATE ERROR:", e)

            # keep last known good value
            pass

    return CACHE["value"]


# -----------------------
# MAIN ROUTE
# -----------------------
@app.route("/")
def total_players():

    value = get_cached_value()

    # first startup and API unavailable
    if value is None:
        return jsonify({"value": "updating"})

    return jsonify({"value": value})


# -----------------------
# DEBUG ROUTE
# -----------------------
@app.route("/debug")
def debug():

    try:

        r = requests.get(API_URL, timeout=15)

        return jsonify({
            "status_code": r.status_code,
            "raw_response": r.json()
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


# -----------------------
# CACHE DEBUG ROUTE
# -----------------------
@app.route("/cache")
def cache_debug():

    return jsonify(CACHE)


# -----------------------
# HEALTHCHECK
# -----------------------
@app.route("/health")
def health():

    return jsonify({
        "status": "online"
    })


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
