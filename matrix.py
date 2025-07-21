#!/usr/bin/env python3
"""
LED Matrix Project - Unified Entry Point
Single command-line interface for all LED matrix functionality

Usage:
    python matrix.py --help                    # Show all available commands
    python matrix.py controller               # Start the GUI controller
    python matrix.py web                      # Start unified web server (control + docs at /control and /docs)
    python matrix.py start                    # Start both GUI and web interface
    python matrix.py generate arduino uno 16 16  # Generate Arduino code
    python matrix.py design                   # Start design library
    python matrix.py wiring esp32 32 32       # Generate wiring diagrams
    python matrix.py config                   # Configure matrix settings
    python matrix.py test                     # Run test suite
"""

import sys
import os
import argparse
from datetime import datetime

# Add current directory and modules directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, "modules")
sys.path.insert(0, current_dir)
sys.path.insert(0, modules_dir)


def print_banner():
    """Print the LED Matrix Project banner"""
    print("=" * 70)
    print("🔥 LED Matrix Project - Unified Control Interface")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def cmd_controller(args):
    """Start the matrix controller (web-based)"""
    print("🎮 Starting LED Matrix Controller...")
    try:
        from web_matrix_controller import WebMatrixController

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


def cmd_web(args):
    """Start the unified web interface server"""
    site_type = getattr(args, 'type', 'unified')
    
    # Get port from args or use default
    if hasattr(args, 'port') and args.port is not None:
        port = args.port
    else:
        port = 3000  # Always use port 3000 for unified server
    
    print(f"🌐 Starting Unified Web Server...")
    try:
        from modules.web_server import UnifiedMatrixWebServer
        
        server = UnifiedMatrixWebServer(port=port)
        return server.start()
    except ImportError as e:
        print(f"❌ Error importing unified web server: {e}")
        print("💡 Falling back to legacy server...")
        try:
            from modules.web_server import MatrixWebServer
            server = MatrixWebServer(port=port, site_type=site_type if site_type != 'unified' else 'control')
            return server.start()
        except Exception as fallback_e:
            print(f"❌ Error starting fallback server: {fallback_e}")
            return False
    except Exception as e:
        print(f"❌ Error starting unified web server: {e}")
        return False


def cmd_start(args):
    """Start both controller and web interfaces in a unified web-only solution"""
    import threading
    import time
    
    print("🚀 Starting Complete LED Matrix System...")
    print("   - Web-based Matrix Controller")
    print("   - Control Interface Server")
    print("   - Documentation Server")
    print()
    
    # Start web controller in a separate thread
    def start_controller():
        from modules.web_matrix_controller import WebMatrixController
        controller = WebMatrixController(port=8080)
        controller.run()
    
    # Start unified web server
    def start_unified_web():
        time.sleep(1)  # Give controller time to start
        from modules.web_server import UnifiedMatrixWebServer
        server = UnifiedMatrixWebServer(port=3000)
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
    """Generate Arduino code"""
    print(f"🔧 Generating Arduino code for {args.model}...")
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
    """Start design library or perform design operations"""
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
    """Generate wiring diagrams and documentation"""
    print(f"📋 Generating wiring diagrams for {args.controller}...")
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
        import json

        with open(shopping_filename, "w") as f:
            json.dump(shopping_list, f, indent=2)

        # Show summary
        power_req = generator.calculate_power_requirements(args.width, args.height)
        ctrl_info = generator.controllers[args.controller]

        print(f"\n📊 Wiring Configuration Summary:")
        print(f"   Controller: {ctrl_info['name']}")
        print(f"   Matrix: {args.width}×{args.height} = {power_req['total_leds']} LEDs")
        print(f"   Max Current: {power_req['total_current_amps']:.2f}A")
        print(f"   Recommended PSU: {power_req['recommended_psu']}")
        print(
            f"   Level Shifter: {'Required' if ctrl_info['needs_level_shifter'] else 'Not needed'}"
        )
        print(f"   Estimated Cost: ${shopping_list['project_info']['estimated_cost']}")
        print(f"\n📁 Generated Files:")
        print(f"   📄 Wiring Guide: {guide_filename}")
        print(f"   ⚙️  JSON Config: {json_filename}")
        print(f"   🛒 Shopping List: {shopping_filename}")

        return True

    except Exception as e:
        print(f"❌ Error generating wiring diagrams: {e}")
        return False


def cmd_config(args):
    """Configure matrix settings"""
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
    """Run test suite"""
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
            from tests.run_all_tests import main

            return main()

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def cmd_info(args):
    """Show project information and status"""
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
            f"   Total LEDs: {config.get('matrix_width') * config.get('matrix_height')}"
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
            from tests.run_all_tests import TestResult

            print("   Test Suite: ✅ Available")
            print("   Run 'python matrix.py test' to execute tests")
        except Exception:
            print("   Test Suite: ❌ Error")

        return True

    except Exception as e:
        print(f"❌ Error getting project info: {e}")
        return False


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="LED Matrix Project - Unified Control Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python matrix.py controller                    # Start GUI controller
  python matrix.py web --type control           # Start control interface (port 3000)
  python matrix.py web --type docs              # Start documentation (port 3001)
  python matrix.py web --type all               # Start both web interfaces
  python matrix.py start                        # Start everything (GUI + control + docs)
  python matrix.py generate uno 16 16           # Generate Arduino code for Uno
  python matrix.py generate esp32 32 32 --compare  # Compare models for ESP32
  python matrix.py design --interactive         # Interactive design mode
  python matrix.py wiring arduino_uno 16 16     # Generate wiring diagrams
  python matrix.py config --show                # Show current configuration
  python matrix.py test                         # Run all tests
  python matrix.py test --module arduino_models # Run specific test module
  python matrix.py info                         # Show project information
        """,
    )

    # Add global options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Controller command
    controller_parser = subparsers.add_parser(
        "controller", help="Start the matrix controller GUI"
    )

    # Web command
    web_parser = subparsers.add_parser(
        "web", help="Start the unified web interface server"
    )
    web_parser.add_argument(
        "--type", choices=["control", "docs", "all"], default="control",
        help="Type of web interface (control, docs, or all)"
    )
    web_parser.add_argument(
        "--port", type=int, help="Web server port (default: 3000 for unified server)"
    )

    # Start command (both controller and web)
    start_parser = subparsers.add_parser(
        "start", help="Start both controller and web interface"
    )
    start_parser.add_argument(
        "--port", type=int, default=3000, help="Web server port (default: 3000)"
    )

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate Arduino code")
    generate_parser.add_argument(
        "model",
        choices=["uno", "nano", "esp32", "esp8266", "mega"],
        help="Arduino model",
    )
    generate_parser.add_argument("width", type=int, help="Matrix width")
    generate_parser.add_argument("height", type=int, help="Matrix height")
    generate_parser.add_argument(
        "--compare", action="store_true", help="Show model comparison"
    )
    generate_parser.add_argument(
        "--organized", action="store_true", help="Save to organized directory"
    )
    generate_parser.add_argument(
        "--upload-help", action="store_true", help="Show upload instructions"
    )

    # Design command
    design_parser = subparsers.add_parser("design", help="Design library operations")
    design_parser.add_argument("--width", type=int, default=16, help="Matrix width")
    design_parser.add_argument("--height", type=int, default=16, help="Matrix height")
    design_parser.add_argument(
        "--samples", action="store_true", help="Create sample designs"
    )
    design_parser.add_argument(
        "--interactive", action="store_true", help="Interactive design mode"
    )

    # Wiring command
    wiring_parser = subparsers.add_parser("wiring", help="Generate wiring diagrams")
    wiring_parser.add_argument(
        "controller",
        choices=["arduino_uno", "arduino_nano", "esp32", "esp8266"],
        help="Controller type",
    )
    wiring_parser.add_argument("width", type=int, help="Matrix width")
    wiring_parser.add_argument("height", type=int, help="Matrix height")
    wiring_parser.add_argument("--data-pin", type=int, help="Data pin number")
    wiring_parser.add_argument(
        "--psu",
        choices=["5V5A", "5V10A", "5V20A", "5V30A", "5V40A"],
        help="Power supply",
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Configure matrix settings")
    config_parser.add_argument(
        "--show", action="store_true", help="Show current configuration"
    )
    config_parser.add_argument(
        "--interactive", action="store_true", help="Interactive configuration"
    )
    config_parser.add_argument("--width", type=int, help="Set matrix width")
    config_parser.add_argument("--height", type=int, help="Set matrix height")
    config_parser.add_argument("--brightness", type=int, help="Set brightness (0-255)")
    config_parser.add_argument("--port", help="Set serial port")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.add_argument(
        "--module", help="Run specific test module (e.g., arduino_models)"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show project information")

    # Parse arguments
    args = parser.parse_args()

    # Show banner unless quiet mode
    if not args.quiet:
        print_banner()

    # Handle no command
    if not args.command:
        parser.print_help()
        return True

    # Route to appropriate command handler
    command_handlers = {
        "controller": cmd_controller,
        "web": cmd_web,
        "start": cmd_start,
        "generate": cmd_generate,
        "design": cmd_design,
        "wiring": cmd_wiring,
        "config": cmd_config,
        "test": cmd_test,
        "info": cmd_info,
    }

    handler = command_handlers.get(args.command)
    if handler:
        try:
            success = handler(args)
            if not args.quiet:
                if success:
                    print("\n✅ Command completed successfully!")
                else:
                    print("\n❌ Command failed!")
            return success
        except KeyboardInterrupt:
            print("\n⚠️ Operation cancelled by user")
            return False
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
            return False
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
