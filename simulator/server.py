"""
Local Web Server for Dark Pattern Test Simulator Scenarios (Port 8080)
Serves 14 ground-truth controlled scenarios with Dark / Clean variants.
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent / "scenarios"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

def run_server():
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"⚡ Dark Pattern Simulator Web Server running on http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
