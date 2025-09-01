import os, time, platform, socket
from datetime import datetime, timezone
from collections import deque
from flask import Flask, render_template, jsonify, request, abort
from hmac import compare_digest
from threading import Lock

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

# ---- Live CI state (updated by /api/ci/update) ----
CI_STATE = {
    "stages": {"build": None, "test": None, "deploy": None},
    "git": {"branch": None, "commit": None, "author": None, "date": None},
    "ts": None
}
_CI_LOCK = Lock()  # thread-safety for CI_STATE


def now_utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")


def uptime_seconds():
    return int(time.time() - APP_START)


def get_cpu_mem():
    if psutil is None:
        return None, None
    # short interval gives a real sample instead of “since last call”
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    CPU_HISTORY.append(cpu)
    MEM_HISTORY.append(mem)
    return cpu, mem


def log_line(path, status):
    # "29 07:44:44" style like your screenshot (day hour:minute:second UTC)
    LOGS.appendleft({
        "ts": datetime.utcnow().strftime("%d %H:%M:%S"),
        "path": path,
        "status": status
    })


def _valid_ci_token(req: request) -> bool:
    """Check shared secret from header or query against CI_UPDATE_TOKEN env."""
    expected = os.getenv("CI_UPDATE_TOKEN", "")
    provided = req.headers.get("X-CI-TOKEN", "") or req.args.get("token", "")
    return bool(expected) and compare_digest(provided, expected)


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
    # Prefer live CI state; fall back to env vars if not set yet
    with _CI_LOCK:
        stages = {
            "build":  CI_STATE["stages"]["build"]  or os.getenv("STAGE_BUILD",  "Succeeded"),
            "test":   CI_STATE["stages"]["test"]   or os.getenv("STAGE_TEST",   "Succeeded"),
            "deploy": CI_STATE["stages"]["deploy"] or os.getenv("STAGE_DEPLOY", "Succeeded"),
        }
        git = {
            "branch": CI_STATE["git"]["branch"] or os.getenv("GIT_BRANCH", "main"),
            "commit": CI_STATE["git"]["commit"] or os.getenv("GIT_COMMIT", "n/a"),
            "author": CI_STATE["git"]["author"] or os.getenv("GIT_AUTHOR", "n/a"),
            "date":   CI_STATE["git"]["date"]   or os.getenv("GIT_COMMIT_DATE", "n/a"),
        }

    return jsonify({
        "git": git,
        "stages": stages,
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


@app.post("/api/ci/update")
def ci_update():
    """Secure webhook for CI to update pipeline + git info."""
    if not _valid_ci_token(request):
        abort(401, description="Unauthorized")

    data = request.get_json(silent=True) or {}

    with _CI_LOCK:
        # Accept stage updates: build/test/deploy (strings like "Running", "Succeeded", "Failed")
        for k in ("build", "test", "deploy"):
            v = data.get(k)
            if isinstance(v, str) and v:
                CI_STATE["stages"][k] = v

        # Accept git metadata: branch, commit (short SHA), author, date
        for k in ("branch", "commit", "author", "date"):
            v = data.get(k)
            if isinstance(v, str) and v:
                CI_STATE["git"][k] = v

        CI_STATE["ts"] = now_utc_iso()

    return jsonify({"ok": True, "ts": CI_STATE["ts"], "state": CI_STATE})


# legacy
@app.get("/health")
def simple_health():
    return jsonify(status="ok")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
