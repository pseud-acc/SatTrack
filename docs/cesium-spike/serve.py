"""Serve the Cesium spike page (roadmap 3.1) with a published objects dataset, as the app delivers it.

    python docs/cesium-spike/serve.py <folder with objects.json.br/.gz> [port] [--lan]

GET / returns index.html, GET /worker.js the propagation worker; GET /data/<name>.json returns <name>.json.br or .gz from the folder with its
Content-Encoding, like app/core/data_files.py. Standard library only. --lan listens on every interface (to open the
page from a phone on the same network); the default is 127.0.0.1. Throwaway spike tooling, not part of the app.
"""
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = Path(__file__).with_name("index.html")


def make_handler(data_dir):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                return self._send(PAGE.read_bytes(), "text/html; charset=utf-8")
            if path == "/worker.js":
                return self._send(PAGE.with_name("worker.js").read_bytes(), "text/javascript; charset=utf-8")
            if path.startswith("/data/") and path.endswith(".json"):
                name = path[len("/data/"):-len(".json")]
                accepted = self.headers.get("Accept-Encoding", "")
                for enc, ext in (("br", ".json.br"), ("gzip", ".json.gz")):
                    f = data_dir / (name + ext)
                    if enc in accepted and "/" not in name and f.is_file():
                        return self._send(f.read_bytes(), "application/json", enc)
            self.send_error(404)

        def _send(self, body, content_type, encoding=None):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            if encoding:
                self.send_header("Content-Encoding", encoding)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data_dir, port = Path(args[0]), int(args[1]) if len(args) > 1 else 8765
    host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"
    print(f"Cesium spike on http://{host}:{port}/ with data from {data_dir}", flush=True)
    ThreadingHTTPServer((host, port), make_handler(data_dir)).serve_forever()
