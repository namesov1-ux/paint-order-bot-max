import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Hello from test app!"})

@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting test app on port {port}")
    app.run(host='0.0.0.0', port=port)
