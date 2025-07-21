#!/usr/bin/env python3
"""
Web-Based LED Matrix Controller
Provides a unified web interface for all LED matrix functionality
"""

import threading
import time
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import colorsys
import urllib.parse
import json
import os
import sys
import psutil  # For system monitoring
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import socketserver
import mimetypes
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('matrix_controller.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('MatrixController')

# Robust resampling filter imports for Pillow compatibility
try:
    from PIL import Image as PILImage
    Resampling = getattr(PILImage, "Resampling", None)
    if Resampling is not None:
        LANCZOS_RESAMPLE = Resampling.LANCZOS
        NEAREST_RESAMPLE = Resampling.NEAREST
    else:
        LANCZOS_RESAMPLE = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", getattr(Image, "BILINEAR", 0)))
        NEAREST_RESAMPLE = getattr(Image, "NEAREST", getattr(Image, "BILINEAR", 0))
except Exception:
    LANCZOS_RESAMPLE = getattr(Image, "LANCZOS", getattr(Image, "BICUBIC", getattr(Image, "BILINEAR", 0)))
    NEAREST_RESAMPLE = getattr(Image, "NEAREST", getattr(Image, "BILINEAR", 0))

# Import shared modules
from matrix_config import config
from matrix_hardware import hardware
from wiring_diagram_generator import WiringDiagramGenerator


class WebMatrixController:
    def __init__(self, port=8080):
        logger.info(f"INIT: Initializing WebMatrixController on port {port}")
        
        # Matrix properties from shared config
        self.config = config
        self.W = int(config.get("matrix_width", 16))
        self.H = int(config.get("matrix_height", 16))
        self.port = port
        
        logger.info(f"MATRIX: Matrix size: {self.W}×{self.H}")

        # State attributes
        self.start_time = datetime.now()
        self.current_mode = "idle"
        self.is_streaming = False
        
        # Matrix data
        self.matrix_data = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        logger.info(f"BUFFER: Matrix data buffer initialized: {self.matrix_data.shape}")
        
        # Animation thread
        self.animation_thread = None
        
        # Start web server
        logger.info("SERVER: Starting web server...")
        self._start_web_server()

    def _start_web_server(self):
        """Start the web API server"""
        controller = self

        class WebHandler(BaseHTTPRequestHandler):
            def send_cors_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def send_json_response(self, data, status=200):
                self.send_response(status)
                self.send_cors_headers()
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_cors_headers()
                self.end_headers()

            def do_GET(self):
                parsed_url = urllib.parse.urlparse(self.path)
                path = parsed_url.path
                client_ip = self.client_address[0]
                
                logger.info(f"GET: {path} from {client_ip}")

                # Normalize API paths to handle all variations
                normalized_path = path
                if path.startswith("/control/api/"):
                    normalized_path = "/api/" + path[12:]
                    logger.info(f"NORMALIZE: {path} -> {normalized_path}")
                elif path.startswith("/api/"):
                    normalized_path = path
                
                # API endpoints with normalized paths
                if normalized_path == "/api/status" or path == "/status":
                    logger.info("STATUS: Serving status endpoint")
                    status = {
                        "connected": True,
                        "matrix": {"width": controller.W, "height": controller.H},
                        "current_mode": getattr(controller, "current_mode", "idle"),
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.send_json_response(status)

                elif path == "/api/config":
                    config_data = {
                        "connectionMode": controller.config.get("connection_mode", "USB"),
                        "serialPort": controller.config.get("serial_port", ""),
                        "baudRate": controller.config.get("baud_rate", 115200),
                        "matrixWidth": controller.W,
                        "matrixHeight": controller.H,
                    }
                    self.send_json_response(config_data)

                elif path == "/api/system":
                    try:
                        cpu_percent = psutil.cpu_percent()
                        memory = psutil.virtual_memory()
                        system_stats = {
                            "cpu": cpu_percent,
                            "memory": memory.percent,
                            "uptime": str(datetime.now() - controller.start_time).split(".")[0],
                            "temperature": "N/A",  # Would need platform-specific implementation
                        }
                    except:
                        system_stats = {
                            "cpu": "N/A",
                            "memory": "N/A",
                            "uptime": "N/A",
                            "temperature": "N/A",
                        }
                    self.send_json_response(system_stats)

                elif path == "/api/hardware":
                    hardware_info = {
                        "controller": "Web Matrix Controller",
                        "port": controller.config.get("serial_port", "Not connected"),
                        "baudRate": controller.config.get("baud_rate", 115200),
                        "matrixSize": f"{controller.W}×{controller.H}",
                    }
                    self.send_json_response(hardware_info)

                elif path == "/api/backups":
                    # List available backups
                    backups = []
                    try:
                        backup_dir = os.path.join(os.path.dirname(__file__), "..", "backups")
                        if os.path.exists(backup_dir):
                            backups = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
                    except:
                        pass
                    self.send_json_response(backups)
                
                elif path == "/api/options":
                    # Get available options for LED density, power supplies, etc.
                    options = {
                        "ledsPerMeter": [
                            {"value": 30, "label": "30 LEDs/m (Low Density)", "spacing": "33.3mm"},
                            {"value": 60, "label": "60 LEDs/m (Medium Density)", "spacing": "16.7mm"},
                            {"value": 144, "label": "144 LEDs/m (High Density)", "spacing": "6.9mm"},
                            {"value": 256, "label": "256 LEDs/m (Ultra High Density)", "spacing": "3.9mm"}
                        ],
                        "powerSupplies": [
                            {"value": "5V2A", "label": "5V 2A (10W)", "maxLeds": 33, "price": 15},
                            {"value": "5V5A", "label": "5V 5A (25W)", "maxLeds": 83, "price": 25},
                            {"value": "5V10A", "label": "5V 10A (50W)", "maxLeds": 167, "price": 35},
                            {"value": "5V20A", "label": "5V 20A (100W)", "maxLeds": 333, "price": 55},
                            {"value": "5V30A", "label": "5V 30A (150W)", "maxLeds": 500, "price": 75},
                            {"value": "5V40A", "label": "5V 40A (200W)", "maxLeds": 667, "price": 95}
                        ],
                        "controllers": [
                            {"value": "arduino_uno", "label": "Arduino Uno R3", "voltage": "5V", "price": 25},
                            {"value": "arduino_nano", "label": "Arduino Nano", "voltage": "5V", "price": 15},
                            {"value": "esp32", "label": "ESP32 Dev Board", "voltage": "3.3V", "price": 12},
                            {"value": "esp8266", "label": "ESP8266 NodeMCU", "voltage": "3.3V", "price": 8}
                        ]
                    }
                    self.send_json_response(options)
                
                elif path == "/api/matrix/preview":
                    # Return current matrix state as base64 image
                    try:
                        import base64
                        from io import BytesIO
                        
                        # Create a larger preview image
                        preview_size = 16  # Pixels per LED
                        preview = Image.new('RGB', (controller.W * preview_size, controller.H * preview_size))
                        draw = ImageDraw.Draw(preview)
                        
                        # Draw each LED
                        for y in range(controller.H):
                            for x in range(controller.W):
                                color = tuple(controller.matrix_data[y, x])
                                draw.rectangle(
                                    [x * preview_size, y * preview_size, 
                                     (x + 1) * preview_size - 1, (y + 1) * preview_size - 1],
                                    fill=color
                                )
                        
                        # Convert to base64
                        buffer = BytesIO()
                        preview.save(buffer, format="PNG")
                        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        
                        self.send_json_response({
                            "image": f"data:image/png;base64,{img_str}",
                            "width": controller.W,
                            "height": controller.H
                        })
                    except Exception as e:
                        self.send_json_response({"error": str(e)}, 500)

                else:
                    # Serve static files
                    try:
                        # Default to index.html for root path
                        if path == "/":
                            path = "/index.html"
                        
                        # Remove leading slash
                        file_path = path.lstrip('/')
                        
                        # Look in sites directory
                        sites_dir = os.path.join(os.path.dirname(__file__), "..", "sites")
                        control_dir = os.path.join(sites_dir, "control")
                        
                        # Check if file exists in control directory
                        full_path = os.path.join(control_dir, file_path)
                        
                        if os.path.exists(full_path) and os.path.isfile(full_path):
                            # Determine MIME type
                            mime_type, _ = mimetypes.guess_type(full_path)
                            if mime_type is None:
                                mime_type = 'application/octet-stream'
                            
                            # Read and serve file
                            with open(full_path, 'rb') as f:
                                content = f.read()
                            
                            self.send_response(200)
                            self.send_header('Content-Type', mime_type)
                            self.send_cors_headers()
                            self.end_headers()
                            self.wfile.write(content)
                        else:
                            # File not found
                            self.send_response(404)
                            self.send_header('Content-Type', 'text/html')
                            self.send_cors_headers()
                            self.end_headers()
                            self.wfile.write(b"<html><body><h1>404 Not Found</h1></body></html>")
                    except Exception as e:
                        print(f"Error serving file: {e}")
                        self.send_response(500)
                        self.send_header('Content-Type', 'text/html')
                        self.send_cors_headers()
                        self.end_headers()
                        self.wfile.write(f"<html><body><h1>500 Server Error</h1><p>{str(e)}</p></body></html>".encode())

            def do_POST(self):
                parsed_url = urllib.parse.urlparse(self.path)
                path = parsed_url.path
                client_ip = self.client_address[0]

                logger.info(f"POST: {path} from {client_ip}")

                # Read POST data
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)

                try:
                    data = json.loads(post_data.decode()) if post_data else {}
                    logger.debug(f"DATA: POST data: {data}")
                except Exception as e:
                    logger.error(f"ERROR: Failed to parse POST data: {e}")
                    data = {}

                if path == "/api/pattern":
                    logger.info(f"PATTERN: Pattern request: {data.get('pattern', 'unknown')}")
                    try:
                        pattern = data.get("pattern", "solid")
                        color = data.get("color", "#ff0000")
                        brightness = int(data.get("brightness", 128))
                        speed = int(data.get("speed", 50))

                        # Apply pattern
                        controller.apply_pattern(pattern, color, brightness, speed)
                        self.send_json_response({
                            "status": "success",
                            "message": f"Applied {pattern} pattern",
                        })
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                elif path == "/api/clear":
                    try:
                        controller.clear_matrix()
                        self.send_json_response({"status": "success", "message": "Matrix cleared"})
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                elif path == "/api/text":
                    try:
                        text = data.get("text", "")
                        scroll = data.get("scroll", False)
                        
                        if scroll:
                            controller.scroll_text(text)
                        else:
                            controller.draw_text(text)
                            
                        self.send_json_response({
                            "status": "success", 
                            "message": f"Text {'scrolling' if scroll else 'displayed'}"
                        })
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                elif path == "/api/generate":
                    try:
                        from arduino_generator import ArduinoGenerator
                        generator = ArduinoGenerator()

                        board = data.get("board", "uno")
                        width = data.get("width", 16)
                        height = data.get("height", 16)

                        code = generator.generate_code(board, matrix_width=width, matrix_height=height)
                        self.send_json_response({"status": "success", "code": code})
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                elif path == "/api/wiring":
                    try:
                        controller_type = data.get("controller", "arduino_uno")
                        width = data.get("width", 16)
                        height = data.get("height", 16)
                        leds_per_meter = data.get("ledsPerMeter", 144)
                        power_supply = data.get("powerSupply", "5V10A")
                        
                        # Create wiring diagram generator
                        wiring_gen = WiringDiagramGenerator()
                        
                        # Calculate power requirements
                        power_req = wiring_gen.calculate_power_requirements(width, height)
                        total_leds = power_req["total_leds"]
                        
                        # Calculate strip length
                        strip_length = total_leds / leds_per_meter
                        
                        # Generate Mermaid wiring diagram
                        mermaid_diagram = wiring_gen.generate_mermaid_diagram(controller_type, width, height, psu=power_supply)
                        
                        # Generate component list using the wiring generator
                        components = wiring_gen._generate_component_list(
                            wiring_gen.controllers[controller_type], 
                            wiring_gen.power_supplies.get(power_supply, wiring_gen.power_supplies["5V40A"])
                        )
                        
                        # Calculate estimated cost
                        estimated_cost = wiring_gen._estimate_project_cost(
                            wiring_gen.controllers[controller_type],
                            wiring_gen.power_supplies.get(power_supply, wiring_gen.power_supplies["5V40A"]),
                            total_leds
                        )
                        
                        wiring_data = {
                            "controller": controller_type,
                            "matrix": {"width": width, "height": height, "totalLeds": total_leds},
                            "power": {
                                "maxCurrent": round(power_req["total_current_amps"], 2),
                                "maxPower": round(power_req["total_current_amps"] * 5, 1),
                                "recommendedPSU": power_req["recommended_psu"],
                                "selectedPSU": power_supply
                            },
                            "strip": {
                                "ledsPerMeter": leds_per_meter,
                                "totalLength": round(strip_length, 2),
                                "segments": max(1, int(strip_length))
                            },
                            "mermaidDiagram": mermaid_diagram,
                            "components": components,
                            "estimatedCost": estimated_cost
                        }
                        
                        self.send_json_response({"status": "success", "wiring": wiring_data})
                    except Exception as e:
                        logger.error(f"ERROR: Wiring generation failed: {e}")
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                elif path == "/api/config":
                    try:
                        # Save configuration
                        for key, value in data.items():
                            if key == "connectionMode":
                                controller.config.set("connection_mode", value)
                            elif key == "serialPort":
                                controller.config.set("serial_port", value)
                            elif key == "baudRate":
                                controller.config.set("baud_rate", value)
                            elif key == "matrixWidth":
                                controller.W = int(value)
                                controller.config.set("matrix_width", value)
                                controller.matrix_data = np.zeros((controller.H, controller.W, 3), dtype=np.uint8)
                            elif key == "matrixHeight":
                                controller.H = int(value)
                                controller.config.set("matrix_height", value)
                                controller.matrix_data = np.zeros((controller.H, controller.W, 3), dtype=np.uint8)

                        controller.config.save_config()
                        self.send_json_response({"status": "success", "message": "Configuration saved"})
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                elif path == "/api/backup":
                    try:
                        # Create backup
                        backup_filename = controller.config.create_backup()
                        self.send_json_response({"status": "success", "filename": backup_filename})
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)
                
                elif path == "/api/upload":
                    try:
                        # Handle image upload
                        import base64
                        from io import BytesIO
                        
                        image_data = data.get("image", "")
                        if image_data.startswith("data:image"):
                            # Extract base64 data
                            image_data = image_data.split(",")[1]
                            image_bytes = base64.b64decode(image_data)
                            
                            # Open image
                            img = Image.open(BytesIO(image_bytes))
                            
                            # Resize to matrix dimensions
                            img = img.convert("RGB").resize((controller.W, controller.H), LANCZOS_RESAMPLE)
                            controller.matrix_data = np.array(img)
                            controller.send_frame()
                            
                            self.send_json_response({
                                "status": "success", 
                                "message": "Image uploaded and displayed"
                            })
                        else:
                            self.send_json_response({
                                "status": "error", 
                                "message": "Invalid image data"
                            }, 400)
                    except Exception as e:
                        self.send_json_response({"status": "error", "message": str(e)}, 500)

                else:
                    self.send_json_response({"status": "error", "message": "Endpoint not found"}, 404)

        def run_server():
            try:
                server = socketserver.ThreadingTCPServer(("", controller.port), WebHandler)
                print(f"\n🌐 Web Matrix Controller started on http://localhost:{controller.port}")
                print(f"📊 Matrix size: {controller.W}×{controller.H}")
                server.serve_forever()
            except Exception as e:
                print(f"Web server error: {e}")

        threading.Thread(target=run_server, daemon=True).start()

    def clear_matrix(self):
        """Clear the LED matrix display"""
        self.matrix_data.fill(0)
        self.send_frame()
        return True

    def rainbow_pattern(self):
        """Display a rainbow pattern on the matrix"""
        for y in range(int(self.H)):
            for x in range(int(self.W)):
                hue = (x + y) * 360 / (int(self.W) + int(self.H))
                rgb = colorsys.hsv_to_rgb(hue / 360, 1, 1)
                self.matrix_data[y, x] = [int(c * 255) for c in rgb]
        self.send_frame()
        return True

    def send_frame(self):
        """Send the current matrix frame to hardware"""
        try:
            hardware.send_frame(self.matrix_data)
            return True
        except Exception as e:
            print(f"Hardware send error: {e}")
            return False

    def draw_text(self, text):
        """Draw text on the matrix"""
        try:
            if not text:
                return False

            # Create larger canvas for better text rendering
            img = Image.new("RGB", (self.W * 4, self.H * 4), color="black")
            draw = ImageDraw.Draw(img)

            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Get text size and center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2

            # Draw text in white
            draw.text((x, y), text, fill="white", font=font)

            # Resize to matrix dimensions
            img_resized = img.resize((self.W, self.H), LANCZOS_RESAMPLE)
            self.matrix_data = np.array(img_resized)
            self.send_frame()
            return True

        except Exception as e:
            print(f"Failed to draw text: {e}")
            return False

    def scroll_text(self, text):
        """Scroll text across matrix"""
        if not text:
            return False
            
        # Stop any existing animation
        self.stop_animation()
        
        self.current_mode = "text"
        self.is_streaming = True
        self.animation_thread = threading.Thread(target=self._text_loop, args=(text,), daemon=True)
        self.animation_thread.start()
        return True

    def _text_loop(self, text):
        """Text scrolling loop"""
        scroll_pos = int(self.W)

        while self.is_streaming and self.current_mode == "text":
            self.matrix_data.fill(0)

            # Simple character rendering
            for i, char in enumerate(text):
                char_x = scroll_pos + i * 6
                if -6 <= char_x <= int(self.W):
                    self._draw_char(char, char_x, int(self.H) // 2)

            scroll_pos -= 1
            if scroll_pos < -len(text) * 6:
                scroll_pos = int(self.W)

            self.send_frame()
            time.sleep(0.1)

    def _draw_char(self, char, x, y):
        """Simple character drawing"""
        # Basic 5x5 character patterns
        patterns = {
            "A": [
                [0, 1, 1, 1, 0],
                [1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1],
                [1, 0, 0, 0, 1],
            ],
            "B": [
                [1, 1, 1, 1, 0],
                [1, 0, 0, 0, 1],
                [1, 1, 1, 1, 0],
                [1, 0, 0, 0, 1],
                [1, 1, 1, 1, 0],
            ],
            "C": [
                [0, 1, 1, 1, 0],
                [1, 0, 0, 0, 1],
                [1, 0, 0, 0, 0],
                [1, 0, 0, 0, 1],
                [0, 1, 1, 1, 0],
            ],
            # Add more characters as needed
            " ": [
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
        }

        pattern = patterns.get(char.upper(), patterns[" "])

        for py, row in enumerate(pattern):
            for px, pixel in enumerate(row):
                if pixel and 0 <= x + px < self.W and 0 <= y + py < self.H:
                    self.matrix_data[y + py, x + px] = [255, 255, 255]

    def stop_animation(self):
        """Stop current animation"""
        self.is_streaming = False
        self.current_mode = "idle"
        if hasattr(self, 'animation_thread') and self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        return True

    def apply_pattern(self, pattern, color, brightness, speed):
        """Apply a pattern to the matrix"""
        try:
            # Stop any existing animation
            self.stop_animation()
            
            self.current_mode = pattern

            # Convert hex color to RGB
            if color.startswith("#"):
                color = color[1:]
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

            # Apply brightness scaling
            brightness_factor = brightness / 255.0
            r, g, b = (
                int(r * brightness_factor),
                int(g * brightness_factor),
                int(b * brightness_factor),
            )

            if pattern == "solid":
                self.matrix_data.fill(0)
                self.matrix_data[:, :] = [r, g, b]
                self.send_frame()
                return True

            elif pattern == "rainbow":
                self.rainbow_pattern()
                return True

            elif pattern == "plasma":
                self.is_streaming = True
                self.animation_thread = threading.Thread(
                    target=self._plasma_animation_loop, 
                    args=(speed,), 
                    daemon=True
                )
                self.animation_thread.start()
                return True

            elif pattern == "fire":
                self.is_streaming = True
                self.animation_thread = threading.Thread(
                    target=self._fire_animation_loop, 
                    args=(speed,), 
                    daemon=True
                )
                self.animation_thread.start()
                return True

            elif pattern == "matrix":
                self.is_streaming = True
                self.animation_thread = threading.Thread(
                    target=self._matrix_rain_animation_loop, 
                    args=(speed,), 
                    daemon=True
                )
                self.animation_thread.start()
                return True

            elif pattern == "custom":
                # Handle custom pattern data
                custom_data = data.get("data", [])
                if custom_data:
                    self._apply_custom_pattern(custom_data)
                    return True
                else:
                    print("No custom pattern data provided")
                    return False

            return False

        except Exception as e:
            print(f"Error applying pattern: {e}")
            return False

    def _apply_custom_pattern(self, pattern_data):
        """Apply custom pattern data to the matrix"""
        try:
            # Stop any existing animation
            self.stop_animation()
            
            # Clear the matrix
            self.matrix_data.fill(0)
            
            # Apply custom pattern data
            # pattern_data should be a 2D array of RGB values
            for y in range(min(len(pattern_data), self.H)):
                for x in range(min(len(pattern_data[y]), self.W)):
                    rgb = pattern_data[y][x]
                    if isinstance(rgb, list) and len(rgb) >= 3:
                        self.matrix_data[y, x] = [rgb[0], rgb[1], rgb[2]]
            
            # Send the frame
            self.send_frame()
            
        except Exception as e:
            print(f"Error applying custom pattern: {e}")

    def _plasma_animation_loop(self, speed):
        """Plasma animation loop"""
        import math
        
        frame = 0
        while self.is_streaming and self.current_mode == "plasma":
            time_factor = frame * speed / 100.0

            for y in range(self.H):
                for x in range(self.W):
                    # Plasma formula
                    v1 = math.sin(x / 16.0)
                    v2 = math.sin(y / 8.0)
                    v3 = math.sin((x + y) / 16.0)
                    v4 = math.sin(math.sqrt(x * x + y * y) / 8.0)

                    plasma = v1 + v2 + v3 + v4 + 4 * math.sin(time_factor)

                    # Convert to RGB
                    hue = (plasma + 4) / 8 * 360
                    rgb = colorsys.hsv_to_rgb(hue / 360, 1, 1)
                    self.matrix_data[y, x] = [int(c * 255) for c in rgb]

            self.send_frame()
            frame += 1
            time.sleep(0.05)

    def _fire_animation_loop(self, speed):
        """Fire animation loop"""
        import random
        
        # Create fire buffer (with extra row at bottom for heat source)
        fire_height = self.H + 1
        fire_buffer = np.zeros((fire_height, self.W), dtype=np.uint8)
        
        while self.is_streaming and self.current_mode == "fire":
            # Random heat source at bottom row
            for x in range(self.W):
                fire_buffer[fire_height-1, x] = random.randint(0, 255)
            
            # Propagate fire upwards
            for y in range(fire_height-1):
                for x in range(self.W):
                    # Average of pixels below, with random cooling
                    below = min(fire_height-1, y+1)
                    left = (x-1) % self.W
                    right = (x+1) % self.W
                    
                    cooling = random.randint(0, 3) * (speed / 50.0)
                    new_value = (
                        fire_buffer[below, left] + 
                        fire_buffer[below, x] + 
                        fire_buffer[below, right]
                    ) / 3.0
                    
                    new_value = max(0, new_value - cooling)
                    fire_buffer[y, x] = int(new_value)
            
            # Convert fire buffer to RGB
            for y in range(self.H):
                for x in range(self.W):
                    value = fire_buffer[y, x]
                    # Fire color palette: black -> red -> orange -> yellow -> white
                    if value < 64:
                        r, g, b = value * 3, 0, 0
                    elif value < 128:
                        r, g, b = 255, (value - 64) * 4, 0
                    elif value < 192:
                        r, g, b = 255, 255, (value - 128) * 4
                    else:
                        r, g, b = 255, 255, 255
                        
                    self.matrix_data[y, x] = [r, g, b]
            
            self.send_frame()
            time.sleep(0.05)

    def _matrix_rain_animation_loop(self, speed):
        """Matrix-style digital rain animation"""
        import random
        
        # Initialize drops
        drops = np.zeros(self.W, dtype=int)
        intensity = np.zeros((self.H, self.W), dtype=np.uint8)
        
        while self.is_streaming and self.current_mode == "matrix":
            # Clear matrix
            self.matrix_data.fill(0)
            
            # Update each column
            for x in range(self.W):
                # Create new drop
                if drops[x] == 0 and random.random() < 0.05 * (speed / 50.0):
                    drops[x] = 1
                
                # Draw existing drop
                if drops[x] > 0:
                    # Head of the drop
                    y = drops[x] - 1
                    if 0 <= y < self.H:
                        self.matrix_data[y, x] = [180, 255, 180]  # Bright green
                        intensity[y, x] = 255
                    
                    # Tail
                    for i in range(5):
                        tail_y = y - i - 1
                        if 0 <= tail_y < self.H:
                            val = 255 - (i * 50)
                            if val > 0:
                                self.matrix_data[tail_y, x] = [0, val, 0]  # Fading green
                                intensity[tail_y, x] = val
                    
                    # Move drop down
                    drops[x] += 1
                    
                    # Reset if off screen
                    if drops[x] > self.H + 5:
                        drops[x] = 0
            
            # Fade existing pixels
            for y in range(self.H):
                for x in range(self.W):
                    if intensity[y, x] > 0:
                        intensity[y, x] = max(0, intensity[y, x] - 5)
                        if sum(self.matrix_data[y, x]) > 0:
                            self.matrix_data[y, x] = [0, intensity[y, x], 0]
            
            self.send_frame()
            time.sleep(0.1 * (100 - speed) / 100.0)  # Adjust speed

    def run(self):
        """Run the controller"""
        try:
            print("Web Matrix Controller running. Press Ctrl+C to exit.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nController stopped by user")
        finally:
            self.stop_animation()


if __name__ == "__main__":
    controller = WebMatrixController()
    controller.run()    
    def generate_mermaid_wiring(self, controller_type, width, height, power_supply):
        """Generate Mermaid diagram for wiring"""
        total_leds = width * height
        
        # Controller pin mappings
        controller_pins = {
            "arduino_uno": {"data": "D6", "power": "5V", "ground": "GND"},
            "arduino_nano": {"data": "D6", "power": "5V", "ground": "GND"},
            "esp32": {"data": "GPIO18", "power": "3V3", "ground": "GND"},
            "esp8266": {"data": "D4", "power": "3V3", "ground": "GND"}
        }
        
        pins = controller_pins.get(controller_type, controller_pins["arduino_uno"])
        
        # Generate Mermaid flowchart
        mermaid = f"""graph TD
    PSU["{power_supply} Power Supply"]
    CTRL["{controller_type.replace('_', ' ').title()}"]
    MATRIX["LED Matrix {width}×{height}<br/>{total_leds} LEDs"]
    LEVEL["Level Shifter<br/>(74HCT245)"]
    
    PSU -->|+5V| LEVEL
    PSU -->|GND| LEVEL
    PSU -->|+5V| MATRIX
    PSU -->|GND| MATRIX
    
    CTRL -->|{pins['data']}| LEVEL
    CTRL -->|{pins['power']}| LEVEL
    CTRL -->|{pins['ground']}| LEVEL
    
    LEVEL -->|Data Signal| MATRIX
    
    style PSU fill:#ff9999
    style CTRL fill:#99ccff
    style MATRIX fill:#99ff99
    style LEVEL fill:#ffcc99
    
    classDef powerLine stroke:#ff0000,stroke-width:3px
    classDef dataLine stroke:#0000ff,stroke-width:2px
    classDef groundLine stroke:#000000,stroke-width:2px
    
    class PSU,MATRIX powerLine
    class CTRL,LEVEL dataLine"""
        
        return mermaid
    
    def get_psu_recommendations(self, max_current):
        """Get power supply recommendations based on current requirements"""
        # Add 20% safety margin
        recommended_current = max_current * 1.2
        
        psu_options = [
            {"name": "5V2A", "current": 2.0, "power": 10, "price": 15},
            {"name": "5V5A", "current": 5.0, "power": 25, "price": 25},
            {"name": "5V10A", "current": 10.0, "power": 50, "price": 35},
            {"name": "5V20A", "current": 20.0, "power": 100, "price": 55},
            {"name": "5V30A", "current": 30.0, "power": 150, "price": 75},
            {"name": "5V40A", "current": 40.0, "power": 200, "price": 95}
        ]
        
        # Find the smallest PSU that can handle the load
        recommended = None
        for psu in psu_options:
            if psu["current"] >= recommended_current:
                recommended = psu
                break
        
        if not recommended:
            recommended = psu_options[-1]  # Use the largest if none are sufficient
        
        return {
            "recommended": recommended["name"],
            "options": psu_options,
            "requiredCurrent": round(recommended_current, 2)
        }
    
    def generate_component_list(self, controller_type, total_leds, strip_length, power_supply):
        """Generate component shopping list"""
        components = []
        
        # Controller
        controller_info = {
            "arduino_uno": {"name": "Arduino Uno R3", "price": 25, "url": ""},
            "arduino_nano": {"name": "Arduino Nano", "price": 15, "url": ""},
            "esp32": {"name": "ESP32 Dev Board", "price": 12, "url": ""},
            "esp8266": {"name": "ESP8266 NodeMCU", "price": 8, "url": ""}
        }
        
        ctrl_info = controller_info.get(controller_type, controller_info["arduino_uno"])
        components.append({
            "category": "Controller",
            "name": ctrl_info["name"],
            "quantity": 1,
            "price": ctrl_info["price"],
            "total": ctrl_info["price"]
        })
        
        # LED Strip
        strip_segments = max(1, int(strip_length))
        led_price_per_meter = 25  # Approximate price for WS2812B strip
        components.append({
            "category": "LEDs",
            "name": f"WS2812B LED Strip (144 LEDs/m)",
            "quantity": strip_segments,
            "price": led_price_per_meter,
            "total": strip_segments * led_price_per_meter
        })
        
        # Power Supply
        psu_prices = {
            "5V2A": 15, "5V5A": 25, "5V10A": 35,
            "5V20A": 55, "5V30A": 75, "5V40A": 95
        }
        psu_price = psu_prices.get(power_supply, 35)
        components.append({
            "category": "Power",
            "name": f"{power_supply} Power Supply",
            "quantity": 1,
            "price": psu_price,
            "total": psu_price
        })
        
        # Level Shifter (needed for 3.3V controllers)
        if controller_type in ["esp32", "esp8266"]:
            components.append({
                "category": "Logic",
                "name": "74HCT245 Level Shifter",
                "quantity": 1,
                "price": 3,
                "total": 3
            })
        
        # Capacitors for power smoothing
        if total_leds > 50:
            cap_quantity = max(1, total_leds // 100)
            components.append({
                "category": "Power",
                "name": "1000µF Capacitor",
                "quantity": cap_quantity,
                "price": 2,
                "total": cap_quantity * 2
            })
        
        # Resistor for data line
        components.append({
            "category": "Logic",
            "name": "470Ω Resistor",
            "quantity": 1,
            "price": 0.5,
            "total": 0.5
        })
        
        # Jumper wires and breadboard
        components.append({
            "category": "Wiring",
            "name": "Jumper Wires & Breadboard",
            "quantity": 1,
            "price": 10,
            "total": 10
        })
        
        return components
    
    def calculate_estimated_cost(self, components):
        """Calculate total estimated cost"""
        total = sum(component["total"] for component in components)
        return {
            "subtotal": round(total, 2),
            "shipping": round(total * 0.1, 2),  # 10% shipping estimate
            "total": round(total * 1.1, 2)
        }