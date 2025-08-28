from flask import Flask, jsonify, render_template, request
import os, time, socket, platform
from datetime import datetime

# IMPORTANT: point Flask to the top-level templates/static folders
app = Flask(__name__, template_folder="templates", static_folder="static")

REQUEST_COUNT = 0
START_TIME = time.time()

def get_basic_stats():
    info = {
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
        "image_tag": os.environ.get("IMAGE_TAG", "unknown"),
        "commit_sha": os.environ.get("GIT_COMMIT_SHA", "unknown"),
        "uptime_seconds": int(time.time() - START_TIME),
    }
    try:
        import psutil
        info.update({
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent
        })
    except Exception:
        info.update({"cpu": None, "memory": None})
    return info

@app.before_request
def count_requests():
    global REQUEST_COUNT
    if request.path.startswith("/static"):
        return
    REQUEST_COUNT += 1

# DASHBOARD PAGE (HTML)
@app.route("/")
def index():
    return render_template("index.html")

# JSON APIs used by the dashboard
@app.route("/api/health")
def api_health():
    return jsonify(status="ok"), 200

@app.route("/api/stats")
def api_stats():
    stats = get_basic_stats()
    stats.update({
        "requests": REQUEST_COUNT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "ok",
    })
    return jsonify(stats), 200

# Back-compat for older checks
@app.route("/health")
def health():
    return jsonify(status="ok"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
