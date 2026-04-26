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

        total = sum(
            int(s.get("playerAmount", 0))
            for s in servers
            if int(s.get("playerAmount", 0)) > 0
        )

        return jsonify({"count": total})

    except Exception as e:
        print("Error:", e)
        return jsonify({"count": 0})
