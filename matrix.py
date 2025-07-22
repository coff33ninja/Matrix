#!/usr/bin/env python3
"""
LED Matrix Project - Unified Entry Point
Single command-line interface for all LED matrix functionality
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

from modules.commands import (
    cmd_controller,
    cmd_start,
    cmd_generate,
    cmd_design,
    cmd_wiring,
    cmd_config,
    cmd_test,
    cmd_info,
)


def print_banner():
    """
    Display a formatted banner with the LED Matrix Project name and the current date and time.
    """
    print("=" * 70)
    print("🔥 LED Matrix Project - Unified Control Interface")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def main():
    """
    Parses command-line arguments and dispatches commands for the LED Matrix Project CLI.
    
    Returns:
        bool: True if the selected command completes successfully, False otherwise.
    """
    parser = argparse.ArgumentParser(
        description="LED Matrix Project - Unified Control Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python matrix.py controller                    # Start GUI controller
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
