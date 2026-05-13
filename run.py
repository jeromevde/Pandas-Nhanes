#!/usr/bin/env python3
"""run.py — start a local HTTP server, killing whatever is already on the port.
Serves data/*.json with gzip compression so local testing mirrors GitHub Pages CDN."""
import gzip, io, os, signal, subprocess, sys, time
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def kill_port(port: int):
    try:
        out = subprocess.check_output(["lsof", "-ti", f"tcp:{port}"], text=True).strip()
        for pid in out.splitlines():
            os.kill(int(pid), signal.SIGKILL)
        print(f"Killed process(es) on port {port}.")
    except subprocess.CalledProcessError:
        pass  # nothing was listening


class GzipHandler(SimpleHTTPRequestHandler):
    """Transparently gzip JSON responses when the client supports it."""

    def send_head(self):
        # Only gzip .json files whose path starts with /data/
        path = self.translate_path(self.path)
        if (self.path.startswith("/data/") and self.path.endswith(".json")
                and "gzip" in self.headers.get("Accept-Encoding", "")):
            try:
                with open(path, "rb") as f:
                    raw = f.read()
                buf = io.BytesIO()
                with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz:
                    gz.write(raw)
                data = buf.getvalue()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                return io.BytesIO(data)
            except FileNotFoundError:
                self.send_error(404)
                return None
        return super().send_head()

    def log_message(self, fmt, *args):
        # Suppress per-request noise; show only errors and first-byte of large files
        if args and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)


class ReuseAddrServer(HTTPServer):
    allow_reuse_address = True


kill_port(PORT)
time.sleep(0.2)  # let OS release the port

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Serving at http://localhost:{PORT}  (gzip enabled for data/*.json)")
ReuseAddrServer(("", PORT), GzipHandler).serve_forever()

