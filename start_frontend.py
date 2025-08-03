"""
HLAS Insurance Frontend Server

Simple HTTP server to serve the frontend files for testing.
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

def main():
    """Start the frontend server"""
    print("🌐 Starting HLAS Insurance Frontend Server...")
    print("=" * 50)
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    PORT = 3000
    
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🎯 Frontend available at: http://localhost:{PORT}")
        print(f"📁 Serving files from: {frontend_dir}")
        print()
        print("Make sure the API server is running on http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Open browser automatically
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    main()
