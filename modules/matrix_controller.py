#!/usr/bin/env python3
"""
Unified LED Matrix Controller
Combines basic and advanced features into one comprehensive controller
"""

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
import threading
import time
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance
import colorsys
import urllib.parse
import json
import os
import sys
import psutil  # For system monitoring
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Robust resampling filter imports for Pillow compatibility
try:
    from PIL import Image as PILImage

    Resampling = getattr(PILImage, "Resampling", None)
    if Resampling is not None:
        LANCZOS_RESAMPLE = Resampling.LANCZOS
        NEAREST_RESAMPLE = Resampling.NEAREST
    else:
        LANCZOS_RESAMPLE = getattr(
            Image, "LANCZOS", getattr(Image, "BICUBIC", getattr(Image, "BILINEAR", 0))
        )
        NEAREST_RESAMPLE = getattr(Image, "NEAREST", getattr(Image, "BILINEAR", 0))
except Exception:
    LANCZOS_RESAMPLE = getattr(
        Image, "LANCZOS", getattr(Image, "BICUBIC", getattr(Image, "BILINEAR", 0))
    )
    NEAREST_RESAMPLE = getattr(Image, "NEAREST", getattr(Image, "BILINEAR", 0))

# Import shared modules
from matrix_config import config
from matrix_hardware import hardware


class UnifiedMatrixController:
    def __init__(self):
        # Matrix properties from shared config
        self.config = config
        self.W = int(config.get("matrix_width", 16))
        self.H = int(config.get("matrix_height", 16))

        # GUI and state attributes
        self.root = tk.Tk()
        self.start_time = datetime.now()
        self.current_mode = "idle"
        self.text_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.width_var = tk.IntVar(value=self.W)
        self.height_var = tk.IntVar(value=self.H)
        self.port_var = tk.StringVar()
        self.mode_var = tk.StringVar()
        self.arduino_model_var = tk.StringVar()
        self.monitor_enabled = tk.BooleanVar(value=False)
        self.show_cpu = tk.BooleanVar(value=True)
        self.show_memory = tk.BooleanVar(value=True)

        # Canvas and matrix data
        self.canvas = tk.Canvas(self.root, width=240, height=240, bg="black")
        self.canvas.pack()
        self.matrix_data = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        self.current_mode = "manual"
        self.is_streaming = False
        self.last_text_photo = None

        # Start web server
        self._start_web_server()

    def _start_web_server(self):
        """Start the web API server"""
        controller = self

        def run_server():
            class WebHandler(BaseHTTPRequestHandler):
                def send_cors_headers(self):
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header(
                        "Access-Control-Allow-Methods", "GET, POST, OPTIONS"
                    )
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

                    if path == "/status":
                        status = {
                            "connected": True,
                            "matrix": {"width": controller.W, "height": controller.H},
                            "current_mode": getattr(controller, "current_mode", "idle"),
                            "timestamp": datetime.now().isoformat(),
                        }
                        self.send_json_response(status)

                    elif path == "/config":
                        config_data = {
                            "connectionMode": controller.config.get(
                                "connection_mode", "USB"
                            ),
                            "serialPort": controller.config.get("serial_port", ""),
                            "baudRate": controller.config.get("baud_rate", 115200),
                        }
                        self.send_json_response(config_data)

                    elif path == "/system":
                        try:
                            cpu_percent = psutil.cpu_percent()
                            memory = psutil.virtual_memory()
                            system_stats = {
                                "cpu": cpu_percent,
                                "memory": memory.percent,
                                "uptime": str(
                                    datetime.now() - controller.start_time
                                ).split(".")[0],
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

                    elif path == "/hardware":
                        hardware_info = {
                            "controller": "Python Matrix Controller",
                            "port": controller.config.get(
                                "serial_port", "Not connected"
                            ),
                            "baudRate": controller.config.get("baud_rate", 115200),
                            "matrixSize": f"{controller.W}×{controller.H}",
                        }
                        self.send_json_response(hardware_info)

                    elif path == "/backups":
                        # List available backups
                        backups = []
                        try:
                            backup_dir = os.path.join(
                                os.path.dirname(__file__), "..", "backups"
                            )
                            if os.path.exists(backup_dir):
                                backups = [
                                    f
                                    for f in os.listdir(backup_dir)
                                    if f.endswith(".json")
                                ]
                        except:
                            pass
                        self.send_json_response(backups)

                    else:
                        # Serve the main web interface
                        self.send_response(200)
                        self.send_cors_headers()
                        self.send_header("Content-type", "text/html")
                        self.end_headers()

                        # Try to serve the actual HTML file
                        try:
                            sites_dir = os.path.join(
                                os.path.dirname(__file__), "..", "sites"
                            )
                            html_file = os.path.join(sites_dir, "index.html")
                            if os.path.exists(html_file):
                                with open(html_file, "r", encoding="utf-8") as f:
                                    self.wfile.write(f.read().encode())
                            else:
                                raise FileNotFoundError
                        except:
                            # Fallback HTML
                            html = f"""
                            <html><head><title>Matrix Controller API</title></head>
                            <body>
                                <h1>LED Matrix Remote Control API</h1>
                                <p>Matrix: {controller.W}×{controller.H}</p>
                                <p>Status: Running</p>
                                <h2>Available Endpoints:</h2>
                                <ul>
                                    <li>GET /status - Get controller status</li>
                                    <li>POST /pattern - Apply pattern</li>
                                    <li>POST /clear - Clear matrix</li>
                                    <li>POST /generate - Generate Arduino code</li>
                                    <li>POST /wiring - Generate wiring guide</li>
                                    <li>GET /config - Get configuration</li>
                                    <li>POST /config - Save configuration</li>
                                </ul>
                            </body></html>
                            """
                            self.wfile.write(html.encode())

                def do_POST(self):
                    parsed_url = urllib.parse.urlparse(self.path)
                    path = parsed_url.path

                    # Read POST data
                    content_length = int(self.headers.get("Content-Length", 0))
                    post_data = self.rfile.read(content_length)

                    try:
                        data = json.loads(post_data.decode()) if post_data else {}
                    except:
                        data = {}

                    if path == "/pattern":
                        try:
                            pattern = data.get("pattern", "solid")
                            color = data.get("color", "#ff0000")
                            brightness = int(data.get("brightness", 128))
                            speed = int(data.get("speed", 50))

                            # Apply pattern (simplified implementation)
                            controller.apply_pattern(pattern, color, brightness, speed)
                            self.send_json_response(
                                {
                                    "status": "success",
                                    "message": f"Applied {pattern} pattern",
                                }
                            )
                        except Exception as e:
                            self.send_json_response(
                                {"status": "error", "message": str(e)}, 500
                            )

                    elif path == "/clear":
                        try:
                            controller.clear_matrix()
                            self.send_json_response(
                                {"status": "success", "message": "Matrix cleared"}
                            )
                        except Exception as e:
                            self.send_json_response(
                                {"status": "error", "message": str(e)}, 500
                            )

                    elif path == "/generate":
                        try:
                            from arduino_generator import ArduinoGenerator

                            generator = ArduinoGenerator()

                            board = data.get("board", "uno")
                            width = data.get("width", 16)
                            height = data.get("height", 16)

                            code = generator.generate_code(
                                board, matrix_width=width, matrix_height=height
                            )
                            self.send_json_response({"status": "success", "code": code})
                        except Exception as e:
                            self.send_json_response(
                                {"status": "error", "message": str(e)}, 500
                            )

                    elif path == "/wiring":
                        try:
                            from wiring_diagram_generator import WiringDiagramGenerator

                            generator = WiringDiagramGenerator()

                            controller_type = data.get("controller", "arduino_uno")
                            width = data.get("width", 16)
                            height = data.get("height", 16)

                            guide = generator.generate_complete_guide(
                                controller_type, width, height
                            )
                            self.send_json_response(
                                {"status": "success", "guide": guide}
                            )
                        except Exception as e:
                            self.send_json_response(
                                {"status": "error", "message": str(e)}, 500
                            )

                    elif path == "/config":
                        try:
                            # Save configuration
                            for key, value in data.items():
                                if key == "connectionMode":
                                    controller.config.set("connection_mode", value)
                                elif key == "serialPort":
                                    controller.config.set("serial_port", value)
                                elif key == "baudRate":
                                    controller.config.set("baud_rate", value)

                            controller.config.save_config()
                            self.send_json_response(
                                {"status": "success", "message": "Configuration saved"}
                            )
                        except Exception as e:
                            self.send_json_response(
                                {"status": "error", "message": str(e)}, 500
                            )

                    elif path == "/backup":
                        try:
                            # Create backup
                            backup_filename = controller.config.create_backup()
                            self.send_json_response(
                                {"status": "success", "filename": backup_filename}
                            )
                        except Exception as e:
                            self.send_json_response(
                                {"status": "error", "message": str(e)}, 500
                            )

                    else:
                        self.send_json_response(
                            {"status": "error", "message": "Endpoint not found"}, 404
                        )

            try:
                server = HTTPServer(
                    ("localhost", config.get("web_port", 8080)), WebHandler
                )
                print(
                    f"\n🌐 Web API server started on http://localhost:{config.get('web_port', 8080)}"
                )
                server.serve_forever()
            except Exception as e:
                print(f"Web server error: {e}")

        threading.Thread(target=run_server, daemon=True).start()

    def clear_matrix(self):
        """Clear the LED matrix display"""
        self.matrix_data.fill(0)
        self.update_canvas()
        self.send_frame()

    def rainbow_pattern(self):
        """Display a rainbow pattern on the matrix"""
        for y in range(int(self.H)):
            for x in range(int(self.W)):
                hue = (x + y) * 360 / (int(self.W) + int(self.H))
                rgb = colorsys.hsv_to_rgb(hue / 360, 1, 1)
                self.matrix_data[y, x] = [int(c * 255) for c in rgb]
        self.update_canvas()
        self.send_frame()

    def update_canvas(self):
        """Update the GUI canvas with the current matrix data"""
        self.canvas.delete("all")
        h, w = int(self.H), int(self.W)
        for y in range(h):
            for x in range(w):
                color = "#%02x%02x%02x" % tuple(self.matrix_data[y, x])
                self.canvas.create_rectangle(
                    x * 15, y * 15, (x + 1) * 15, (y + 1) * 15, fill=color, outline=""
                )

    def send_frame(self):
        """Send the current matrix frame to hardware"""
        try:
            hardware.send_frame(self.matrix_data)
        except Exception as e:
            print(f"Hardware send error: {e}")

    def load_image(self):
        """Load and display an image with enhancement options"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.avi")]
        )
        if file_path:
            try:
                # Check if it's a video file
                if file_path.lower().endswith((".mp4", ".avi", ".mov")):
                    self._load_video_frame(file_path)
                    return

                # Load and enhance image
                img = Image.open(file_path)

                # Apply image enhancements
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)  # Increase contrast

                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)  # Slight sharpening

                img = img.convert("RGB").resize((self.W, self.H), LANCZOS_RESAMPLE)
                self.matrix_data = np.array(img)
                self.update_canvas()
                self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def _load_video_frame(self, file_path):
        """Load first frame from video file using cv2"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                messagebox.showerror("Error", "Could not open video file")
                return

            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((self.W, self.H), LANCZOS_RESAMPLE)
                self.matrix_data = np.array(img)
                self.update_canvas()
                self.status_var.set(
                    f"Loaded video frame: {os.path.basename(file_path)}"
                )

            cap.release()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")

    def scroll_text(self):
        """Scroll text across matrix"""
        text = self.text_var.get()
        if text:
            self.current_mode = "text"
            self.is_streaming = True
            threading.Thread(target=self._text_loop, args=(text,), daemon=True).start()

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

            self.root.after(0, self.update_canvas)
            self.root.after(0, self.send_frame)
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
        self.current_mode = "manual"
        self.status_var.set("Animation stopped")

    def choose_color(self):
        """Open color chooser and fill matrix with selected color"""
        color = colorchooser.askcolor(title="Choose Matrix Color")
        if color[0]:  # color[0] is RGB tuple, color[1] is hex
            rgb = [int(c) for c in color[0]]
            self.matrix_data.fill(0)
            self.matrix_data[:, :] = rgb
            self.update_canvas()
            self.send_frame()
            self.status_var.set(f"Matrix filled with color: {color[1]}")

    def draw_text_image(self):
        """Draw text using PIL ImageDraw and ImageFont with better rendering"""
        try:
            text = self.text_var.get()
            if not text:
                return

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
            self.update_canvas()
            self.send_frame()

            # Create PhotoImage for preview
            self.last_text_photo = ImageTk.PhotoImage(
                img_resized.resize((self.W * 8, self.H * 8), NEAREST_RESAMPLE)
            )

            self.status_var.set(f"Text rendered: '{text}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to draw text: {str(e)}")

    def system_monitor(self):
        """Display system monitoring information"""
        if not hasattr(self, "monitor_thread") or not self.monitor_thread.is_alive():
            self.current_mode = "monitor"
            self.is_streaming = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitor_thread.start()
        else:
            self.stop_animation()

    def _monitor_loop(self):
        """System monitoring loop using psutil"""
        while self.is_streaming and self.current_mode == "monitor":
            try:
                # Get system stats
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()

                # Clear matrix
                self.matrix_data.fill(0)

                # Draw CPU usage bar (left side)
                cpu_height = int((cpu_percent / 100) * self.H)
                for y in range(self.H - cpu_height, self.H):
                    for x in range(min(3, self.W)):
                        intensity = int(255 * (cpu_percent / 100))
                        self.matrix_data[y, x] = [intensity, 0, 0]  # Red for CPU

                # Draw memory usage bar (right side)
                mem_height = int((memory.percent / 100) * self.H)
                start_x = max(self.W - 3, 4)
                for y in range(self.H - mem_height, self.H):
                    for x in range(start_x, self.W):
                        intensity = int(255 * (memory.percent / 100))
                        self.matrix_data[y, x] = [0, intensity, 0]  # Green for memory

                # Add timestamp info in middle
                current_time = datetime.now()
                if current_time.second % 2 == 0:  # Blink every second
                    mid_x = self.W // 2
                    mid_y = self.H // 2
                    self.matrix_data[mid_y, mid_x] = [0, 0, 255]  # Blue dot

                self.root.after(0, self.update_canvas)
                self.root.after(0, self.send_frame)

                # Update status with current stats
                status_text = f"CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}% | {current_time.strftime('%H:%M:%S')}"
                self.root.after(0, lambda: self.status_var.set(status_text))

                time.sleep(1)

            except Exception as e:
                print(f"Monitor error: {e}", file=sys.stderr)
                break

    @staticmethod
    def _safe_int(val, default):
        return int(val) if str(val).isdigit() else default

    def apply_matrix_config(self):
        """Apply new matrix configuration"""
        new_w = self._safe_int(self.width_var.get(), 16)
        new_h = self._safe_int(self.height_var.get(), 16)

        if new_w != int(self.W) or new_h != int(self.H):
            self.W = new_w
            self.H = new_h
            self.matrix_data = np.zeros((self.H, self.W, 3), dtype=np.uint8)
            self.update_canvas()
            self.config.update({"matrix_width": new_w, "matrix_height": new_h})
            self.status_var.set(f"Matrix resized to {new_w}x{new_h}")

    def apply_pattern(self, pattern, color, brightness, speed):
        """Apply a pattern to the matrix"""
        try:
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

            elif pattern == "rainbow":
                self.rainbow_pattern()
                return  # rainbow_pattern handles its own update

            elif pattern == "plasma":
                self._generate_plasma_pattern(speed)
                return  # plasma handles its own update

            elif pattern == "fire":
                self._generate_fire_pattern(speed)
                return  # fire handles its own update

            elif pattern == "matrix":
                self._generate_matrix_rain_pattern(speed)
                return  # matrix rain handles its own update

            self.update_canvas()
            self.send_frame()

        except Exception as e:
            print(f"Error applying pattern: {e}")

    def _generate_plasma_pattern(self, speed):
        """Generate plasma effect pattern"""
        import math

        time_factor = time.time() * speed / 10.0

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

        self.update_canvas()
        self.send_frame()

    def _generate_fire_pattern(self, speed):
        """Generate fire effect pattern"""
        # Simple fire simulation
        for y in range(self.H):
            for x in range(self.W):
                # Fire intensity based on position and randomness
                intensity = max(
                    0, (self.H - y) / self.H + np.random.random() * 0.3 - 0.15
                )

                # Fire colors: red to yellow to white
                if intensity > 0.8:
                    self.matrix_data[y, x] = [255, 255, int(255 * intensity)]
                elif intensity > 0.4:
                    self.matrix_data[y, x] = [255, int(255 * intensity), 0]
                else:
                    self.matrix_data[y, x] = [int(255 * intensity), 0, 0]

        self.update_canvas()
        self.send_frame()

    def _generate_matrix_rain_pattern(self, speed):
        """Generate Matrix rain effect"""
        # Simple matrix rain simulation
        for x in range(self.W):
            # Random chance to start a new drop
            if np.random.random() < 0.1:
                for y in range(self.H):
                    if np.random.random() < 0.3:
                        self.matrix_data[y, x] = [0, 255, 0]  # Green
                    else:
                        self.matrix_data[y, x] = [0, 0, 0]  # Black

        self.update_canvas()
        self.send_frame()

    def run(self):
        """Run the controller"""
        self.root.title("Unified Matrix Controller")
        self.root.geometry("800x600")

        # Create basic GUI
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)

        ttk.Button(control_frame, text="Clear", command=self.clear_matrix).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Rainbow", command=self.rainbow_pattern).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Load Image", command=self.load_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Choose Color", command=self.choose_color).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            control_frame, text="System Monitor", command=self.system_monitor
        ).pack(side=tk.LEFT, padx=5)

        text_frame = ttk.Frame(self.root)
        text_frame.pack(pady=10)

        ttk.Label(text_frame, text="Text:").pack(side=tk.LEFT)
        ttk.Entry(text_frame, textvariable=self.text_var, width=20).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(text_frame, text="Scroll", command=self.scroll_text).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(text_frame, text="Draw Text", command=self.draw_text_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(text_frame, text="Stop", command=self.stop_animation).pack(
            side=tk.LEFT, padx=5
        )

        status_frame = ttk.Frame(self.root)
        status_frame.pack(pady=10)
        ttk.Label(status_frame, textvariable=self.status_var).pack()

        self.status_var.set("Matrix Controller Ready")
        self.root.mainloop()


if __name__ == "__main__":
    controller = UnifiedMatrixController()
    controller.run()
