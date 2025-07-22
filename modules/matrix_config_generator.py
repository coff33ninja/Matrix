#!/usr/bin/env python3
"""
LED Matrix Configuration Generator
Generates Arduino and Python code for custom matrix configurations
"""

import json
import math
from matrix_config import config as shared_config
from arduino_generator import ArduinoGenerator
from arduino_models import (
    get_available_models,
    get_model_display_names,
    validate_model,
    get_model_info,
)


class MatrixConfigGenerator:
    def __init__(self):
        # Use shared config as base, allow overrides
        defaults = {
            "width": 21,
            "height": 24,
            "leds_per_meter": 144,
            "wiring_pattern": "serpentine",
            "physical_width": 146,
            "physical_height": 167,
            "brightness": 128,
            "data_pin": 6,
        }
        self.config = {
            "width": shared_config.get("matrix_width"),
            "height": shared_config.get("matrix_height"),
            "leds_per_meter": shared_config.get("leds_per_meter"),
            "wiring_pattern": shared_config.get("wiring_pattern"),
            "physical_width": shared_config.get("physical_width"),
            "physical_height": shared_config.get("physical_height"),
            "brightness": shared_config.get("brightness"),
            "data_pin": shared_config.get("data_pin"),
        }
        # Validate and fill missing/None values with defaults
        for k, v in defaults.items():
            if self.config.get(k) is None:
                self.config[k] = v
        self.arduino_generator = ArduinoGenerator()

    def set_config(self, **kwargs):
        """Update configuration parameters"""
        self.config.update(kwargs)

    def calculate_specs(self):
        """Calculate derived specifications"""
        specs = {}

        # Defensive: ensure all required config values are present and not None
        required = ["width", "height", "leds_per_meter", "brightness"]
        defaults = {"width": 21, "height": 24, "leds_per_meter": 144, "brightness": 128}
        for k in required:
            if self.config.get(k) is None:
                self.config[k] = defaults[k]

        # Basic calculations
        width = self.config["width"] if self.config["width"] is not None else 21
        height = self.config["height"] if self.config["height"] is not None else 24
        specs["total_leds"] = width * height
        leds_per_meter = self.config["leds_per_meter"] or 1  # avoid division by zero
        specs["led_spacing"] = 1000 / leds_per_meter  # mm
        specs["strip_length"] = specs["total_leds"] / leds_per_meter  # meters

        # Power calculations
        specs["max_current_per_led"] = 0.06  # 60mA
        specs["max_current_total"] = specs["total_leds"] * specs["max_current_per_led"]
        specs["typical_current"] = specs["max_current_total"] * 0.5  # 50% usage
        specs["actual_current"] = specs["max_current_total"] * (
            (self.config["brightness"] or 128) / 255
        )

        # Memory usage
        specs["memory_usage"] = specs["total_leds"] * 3  # 3 bytes per LED (RGB)

        # Performance estimates
        specs["max_frame_rate"] = min(60, math.floor(16000 / specs["total_leds"]))
        specs["data_rate"] = (
            specs["total_leds"] * 3 * specs["max_frame_rate"]
        )  # bytes/sec

        # Cost estimates (rough)
        specs["led_strip_cost"] = math.ceil(specs["strip_length"] * 10)  # $10/meter
        specs["power_supply_cost"] = (
            45
            if specs["max_current_total"] > 20
            else 35 if specs["max_current_total"] > 15 else 25
        )
        specs["total_cost"] = (
            specs["led_strip_cost"] + specs["power_supply_cost"] + 25
        )  # +25 for controller/components

        return specs

    def generate_arduino_code(self, model_key="uno"):
        """Generate Arduino code for the specified model using new generator"""
        if not validate_model(model_key):
            raise ValueError(f"Invalid Arduino model: {model_key}")

        return self.arduino_generator.generate_code(
            model_key,
            matrix_width=self.config["width"],
            matrix_height=self.config["height"],
            data_pin=self.config["data_pin"],
            brightness=self.config["brightness"],
        )

    def get_arduino_recommendations(self):
        """Get Arduino model recommendations for current configuration"""
        return self.arduino_generator.get_model_recommendations(
            matrix_width=self.config["width"], matrix_height=self.config["height"]
        )

    def generate_python_code(self):
        """Generate Python code for the configuration"""
        specs = self.calculate_specs()

        python_code = f"""#!/usr/bin/env python3
\"\"\"
Custom LED Matrix Configuration
Generated for {self.config['width']}x{self.config['height']} matrix
Total LEDs: {specs['total_leds']}
Strip Length: {specs['strip_length']:.1f}m
Max Current: {specs['max_current_total']:.2f}A
\"\"\"

import numpy as np
import serial
import struct
import time
from PIL import Image

# Matrix Configuration
MATRIX_WIDTH = {self.config['width']}
MATRIX_HEIGHT = {self.config['height']}
NUM_LEDS = {specs['total_leds']}
LED_SPACING = {specs['led_spacing']:.2f}  # mm
BRIGHTNESS = {self.config['brightness']}
WIRING_PATTERN = "{self.config['wiring_pattern']}"

# Physical dimensions (mm)
PHYSICAL_WIDTH = {self.config['physical_width']}
PHYSICAL_HEIGHT = {self.config['physical_height']}

# Power specifications
MAX_CURRENT_PER_LED = {specs['max_current_per_led']}  # Amps
MAX_CURRENT_TOTAL = {specs['max_current_total']:.3f}  # Amps
ACTUAL_CURRENT = {specs['actual_current']:.3f}  # Amps at current brightness

# Performance specifications
MAX_FRAME_RATE = {specs['max_frame_rate']}  # FPS
MEMORY_USAGE = {specs['memory_usage']}  # bytes
DATA_RATE = {specs['data_rate']}  # bytes/second

class MatrixController:
    def __init__(self, port='COM3', baud_rate=500000):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.matrix_data = np.zeros((MATRIX_HEIGHT, MATRIX_WIDTH, 3), dtype=np.uint8)
    
    def connect(self):
        \"\"\"Connect to Arduino\"\"\"
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Connected to {{self.port}}")
            return True
        except Exception as e:
            print(f"Connection failed: {{e}}")
            return False
    
    def disconnect(self):
        \"\"\"Disconnect from Arduino\"\"\"
        if self.ser:
            self.ser.close()
            self.ser = None
    
    def send_frame(self):
        \"\"\"Send current matrix data to Arduino\"\"\"
        if not self.ser:
            print("Not connected!")
            return
        
        # Apply brightness
        brightness_factor = BRIGHTNESS / 255.0
        data = (self.matrix_data * brightness_factor).astype(np.uint8)
        
        # Send as bytes
        frame_data = data.flatten().tobytes()
        self.ser.write(frame_data)
    
    def clear(self):
        \"\"\"Clear the matrix\"\"\"
        self.matrix_data.fill(0)
        self.send_frame()
    
    def fill(self, color):
        \"\"\"Fill matrix with color (r, g, b)\"\"\"
        self.matrix_data[:] = color
        self.send_frame()
    
    def set_pixel(self, x, y, color):
        \"\"\"Set individual pixel\"\"\"
        if 0 <= x < MATRIX_WIDTH and 0 <= y < MATRIX_HEIGHT:
            self.matrix_data[y, x] = color
    
    def load_image(self, image_path):
        \"\"\"Load and display image\"\"\"
        try:
            img = Image.open(image_path)
            img = img.convert('RGB').resize((MATRIX_WIDTH, MATRIX_HEIGHT), Image.LANCZOS)
            self.matrix_data = np.array(img)
            self.send_frame()
            print(f"Loaded image: {{image_path}}")
        except Exception as e:
            print(f"Failed to load image: {{e}}")
    
    def rainbow(self):
        \"\"\"Create rainbow pattern\"\"\"
        for y in range(MATRIX_HEIGHT):
            for x in range(MATRIX_WIDTH):
                hue = (x + y) * 360 / (MATRIX_WIDTH + MATRIX_HEIGHT)
                # Convert HSV to RGB
                import colorsys
                rgb = colorsys.hsv_to_rgb(hue/360, 1, 1)
                self.matrix_data[y, x] = [int(c * 255) for c in rgb]
        self.send_frame()
    
    def print_specs(self):
        \"\"\"Print matrix specifications\"\"\"
        print(f"Matrix Configuration:")
        print(f"  Dimensions: {{MATRIX_WIDTH}}×{{MATRIX_HEIGHT}} = {{NUM_LEDS}} LEDs")
        print(f"  Physical Size: {{PHYSICAL_WIDTH}}×{{PHYSICAL_HEIGHT}} mm")
        print(f"  LED Spacing: {{LED_SPACING:.2f}} mm")
        print(f"  Strip Length: {specs['strip_length']:.1f} meters")
        print(f"  Wiring Pattern: {{WIRING_PATTERN}}")
        print("")
        print(f"Power Requirements:")
        print(f"  Max Current: {{MAX_CURRENT_TOTAL:.2f}}A")
        print(f"  Current @ {{BRIGHTNESS}}: {{ACTUAL_CURRENT:.2f}}A")
        print(f"  Recommended PSU: 5V {{math.ceil(MAX_CURRENT_TOTAL * 1.2)}}A")
        print("")
        print(f"Performance:")
        print(f"  Max Frame Rate: {{MAX_FRAME_RATE}} FPS")
        print(f"  Memory Usage: {{MEMORY_USAGE / 1024:.1f}} KB")
        print(f"  Data Rate: {{DATA_RATE / 1024:.1f}} KB/s")

# Example usage
if __name__ == "__main__":
    matrix = MatrixController()
    matrix.print_specs()
    
    if matrix.connect():
        print("\\nTesting matrix...")
        
        # Clear matrix
        matrix.clear()
        time.sleep(1)
        
        # Fill with red
        matrix.fill([255, 0, 0])
        time.sleep(1)
        
        # Rainbow pattern
        matrix.rainbow()
        time.sleep(2)
        
        # Clear and disconnect
        matrix.clear()
        matrix.disconnect()
        print("Test complete!")
    else:
        print("Could not connect to matrix")"""

        return python_code

    def generate_config_file(self):
        """Generate JSON configuration file"""
        specs = self.calculate_specs()

        config_data = {
            "matrix_configuration": self.config,
            "calculated_specs": specs,
            "generated_timestamp": "2024-01-01T00:00:00Z",
            "notes": [
                f"Matrix size: {self.config['width']}×{self.config['height']} = {specs['total_leds']} LEDs",
                f"Strip length required: {specs['strip_length']:.1f} meters",
                f"Maximum current draw: {specs['max_current_total']:.2f}A",
                f"Recommended power supply: 5V {math.ceil(specs['max_current_total'] * 1.2)}A",
            ],
        }

        return json.dumps(config_data, indent=2)

    def save_files(self, base_name="custom_matrix", arduino_model="uno"):
        """Save all generated files with selected Arduino model"""
        if not validate_model(arduino_model):
            print(f"⚠️  Invalid Arduino model: {arduino_model}")
            print(f"Available models: {', '.join(get_available_models())}")
            return

        # Generate Arduino code for selected model only
        arduino_filename = self.arduino_generator.save_arduino_file(
            arduino_model,
            f"{base_name}_{arduino_model}.ino",
            matrix_width=self.config["width"],
            matrix_height=self.config["height"],
            data_pin=self.config["data_pin"],
            brightness=self.config["brightness"],
        )

        # Python code
        with open(f"{base_name}_controller.py", "w") as f:
            f.write(self.generate_python_code())

        # Configuration file
        with open(f"{base_name}_config.json", "w") as f:
            f.write(self.generate_config_file())

        specs = self.calculate_specs()
        print(
            f"\n📁 Generated files for {self.config['width']}×{self.config['height']} matrix:"
        )
        print(f"  - {arduino_filename} (Arduino code for {arduino_model})")
        print(f"  - {base_name}_controller.py (Python controller)")
        print(f"  - {base_name}_config.json (Configuration)")
        print("")
        print(
            f"📊 Matrix specs: {specs['total_leds']} LEDs, {specs['strip_length']:.1f}m strip, {specs['max_current_total']:.2f}A max"
        )


def main():
    """Interactive configuration generator"""
    print("LED Matrix Configuration Generator")
    print("=" * 40)

    generator = MatrixConfigGenerator()

    # Get user input
    try:
        # Helper to safely get int from input or config
        def safe_int_input(prompt, config_value, default=0):
            val = input(prompt)
            if val.strip():
                try:
                    return int(val)
                except Exception:
                    return int(default)
            if config_value is not None:
                try:
                    return int(config_value)
                except Exception:
                    return int(default)
            return int(default)

        width = safe_int_input(f"Matrix width in LEDs [{generator.config.get('width', 21)}]: ", generator.config.get("width"), 21)
        height = safe_int_input(f"Matrix height in LEDs [{generator.config.get('height', 24)}]: ", generator.config.get("height"), 24)

        print("\n🔧 Arduino Model Selection:")
        models = get_model_display_names()
        for i, (key, name) in enumerate(models.items(), 1):
            model_info = get_model_info(key)
            shifter = (
                " (Level shifter required)" if model_info and model_info.get("needs_level_shifter") else ""
            )
            voltage = model_info["voltage"] if model_info and "voltage" in model_info else "?V"
            max_leds = model_info["max_leds_recommended"] if model_info and "max_leds_recommended" in model_info else "?"
            print(f"{i}. {name} ({voltage}, max {max_leds} LEDs){shifter}")

        model_choice = safe_int_input("Choose Arduino model [1]: ", 1, 1) - 1
        model_keys = list(models.keys())
        arduino_model = model_keys[model_choice] if 0 <= model_choice < len(model_keys) else "uno"

        print("\nLED Strip Options:")
        print("1. 30 LEDs/m (33.3mm spacing)")
        print("2. 60 LEDs/m (16.7mm spacing)")
        print("3. 144 LEDs/m (6.94mm spacing) [Default]")
        print("4. 256 LEDs/m (3.91mm spacing)")

        led_options = {1: 30, 2: 60, 3: 144, 4: 256}
        led_choice = safe_int_input("Choose LED density [3]: ", 3, 3)
        leds_per_meter = led_options.get(led_choice, 144)

        print("\nWiring Pattern:")
        print("1. Serpentine (zigzag) [Default]")
        print("2. Progressive (left-to-right)")
        print("3. Custom")

        pattern_options = {1: "serpentine", 2: "progressive", 3: "custom"}
        pattern_choice = safe_int_input("Choose wiring pattern [1]: ", 1, 1)
        wiring_pattern = pattern_options.get(pattern_choice, "serpentine")

        brightness = safe_int_input(f"Brightness (0-255) [{generator.config.get('brightness', 128)}]: ", generator.config.get("brightness"), 128)

        # Update configuration
        generator.set_config(
            width=width,
            height=height,
            leds_per_meter=leds_per_meter,
            wiring_pattern=wiring_pattern,
            brightness=brightness,
        )

        # Show model recommendations
        generator.arduino_generator.print_model_comparison(width, height)

        # Show specifications
        specs = generator.calculate_specs()
        print("\n📋 Generated Configuration:")
        print(f"  Matrix: {width}×{height} = {specs['total_leds']} LEDs")
        print(f"  Arduino: {models[arduino_model]}")
        print(f"  Strip: {specs['strip_length']:.1f}m @ {leds_per_meter} LEDs/m")
        print(f"  Power: {specs['max_current_total']:.2f}A max, {specs['actual_current']:.2f}A @ {brightness}")
        print(f"  Cost estimate: ${specs['total_cost']}")

        # Save files
        base_name = input("\nBase filename [custom_matrix]: ") or "custom_matrix"
        generator.save_files(base_name, arduino_model)

        print("\n🎉 Files generated successfully!")
        print(f"Upload the generated .ino file to your {models[arduino_model]} and run {base_name}_controller.py")

    except KeyboardInterrupt:
        print("\nCancelled by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
