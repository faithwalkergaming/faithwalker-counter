from flask import Flask, jsonify
import requests

app = Flask(__name__)

API_URL = "https://api.gametools.network/bf6/servers/?name=faithwalker&limit=50"


@app.route("/")
def total_players():
    try:
        r = requests.get(API_URL, timeout=10)
        data = r.json()

        servers = data.get("servers", [])

        total = 0

        for s in servers:
            players = s.get("playerAmount", 0)

            try:
                total += int(players)
            except:
                pass

        return jsonify({"value": total})

    except Exception as e:
        return jsonify({"value": "ERROR", "debug": str(e)})
