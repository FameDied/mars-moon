#!/usr/bin/env python3
"""
ATLAS-X Mission Cockpit Preview Launcher
Serves the Swiss/NASA 1975 Graphic Standards Mission Cockpit preview locally and opens it in your default browser.
"""

import http.server
import socketserver
import webbrowser
from pathlib import Path
import sys

PORT = 8085
DIRECTORY = Path(__file__).resolve().parent.parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

def main():
    print(f"==================================================================")
    print(f" ATLAS-X // NASA 1975 GRAPHIC STANDARDS MISSION COCKPIT PREVIEW")
    print(f"==================================================================")
    print(f" Serving directory: {DIRECTORY}")
    print(f" Local URL:         http://localhost:{PORT}/atlas_x_preview.html")
    print(f" Press Ctrl+C to terminate the preview server.")
    print(f"==================================================================")
    
    webbrowser.open(f"http://localhost:{PORT}/atlas_x_preview.html")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nPreview server stopped cleanly.")
            sys.exit(0)

if __name__ == "__main__":
    main()
