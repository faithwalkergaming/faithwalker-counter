from flask import Flask, jsonify
import requests
import time
import random

app = Flask(__name__)

FW_API = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"
STEAM_API = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=123456"

CACHE = {"timestamp": 0, "data": {"count": 0}}
CACHE_TIME = 310


def get_fw_total():
    try:
        r = requests.get(FW_API, timeout=5)
        r.raise_for_status()
        servers = r.json().get("servers", [])

        return sum(
            int(s.get("playerAmount", 0))
            for s in servers
            if int(s.get("playerAmount", 0)) > 0
        )
    except:
        return 0


def get_steam_players():
    try:
        r = requests.get(STEAM_API, timeout=5)
        r.raise_for_status()
        return int(r.json().get("response", {}).get("player_count", 0))
    except:
        return 0


@app.route("/")
def total_players():
    now = time.time()

    # Always return cached if available (prevents timeouts)
    if now - CACHE["timestamp"] < CACHE_TIME:
        return jsonify(CACHE["data"])

    try:
        fw_total = get_fw_total()
        steam_players = get_steam_players()

        variation = random.uniform(0.18, 0.20)
        steam_addition = int(steam_players * variation)

        total = fw_total + steam_addition

        CACHE["data"] = {"count": total}
        CACHE["timestamp"] = now

    except Exception as e:
        print("Error:", e)

    return jsonify(CACHE["data"])
