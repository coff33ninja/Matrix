#!/usr/bin/env python3
"""
Unified web server module for LED Matrix Control Center
Serves both control interface and documentation through path-based routing
"""

import os
import http.server
import socketserver
import urllib.parse
import mimetypes
import logging
from pathlib import Path
from dataclasses import dataclass

try:
    import requests
except ImportError:
    print("⚠️  requests library not found. API proxy functionality will be limited.")
    requests = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("web_server.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("WebServer")


def get_env_config():
    """Get environment configuration for debugging"""
    env_vars = {
        "WEB_SERVER_PORT": os.getenv("WEB_SERVER_PORT"),
        "WEB_SERVER_HOST": os.getenv("WEB_SERVER_HOST"),
        "API_PROXY_PORT": os.getenv("API_PROXY_PORT"),
        "ENABLE_CORS": os.getenv("ENABLE_CORS"),
        "ENABLE_CACHING": os.getenv("ENABLE_CACHING"),
        "SITES_DIR": os.getenv("SITES_DIR"),
        "AUTOCREATE_DIRS": os.getenv("AUTOCREATE_DIRS"),
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "PATH": (lambda path: path[:100] + "..." if path and len(path) > 100 else path)(
            os.getenv("PATH")
        ),
    }
    return {k: v for k, v in env_vars.items() if v is not None}


@dataclass
class ServerConfig:
    port: int = int(os.getenv("WEB_SERVER_PORT", 3000))
    host: str = os.getenv("WEB_SERVER_HOST", "localhost")
    control_path: str = os.getenv("CONTROL_PATH", "sites/control")
    docs_path: str = os.getenv("DOCS_PATH", "sites/docs")
    api_proxy_port: int = int(os.getenv("API_PROXY_PORT", 8080))
    enable_cors: bool = os.getenv("ENABLE_CORS", "true").lower() == "true"
    enable_caching: bool = os.getenv("ENABLE_CACHING", "true").lower() == "true"


class UnifiedMatrixWebServer:
    def __init__(self, port=None):
        # Use environment variable or passed port
        if port is None:
            port = int(os.getenv("WEB_SERVER_PORT", 3000))
        self.config = ServerConfig(port=port)

        # Use environment variable for sites directory if available
        sites_base = os.getenv("SITES_DIR", str(Path(__file__).parent.parent / "sites"))
        self.sites_dir = Path(sites_base)
        self.control_dir = self.sites_dir / "control"
        self.docs_dir = self.sites_dir / "docs"
        self.errors_dir = self.sites_dir / "errors"

        # Create directories if they don't exist (when AUTOCREATE_DIRS is set)
        if os.getenv("AUTOCREATE_DIRS", "false").lower() == "true":
            os.makedirs(self.control_dir, exist_ok=True)
            os.makedirs(self.docs_dir, exist_ok=True)
            os.makedirs(self.errors_dir, exist_ok=True)

        # Ensure directories exist
        if not self.control_dir.exists():
            print(f"❌ Control directory not found: {self.control_dir}")
        if not self.docs_dir.exists():
            print(f"❌ Documentation directory not found: {self.docs_dir}")
        if not self.errors_dir.exists():
            print(f"❌ Error pages directory not found: {self.errors_dir}")

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
                client_ip = self.client_address[0]

                logger.info(f"📥 {self.command} {path} from {client_ip}")

                try:
                    # Handle API requests first, regardless of prefix
                    if path.startswith("/api") or path.startswith("/control/api"):
                        logger.info(f"🔌 Proxying API request: {path}")
                        self.proxy_api_request(path, parsed_path.query)
                    elif path == "/" or path == "":
                        logger.info("🏠 Serving landing page")
                        self.serve_landing_page()
                    elif path.startswith("/control"):
                        logger.info(f"🎮 Serving control interface: {path}")
                        self.serve_control_interface(path)
                    elif path.startswith("/docs"):
                        logger.info(f"📚 Serving docs interface: {path}")
                        self.serve_docs_interface(path)
                    # Handle static assets that should be served from control directory
                    elif (
                        path.startswith("/css/")
                        or path.startswith("/js/")
                        or path.startswith("/sections/")
                        or path.startswith("/favicon.ico")
                        or path.startswith("/app.js")
                    ):
                        # Check if referrer is from control interface
                        referrer = self.headers.get("Referer", "")
                        if "/control" in referrer:
                            logger.info(f"🎮 Serving control static asset: {path}")
                            self.serve_control_interface(path)
                        else:
                            logger.warning(
                                f"❓ Static asset requested without control context: {path}"
                            )
                            self.serve_404()
                    else:
                        logger.warning(f"❓ Unknown path requested: {path}")
                        self.serve_404()
                except Exception as e:
                    logger.error(
                        f"❌ Error handling request {path}: {e}", exc_info=True
                    )
                    self.serve_500(str(e))

            def serve_landing_page(self):
                """Serve the navigation landing page"""
                content = server_instance.create_landing_page()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))

            def serve_control_interface(self, path):
                """Serve files from control interface"""
                # Handle different path patterns
                if path.startswith("/control"):
                    # Remove /control prefix and serve from control directory
                    file_path = path[8:] if len(path) > 8 else "/"
                    if file_path == "/" or file_path == "":
                        file_path = "/index.html"
                else:
                    # Direct static asset request (css, js, etc.)
                    file_path = path

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
                    file_path = file_path.lstrip("/")
                    full_path = base_dir / file_path

                    # Ensure the path is within the base directory using os.path.commonpath
                    try:
                        common_path = os.path.commonpath(
                            [str(full_path.resolve()), str(base_dir.resolve())]
                        )
                        if common_path != str(base_dir.resolve()):
                            self.serve_404()
                            return
                    except ValueError:
                        # Paths are on different drives (Windows) or invalid
                        self.serve_404()
                        return

                    if full_path.is_file():
                        # Determine MIME type
                        mime_type, _ = mimetypes.guess_type(str(full_path))
                        if mime_type is None:
                            mime_type = "application/octet-stream"

                        # Read and serve file
                        with open(full_path, "rb") as f:
                            content = f.read()

                        self.send_response(200)
                        self.send_header("Content-Type", mime_type)
                        self.send_cors_headers()
                        if server_instance.config.enable_caching:
                            self.send_header("Cache-Control", "public, max-age=3600")
                        self.end_headers()
                        self.wfile.write(content)
                    else:
                        self.serve_404()

                except Exception as e:
                    print(f"❌ Error serving static file {file_path}: {e}")
                    self.serve_500(str(e))

            def proxy_api_request(self, path, query):
                """Proxy API requests to the Python controller"""
                if not requests:
                    logger.error("❌ Requests library not available for API proxy")
                    self.serve_503("Requests library not available")
                    return

                try:
                    # Handle both /api and /control/api paths
                    if path.startswith("/control/api"):
                        api_path = "/api" + path[12:]  # Convert /control/api to /api
                        logger.info(f"🔄 Converting {path} to {api_path}")
                    else:
                        api_path = path  # Keep full /api path

                    if query:
                        api_path += f"?{query}"

                    # Proxy to controller
                    controller_url = f"http://localhost:{server_instance.config.api_proxy_port}{api_path}"
                    logger.info(f"🔗 Proxying to: {controller_url}")

                    if self.command == "GET":
                        response = requests.get(controller_url, timeout=5)
                    elif self.command == "POST":
                        content_length = int(self.headers.get("Content-Length", 0))
                        post_data = self.rfile.read(content_length)
                        logger.info(f"📤 POST data length: {content_length}")
                        response = requests.post(
                            controller_url,
                            data=post_data,
                            headers={
                                "Content-Type": self.headers.get(
                                    "Content-Type", "application/json"
                                )
                            },
                            timeout=5,
                        )
                    else:
                        logger.warning(f"❓ Unsupported method: {self.command}")
                        self.serve_404()
                        return

                    # Forward response
                    self.send_response(response.status_code)
                    for header, value in response.headers.items():
                        if header.lower() not in [
                            "content-encoding",
                            "transfer-encoding",
                            "connection",
                        ]:
                            self.send_header(header, value)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(response.content)

                except requests.exceptions.ConnectionError:
                    self.serve_503("Python controller not running on port 8080")
                except requests.exceptions.Timeout:
                    self.serve_503("Controller request timeout")
                except ConnectionAbortedError:
                    # Client disconnected - this is normal, don't log as error
                    pass
                except Exception as e:
                    print(f"❌ API proxy error: {e}")
                    self.serve_500(str(e))

            def serve_404(self):
                """Serve custom 404 page"""
                try:
                    error_page_path = server_instance.errors_dir / "404.html"
                    if error_page_path.exists():
                        with open(error_page_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    else:
                        # Fallback content if error page doesn't exist
                        content = """<!DOCTYPE html>
<html><head><title>404 - Page Not Found</title></head>
<body><h1>404 - Page Not Found</h1><p>The page you're looking for doesn't exist.</p>
<a href="/">Return Home</a></body></html>"""

                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except (ConnectionAbortedError, BrokenPipeError):
                    # Client disconnected - this is normal, just log and continue
                    print(f"🔌 Client disconnected during 404 response for {self.path}")
                except Exception as e:
                    print(f"❌ Error serving 404 page: {e}")

            def serve_500(self, error_msg):
                """Serve custom 500 error page"""
                try:
                    error_page_path = server_instance.errors_dir / "500.html"
                    if error_page_path.exists():
                        with open(error_page_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        # Replace placeholder with actual error message
                        content = content.replace("{{ERROR_MESSAGE}}", error_msg)
                    else:
                        # Fallback content if error page doesn't exist
                        content = f"""<!DOCTYPE html>
<html><head><title>500 - Server Error</title></head>
<body><h1>500 - Server Error</h1><p>Something went wrong: {error_msg}</p>
<a href="/">Return Home</a></body></html>"""

                    self.send_response(500)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except (ConnectionAbortedError, BrokenPipeError):
                    # Client disconnected - this is normal, just log and continue
                    print(f"🔌 Client disconnected during 500 response for {self.path}")
                except Exception as e:
                    print(f"❌ Error serving 500 page: {e}")

            def serve_503(self, error_msg):
                """Serve service unavailable page from external file"""
                try:
                    error_page_path = server_instance.errors_dir / "503.html"
                    if error_page_path.exists():
                        with open(error_page_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        # Replace placeholder with actual error message
                        content = content.replace("{{ERROR_MESSAGE}}", error_msg)
                    else:
                        # Fallback content if error page doesn't exist
                        content = f"""<!DOCTYPE html>
<html><head><title>503 - Service Unavailable</title></head>
<body><h1>503 - Service Unavailable</h1><p>{error_msg}</p>
<a href="/">Return Home</a></body></html>"""

                    self.send_response(503)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except (ConnectionAbortedError, BrokenPipeError):
                    # Client disconnected - this is normal, just log and continue
                    print(f"🔌 Client disconnected during 503 response for {self.path}")
                except Exception as e:
                    print(f"❌ Error serving 503 page: {e}")

            def send_cors_headers(self):
                """Send CORS headers if enabled"""
                if server_instance.config.enable_cors:
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header(
                        "Access-Control-Allow-Methods", "GET, POST, OPTIONS"
                    )
                    self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def log_message(self, format, *args):
                """Override to provide better logging"""
                print(f"🌐 {self.address_string()} - {format % args}")

        return UnifiedRequestHandler

    def start(self):
        """
        Starts the unified web server, serving the landing page, control interface, documentation, and API proxy.

        Checks if the configured port is available, prints startup information, and runs the server until interrupted. Handles keyboard interrupts and port conflicts gracefully, providing user guidance for resolving issues.

        Returns:
            bool: True if stopped by user, False if an error occurred during startup.
        """
        try:
            handler_class = self.create_custom_handler()

            # Check if port is available using os
            if os.name == "nt":  # Windows
                # On Windows, we can check if the port is in use
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(("localhost", self.config.port))
                sock.close()
                if result == 0:
                    print(f"⚠️  Port {self.config.port} appears to be in use")

            with socketserver.TCPServer(("", self.config.port), handler_class) as httpd:
                print("=" * 70)
                print("🌐 LED Matrix Unified Web Server")
                print("=" * 70)
                print(
                    f"📅 Started: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                print(f"🌍 Server: http://localhost:{self.config.port}")
                print(f"📁 Sites Directory: {self.sites_dir}")
                print(
                    f"🖥️  Platform: {os.name} ({'Windows' if os.name == 'nt' else 'Unix-like'})"
                )
                print(f"🔧 Process ID: {os.getpid()}")
                print("=" * 70)
                print("🎯 Available Interfaces:")
                print(f"   🏠 Landing Page:     http://localhost:{self.config.port}/")
                print(
                    f"   🎮 Control Interface: http://localhost:{self.config.port}/control"
                )
                print(
                    f"   📚 Documentation:     http://localhost:{self.config.port}/docs"
                )
                print(
                    f"   🔌 API Proxy:         http://localhost:{self.config.port}/api/*"
                )
                print("=" * 70)
                print("💡 For full functionality, ensure Python controller is running:")
                print("   Command: python matrix.py controller")
                print("=" * 70)
                print("🌍 Environment Variables:")
                print(f"   WEB_SERVER_PORT: {os.getenv('WEB_SERVER_PORT', 'not set')}")
                print(f"   API_PROXY_PORT: {os.getenv('API_PROXY_PORT', 'not set')}")
                print(f"   ENABLE_CORS: {os.getenv('ENABLE_CORS', 'not set')}")
                print("=" * 70)
                print("Press Ctrl+C to stop the server")
                print()

                httpd.serve_forever()

        except KeyboardInterrupt:
            print("\n🛑 Unified server stopped by user")
            return True
        except OSError as e:
            if e.errno == 98 or "Address already in use" in str(e):
                print(
                    f"❌ Port {self.config.port} is already in use. Try a different port or stop the existing server."
                )
                print(
                    "💡 Set WEB_SERVER_PORT environment variable to use a different port"
                )
            else:
                print(f"❌ OS error starting server: {e}")
            return False
        except Exception as e:
            print(f"❌ Unified server error: {e}")
            return False


def setup_signal_handlers():
    """
    Register signal handlers to enable graceful shutdown of the server on SIGTERM and SIGINT signals.
    """
    import signal

    def signal_handler(signum, frame):
        print(f"\n🔔 Received signal {signum}")
        print("🛑 Shutting down gracefully...")
        os._exit(0)

    # Register signal handlers if available
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, signal_handler)


def main():
    """
    Starts the unified web server for the LED Matrix Control Center as a standalone application.

    Initializes signal handlers for graceful shutdown, optionally prints environment configuration if debug mode is enabled, and launches the server.
    """
    # Setup signal handlers
    setup_signal_handlers()

    # Print environment info if DEBUG is set
    if os.getenv("DEBUG", "false").lower() == "true":
        print("🐛 Debug mode enabled")
        print("🌍 Environment configuration:")
        for key, value in get_env_config().items():
            print(f"   {key}: {value}")
        print()

    server = UnifiedMatrixWebServer()
    server.start()


if __name__ == "__main__":
    main()
