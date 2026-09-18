#!/usr/bin/env python
"""Serve the offline wiki (build/site) over HTTP so it works as a multi-page
site with working search on desktop and phone.

    python serve.py            # http://localhost:8000
    python serve.py 8080

On the phone (same Wi-Fi or Tailscale), open the printed LAN URL. For a fully
offline phone setup, run the same command under Termux on the device and open
http://localhost:8000.
"""
import os
import sys
import socket
import http.server
import socketserver

HERE = os.path.dirname(os.path.abspath(__file__))   # .../pipeline
SITE = os.path.join(os.path.dirname(HERE), "build", "site")


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    if not os.path.isdir(SITE):
        print("site/ not found. Build it first:  python build_study.py")
        return 1
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(SITE)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving {SITE}")
        print(f"  desktop: http://localhost:{port}/")
        print(f"  phone:   http://{lan_ip()}:{port}/   (same network)")
        print("Ctrl+C to stop")
        httpd.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
