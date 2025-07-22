#!/usr/bin/env python3
"""
Command handlers for the LED Matrix Project
"""

import sys
import os
import threading
import time

# Add current directory and modules directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, "..", "modules")
sys.path.insert(0, current_dir)
sys.path.insert(0, modules_dir)

def cmd_controller(args):
    """
    Starts the web-based LED Matrix Controller.

    Returns:
        bool: True if the controller starts successfully, False if an error occurs.
    """
    print("🎮 Starting LED Matrix Controller...")
    try:
        from matrix_controller import WebMatrixController

        controller = WebMatrixController()
        controller.run()
    except ImportError as e:
        print(f"❌ Error importing controller: {e}")
        print(
            "Make sure all dependencies are installed: pip install -r requirements.txt"
        )
        return False
    except Exception as e:
        print(f"❌ Error starting controller: {e}")
        return False
    return True


def cmd_start(args):
    """
    Starts the complete LED matrix system, launching both the web-based matrix controller and the unified web server in separate daemon threads.

    Returns:
        bool: True if services are stopped via keyboard interrupt, False if an error occurs during startup.
    """


    print("🚀 Starting Complete LED Matrix System...")
    print("   - Web-based Matrix Controller")
    print("   - Control Interface Server")
    print("   - Documentation Server")
    print()

    # Start web controller in a separate thread
    def start_controller():
        """
        Starts the web-based LED matrix controller using the configured port.
        """
        from modules.matrix_controller import WebMatrixController
        from modules.matrix_config import config
        controller = WebMatrixController(port=config.get("web_port") or 8080)
        controller.run()

    # Start unified web server
    def start_unified_web():
        """
        Starts the unified web server for the LED matrix system after a brief delay to allow the controller to initialize.
        """
        time.sleep(1)  # Give controller time to start
        from modules.web_server import UnifiedMatrixWebServer
        from modules.matrix_config import config
        server = UnifiedMatrixWebServer(port=config.get("web_server_port") or 3000)
        server.start()

    try:
        controller_thread = threading.Thread(target=start_controller, daemon=True)
        unified_web_thread = threading.Thread(target=start_unified_web, daemon=True)

        controller_thread.start()
        unified_web_thread.start()

        print("✅ Services starting...")
        print("🏠 Landing Page: http://localhost:3000")
        print("🎮 Control Interface: http://localhost:3000/control")
        print("📚 Documentation: http://localhost:3000/docs")
        print("🔌 API Server: http://localhost:8080")
        print()
        print("Press Ctrl+C to stop all services")
        print("=" * 70)

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        return True
    except Exception as e:
        print(f"❌ Error in startup: {e}")
        return False


def cmd_generate(args):
    """
    Generates Arduino code for a specified LED matrix model, with options for model comparison, organized output, and upload instructions.

    Returns:
        bool: True if code generation succeeds or model comparison is shown; False if an error occurs or the model is invalid.
    """
    print("🔧 Generating Arduino code for {}...".format(args.model))
    try:
        from arduino_generator import ArduinoGenerator
        from arduino_models import validate_model

        if not validate_model(args.model):
            print(f"❌ Invalid Arduino model: {args.model}")
            print("Available models: uno, nano, esp32, esp8266, mega")
            return False

        generator = ArduinoGenerator()

        # Show model comparison if requested
        if args.compare:
            generator.print_model_comparison(args.width, args.height)
            return True

        # Generate code
        if args.organized:
            filename = generator.save_to_organized_directory(
                args.model, matrix_width=args.width, matrix_height=args.height
            )
        else:
            filename = generator.save_arduino_file(
                args.model, matrix_width=args.width, matrix_height=args.height
            )

        print(f"✅ Arduino code generated: {filename}")

        # Show upload instructions if requested
        if args.upload_help:
            generator.upload_helper_info(args.model, filename)

        return True

    except Exception as e:
        print(f"❌ Error generating Arduino code: {e}")
        return False


def cmd_design(args):
    """
    Launches the LED Matrix Design Library to create, export, or generate code for matrix designs.

    Depending on the arguments, this function can create sample designs, enter an interactive mode for custom pattern creation (including rainbow, gradient, checkerboard, and plasma effects), export designs, or generate Arduino code. Returns True on success, or False if an error occurs.
    """
    print("🎨 LED Matrix Design Library...")
    try:
        from matrix_design_library import MatrixDesign, create_sample_designs

        if args.samples:
            print("Creating sample designs...")
            create_sample_designs()
            return True

        if args.interactive:
            # Interactive design creation
            print("🎨 Interactive Design Mode")
            width = int(input(f"Matrix width [{args.width}]: ") or args.width)
            height = int(input(f"Matrix height [{args.height}]: ") or args.height)

            design = MatrixDesign(width, height)

            while True:
                print("\nDesign Options:")
                print("1. Rainbow pattern")
                print("2. Gradient pattern")
                print("3. Checkerboard pattern")
                print("4. Plasma effect")
                print("5. Export design")
                print("6. Generate Arduino code")
                print("0. Exit")

                choice = input("Choose option: ").strip()

                if choice == "1":
                    design.generate_rainbow()
                    print("✅ Rainbow pattern applied")
                elif choice == "2":
                    color1 = input("Start color [#ff0000]: ") or "#ff0000"
                    color2 = input("End color [#0000ff]: ") or "#0000ff"
                    direction = (
                        input("Direction (horizontal/vertical/diagonal) [horizontal]: ")
                        or "horizontal"
                    )
                    design.generate_gradient(color1, color2, direction)
                    print("✅ Gradient pattern applied")
                elif choice == "3":
                    color1 = input("Color 1 [#ffffff]: ") or "#ffffff"
                    color2 = input("Color 2 [#000000]: ") or "#000000"
                    size = int(input("Square size [2]: ") or 2)
                    design.generate_checkerboard(color1, color2, size)
                    print("✅ Checkerboard pattern applied")
                elif choice == "4":
                    frames = int(input("Number of frames [10]: ") or 10)
                    design.create_plasma_animation(frames)
                    print(f"✅ Plasma animation created ({frames} frames)")
                elif choice == "5":
                    filename = input("Export filename [design.json]: ") or "design.json"
                    if design.export_design(filename):
                        print(f"✅ Design exported to {filename}")
                elif choice == "6":
                    model = input("Arduino model [uno]: ") or "uno"
                    code = design.generate_arduino_code("designData", model)
                    code_filename = f"design_{model}_{width}x{height}.ino"
                    with open(code_filename, "w") as f:
                        f.write(code)
                    print(f"✅ Arduino code generated: {code_filename}")
                elif choice == "0":
                    break
                else:
                    print("Invalid option")

            return True

        # Non-interactive mode - just create samples
        create_sample_designs()
        return True

    except Exception as e:
        print(f"❌ Error in design library: {e}")
        return False


def cmd_wiring(args):
    """
    Generates wiring diagrams, configuration files, and a shopping list for a specified LED matrix controller and matrix size.

    Creates a markdown wiring guide, exports a JSON configuration, and generates a shopping list JSON file based on the provided controller, matrix dimensions, data pin, and power supply. Prints a summary of the wiring configuration, including power requirements and estimated cost. Returns True on success, or False if an error occurs.
    """
    print("📋 Generating wiring diagrams for {}...".format(args.controller))
    try:
        from wiring_diagram_generator import WiringDiagramGenerator

        generator = WiringDiagramGenerator()

        # Generate markdown guide
        guide_filename = generator.save_guide(
            args.controller,
            args.width,
            args.height,
            data_pin=args.data_pin,
            psu=args.psu,
        )

        # Generate JSON configuration
        json_filename = generator.export_configuration_json(
            args.controller,
            args.width,
            args.height,
            data_pin=args.data_pin,
            psu=args.psu,
        )

        # Generate shopping list
        shopping_list = generator.generate_shopping_list_json(
            args.controller,
            args.width,
            args.height,
            data_pin=args.data_pin,
            psu=args.psu,
        )

        shopping_filename = (
            f"shopping_list_{args.controller}_{args.width}x{args.height}.json"
        )
        # Save shopping list to JSON file
        import json

        with open(shopping_filename, "w") as f:
            json.dump(shopping_list, f, indent=2)

        # Show summary
        power_req = generator.calculate_power_requirements(args.width, args.height)
        ctrl_info = generator.controllers[args.controller]

        print("\n📊 Wiring Configuration Summary:")
        print(f"   Controller: {ctrl_info['name']}")
        print(f"   Matrix: {args.width}×{args.height} = {power_req['total_leds']} LEDs")
        print(f"   Max Current: {power_req['total_current_amps']:.2f}A")
        print(f"   Recommended PSU: {power_req['recommended_psu']}")
        print(
            f"   Level Shifter: {'Required' if ctrl_info['needs_level_shifter'] else 'Not needed'}"
        )
        print(f"   Estimated Cost: ${shopping_list['project_info']['estimated_cost']}")
        print("\n📁 Generated Files:")
        print(f"   📄 Wiring Guide: {guide_filename}")
        print(f"   ⚙️  JSON Config: {json_filename}")
        print(f"   🛒 Shopping List: {shopping_filename}")

        return True

    except Exception as e:
        print(f"❌ Error generating wiring diagrams: {e}")
        return False


def cmd_config(args):
    """
    Configures LED matrix settings, allowing users to view, interactively update, or set configuration values for the matrix.

    Depending on the provided arguments, this function can display the current configuration, prompt the user for interactive updates, or set individual configuration parameters such as matrix width, height, brightness, and serial port. Changes are saved persistently. Returns True on success, or False if an error occurs.
    """
    print("⚙️ Matrix Configuration...")
    try:
        from matrix_config import config

        if args.show:
            print("Current Configuration:")
            info = config.get_config_info()
            print(f"   Config File: {info['config_file']}")
            print(
                f"   Matrix Size: {config.get('matrix_width')}×{config.get('matrix_height')}"
            )
            print(f"   Brightness: {config.get('brightness')}")
            print(f"   Connection: {config.get('connection_mode')}")
            print(f"   Serial Port: {config.get('serial_port')}")
            print(f"   Data Pin: {config.get('data_pin')}")
            return True

        if args.interactive:
            print("🔧 Interactive Configuration")

            # Get current values
            current_width = config.get("matrix_width")
            current_height = config.get("matrix_height")
            current_brightness = config.get("brightness")
            current_port = config.get("serial_port")

            # Interactive input
            width = input(f"Matrix width [{current_width}]: ").strip()
            if width:
                config.set("matrix_width", int(width))

            height = input(f"Matrix height [{current_height}]: ").strip()
            if height:
                config.set("matrix_height", int(height))

            brightness = input(f"Brightness 0-255 [{current_brightness}]: ").strip()
            if brightness:
                config.set("brightness", int(brightness))

            port = input(f"Serial port [{current_port}]: ").strip()
            if port:
                config.set("serial_port", port)

            # Save configuration
            config.save_config()
            print("✅ Configuration saved")
            return True

        # Set individual values
        if args.width:
            config.set("matrix_width", args.width)
        if args.height:
            config.set("matrix_height", args.height)
        if args.brightness:
            config.set("brightness", args.brightness)
        if args.port:
            config.set("serial_port", args.port)

        if any([args.width, args.height, args.brightness, args.port]):
            config.save_config()
            print("✅ Configuration updated")

        return True

    except Exception as e:
        print(f"❌ Error configuring matrix: {e}")
        return False


def cmd_test(args):
    """
    Runs the LED matrix test suite, either for a specific module or the entire project.

    If `args.module` is specified, runs tests for that module using the unittest framework. Otherwise, executes the full test suite. Prints status messages and returns `True` if tests pass, `False` otherwise.
    """
    print("🧪 Running LED Matrix Test Suite...")
    try:
        if args.module:
            # Run specific test module
            import unittest

            test_module = f"tests.test_{args.module}"
            suite = unittest.TestLoader().loadTestsFromName(test_module)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            return result.wasSuccessful()
        else:
            # Run full test suite
            from tests.run_all_tests import run_all_tests

            return run_all_tests()

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def cmd_info(args):
    """
    Displays detailed information about the LED Matrix Project, including matrix configuration, available modules, hardware status, and test suite availability.

    Returns:
        bool: True if information is displayed successfully, False if an error occurs.
    """
    print("ℹ️ LED Matrix Project Information")
    print()

    try:
        # Project status
        from matrix_config import config

        print("📊 Project Status:")
        print(
            f"   Matrix Size: {config.get('matrix_width')}×{config.get('matrix_height')}"
        )
        print(
            f"   Total LEDs: {(config.get('matrix_width') or 0) * (config.get('matrix_height') or 0)}"
        )
        print(f"   Connection: {config.get('connection_mode')}")
        print()

        # Available modules
        print("📦 Available Modules:")
        modules = [
            ("matrix_controller", "🎮 Unified Matrix Controller"),
            ("arduino_generator", "🔧 Arduino Code Generator"),
            ("matrix_design_library", "🎨 Design Library"),
            ("wiring_diagram_generator", "📋 Wiring Diagram Generator"),
            ("matrix_config", "⚙️ Configuration Manager"),
        ]

        for module_name, description in modules:
            try:
                __import__(module_name)
                status = "✅"
            except ImportError:
                status = "❌"
            print(f"   {status} {description}")

        print()

        # Hardware status
        print("🔌 Hardware Status:")
        try:
            from matrix_hardware import hardware

            print(f"   Connection Mode: {hardware.connection_mode}")
            print("   Hardware Module: ✅ Available")
        except Exception:
            print("   Hardware Module: ❌ Error")

        print()

        # Test status
        print("🧪 Test Status:")
        try:
            # Try to import to check availability
            __import__('tests.run_all_tests')
            print("   Test Suite: ✅ Available")
            print("   Run 'python matrix.py test' to execute tests")
        except Exception:
            print("   Test Suite: ❌ Error")

        return True

    except Exception as e:
        print(f"❌ Error getting project info: {e}")
        return False
