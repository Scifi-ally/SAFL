import csv
import json
import os
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
FINAL = ROOT / "data" / "final.csv"
PORT = 8000
STEPS = ["fetch.py", "normalize.py", "classify.py", "dedupe.py"]
STEP_NAMES = [Path(s).stem for s in STEPS] + ["export"]

lock = threading.Lock()
last_run = {"at": None, "ok": None}


def load_rows():
    if not FINAL.exists():
        return []
    with FINAL.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "state": r.get("state", ""),
            "title": r.get("title", ""),
            "date": r.get("date", ""),
            "date_precision": r.get("date_precision", ""),
            "source_name": r.get("source_name", ""),
            "url": r.get("source_url") or r.get("link", ""),
            "summary": r.get("summary", ""),
            "category": r.get("category", ""),
            "duplicate_count": r.get("duplicate_count") or "1",
            "also_reported_by": r.get("also_reported_by", ""),
        }
        for r in rows
    ]


def export_json():
    rows = load_rows()
    DOCS.mkdir(exist_ok=True)
    (DOCS / "data.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return len(rows)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            self.send_json(
                {
                    "steps": STEP_NAMES,
                    "running": lock.locked(),
                    "last_run": last_run,
                }
            )
        elif path == "/api/data":
            self.send_json(load_rows())
        elif path == "/api/run":
            self.run_pipeline()
        else:
            super().do_GET()

    def sse(self, event, data):
        if not getattr(self, "alive", True):
            return
        try:
            msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            self.alive = False 

    def run_pipeline(self):
        self.alive = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        if not lock.acquire(blocking=False):
            self.sse("fail", {"message": "a run is already in progress"})
            return

        ok = True
        try:
            env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            for name in STEPS:
                stem = Path(name).stem
                script = ROOT / name
                if not script.exists():
                    self.sse("log", {"line": f"[skip] {name} not found"})
                    self.sse("step", {"name": stem, "status": "skipped"})
                    continue

                self.sse("step", {"name": stem, "status": "running"})
                self.sse("log", {"line": f"$ python {name}"})
                proc = subprocess.Popen(
                    [sys.executable, "-u", str(script)],
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
                for line in proc.stdout:
                    self.sse("log", {"line": line.rstrip()})
                code = proc.wait()

                if code != 0:
                    ok = False
                    self.sse("step", {"name": stem, "status": "error"})
                    self.sse("fail", {"message": f"{name} exited with code {code}"})
                    break
                self.sse("step", {"name": stem, "status": "done"})

            if ok:
                self.sse("step", {"name": "export", "status": "running"})
                n = export_json()
                self.sse("log", {"line": f"[export] wrote {n} records to docs/data.json"})
                self.sse("step", {"name": "export", "status": "done"})
                self.sse("done", {"records": n})
        except Exception as exc:  
            ok = False
            self.sse("fail", {"message": f"server error: {exc}"})
        finally:
            last_run["at"] = time.strftime("%Y-%m-%d %H:%M")
            last_run["ok"] = ok
            lock.release()


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"dashboard: http://localhost:{PORT}  (ctrl+c to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")