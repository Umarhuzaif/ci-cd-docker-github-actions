
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify(message="Hello from CI/CD pipeline(DevOPs!"), 200

@app.route("/health")
def health():
    return jsonify(status="ok"), 200

if __name__ == "__main__":
    # Bind to 0.0.0.0 so it's reachable from outside the container
    app.run(host="0.0.0.0", port=5000)
