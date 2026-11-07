"""hud_server.py - tiny local web server for the holographic HUD (no extra packages)."""
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .. import config
from . import state as hud_state

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/state":
            lv = int(parse_qs(u.query).get("lv", ["0"])[0] or 0)
            self._send(200, "application/json", json.dumps(hud_state.snapshot(lv)).encode())
        elif u.path in ("/", "/index.html"):
            import re
            name = re.sub(r"[^\w \-]", "", config.load()["name"]) or "Jarvis"
            with open(os.path.join(HERE, "jarvis_workplace.html"), encoding="utf-8") as f:
                html = f.read()
            # show YOUR name on the HUD (file on disk is not modified)
            html = html.replace("JARVIS", name.upper()).replace("Jarvis", name)
            self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))
        else:
            self._send(404, "text/plain", b"not found")


def start(open_browser=True):
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"[HUD] port {PORT} busy - HUD already running? open http://127.0.0.1:{PORT}")
        return None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    hud_state.start_background()
    url = f"http://127.0.0.1:{PORT}"
    print(f"[HUD] Holographic HUD live at {url}")
    if open_browser:
        webbrowser.open(url)
    return srv
