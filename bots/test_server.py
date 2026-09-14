"""
SentinelNet - Local Test Server
A lightweight Flask web application providing dummy endpoints for bot traffic generation research.
"""

import argparse
import time
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

HOME_HTML = """
<!DOCTYPE html>
<html>
<head><title>SentinelNet Test Server</title></head>
<body>
    <h1>Welcome to SentinelNet Test Server</h1>
    <p>Status: Active</p>
    <ul>
        <li><a href="/api/data">API Data</a></li>
        <li><a href="/search?q=security">Search Example</a></li>
        <li><a href="/product/101">Product 101</a></li>
    </ul>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HOME_HTML)

@app.route("/api/data", methods=["GET"])
def api_data():
    return jsonify({
        "status": "success",
        "timestamp": time.time(),
        "items": [
            {"id": 1, "name": "Telemetry Node Alpha", "type": "sensor"},
            {"id": 2, "name": "Telemetry Node Beta", "type": "gateway"},
            {"id": 3, "name": "AI Classifier Service", "type": "model"}
        ]
    })

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        username = data.get("username", "guest")
        return jsonify({"status": "authenticated", "user": username, "token": "mock-jwt-token-12345"})
    return jsonify({"status": "login_page", "methods_supported": ["POST"]})

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "default")
    return jsonify({
        "query": query,
        "results_count": len(query) * 3,
        "results": [f"Result for '{query}' #{i+1}" for i in range(3)]
    })

@app.route("/product/<int:item_id>", methods=["GET"])
def product(item_id):
    return jsonify({
        "product_id": item_id,
        "title": f"Security Suite SKU #{item_id}",
        "in_stock": True,
        "price": round(19.99 + (item_id % 10), 2)
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelNet Test Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    print(f"[*] Starting SentinelNet Test Server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
