from flask import Flask, Response
import requests
import json
import time
import os
import threading

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faith&limit=50"

CACHE = {
    "value": 0,
    "last_update": 0,
    "updating": False
}

CACHE_TIME = 60

# -----------------------
# REQUEST SESSION
# -----------------------
requests_session = requests.Session()

requests_session.headers.update({
    "User-Agent": "FaithWalkerCounter/1.0"
})

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry_strategy)

requests_session.mount("https://", adapter)
requests_session.mount("http://", adapter)


# -----------------------
# SAFE JSON RESPONSE
# -----------------------
def safe_json(value):

    try:
        value = int(value)
    except:
        value = 0

    return Response(
        json.dumps({"value": str(value)}),
        status=200,
        mimetype="application/json"
    )


# -----------------------
# FETCH TOTAL PLAYERS
# -----------------------
def fetch_total():

    print("FETCHING API")

    r = requests_session.get(API_URL, timeout=10)

    print("STATUS:", r.status_code)

    r.raise_for_status()

    data = r.json()

    servers = data.get("servers", [])

    if not servers:
        raise Exception("Empty server list")

    total = 0

    for s in servers:
        total += int(s.get("playerAmount", 0))

    print("TOTAL:", total)

    return total


# -----------------------
# BACKGROUND CACHE UPDATE
# -----------------------
def update_cache():

    if CACHE["updating"]:
        return

    CACHE["updating"] = True

    try:

        new_value = fetch_total()

        CACHE["value"] = new_value
        CACHE["last_update"] = time.time()

        print("CACHE UPDATED:", CACHE)

    except Exception as e:

        print("CACHE UPDATE ERROR:", e)

    finally:

        CACHE["updating"] = False


# -----------------------
# GET VALUE
# -----------------------
def get_value():

    now = time.time()

    # Trigger background refresh if cache expired
    if now - CACHE["last_update"] > CACHE_TIME:

        threading.Thread(
            target=update_cache,
            daemon=True
        ).start()

    # ALWAYS instantly return cached value
    return CACHE["value"]


# -----------------------
# MAIN ENDPOINT
# -----------------------
@app.route("/")
def total_players():

    try:

        return safe_json(get_value())

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

    return Response(
        json.dumps(CACHE),
        status=200,
        mimetype="application/json"
    )


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
