#!/usr/bin/env python3
"""
Arduino Code Generator
Generates Arduino .ino files based on model selection and configuration
"""

import os
from datetime import datetime

try:
    import serial
    import serial.tools.list_ports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️  PySerial not available. Install with: pip install pyserial")

from arduino_models import ARDUINO_MODELS, get_model_info, validate_model
from matrix_config import config


class ArduinoGenerator:
    def __init__(self):
        self.config = config

    def generate_code(
        self,
        model_key,
        matrix_width=None,
        matrix_height=None,
        data_pin=None,
        brightness=None,
        custom_config=None,
        num_leds=None,
    ):
        """Generate Arduino code for specified model and configuration"""

        if not validate_model(model_key):
            raise ValueError(f"Invalid Arduino model: {model_key}")

        model = get_model_info(model_key)
        if not model:
            raise ValueError(f"Could not get model info for: {model_key}")

        # Use provided values or fall back to config/defaults
        width = matrix_width or self.config.get("matrix_width") or 16
        height = matrix_height or self.config.get("matrix_height") or 16
        pin = data_pin or model["default_pin"]
        bright = brightness or self.config.get("brightness") or 128

        # Apply custom configuration if provided
        if custom_config:
            width = custom_config.get("width", width)
            height = custom_config.get("height", height)
            pin = custom_config.get("data_pin", pin)
            bright = custom_config.get("brightness", bright)
            num_leds = custom_config.get("num_leds", num_leds)

        if num_leds is None:
            num_leds = (width or 16) * (height or 16)

        # Check if configuration is suitable for this model
        if num_leds > model["max_leds_recommended"]:
            print(
                f"⚠️  Warning: {num_leds} LEDs exceeds recommended limit of {model['max_leds_recommended']} for {model['display_name']}"
            )

        # Generate the code
        code = self._build_arduino_code(model, width, height, pin, bright, num_leds)

        return code

    def _build_arduino_code(self, model, width, height, pin, brightness, num_leds):
        """Build the complete Arduino code"""

        if not model:
            raise ValueError("Model information is required")

        # Header comment
        header = f"""/*
 * LED Matrix Controller for {model['display_name']}
 * Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * Matrix Configuration:
 * - Size: {width}×{height} = {num_leds} LEDs
 * - OR
 * - Strip Length: {num_leds} LEDs
 * - Data Pin: {pin}
 * - Brightness: {brightness}/255
 * - Controller: {model['display_name']} ({model['voltage']})
 * - Level Shifter Required: {'Yes' if model['needs_level_shifter'] else 'No'}
 * 
 * Memory Usage Estimate:
 * - LED Array: {num_leds * 3} bytes
 * - Available SRAM: {model['memory_sram']} bytes
 * - Memory Efficiency: {((model['memory_sram'] - num_leds * 3) / model['memory_sram'] * 100):.1f}%
 */

"""

        # Includes
        includes = "\n".join(f"#include {inc}" for inc in model["includes"])

        # Configuration defines
        if width and height:
            defines = f"""
// Matrix Configuration - Update these values for your setup
#define MATRIX_WIDTH {width}
#define MATRIX_HEIGHT {height}
#define NUM_LEDS (MATRIX_WIDTH * MATRIX_HEIGHT)  // {num_leds} LEDs
#define DATA_PIN {pin}
#define BRIGHTNESS {brightness}

CRGB leds[NUM_LEDS];"""
        else:
            defines = f"""
// LED Strip Configuration - Update these values for your setup
#define NUM_LEDS {num_leds}
#define DATA_PIN {pin}
#define BRIGHTNESS {brightness}

CRGB leds[NUM_LEDS];"""

        # Additional defines (for WiFi models)
        additional_defines = model.get("additional_defines", "")

        # Setup function
        setup_code = model["setup_code"].format(baud_rate=model["baud_rate"])

        setup_function = f"""
void setup() {{
  {setup_code}
}}"""

        # Additional functions
        additional_functions = model.get("additional_functions", "")

        # Loop function
        loop_function = f"""
void loop() {{
  {model['loop_code']}
}}"""

        # Combine all parts
        full_code = f"""{header}{includes}{defines}{additional_defines}{setup_function}{additional_functions}{loop_function}"""

        return full_code

    def save_arduino_file(self, model_key, filename=None, **kwargs):
        """Generate and save Arduino code to file"""

        if not validate_model(model_key):
            raise ValueError(f"Invalid Arduino model: {model_key}")

        model = get_model_info(model_key)

        # Generate filename if not provided
        if not filename:
            width = kwargs.get("matrix_width", self.config.get("matrix_width"))
            height = kwargs.get("matrix_height", self.config.get("matrix_height"))
            filename = f"led_matrix_{model_key}_{width}x{height}.ino"

        # Ensure .ino extension
        if not filename.endswith(".ino"):
            filename += ".ino"

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(filename) if os.path.dirname(filename) else "."
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Check if file exists and warn user
        if os.path.exists(filename):
            print(f"⚠️  File {filename} already exists and will be overwritten")

        # Generate code
        code = self.generate_code(model_key, **kwargs)

        # Save to file
        with open(filename, "w") as f:
            f.write(code)

        # Calculate some stats
        width = kwargs.get("matrix_width", self.config.get("matrix_width")) or 16
        height = kwargs.get("matrix_height", self.config.get("matrix_height")) or 16
        num_leds = width * height

        model = get_model_info(model_key)
        if not model:
            print("✅ Arduino code generated successfully!")
            print(f"   File: {filename}")
            return filename

        print("✅ Arduino code generated successfully!")
        print(f"   File: {filename}")
        print(f"   Model: {model['display_name']}")
        print(f"   Matrix: {width}×{height} = {num_leds} LEDs")
        print(
            f"   Memory Usage: {num_leds * 3}/{model['memory_sram']} bytes ({(num_leds * 3 / model['memory_sram'] * 100):.1f}%)"
        )

        if model["needs_level_shifter"]:
            print(f"   ⚠️  Level shifter required for {model['voltage']} logic")

        return filename

    def save_to_organized_directory(self, model_key, base_name="led_matrix", **kwargs):
        """Save Arduino file to an organized directory structure"""
        # Create organized directory structure
        output_dir = os.path.join("generated_arduino", model_key)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate filename with directory
        width = kwargs.get("matrix_width", self.config.get("matrix_width"))
        height = kwargs.get("matrix_height", self.config.get("matrix_height"))
        filename = os.path.join(output_dir, f"{base_name}_{width}x{height}.ino")

        return self.save_arduino_file(model_key, filename, **kwargs)

    def list_generated_files(self, model_key=None):
        """List all generated Arduino files, optionally filtered by model"""
        generated_files = []
        base_dir = "generated_arduino"

        if not os.path.exists(base_dir):
            return generated_files

        if model_key:
            # List files for specific model
            model_dir = os.path.join(base_dir, model_key)
            if os.path.exists(model_dir):
                for file in os.listdir(model_dir):
                    if file.endswith(".ino"):
                        generated_files.append(os.path.join(model_dir, file))
        else:
            # List all generated files
            for model_dir in os.listdir(base_dir):
                model_path = os.path.join(base_dir, model_dir)
                if os.path.isdir(model_path):
                    for file in os.listdir(model_path):
                        if file.endswith(".ino"):
                            generated_files.append(os.path.join(model_path, file))

        return generated_files

    def cleanup_generated_files(self, model_key=None, confirm=True):
        """Clean up generated Arduino files"""
        files_to_delete = self.list_generated_files(model_key)

        if not files_to_delete:
            print("No generated files found to clean up")
            return

        print(f"Found {len(files_to_delete)} generated files:")
        for file in files_to_delete:
            print(f"  - {file}")

        if confirm:
            response = input("Delete these files? (y/N): ").lower()
            if response not in ["y", "yes"]:
                print("Cleanup cancelled")
                return

        deleted_count = 0
        for file in files_to_delete:
            try:
                os.remove(file)
                deleted_count += 1
            except OSError as e:
                print(f"Error deleting {file}: {e}")

        print(f"Deleted {deleted_count} files")

        # Remove empty directories
        if model_key:
            model_dir = os.path.join("generated_arduino", model_key)
            if os.path.exists(model_dir) and not os.listdir(model_dir):
                os.rmdir(model_dir)

    def list_serial_ports(self):
        """List available serial ports for Arduino connection"""
        if not SERIAL_AVAILABLE:
            print("❌ PySerial not available. Cannot list serial ports.")
            return []

        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(
                {
                    "device": port.device,
                    "description": port.description,
                    "hwid": port.hwid,
                    "manufacturer": getattr(port, "manufacturer", "Unknown"),
                }
            )

        return ports

    def find_arduino_ports(self):
        """Find likely Arduino ports based on description/manufacturer"""
        if not SERIAL_AVAILABLE:
            return []

        arduino_keywords = ["arduino", "ch340", "cp210", "ftdi", "usb serial"]
        likely_ports = []

        for port_info in self.list_serial_ports():
            description = port_info["description"].lower()
            manufacturer = port_info["manufacturer"].lower()

            for keyword in arduino_keywords:
                if keyword in description or keyword in manufacturer:
                    likely_ports.append(port_info)
                    break

        return likely_ports

    def test_arduino_connection(self, port, baud_rate=115200, timeout=2):
        """Test connection to Arduino on specified port"""
        if not SERIAL_AVAILABLE:
            print("❌ PySerial not available. Cannot test connection.")
            return False

        try:
            print(f"🔌 Testing connection to {port} at {baud_rate} baud...")
            with serial.Serial(port, baud_rate, timeout=timeout) as ser:
                # Wait for Arduino to reset
                import time

                time.sleep(2)

                # Try to read any initial output
                if ser.in_waiting > 0:
                    initial_data = ser.read(ser.in_waiting).decode(
                        "utf-8", errors="ignore"
                    )
                    print(f"📡 Received: {initial_data.strip()}")

                print(f"✅ Connection successful to {port}")
                return True

        except serial.SerialException as e:
            print(f"❌ Connection failed to {port}: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error testing {port}: {e}")
            return False

    def upload_helper_info(self, model_key, filename):
        """Provide upload instructions for the generated Arduino file"""
        model = get_model_info(model_key)
        if not model:
            return

        print(f"\n📋 Upload Instructions for {model['display_name']}:")
        print("=" * 50)

        # Find likely Arduino ports
        arduino_ports = self.find_arduino_ports()
        if arduino_ports:
            print("🔌 Detected Arduino-compatible ports:")
            for port in arduino_ports:
                print(f"  - {port['device']}: {port['description']}")
        else:
            print("⚠️  No Arduino ports detected. Check USB connection.")

        print(f"\n📝 Steps to upload {os.path.basename(filename)}:")
        print("1. Open Arduino IDE")
        print(
            "2. Install FastLED library (Tools → Manage Libraries → Search 'FastLED')"
        )

        if "esp" in model_key.lower():
            print(f"3. Install {model['display_name']} board support:")
            if "esp32" in model_key:
                print("   - File → Preferences → Additional Board Manager URLs")
                print("   - Add: https://dl.espressif.com/dl/package_esp32_index.json")
                print("   - Tools → Board → Boards Manager → Search 'ESP32'")
            else:
                print("   - File → Preferences → Additional Board Manager URLs")
                print(
                    "   - Add: http://arduino.esp8266.com/stable/package_esp8266com_index.json"
                )
                print("   - Tools → Board → Boards Manager → Search 'ESP8266'")

        print(f"4. Open {os.path.basename(filename)} in Arduino IDE")
        print("5. Select correct board and port:")

        if arduino_ports:
            print(f"   - Board: {model['display_name']}")
            print(
                f"   - Port: {arduino_ports[0]['device']} (or try others if this fails)"
            )
        else:
            print(f"   - Board: {model['display_name']}")
            print("   - Port: Check Tools → Port menu")

        print("6. Click Upload button (→)")
        print("7. Wait for 'Done uploading' message")

        if model["needs_level_shifter"]:
            print(f"\n⚠️  IMPORTANT: {model['display_name']} requires level shifter!")
            print("   Connect 74HCT125 or similar between Arduino and LED strip")

        print("\n🔧 Troubleshooting:")
        print("- If upload fails, try different baud rate or port")
        print("- Press reset button on Arduino before upload")
        print("- Check USB cable (some are power-only)")
        if "esp" in model_key.lower():
            print("- Hold BOOT button during upload for ESP boards")

    def get_model_recommendations(self, matrix_width=None, matrix_height=None):
        """Get model recommendations based on matrix size"""
        width = matrix_width or self.config.get("matrix_width") or 16
        height = matrix_height or self.config.get("matrix_height") or 16
        num_leds = width * height

        recommendations = []

        for key, model in ARDUINO_MODELS.items():
            memory_used = num_leds * 3
            memory_available = model["memory_sram"]
            memory_efficiency = (memory_available - memory_used) / memory_available

            suitable = num_leds <= model["max_leds_recommended"]

            recommendations.append(
                {
                    "key": key,
                    "name": model["display_name"],
                    "suitable": suitable,
                    "memory_efficiency": memory_efficiency,
                    "memory_used": memory_used,
                    "memory_available": memory_available,
                    "needs_level_shifter": model["needs_level_shifter"],
                    "voltage": model["voltage"],
                    "max_leds": model["max_leds_recommended"],
                }
            )

        # Sort by suitability and memory efficiency
        recommendations.sort(
            key=lambda x: (x["suitable"], x["memory_efficiency"]), reverse=True
        )

        return recommendations

    def print_model_comparison(self, matrix_width=None, matrix_height=None):
        """Print a comparison table of Arduino models"""
        recommendations = self.get_model_recommendations(matrix_width, matrix_height)

        width = matrix_width or self.config.get("matrix_width") or 16
        height = matrix_height or self.config.get("matrix_height") or 16
        num_leds = width * height

        print(
            f"\n🔍 Arduino Model Comparison for {width}×{height} matrix ({num_leds} LEDs):"
        )
        print("=" * 80)
        print(
            f"{'Model':<20} {'Suitable':<10} {'Memory':<15} {'Level Shifter':<15} {'Voltage':<8}"
        )
        print("-" * 80)

        for rec in recommendations:
            suitable = "✅ Yes" if rec["suitable"] else "❌ No"
            memory = f"{rec['memory_used']}/{rec['memory_available']}"
            shifter = "Required" if rec["needs_level_shifter"] else "Not needed"

            print(
                f"{rec['name']:<20} {suitable:<10} {memory:<15} {shifter:<15} {rec['voltage']:<8}"
            )

        print("=" * 80)

        # Show recommendation
        best = recommendations[0]
        if best["suitable"]:
            print(
                f"💡 Recommended: {best['name']} (Memory efficiency: {best['memory_efficiency']*100:.1f}%)"
            )
        else:
            print("⚠️  Warning: Matrix size exceeds recommended limits for all models")
            print(
                f"   Consider reducing matrix size or using {best['name']} with caution"
            )


def main():
    """Interactive Arduino code generator"""
    print("🔧 Arduino Code Generator")
    print("=" * 40)

    generator = ArduinoGenerator()

    # Show available models
    print("\nAvailable Arduino Models:")
    for i, (key, model) in enumerate(ARDUINO_MODELS.items(), 1):
        print(f"  {i}. {model['display_name']} ({key})")

    try:
        # Get user input
        choice = input(
            f"\nSelect Arduino model (1-{len(ARDUINO_MODELS)}) or enter model key: "
        ).strip()

        # Handle numeric choice
        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(ARDUINO_MODELS):
                model_key = list(ARDUINO_MODELS.keys())[choice_num - 1]
            else:
                print("Invalid choice number")
                return
        else:
            model_key = choice.lower()

        if not validate_model(model_key):
            print(f"Invalid model: {model_key}")
            return

        # Get matrix configuration
        width = int(
            input(f"Matrix width [{config.get('matrix_width') or 16}]: ")
            or config.get("matrix_width")
            or 16
        )
        height = int(
            input(f"Matrix height [{config.get('matrix_height') or 16}]: ")
            or config.get("matrix_height")
            or 16
        )

        # Show model comparison
        generator.print_model_comparison(width, height)

        # Confirm generation
        model = get_model_info(model_key)
        if not model:
            print(f"Error: Could not get model info for {model_key}")
            return
        print(f"\nGenerating code for {model['display_name']}...")

        # Ask user about file organization
        organize = input("Save to organized directory structure? (y/N): ").lower()

        if organize in ["y", "yes"]:
            filename = generator.save_to_organized_directory(
                model_key, matrix_width=width, matrix_height=height
            )
        else:
            filename = generator.save_arduino_file(
                model_key, matrix_width=width, matrix_height=height
            )

        print(f"\n🎉 Success! Generated {filename}")

        # Show upload instructions
        generator.upload_helper_info(model_key, filename)

        # Offer to test Arduino connection
        if SERIAL_AVAILABLE:
            test_connection = input("\nTest Arduino connection? (y/N): ").lower()
            if test_connection in ["y", "yes"]:
                arduino_ports = generator.find_arduino_ports()
                if arduino_ports:
                    for port_info in arduino_ports:
                        if generator.test_arduino_connection(
                            port_info["device"], model["baud_rate"] if model else 115200
                        ):
                            break
                else:
                    # Manual port entry
                    manual_port = input(
                        "Enter COM port manually (e.g., COM3): "
                    ).strip()
                    if manual_port:
                        generator.test_arduino_connection(
                            manual_port, model["baud_rate"] if model else 115200
                        )

        # Show existing files for this model
        existing_files = generator.list_generated_files(model_key)
        if len(existing_files) > 1:
            print(f"\nOther {model['display_name']} files:")
            for file in existing_files:
                if file != filename:
                    print(f"  - {os.path.basename(file)}")

    except KeyboardInterrupt:
        print("\nCancelled by user")
    except Exception as e:
        print(f"Error: {e}")


def find_arduino():
    """Standalone function to find and test Arduino connections"""
    print("🔍 Arduino Port Scanner")
    print("=" * 30)

    if not SERIAL_AVAILABLE:
        print("❌ PySerial not available. Install with: pip install pyserial")
        return

    generator = ArduinoGenerator()

    # List all serial ports
    all_ports = generator.list_serial_ports()
    if not all_ports:
        print("❌ No serial ports found")
        return

    print("📡 All available serial ports:")
    for i, port in enumerate(all_ports, 1):
        print(f"  {i}. {port['device']}: {port['description']}")

    # Show likely Arduino ports
    arduino_ports = generator.find_arduino_ports()
    if arduino_ports:
        print("\n🎯 Likely Arduino ports:")
        for port in arduino_ports:
            print(f"  - {port['device']}: {port['description']}")

        # Test connections
        print("\n🔌 Testing connections...")
        for port_info in arduino_ports:
            generator.test_arduino_connection(port_info["device"])
    else:
        print("\n⚠️  No obvious Arduino ports detected")
        print("Try testing ports manually or check USB connection")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "find":
        find_arduino()
    else:
        main()
