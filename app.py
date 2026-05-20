from flask import Flask, Response
import requests
import json
import time
import os

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faith&limit=50"

CACHE = {
    "value": 0,
    "last_update": 0
}

CACHE_TIME = 310  # seconds

# Persistent session for better stability
requests_session = requests.Session()


# -----------------------
# SAFE JSON RESPONSE
# -----------------------
def safe_json(value):
    """
    ALWAYS return valid JSON with a value field.
    """

    try:
        value = int(value)
    except Exception:
        value = 0

    return Response(
        json.dumps({"value": value}),
        status=200,
        mimetype="application/json"
    )


# -----------------------
# FETCH TOTAL PLAYERS
# -----------------------
def fetch_total():

    for attempt in range(3):

        try:

            print(f"Fetching API (attempt {attempt + 1})")

            r = requests_session.get(API_URL, timeout=15)

            print("STATUS:", r.status_code)

            r.raise_for_status()

            # Safely parse JSON
            try:
                data = r.json()

            except Exception:

                print("INVALID JSON RESPONSE")
                print(r.text[:500])

                raise Exception("Bad JSON from API")

            servers = data.get("servers", [])

            print("SERVERS FOUND:", len(servers))

            # Empty list = failure
            if not servers:
                raise Exception("Empty server list")

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
# CACHE LOGIC
# -----------------------
def get_cached_value():

    now = time.time()

    # Only refresh cache if expired
    if now - CACHE["last_update"] > CACHE_TIME:

        try:

            new_value = fetch_total()

            CACHE["value"] = int(new_value)
            CACHE["last_update"] = now

            print("CACHE UPDATED:", CACHE)

        except Exception as e:

            print("CACHE UPDATE ERROR:", e)

            # Keep last known good value

    return CACHE["value"]


# -----------------------
# MAIN ENDPOINT
# -----------------------
@app.route("/")
def total_players():

    try:

        value = get_cached_value()

        if value is None:
            value = 0

        return safe_json(value)

    except Exception as e:

        print("ROUTE ERROR:", e)

        return safe_json(0)


# -----------------------
# HEALTH CHECK
# -----------------------
@app.route("/health")
def health():

    return safe_json(1)


# -----------------------
# DEBUG
# -----------------------
@app.route("/debug")
def debug():

    try:

        r = requests_session.get(API_URL, timeout=15)

        return Response(
            r.text,
            status=200,
            mimetype="application/json"
        )

    except Exception as e:

        print("DEBUG ERROR:", e)

        return safe_json(0)


# -----------------------
# GLOBAL ERROR HANDLER
# -----------------------
@app.errorhandler(Exception)
def handle_error(e):

    print("GLOBAL ERROR:", e)

    return safe_json(0)


# -----------------------
# STARTUP
# -----------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
