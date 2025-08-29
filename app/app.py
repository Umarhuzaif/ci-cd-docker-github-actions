from flask import Flask, jsonify, render_template, request
import os, time, socket, platform
from datetime import datetime
from collections import deque

try:
    import psutil
except ImportError:
    psutil = None

# Point Flask to top-level template/static folders
app = Flask(__name__, template_folder="templates", static_folder="static")

# Globals
START_TIME = time.time()
REQUEST_COUNT = 0
LOGS = deque(maxlen=100)   # keep last 100 requests


def get_basic_stats():
    info = {
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
        "image_tag": os.environ.get("IMAGE_TAG", "unknown"),
        "commit_sha": os.environ.get("GIT_COMMIT_SHA", "unknown"),
        "uptime_seconds": int(time.time() - START_TIME),
    }
    if psutil:
        info.update({
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent
        })
    else:
        info.update({"cpu": None, "memory": None})
    return info


@app.before_request
def count_requests():
    global REQUEST_COUNT
    if request.path.startswith("/static"):
        return
    REQUEST_COUNT += 1
    LOGS.appendleft({
        "path": request.path,
        "method": request.method,
        "time": datetime.utcnow().isoformat() + "Z"
    })


# -------------------------
# Routes
# -------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def api_health():
    stats = get_basic_stats()
    return jsonify({
        "ok": True,
        "uptime_s": stats["uptime_seconds"],
        "requests_served": REQUEST_COUNT,
        "cpu": stats["cpu"],
        "memory": stats["memory"],
        "utc_time": datetime.utcnow().isoformat() + "Z"
    })


@app.route("/api/stats")
def api_stats():
    stats = get_basic_stats()
    stats.update({
        "requests": REQUEST_COUNT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "ok",
    })
    return jsonify(stats)


@app.route("/api/logs")
def api_logs():
    return jsonify(list(LOGS))


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
