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

    def handle_one_request(self):
        # Browser yang menutup koneksi lebih awal (navigasi cepat, render putus) memicu
        # BrokenPipeError/ConnectionResetError. Itu normal untuk server uji; jangan kotori log.
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True


socketserver.TCPServer.allow_reuse_address = True


class Server(socketserver.TCPServer):
    # Koneksi yang ditutup browser saat server masih menulis (mis. flush di finish())
    # memunculkan BrokenPipeError/ConnectionResetError. Abaikan, jangan cetak traceback.
    def handle_error(self, request, client_address):
        import sys as _sys
        exc = _sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


with Server(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving {ROOT} on http://127.0.0.1:{PORT}")
    httpd.serve_forever()