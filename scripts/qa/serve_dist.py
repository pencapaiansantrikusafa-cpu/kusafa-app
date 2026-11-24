#!/usr/bin/env python3
"""Server statis kecil untuk menguji hasil build `dist/` (SPA: semua rute -> index.html)."""
import http.server
import os
import socketserver
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dist"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4173


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        jalur = self.translate_path(self.path)
        if not os.path.exists(jalur) or os.path.isdir(jalur):
            if "." not in os.path.basename(self.path):
                self.path = "/index.html"
        return super().do_GET()

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving {ROOT} on http://127.0.0.1:{PORT}")
    httpd.serve_forever()