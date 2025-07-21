#!/usr/bin/env python3
"""
Unified web server module for LED Matrix Control Center
Serves both control interface and documentation through path-based routing
"""

import os
import sys
import http.server
import socketserver
import urllib.parse
import mimetypes
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
try:
    import requests
except ImportError:
    print("⚠️  requests library not found. API proxy functionality will be limited.")
    requests = None

@dataclass
class ServerConfig:
    port: int = 3000
    host: str = "localhost"
    control_path: str = "sites/control"
    docs_path: str = "sites/docs"
    api_proxy_port: int = 8080
    enable_cors: bool = True
    enable_caching: bool = True

class UnifiedMatrixWebServer:
    def __init__(self, port=3000):
        self.config = ServerConfig(port=port)
        self.sites_dir = Path(__file__).parent.parent / "sites"
        self.control_dir = self.sites_dir / "control"
        self.docs_dir = self.sites_dir / "docs"
        
        # Ensure directories exist
        if not self.control_dir.exists():
            print(f"❌ Control directory not found: {self.control_dir}")
        if not self.docs_dir.exists():
            print(f"❌ Documentation directory not found: {self.docs_dir}")
    
    def create_landing_page(self):
        """Create the navigation landing page HTML"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LED Matrix Control Center</title>
    <style>
        :root {
            --primary: #1a1a2e;
            --secondary: #16213e;
            --accent: #0f3460;
            --highlight: #e94560;
            --text: #f1f1f1;
            --text-muted: #a0a0a0;
            --success: #4ade80;
            --warning: #fbbf24;
            --error: #ef4444;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .landing-container {
            max-width: 800px;
            padding: 40px;
            text-align: center;
        }

        .landing-header {
            margin-bottom: 50px;
        }

        .landing-header h1 {
            font-size: 3rem;
            margin-bottom: 15px;
            background: linear-gradient(45deg, var(--highlight), #ff6b9d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .landing-header p {
            font-size: 1.2rem;
            color: var(--text-muted);
        }

        .interface-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }

        .interface-card {
            background: rgba(26, 26, 46, 0.8);
            border: 1px solid rgba(233, 69, 96, 0.3);
            border-radius: 15px;
            padding: 30px;
            transition: all 0.3s ease;
        }

        .interface-card:hover {
            border-color: rgba(233, 69, 96, 0.6);
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(233, 69, 96, 0.2);
        }

        .interface-card h2 {
            color: var(--highlight);
            font-size: 1.5rem;
            margin-bottom: 15px;
        }

        .interface-card p {
            color: var(--text-muted);
            margin-bottom: 25px;
            line-height: 1.6;
        }

        .interface-button {
            display: inline-block;
            background: var(--highlight);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .interface-button:hover {
            background: #d63384;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3);
        }

        .status-indicators {
            background: rgba(15, 52, 96, 0.3);
            border: 1px solid rgba(233, 69, 96, 0.2);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--warning);
            animation: pulse 2s infinite;
        }

        .status-dot.connected {
            background: var(--success);
        }

        .status-dot.error {
            background: var(--error);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @media (max-width: 768px) {
            .landing-header h1 {
                font-size: 2rem;
            }
            .interface-cards {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="landing-container">
        <header class="landing-header">
            <h1>🔥 LED Matrix Control Center</h1>
            <p>Choose your interface to get started</p>
        </header>
        
        <div class="interface-cards">
            <div class="interface-card control-card">
                <h2>🎮 Control Interface</h2>
                <p>Real-time matrix control, pattern generation, Arduino code generation, and system monitoring</p>
                <a href="/control" class="interface-button">Launch Control</a>
            </div>
            
            <div class="interface-card docs-card">
                <h2>📚 Documentation</h2>
                <p>Complete project guide, wiring diagrams, component specifications, and troubleshooting</p>
                <a href="/docs" class="interface-button">View Documentation</a>
            </div>
        </div>
        
        <div class="status-indicators">
            <div class="status-item">
                <span class="status-dot" id="controller-status"></span>
                <span>Python Controller Status</span>
            </div>
        </div>
    </div>

    <script>
        // Check controller status
        async function checkControllerStatus() {
            try {
                const response = await fetch('/api/status');
                const statusDot = document.getElementById('controller-status');
                if (response.ok) {
                    statusDot.className = 'status-dot connected';
                } else {
                    statusDot.className = 'status-dot error';
                }
            } catch (error) {
                document.getElementById('controller-status').className = 'status-dot error';
            }
        }

        // Check status on load and periodically
        checkControllerStatus();
        setInterval(checkControllerStatus, 5000);
    </script>
</body>
</html>"""

    def create_custom_handler(self):
        """Create custom HTTP request handler with routing"""
        server_instance = self
        
        class UnifiedRequestHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.handle_request()
            
            def do_POST(self):
                self.handle_request()
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_cors_headers()
                self.end_headers()
            
            def handle_request(self):
                """Route requests based on path"""
                parsed_path = urllib.parse.urlparse(self.path)
                path = parsed_path.path
                
                try:
                    if path == "/" or path == "":
                        self.serve_landing_page()
                    elif path.startswith("/control"):
                        self.serve_control_interface(path)
                    elif path.startswith("/docs"):
                        self.serve_docs_interface(path)
                    elif path.startswith("/api"):
                        self.proxy_api_request(path, parsed_path.query)
                    else:
                        self.serve_404()
                except Exception as e:
                    print(f"❌ Error handling request {path}: {e}")
                    self.serve_500(str(e))
            
            def serve_landing_page(self):
                """Serve the navigation landing page"""
                content = server_instance.create_landing_page()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            
            def serve_control_interface(self, path):
                """Serve files from control interface"""
                # Remove /control prefix and serve from control directory
                file_path = path[8:] if len(path) > 8 else "/"
                if file_path == "/" or file_path == "":
                    file_path = "/index.html"
                
                self.serve_static_file(server_instance.control_dir, file_path)
            
            def serve_docs_interface(self, path):
                """Serve files from documentation interface"""
                # Remove /docs prefix and serve from docs directory
                file_path = path[5:] if len(path) > 5 else "/"
                if file_path == "/" or file_path == "":
                    file_path = "/index.html"
                
                self.serve_static_file(server_instance.docs_dir, file_path)
            
            def serve_static_file(self, base_dir, file_path):
                """Serve static files with proper MIME types"""
                try:
                    # Security: prevent directory traversal
                    file_path = file_path.lstrip('/')
                    full_path = base_dir / file_path
                    
                    # Ensure the path is within the base directory
                    if not str(full_path.resolve()).startswith(str(base_dir.resolve())):
                        self.serve_404()
                        return
                    
                    if full_path.is_file():
                        # Determine MIME type
                        mime_type, _ = mimetypes.guess_type(str(full_path))
                        if mime_type is None:
                            mime_type = 'application/octet-stream'
                        
                        # Read and serve file
                        with open(full_path, 'rb') as f:
                            content = f.read()
                        
                        self.send_response(200)
                        self.send_header('Content-Type', mime_type)
                        self.send_cors_headers()
                        if server_instance.config.enable_caching:
                            self.send_header('Cache-Control', 'public, max-age=3600')
                        self.end_headers()
                        self.wfile.write(content)
                    else:
                        self.serve_404()
                        
                except Exception as e:
                    print(f"❌ Error serving static file {file_path}: {e}")
                    self.serve_500(str(e))
            
            def proxy_api_request(self, path, query):
                """Proxy API requests to the Python controller"""
                try:
                    # Remove /api prefix
                    api_path = path[4:]
                    if query:
                        api_path += f"?{query}"
                    
                    # Proxy to controller
                    controller_url = f"http://localhost:{server_instance.config.api_proxy_port}{api_path}"
                    
                    if self.command == 'GET':
                        response = requests.get(controller_url, timeout=10)
                    elif self.command == 'POST':
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)
                        response = requests.post(controller_url, data=post_data, 
                                               headers={'Content-Type': self.headers.get('Content-Type', 'application/json')},
                                               timeout=10)
                    else:
                        self.serve_404()
                        return
                    
                    # Forward response
                    self.send_response(response.status_code)
                    for header, value in response.headers.items():
                        if header.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                            self.send_header(header, value)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(response.content)
                    
                except requests.exceptions.ConnectionError:
                    self.serve_503("Python controller not running on port 8080")
                except requests.exceptions.Timeout:
                    self.serve_503("Controller request timeout")
                except Exception as e:
                    print(f"❌ API proxy error: {e}")
                    self.serve_500(str(e))
            
            def serve_404(self):
                """Serve custom 404 page"""
                content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found - LED Matrix Control Center</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #f1f1f1; text-align: center; padding: 50px; }
        .error-container { max-width: 600px; margin: 0 auto; }
        h1 { color: #e94560; font-size: 3rem; margin-bottom: 20px; }
        p { font-size: 1.2rem; margin-bottom: 30px; color: #a0a0a0; }
        .nav-links { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .nav-link { background: #e94560; color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; transition: all 0.3s ease; }
        .nav-link:hover { background: #d63384; transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist. Try one of these options:</p>
        <div class="nav-links">
            <a href="/" class="nav-link">🏠 Home</a>
            <a href="/control" class="nav-link">🎮 Control Interface</a>
            <a href="/docs" class="nav-link">📚 Documentation</a>
        </div>
    </div>
</body>
</html>"""
                self.send_response(404)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            
            def serve_500(self, error_msg):
                """Serve custom 500 error page"""
                content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Error - LED Matrix Control Center</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #f1f1f1; text-align: center; padding: 50px; }}
        .error-container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #ef4444; font-size: 3rem; margin-bottom: 20px; }}
        p {{ font-size: 1.2rem; margin-bottom: 30px; color: #a0a0a0; }}
        .error-details {{ background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 20px; margin: 20px 0; text-align: left; }}
        .nav-link {{ background: #e94560; color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; transition: all 0.3s ease; }}
        .nav-link:hover {{ background: #d63384; transform: translateY(-2px); }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>500 - Server Error</h1>
        <p>Something went wrong on our end. Please try again later.</p>
        <div class="error-details">
            <strong>Error:</strong> {error_msg}
        </div>
        <a href="/" class="nav-link">🏠 Return Home</a>
    </div>
</body>
</html>"""
                self.send_response(500)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            
            def serve_503(self, error_msg):
                """Serve service unavailable page"""
                content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Unavailable - LED Matrix Control Center</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #f1f1f1; text-align: center; padding: 50px; }}
        .error-container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #fbbf24; font-size: 3rem; margin-bottom: 20px; }}
        p {{ font-size: 1.2rem; margin-bottom: 30px; color: #a0a0a0; }}
        .help-box {{ background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 8px; padding: 20px; margin: 20px 0; text-align: left; }}
        .nav-link {{ background: #e94560; color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; transition: all 0.3s ease; }}
        .nav-link:hover {{ background: #d63384; transform: translateY(-2px); }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>503 - Service Unavailable</h1>
        <p>{error_msg}</p>
        <div class="help-box">
            <strong>To fix this:</strong><br>
            1. Start the Python controller: <code>python matrix.py controller</code><br>
            2. Ensure port 8080 is not blocked<br>
            3. Check that the controller is running properly
        </div>
        <a href="/" class="nav-link">🏠 Return Home</a>
    </div>
</body>
</html>"""
                self.send_response(503)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            
            def send_cors_headers(self):
                """Send CORS headers if enabled"""
                if server_instance.config.enable_cors:
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            def log_message(self, format, *args):
                """Override to provide better logging"""
                print(f"🌐 {self.address_string()} - {format % args}")
        
        return UnifiedRequestHandler
    
    def start(self):
        """Start the unified web server"""
        try:
            handler_class = self.create_custom_handler()
            
            with socketserver.TCPServer(("", self.config.port), handler_class) as httpd:
                print("=" * 70)
                print("🌐 LED Matrix Unified Web Server")
                print("=" * 70)
                print(f"📅 Started: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"🌍 Server: http://localhost:{self.config.port}")
                print(f"📁 Sites Directory: {self.sites_dir}")
                print("=" * 70)
                print("🎯 Available Interfaces:")
                print(f"   🏠 Landing Page:     http://localhost:{self.config.port}/")
                print(f"   🎮 Control Interface: http://localhost:{self.config.port}/control")
                print(f"   📚 Documentation:     http://localhost:{self.config.port}/docs")
                print(f"   🔌 API Proxy:         http://localhost:{self.config.port}/api/*")
                print("=" * 70)
                print("💡 For full functionality, ensure Python controller is running:")
                print("   Command: python matrix.py controller")
                print("=" * 70)
                print("Press Ctrl+C to stop the server")
                print()
                
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\n🛑 Unified server stopped by user")
            return True
        except Exception as e:
            print(f"❌ Unified server error: {e}")
            return False

# Legacy compatibility - keep old class for backward compatibility
class MatrixWebServer(UnifiedMatrixWebServer):
    def __init__(self, port=3000, site_type="control"):
        super().__init__(port)
        self.site_type = site_type
        print(f"⚠️  Legacy MatrixWebServer used. Consider using UnifiedMatrixWebServer for path-based routing.")
        print(f"   Access your {site_type} interface at: http://localhost:{port}/{site_type}")
    
    def start(self):
        """Start server and redirect to appropriate path"""
        print(f"🔄 Starting unified server with legacy compatibility for {self.site_type}")
        return super().start()

def main():
    """Main entry point for standalone web server"""
    server = MatrixWebServer()
    server.start()

if __name__ == "__main__":
    main()