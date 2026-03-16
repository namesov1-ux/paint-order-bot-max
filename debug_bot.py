# debug_bot.py
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Debug bot works!"})

@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/webhook', methods=['POST'])
def webhook():
    return jsonify({"status": "ok", "received": True})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"Starting debug bot on port {port}")
    app.run(host='0.0.0.0', port=port)