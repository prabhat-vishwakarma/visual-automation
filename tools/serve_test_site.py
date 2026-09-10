"""Serves the authorized local test site for end-to-end runs.

Usage:
    .venv/bin/python -m tools.serve_test_site [--port 8800]
"""

from __future__ import annotations

import argparse
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "test_site"
EXPECTED_CODE = "K7Q2P"


class TestSiteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._serve_index()
        elif self.path == "/challenge.png":
            self._serve_file("challenge.png", "image/png")
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _serve_index(self) -> None:
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        body = html.replace("{{CODE}}", EXPECTED_CODE).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, name: str, content_type: str) -> None:
        path = SITE_DIR / name
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("  %s\n" % (fmt % args))


def serve(port: int, host: str = "127.0.0.1") -> HTTPServer:
    server = HTTPServer((host, port), TestSiteHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def site_url_of(server: HTTPServer) -> str:
    host, port = server.server_address[:2]
    return f"http://{host}:{port}/"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8800)
    args = parser.parse_args()
    print(f"Serving authorized test site at http://127.0.0.1:{args.port}/ (Ctrl+C to stop)")
    server = HTTPServer(("127.0.0.1", args.port), TestSiteHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()