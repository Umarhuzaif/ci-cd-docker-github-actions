import os, time, platform, socket
from datetime import datetime, timezone
from collections import deque
from flask import Flask, render_template, jsonify, request

try:
    import psutil
except Exception:
    psutil = None

# templates/ and static/ are inside this same "app" folder
app = Flask(__name__, template_folder="templates", static_folder="static")

APP_START = time.time()
REQUESTS_SERVED = 0
LOGS = deque(maxlen=120)
CPU_HISTORY = deque(maxlen=60)   # ~5 minutes at 5s poll
MEM_HISTORY = deque(maxlen=60)

def now_utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")

def uptime_seconds():
    return int(time.time() - APP_START)

def get_cpu_mem():
    if psutil is None:
        return None, None
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    CPU_HISTORY.append(cpu)
    MEM_HISTORY.append(mem)
    return cpu, mem

def log_line(path, status):
    # "33 14:44:24" style like your screenshot (day hour:minute:second UTC)
    LOGS.appendleft({
        "ts": datetime.utcnow().strftime("%d %H:%M:%S"),
        "path": path,
        "status": status
    })

@app.after_request
def after(resp):
    global REQUESTS_SERVED
    if not request.path.startswith("/static"):
        REQUESTS_SERVED += 1
        try:
            log_line(request.path, resp.status_code)
        except Exception:
            pass
    return resp

@app.route("/")
def home():
    return render_template(
        "index.html",
        app_env=os.getenv("APP_ENV", "PROD").upper(),
        python_version=platform.python_version(),
        host=socket.gethostname(),
    )

@app.get("/api/health")
def health():
    cpu, mem = get_cpu_mem()
    return jsonify({
        "ok": True,
        "uptime_s": uptime_seconds(),
        "requests_served": REQUESTS_SERVED,
        "cpu": cpu,
        "memory": mem,
        "utc_time": now_utc_iso()
    })

@app.get("/api/stats")
def stats():
    cpu, mem = get_cpu_mem()
    return jsonify({
        "cpu": cpu,
        "memory": mem,
        "cpu_hist": list(CPU_HISTORY),
        "mem_hist": list(MEM_HISTORY)
    })

@app.get("/api/meta")
def meta():
    return jsonify({
        "git": {
           "branch": os.getenv("GIT_BRANCH","main"),
           "commit": os.getenv("GIT_COMMIT","n/a"),
           "author": os.getenv("GIT_AUTHOR","n/a"),
           "date": os.getenv("GIT_COMMIT_DATE","n/a")
        },
        "stages": {  # defaults show green; your CI can override via env
            "build":  os.getenv("STAGE_BUILD",  "Succeeded"),
            "test":   os.getenv("STAGE_TEST",   "Succeeded"),
            "deploy": os.getenv("STAGE_DEPLOY", "Succeeded")
        },
        "container": {
            "id": socket.gethostname(),
            "uptime_s": uptime_seconds(),
            "port_mappings": os.getenv("PORT_MAPPINGS","5000->5000/tcp")
        },
        "system": {
            "python": platform.python_version(),
            "host": socket.gethostname(),
            "utc_time": now_utc_iso()
        }
    })

@app.get("/api/logs")
def recent_logs():
    return jsonify(list(LOGS))

# legacy
@app.get("/health")
def simple_health():
    return jsonify(status="ok")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
