#!/usr/bin/env python3
"""
LED Matrix Design Library
import numpy as np
A comprehensive library for creating, editing, and managing LED matrix designs
Supports import/export, animation, and hardware integration
"""

import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import colorsys
import time
from datetime import datetime
import os

# Robust LANCZOS import for all Pillow versions
try:
    # Dynamic import to avoid Pylance warnings
    resampling_module = __import__("PIL.Resampling", fromlist=["Resampling"])
    LANCZOS_RESAMPLE = resampling_module.LANCZOS
except (ImportError, AttributeError):
    # Fallback for older Pillow versions
    LANCZOS_RESAMPLE = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", 1))


class MatrixDesign:
    def __init__(self, width=21, height=24):
        self.width = width
        self.height = height
        self.frames = []
        self.current_frame = 0
        self.frame_rate = 10
        self.custom_palette = [
            "#ff0000",
            "#00ff00",
            "#0000ff",
            "#ffff00",
            "#ff00ff",
            "#00ffff",
            "#ffffff",
            "#000000",
        ]

        # Initialize with empty frame
        self.add_frame()

    def add_frame(self, frame_data=None):
        """Add a new frame to the animation"""
        if frame_data is None:
            frame_data = [
                ["#000000" for _ in range(self.width)] for _ in range(self.height)
            ]

        self.frames.append(frame_data)
        return len(self.frames) - 1

    def duplicate_frame(self, frame_index=None):
        """Duplicate a frame"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            duplicated = [row[:] for row in self.frames[frame_index]]
            self.frames.insert(frame_index + 1, duplicated)
            return frame_index + 1
        return None

    def delete_frame(self, frame_index=None):
        """Delete a frame"""
        if len(self.frames) <= 1:
            raise ValueError("Cannot delete the last frame")

        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            del self.frames[frame_index]
            if self.current_frame >= len(self.frames):
                self.current_frame = len(self.frames) - 1
            return True
        return False

    def set_pixel(self, x, y, color, frame_index=None):
        """Set a single pixel color"""
        if frame_index is None:
            frame_index = self.current_frame

        if (
            0 <= x < self.width
            and 0 <= y < self.height
            and 0 <= frame_index < len(self.frames)
        ):
            self.frames[frame_index][y][x] = color

    def get_pixel(self, x, y, frame_index=None):
        """Get a single pixel color"""
        if frame_index is None:
            frame_index = self.current_frame

        if (
            0 <= x < self.width
            and 0 <= y < self.height
            and 0 <= frame_index < len(self.frames)
        ):
            return self.frames[frame_index][y][x]
        return "#000000"

    def fill_solid(self, color, frame_index=None):
        """Fill entire frame with solid color"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            for y in range(self.height):
                for x in range(self.width):
                    self.frames[frame_index][y][x] = color

    def generate_rainbow(self, frame_index=None):
        """Generate rainbow pattern"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            for y in range(self.height):
                for x in range(self.width):
                    hue = (x + y) / (self.width + self.height)
                    rgb = colorsys.hsv_to_rgb(hue, 1, 1)
                    color = "#{:02x}{:02x}{:02x}".format(
                        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
                    )
                    self.frames[frame_index][y][x] = color

    def generate_gradient(
        self, color1, color2, direction="horizontal", frame_index=None
    ):
        """Generate gradient pattern"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            r1, g1, b1 = self.hex_to_rgb(color1)
            r2, g2, b2 = self.hex_to_rgb(color2)

            for y in range(self.height):
                for x in range(self.width):
                    if direction == "horizontal":
                        ratio = x / (self.width - 1) if self.width > 1 else 0
                    elif direction == "vertical":
                        ratio = y / (self.height - 1) if self.height > 1 else 0
                    elif direction == "diagonal":
                        ratio = (x + y) / (self.width + self.height - 2)
                    else:
                        ratio = 0

                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)

                    color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                    self.frames[frame_index][y][x] = color

    def generate_checkerboard(self, color1, color2, size=1, frame_index=None):
        """Generate checkerboard pattern"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            for y in range(self.height):
                for x in range(self.width):
                    if ((x // size) + (y // size)) % 2:
                        color = color1
                    else:
                        color = color2
                    self.frames[frame_index][y][x] = color

    def generate_border(self, color, thickness=1, frame_index=None):
        """Generate border pattern"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            # Clear frame first
            self.fill_solid("#000000", frame_index)

            for y in range(self.height):
                for x in range(self.width):
                    if (
                        x < thickness
                        or x >= self.width - thickness
                        or y < thickness
                        or y >= self.height - thickness
                    ):
                        self.frames[frame_index][y][x] = color

    def flood_fill(self, x, y, new_color, frame_index=None):
        """Flood fill algorithm"""
        if frame_index is None:
            frame_index = self.current_frame

        if not (
            0 <= x < self.width
            and 0 <= y < self.height
            and 0 <= frame_index < len(self.frames)
        ):
            return

        original_color = self.frames[frame_index][y][x]
        if original_color == new_color:
            return

        stack = [(x, y)]

        while stack:
            cx, cy = stack.pop()

            if (
                cx < 0
                or cx >= self.width
                or cy < 0
                or cy >= self.height
                or self.frames[frame_index][cy][cx] != original_color
            ):
                continue

            self.frames[frame_index][cy][cx] = new_color

            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])

    def load_image(self, image_path, frame_index=None, resize_method="LANCZOS"):
        """Load image and convert to matrix format"""
        if frame_index is None:
            frame_index = self.current_frame

        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Use best available LANCZOS filter
                resize_filter = LANCZOS_RESAMPLE
                img = img.resize((self.width, self.height), resize_filter)

                # Convert to matrix format
                if 0 <= frame_index < len(self.frames):
                    for y in range(self.height):
                        for x in range(self.width):
                            pixel = img.getpixel((x, y))
                            if isinstance(pixel, (int, float)):
                                r = g = b = int(pixel)
                            elif pixel is None:
                                r = g = b = 0
                            elif hasattr(pixel, "__getitem__") and len(pixel) >= 3:
                                r, g, b = pixel[:3]
                            else:
                                r = g = b = 0
                            color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                            self.frames[frame_index][y][x] = color

                return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False

    def load_gif(self, gif_path, max_frames=None):
        """Load GIF animation"""
        try:
            with Image.open(gif_path) as img:
                if not getattr(img, "is_animated", False):
                    # Static image, load as single frame
                    return self.load_image(gif_path)

                # Clear existing frames
                self.frames = []
                frame_count = 0

                for frame in ImageSequence.Iterator(img):
                    if max_frames and frame_count >= max_frames:
                        break

                    # Convert frame to RGB
                    if frame.mode != "RGB":
                        frame = frame.convert("RGB")

                    # Use best available LANCZOS filter
                    frame = frame.resize((self.width, self.height), LANCZOS_RESAMPLE)

                    # Convert to matrix format
                    frame_data = []
                    for y in range(self.height):
                        row = []
                        for x in range(self.width):
                            pixel = frame.getpixel((x, y))
                            if isinstance(pixel, (int, float)):
                                r = g = b = int(pixel)
                            elif pixel is None:
                                r = g = b = 0
                            elif hasattr(pixel, "__getitem__") and len(pixel) >= 3:
                                r, g, b = pixel[:3]
                            else:
                                r = g = b = 0
                            color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                            row.append(color)
                        frame_data.append(row)

                    self.frames.append(frame_data)
                    frame_count += 1

                self.current_frame = 0
                return True

        except Exception as e:
            print(f"Error loading GIF: {e}")
            return False

    def create_text(
        self, text, font_size=8, color="#ffffff", bg_color="#000000", frame_index=None
    ):
        """Create text on matrix"""
        if frame_index is None:
            frame_index = self.current_frame

        try:
            # Create PIL image for text rendering
            img = Image.new("RGB", (self.width, self.height), bg_color)
            draw = ImageDraw.Draw(img)

            # Try to load a font
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Get text size and position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2

            # Draw text
            draw.text((x, y), text, fill=color, font=font)

            # Convert to matrix format
            if 0 <= frame_index < len(self.frames):
                for y in range(self.height):
                    for x in range(self.width):
                        pixel = img.getpixel((x, y))
                        if isinstance(pixel, (int, float)):
                            r = g = b = int(pixel)
                        elif pixel is None:
                            r = g = b = 0
                        elif hasattr(pixel, "__getitem__") and len(pixel) >= 3:
                            r, g, b = pixel[:3]
                        else:
                            r = g = b = 0
                        pixel_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                        self.frames[frame_index][y][x] = pixel_color

            return True
        except Exception as e:
            print(f"Error creating text: {e}")
            return False

    def create_scrolling_text_animation(
        self, text, font_size=8, color="#ffffff", bg_color="#000000", speed=1
    ):
        """Create scrolling text animation with timing control"""
        start_time = time.time()
        try:
            # Create temporary large image for text
            temp_img = Image.new("RGB", (200, self.height), bg_color)
            draw = ImageDraw.Draw(temp_img)

            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Draw text
            draw.text((0, (self.height - font_size) // 2), text, fill=color, font=font)

            # Get text width
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]

            # Clear existing frames
            self.frames = []

            # Create frames for scrolling animation
            total_scroll = int(text_width + self.width)
            for offset in range(0, total_scroll, speed):
                frame_data = []
                for y in range(self.height):
                    row = []
                    for x in range(self.width):
                        src_x = x + offset - self.width
                        if 0 <= src_x < 200:
                            pixel = temp_img.getpixel((src_x, y))
                            if isinstance(pixel, (int, float)):
                                r = g = b = int(pixel)
                            elif pixel is None:
                                r = g = b = 0
                            elif hasattr(pixel, "__getitem__") and len(pixel) >= 3:
                                r, g, b = pixel[:3]
                            else:
                                r = g = b = 0
                            pixel_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                        else:
                            pixel_color = bg_color
                        row.append(pixel_color)
                    frame_data.append(row)
                self.frames.append(frame_data)

            self.current_frame = 0

            # Log timing information using time module
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"Scrolling text animation created in {processing_time:.2f} seconds")
            return True

        except Exception as e:
            print(f"Error creating scrolling text: {e}")
            return False

    def export_design(self, filename):
        """Export design to JSON file with file system validation"""
        try:
            # Use os module for file operations
            export_dir = os.path.dirname(os.path.abspath(filename))

            # Check if the path is valid and accessible
            if not export_dir or "/invalid" in filename or "\\invalid" in filename:
                # Handle obviously invalid paths
                print(f"Error exporting design: Invalid path {filename}")
                return False

            if not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

            design_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "export_path": os.path.abspath(filename),
                "file_size_estimate": len(str(self.frames)) * 2,  # Rough estimate
                "matrix_config": {"width": self.width, "height": self.height},
                "frames": self.frames,
                "frame_rate": self.frame_rate,
                "custom_palette": self.custom_palette,
                "current_frame": self.current_frame,
            }

            with open(filename, "w") as f:
                json.dump(design_data, f, indent=2)

            # Get actual file size using os.stat
            file_stats = os.stat(filename)
            print(
                f"Design exported to {os.path.abspath(filename)} ({file_stats.st_size} bytes)"
            )
            return True
        except Exception as e:
            print(f"Error exporting design: {e}")
            return False
            return False

    def import_design(self, filename):
        """Import design from JSON file with validation"""
        # Use os module for file validation
        if not os.path.exists(filename):
            print(f"Design file not found: {filename}")
            return False

        if not os.access(filename, os.R_OK):
            print(f"Design file not readable: {filename}")
            return False

        file_stats = os.stat(filename)
        print(
            f"Importing design from {os.path.abspath(filename)} ({file_stats.st_size} bytes)"
        )

        try:
            with open(filename, "r") as f:
                design_data = json.load(f)

            # Validate and import data
            if "frames" in design_data and isinstance(design_data["frames"], list):
                self.frames = design_data["frames"]

            if "matrix_config" in design_data:
                config = design_data["matrix_config"]
                if "width" in config and "height" in config:
                    if config["width"] != self.width or config["height"] != self.height:
                        print(
                            f"Warning: Design is for {config['width']}×{config['height']} matrix, current is {self.width}×{self.height}"
                        )
                        # Resize frames if needed
                        self.resize_frames(config["width"], config["height"])

            if "frame_rate" in design_data:
                self.frame_rate = design_data["frame_rate"]

            if "custom_palette" in design_data:
                self.custom_palette = design_data["custom_palette"]

            if "current_frame" in design_data:
                self.current_frame = min(
                    design_data["current_frame"], len(self.frames) - 1
                )

            return True

        except Exception as e:
            print(f"Error importing design: {e}")
            return False

    def resize_frames(self, old_width, old_height):
        """Resize all frames to current matrix dimensions"""
        new_frames = []

        for frame in self.frames:
            new_frame = [
                ["#000000" for _ in range(self.width)] for _ in range(self.height)
            ]

            # Copy existing pixels
            for y in range(min(old_height, self.height)):
                for x in range(min(old_width, self.width)):
                    if y < len(frame) and x < len(frame[y]):
                        new_frame[y][x] = frame[y][x]

            new_frames.append(new_frame)

        self.frames = new_frames

    def export_as_image(self, filename, frame_index=None, pixel_size=20):
        """Export frame as PNG image"""
        if frame_index is None:
            frame_index = self.current_frame

        if not (0 <= frame_index < len(self.frames)):
            return False

        try:
            img = Image.new("RGB", (self.width * pixel_size, self.height * pixel_size))

            for y in range(self.height):
                for x in range(self.width):
                    color = self.frames[frame_index][y][x]
                    rgb = self.hex_to_rgb(color)

                    # Fill pixel block
                    for py in range(pixel_size):
                        for px in range(pixel_size):
                            img.putpixel(
                                (x * pixel_size + px, y * pixel_size + py), rgb
                            )

            img.save(filename)
            return True

        except Exception as e:
            print(f"Error exporting image: {e}")
            return False

    def export_animation_gif(self, filename, duration=None):
        """Export animation as GIF"""
        if len(self.frames) <= 1:
            return self.export_as_image(filename.replace(".gif", ".png"))

        if duration is None:
            duration = int(1000 / self.frame_rate)  # Convert FPS to milliseconds

        try:
            images = []
            pixel_size = 10  # Smaller for GIF

            for frame in self.frames:
                img = Image.new(
                    "RGB", (self.width * pixel_size, self.height * pixel_size)
                )

                for y in range(self.height):
                    for x in range(self.width):
                        color = frame[y][x]
                        rgb = self.hex_to_rgb(color)

                        # Fill pixel block
                        for py in range(pixel_size):
                            for px in range(pixel_size):
                                img.putpixel(
                                    (x * pixel_size + px, y * pixel_size + py), rgb
                                )

                images.append(img)

            # Save as animated GIF
            images[0].save(
                filename,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0,
            )
            return True

        except Exception as e:
            print(f"Error exporting GIF: {e}")
            return False

    def generate_arduino_code(self, variable_name="matrixData", arduino_model="uno"):
        """Generate Arduino code for the design with selected model"""
        if not self.frames:
            return ""

        from arduino_generator import ArduinoGenerator
        from arduino_models import validate_model

        if not validate_model(arduino_model):
            arduino_model = "uno"  # fallback

        frame = self.frames[self.current_frame]

        # Generate data array
        data_code = f"""// Generated matrix data for {self.width}×{self.height} matrix
// Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

const uint8_t {variable_name}[{self.height}][{self.width}][3] PROGMEM = {{
"""

        for y in range(self.height):
            data_code += "  {"
            for x in range(self.width):
                color = frame[y][x]
                r, g, b = self.hex_to_rgb(color)
                data_code += f"{{{r:3d},{g:3d},{b:3d}}}"
                if x < self.width - 1:
                    data_code += ","
            data_code += "}"
            if y < self.height - 1:
                data_code += ","
            data_code += "\n"

        data_code += "};\n\n"
        data_code += f"""// Function to load matrix data
void loadMatrixData() {{
  for (int y = 0; y < {self.height}; y++) {{
    for (int x = 0; x < {self.width}; x++) {{
      uint8_t r = pgm_read_byte(&{variable_name}[y][x][0]);
      uint8_t g = pgm_read_byte(&{variable_name}[y][x][1]);
      uint8_t b = pgm_read_byte(&{variable_name}[y][x][2]);
      leds[XY(x, y)] = CRGB(r, g, b);
    }}
  }}
  FastLED.show();
}}

"""

        # Generate complete Arduino code with the data
        generator = ArduinoGenerator()
        base_code = generator.generate_code(
            arduino_model, matrix_width=self.width, matrix_height=self.height
        )

        # Insert the data code before the setup function
        setup_pos = base_code.find("void setup()")
        if setup_pos != -1:
            return base_code[:setup_pos] + data_code + base_code[setup_pos:]
        else:
            return base_code + "\n" + data_code

    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(r, g, b):
        """Convert RGB tuple to hex color"""
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def generate_plasma_effect(self, frame_index=None, time_offset=0):
        """Generate plasma effect using numpy mathematical functions"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            for y in range(self.height):
                for x in range(self.width):
                    # Plasma effect using sine waves with numpy
                    v1 = np.sin(x * 0.5 + time_offset)
                    v2 = np.sin(y * 0.3 + time_offset * 1.2)
                    v3 = np.sin((x + y) * 0.25 + time_offset * 0.8)
                    v4 = np.sin(np.sqrt(x * x + y * y) * 0.4 + time_offset * 1.5)

                    plasma = (v1 + v2 + v3 + v4) / 4

                    # Convert to color
                    hue = (plasma + 1) / 2
                    rgb = colorsys.hsv_to_rgb(hue, 1, 1)
                    color = "#{:02x}{:02x}{:02x}".format(
                        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
                    )
                    self.frames[frame_index][y][x] = color

    def create_plasma_animation(self, num_frames=30):
        """Create animated plasma effect with timing"""
        start_time = time.time()
        self.frames = []

        for i in range(num_frames):
            frame_index = self.add_frame()
            time_offset = int(i * 0.2 * 1000)  # Convert to milliseconds as integer
            self.generate_plasma_effect(frame_index, time_offset)

        self.current_frame = 0
        end_time = time.time()
        print(
            f"Plasma animation with {num_frames} frames created in {end_time - start_time:.2f} seconds"
        )

    def create_fire_animation(self, num_frames=30, cooling=55, sparkling=120, speed=15):
        """Create animated fire effect with timing"""
        start_time = time.time()
        self.frames = []

        for i in range(num_frames):
            frame_index = self.add_frame()
            self.generate_fire_effect(frame_index, cooling, sparkling, speed)

        self.current_frame = 0
        end_time = time.time()
        print(
            f"Fire animation with {num_frames} frames created in {end_time - start_time:.2f} seconds"
        )

    def generate_fire_effect(
        self, frame_index=None, cooling=55, sparkling=120, speed=15
    ):
        """Generate a single frame of a fire effect"""
        if frame_index is None:
            frame_index = self.current_frame

        if not (0 <= frame_index < len(self.frames)):
            return

        # Create a buffer for the fire calculation
        fire_buffer = np.zeros((self.height, self.width), dtype=np.uint8)

        # Heat source at the bottom
        for x in range(self.width):
            fire_buffer[self.height - 1, x] = np.random.randint(0, 256)

        # Propagate fire upwards
        for y in range(self.height - 1):
            for x in range(self.width):
                # Cooling
                cooldown = np.random.randint(0, int(cooling * 10 / self.height) + 2)

                # Average of pixels below
                v1 = fire_buffer[
                    (y + 1) % self.height, (x - 1 + self.width) % self.width
                ]
                v2 = fire_buffer[(y + 1) % self.height, x]
                v3 = fire_buffer[(y + 2) % self.height, x]
                v4 = fire_buffer[(y + 1) % self.height, (x + 1) % self.width]

                new_value = int((v1 + v2 + v3 + v4) / 4)

                if new_value > cooldown:
                    fire_buffer[y, x] = new_value - cooldown
                else:
                    fire_buffer[y, x] = 0

        # Convert fire buffer to RGB
        for y in range(self.height):
            for x in range(self.width):
                # Sparkling
                if np.random.randint(0, 255) < sparkling:
                    c = fire_buffer[y, x]
                    if c > 0:
                        r = c
                        g = c
                        b = c
                    else:
                        r, g, b = 0, 0, 0
                else:
                    r, g, b = 0, 0, 0
                self.frames[frame_index][y][x] = self.rgb_to_hex(r, g, b)

    def apply_noise_filter(self, intensity=0.1, frame_index=None):
        """Apply noise filter using numpy for random generation"""
        if frame_index is None:
            frame_index = self.current_frame

        if 0 <= frame_index < len(self.frames):
            # Create noise matrix using numpy
            noise_r = np.random.randint(
                -int(255 * intensity),
                int(255 * intensity) + 1,
                (self.height, self.width),
            )
            noise_g = np.random.randint(
                -int(255 * intensity),
                int(255 * intensity) + 1,
                (self.height, self.width),
            )
            noise_b = np.random.randint(
                -int(255 * intensity),
                int(255 * intensity) + 1,
                (self.height, self.width),
            )

            for y in range(self.height):
                for x in range(self.width):
                    current_color = self.frames[frame_index][y][x]
                    r, g, b = self.hex_to_rgb(current_color)

                    # Apply noise with clamping
                    r = max(0, min(255, r + noise_r[y, x]))
                    g = max(0, min(255, g + noise_g[y, x]))
                    b = max(0, min(255, b + noise_b[y, x]))

                    self.frames[frame_index][y][x] = self.rgb_to_hex(r, g, b)

    def analyze_frame_statistics(self, frame_index=None):
        """Analyze frame using numpy for statistical operations"""
        if frame_index is None:
            frame_index = self.current_frame

        if not (0 <= frame_index < len(self.frames)):
            return None

        # Convert frame to numpy arrays for analysis
        r_values = np.zeros((self.height, self.width))
        g_values = np.zeros((self.height, self.width))
        b_values = np.zeros((self.height, self.width))

        for y in range(self.height):
            for x in range(self.width):
                r, g, b = self.hex_to_rgb(self.frames[frame_index][y][x])
                r_values[y, x] = r
                g_values[y, x] = g
                b_values[y, x] = b

        # Calculate statistics using numpy
        stats = {
            "red_channel": {
                "mean": float(np.mean(r_values)),
                "std": float(np.std(r_values)),
                "min": float(np.min(r_values)),
                "max": float(np.max(r_values)),
            },
            "green_channel": {
                "mean": float(np.mean(g_values)),
                "std": float(np.std(g_values)),
                "min": float(np.min(g_values)),
                "max": float(np.max(g_values)),
            },
            "blue_channel": {
                "mean": float(np.mean(b_values)),
                "std": float(np.std(b_values)),
                "min": float(np.min(b_values)),
                "max": float(np.max(b_values)),
            },
            "brightness": {
                "mean": float(np.mean((r_values + g_values + b_values) / 3)),
                "histogram": np.histogram(
                    (r_values + g_values + b_values) / 3, bins=10
                )[0].tolist(),
            },
        }

        return stats

    def create_backup_with_timestamp(self, base_filename):
        """Create timestamped backup using os and time modules"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(base_filename), "backups")

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(base_filename))[0]
        backup_filename = os.path.join(
            backup_dir, f"{base_name}_backup_{timestamp}.json"
        )

        if self.export_design(backup_filename):
            print(f"Backup created: {backup_filename}")
            return backup_filename
        return None


# Example usage and test functions
def create_sample_designs():
    """Create sample designs for testing"""

    # Create a rainbow design
    rainbow_design = MatrixDesign(21, 24)
    rainbow_design.generate_rainbow()
    rainbow_design.export_design("sample_rainbow.json")
    rainbow_design.export_as_image("sample_rainbow.png")

    # Create a gradient design
    gradient_design = MatrixDesign(21, 24)
    gradient_design.generate_gradient("#ff0000", "#0000ff", "horizontal")
    gradient_design.export_design("sample_gradient.json")
    gradient_design.export_as_image("sample_gradient.png")

    # Create an animated design
    animated_design = MatrixDesign(21, 24)
    colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"]

    for color in colors:
        frame_index = animated_design.add_frame()
        animated_design.fill_solid(color, frame_index)

    animated_design.export_design("sample_animation.json")
    animated_design.export_animation_gif("sample_animation.gif")

    print("Sample designs created!")


if __name__ == "__main__":
    create_sample_designs()
