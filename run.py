#!/usr/bin/env python3
"""run.py — start a local HTTP server, killing whatever is already on the port.
Serves data/*.json with gzip compression so local testing mirrors GitHub Pages CDN."""
import gzip, os, shutil, signal, subprocess, sys, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

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

    def should_gzip_json(self):
        path = urlsplit(self.path).path
        return (path.startswith("/data/") and path.endswith(".json")
                and "gzip" in self.headers.get("Accept-Encoding", ""))

    def send_gzip_json_headers(self, fs_path):
        if not os.path.exists(fs_path):
            self.send_error(404)
            return False
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.end_headers()
        return True

    def do_HEAD(self):
        if self.should_gzip_json():
            self.send_gzip_json_headers(self.translate_path(self.path))
            return
        return super().do_HEAD()

    def do_GET(self):
        if not self.should_gzip_json():
            return super().do_GET()

        fs_path = self.translate_path(self.path)
        if not self.send_gzip_json_headers(fs_path):
            return
        try:
            with open(fs_path, "rb") as src:
                with gzip.GzipFile(fileobj=self.wfile, mode="wb", compresslevel=6) as gz:
                    shutil.copyfileobj(src, gz, length=1024 * 1024)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_head(self):
        return super().send_head()

    def copyfile(self, source, outputfile):
        try:
            return super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            pass

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

