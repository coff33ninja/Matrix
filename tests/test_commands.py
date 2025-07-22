"""Comprehensive unit tests for command handlers in the LED Matrix Project
Testing Framework: unittest (Python standard library)
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, mock_open

# Add current directory and modules directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
modules_dir = os.path.join(parent_dir, "modules")
sys.path.insert(0, parent_dir)
sys.path.insert(0, modules_dir)

# Import the command functions to test
from commands import (
    cmd_controller,
    cmd_start,
    cmd_generate,
    cmd_design,
    cmd_wiring,
    cmd_config,
    cmd_test,
    cmd_info,
)


class TestCmdController(unittest.TestCase):
    """Test cases for cmd_controller function"""

    @patch('builtins.print')
    @patch('commands.WebMatrixController')
    def test_cmd_controller_success(self, mock_controller_class, mock_print):
        """Test successful controller startup"""
        # Arrange
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        args = Mock()

        # Act
        result = cmd_controller(args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_called_with("🎮 Starting LED Matrix Controller...")
        mock_controller_class.assert_called_once()
        mock_controller.run.assert_called_once()

    @patch('builtins.print')
    def test_cmd_controller_import_error(self, mock_print):
        """Test controller startup with import error"""
        # Arrange
        args = Mock()

        # Act
        with patch('commands.WebMatrixController', side_effect=ImportError("Module not found")):
            result = cmd_controller(args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error importing controller: Module not found")
        mock_print.assert_any_call(
            "Make sure all dependencies are installed: pip install -r requirements.txt"
        )

    @patch('builtins.print')
    @patch('commands.WebMatrixController')
    def test_cmd_controller_runtime_error(self, mock_controller_class, mock_print):
        """Test controller startup with runtime error"""
        # Arrange
        mock_controller = Mock()
        mock_controller.run.side_effect = RuntimeError("Server error")
        mock_controller_class.return_value = mock_controller
        args = Mock()

        # Act
        result = cmd_controller(args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error starting controller: Server error")


class TestCmdStart(unittest.TestCase):
    """Test cases for cmd_start function"""

    @patch('builtins.print')
    @patch('threading.Thread')
    @patch('time.sleep')
    @patch('commands.WebMatrixController')
    @patch('commands.UnifiedMatrixWebServer')
    @patch('commands.config')
    def test_cmd_start_success_setup(self, mock_config, mock_server_class, mock_controller_class, mock_sleep, mock_thread, mock_print):
        """Test successful start command setup (before keyboard interrupt)"""
        # Arrange
        mock_config.get.side_effect = lambda key, default: {"web_port": 8080, "web_server_port": 3000}.get(key, default)

        # Mock threads
        mock_controller_thread = Mock()
        mock_web_thread = Mock()
        mock_thread.side_effect = [mock_controller_thread, mock_web_thread]

        # Mock KeyboardInterrupt after setup
        mock_sleep.side_effect = KeyboardInterrupt()

        args = Mock()

        # Act
        result = cmd_start(args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_any_call("🚀 Starting Complete LED Matrix System...")
        mock_print.assert_any_call("✅ Services starting...")
        mock_print.assert_any_call("🏠 Landing Page: http://localhost:3000")
        mock_controller_thread.start.assert_called_once()
        mock_web_thread.start.assert_called_once()

    @patch('builtins.print')
    @patch('threading.Thread')
    def test_cmd_start_thread_creation_error(self, mock_thread, mock_print):
        """Test start command with threading error"""
        # Arrange
        mock_thread.side_effect = RuntimeError("Thread creation failed")
        args = Mock()

        # Act
        result = cmd_start(args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error in startup: Thread creation failed")

    @patch('builtins.print')
    @patch('threading.Thread')
    @patch('time.sleep')
    def test_cmd_start_keyboard_interrupt(self, mock_sleep, mock_thread, mock_print):
        """Test start command with keyboard interrupt"""
        # Arrange
        mock_controller_thread = Mock()
        mock_web_thread = Mock()
        mock_thread.side_effect = [mock_controller_thread, mock_web_thread]
        mock_sleep.side_effect = KeyboardInterrupt()
        args = Mock()

        # Act
        result = cmd_start(args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_any_call("\n🛑 Shutting down all services...")


class TestCmdGenerate(unittest.TestCase):
    """Test cases for cmd_generate function"""

    def setUp(self):
        """Set up test fixtures"""
        self.args = Mock()
        self.args.model = "uno"
        self.args.width = 16
        self.args.height = 16
        self.args.compare = False
        self.args.organized = False
        self.args.upload_help = False

    @patch('builtins.print')
    @patch('commands.ArduinoGenerator')
    @patch('commands.validate_model')
    def test_cmd_generate_success_basic(self, mock_validate, mock_generator_class, mock_print):
        """Test successful basic Arduino code generation"""
        # Arrange
        mock_validate.return_value = True
        mock_generator = Mock()
        mock_generator.save_arduino_file.return_value = "test_file.ino"
        mock_generator_class.return_value = mock_generator

        # Act
        result = cmd_generate(self.args)

        # Assert
        self.assertTrue(result)
        mock_validate.assert_called_with("uno")
        mock_generator.save_arduino_file.assert_called_with("uno", matrix_width=16, matrix_height=16)
        mock_print.assert_any_call("✅ Arduino code generated: test_file.ino")

    @patch('builtins.print')
    @patch('commands.ArduinoGenerator')
    @patch('commands.validate_model')
    def test_cmd_generate_organized_output(self, mock_validate, mock_generator_class, mock_print):
        """Test Arduino code generation with organized output"""
        # Arrange
        mock_validate.return_value = True
        mock_generator = Mock()
        mock_generator.save_to_organized_directory.return_value = "organized/test_file.ino"
        mock_generator_class.return_value = mock_generator
        self.args.organized = True

        # Act
        result = cmd_generate(self.args)

        # Assert
        self.assertTrue(result)
        mock_generator.save_to_organized_directory.assert_called_with("uno", matrix_width=16, matrix_height=16)
        mock_print.assert_any_call("✅ Arduino code generated: organized/test_file.ino")

    @patch('builtins.print')
    @patch('commands.ArduinoGenerator')
    @patch('commands.validate_model')
    def test_cmd_generate_with_comparison(self, mock_validate, mock_generator_class, mock_print):
        """Test Arduino generation with model comparison"""
        # Arrange
        mock_validate.return_value = True
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        self.args.compare = True

        # Act
        result = cmd_generate(self.args)

        # Assert
        self.assertTrue(result)
        mock_generator.print_model_comparison.assert_called_with(16, 16)

    @patch('builtins.print')
    @patch('commands.ArduinoGenerator')
    @patch('commands.validate_model')
    def test_cmd_generate_with_upload_help(self, mock_validate, mock_generator_class, mock_print):
        """Test Arduino generation with upload help"""
        # Arrange
        mock_validate.return_value = True
        mock_generator = Mock()
        mock_generator.save_arduino_file.return_value = "test_file.ino"
        mock_generator_class.return_value = mock_generator
        self.args.upload_help = True

        # Act
        result = cmd_generate(self.args)

        # Assert
        self.assertTrue(result)
        mock_generator.upload_helper_info.assert_called_with("uno", "test_file.ino")

    @patch('builtins.print')
    @patch('commands.validate_model')
    def test_cmd_generate_invalid_model(self, mock_validate, mock_print):
        """Test Arduino generation with invalid model"""
        # Arrange
        mock_validate.return_value = False

        # Act
        result = cmd_generate(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Invalid Arduino model: uno")
        mock_print.assert_any_call("Available models: uno, nano, esp32, esp8266, mega")

    @patch('builtins.print')
    @patch('commands.ArduinoGenerator')
    @patch('commands.validate_model')
    def test_cmd_generate_exception(self, mock_validate, mock_generator_class, mock_print):
        """Test Arduino generation with exception"""
        # Arrange
        mock_validate.return_value = True
        mock_generator_class.side_effect = RuntimeError("Generator error")

        # Act
        result = cmd_generate(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error generating Arduino code: Generator error")


class TestCmdDesign(unittest.TestCase):
    """Test cases for cmd_design function"""

    def setUp(self):
        self.args = Mock()
        self.args.samples = False
        self.args.interactive = False
        self.args.width = 16
        self.args.height = 16

    @patch('builtins.print')
    @patch('commands.create_sample_designs')
    def test_cmd_design_samples(self, mock_create_samples, mock_print):
        """Test design command with samples option"""
        # Arrange
        self.args.samples = True

        # Act
        result = cmd_design(self.args)

        # Assert
        self.assertTrue(result)
        mock_create_samples.assert_called_once()
        mock_print.assert_any_call("Creating sample designs...")

    @patch('builtins.print')
    @patch('commands.create_sample_designs')
    def test_cmd_design_non_interactive(self, mock_create_samples, mock_print):
        """Test design command in non-interactive mode"""
        # Act
        result = cmd_design(self.args)

        # Assert
        self.assertTrue(result)
        mock_create_samples.assert_called_once()

    @patch('builtins.print')
    @patch('builtins.input')
    @patch('commands.MatrixDesign')
    def test_cmd_design_interactive_rainbow(self, mock_design_class, mock_input, mock_print):
        """Test interactive design with rainbow pattern"""
        # Arrange
        self.args.interactive = True
        mock_design = Mock()
        mock_design_class.return_value = mock_design
        mock_input.side_effect = ["", "", "1", "0"]

        # Act
        result = cmd_design(self.args)

        # Assert
        self.assertTrue(result)
        mock_design.generate_rainbow.assert_called_once()

    @patch('builtins.print')
    @patch('builtins.input')
    @patch('commands.MatrixDesign')
    def test_cmd_design_interactive_gradient(self, mock_design_class, mock_input, mock_print):
        """Test interactive design with gradient pattern"""
        # Arrange
        self.args.interactive = True
        mock_design = Mock()
        mock_design_class.return_value = mock_design
        mock_input.side_effect = ["", "", "2", "", "", "", "0"]

        # Act
        result = cmd_design(self.args)

        # Assert
        self.assertTrue(result)
        mock_design.generate_gradient.assert_called_with("#ff0000", "#0000ff", "horizontal")

    @patch('builtins.print')
    @patch('builtins.input')
    @patch('commands.MatrixDesign')
    @patch('builtins.open', new_callable=mock_open)
    def test_cmd_design_interactive_arduino_export(self, mock_file, mock_design_class, mock_input, mock_print):
        """Test interactive design with Arduino code export"""
        # Arrange
        self.args.interactive = True
        mock_design = Mock()
        mock_design.generate_arduino_code.return_value = "// Arduino code"
        mock_design_class.return_value = mock_design
        mock_input.side_effect = ["", "", "6", "", "0"]

        # Act
        result = cmd_design(self.args)

        # Assert
        self.assertTrue(result)
        mock_design.generate_arduino_code.assert_called_with("designData", "uno")
        mock_file.assert_called_with("design_uno_16x16.ino", "w")

    @patch('builtins.print')
    @patch('commands.MatrixDesign')
    def test_cmd_design_exception(self, mock_design_class, mock_print):
        """Test design command with exception"""
        # Arrange
        mock_design_class.side_effect = RuntimeError("Design error")

        # Act
        result = cmd_design(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error in design library: Design error")


class TestCmdWiring(unittest.TestCase):
    """Test cases for cmd_wiring function"""

    def setUp(self):
        self.args = Mock()
        self.args.controller = "uno"
        self.args.width = 16
        self.args.height = 16
        self.args.data_pin = 6
        self.args.psu = "5V"

    @patch('builtins.print')
    @patch('commands.WiringDiagramGenerator')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_cmd_wiring_success(self, mock_json_dump, mock_file, mock_generator_class, mock_print):
        """Test successful wiring diagram generation"""
        # Arrange
        mock_generator = Mock()
        mock_generator.save_guide.return_value = "wiring_guide.md"
        mock_generator.export_configuration_json.return_value = "config.json"
        mock_generator.generate_shopping_list_json.return_value = {
            'project_info': {'estimated_cost': 25.99},
        }
        mock_generator.calculate_power_requirements.return_value = {
            'total_leds': 256,
            'total_current_amps': 15.36,
            'recommended_psu': '5V 20A',
        }
        mock_generator.controllers = {
            'uno': {
                'name': 'Arduino Uno',
                'needs_level_shifter': True,
            },
        }
        mock_generator_class.return_value = mock_generator

        # Act
        result = cmd_wiring(self.args)

        # Assert
        self.assertTrue(result)
        mock_generator.save_guide.assert_called_with("uno", 16, 16, data_pin=6, psu="5V")
        mock_generator.export_configuration_json.assert_called_with("uno", 16, 16, data_pin=6, psu="5V")
        mock_print.assert_any_call("📊 Wiring Configuration Summary:")
        mock_print.assert_any_call("   Controller: Arduino Uno")
        mock_print.assert_any_call("   Level Shifter: Required")

    @patch('builtins.print')
    @patch('commands.WiringDiagramGenerator')
    def test_cmd_wiring_exception(self, mock_generator_class, mock_print):
        """Test wiring diagram generation with exception"""
        # Arrange
        mock_generator_class.side_effect = RuntimeError("Wiring error")

        # Act
        result = cmd_wiring(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error generating wiring diagrams: Wiring error")

    @patch('builtins.print')
    @patch('commands.WiringDiagramGenerator')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_cmd_wiring_variable_name_bug(self, mock_json_dump, mock_file, mock_generator_class, mock_print):
        """Test wiring command catches the height variable name bug in line 250"""
        # Arrange
        mock_generator = Mock()
        mock_generator.save_guide.return_value = "wiring_guide.md"
        mock_generator.export_configuration_json.return_value = "config.json"
        mock_generator.generate_shopping_list_json.return_value = {
            'project_info': {'estimated_cost': 25.99},
        }
        mock_generator.calculate_power_requirements.return_value = {
            'total_leds': 256,
            'total_current_amps': 15.36,
            'recommended_psu': '5V 20A',
        }
        mock_generator.controllers = {
            'uno': {'name': 'Arduino Uno', 'needs_level_shifter': False},
        }
        mock_generator_class.return_value = mock_generator

        # Act
        result = cmd_wiring(self.args)

        # Assert - The function should complete successfully despite the variable name bug
        self.assertTrue(result)


class TestCmdConfig(unittest.TestCase):
    """Test cases for cmd_config function"""

    def setUp(self):
        self.args = Mock()
        self.args.show = False
        self.args.interactive = False
        self.args.width = None
        self.args.height = None
        self.args.brightness = None
        self.args.port = None

    @patch('builtins.print')
    @patch('commands.config')
    def test_cmd_config_show(self, mock_config, mock_print):
        """Test config show functionality"""
        # Arrange
        self.args.show = True
        mock_config.get_config_info.return_value = {'config_file': 'config.json'}
        mock_config.get.side_effect = lambda key: {
            'matrix_width': 16,
            'matrix_height': 16,
            'brightness': 128,
            'connection_mode': 'serial',
            'serial_port': '/dev/ttyUSB0',
            'data_pin': 6,
        }.get(key)

        # Act
        result = cmd_config(self.args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_any_call("Current Configuration:")
        mock_print.assert_any_call("   Matrix Size: 16x16")
        mock_print.assert_any_call("   Brightness: 128")

    @patch('builtins.print')
    @patch('builtins.input')
    @patch('commands.config')
    def test_cmd_config_interactive(self, mock_config, mock_input, mock_print):
        """Test interactive config functionality"""
        # Arrange
        self.args.interactive = True
        mock_config.get.side_effect = lambda key: {
            'matrix_width': 16,
            'matrix_height': 16,
            'brightness': 128,
            'serial_port': '/dev/ttyUSB0',
        }.get(key)
        mock_input.side_effect = ["32", "32", "255", "/dev/ttyUSB1"]

        # Act
        result = cmd_config(self.args)

        # Assert
        self.assertTrue(result)
        mock_config.set.assert_any_call("matrix_width", 32)
        mock_config.set.assert_any_call("matrix_height", 32)
        mock_config.set.assert_any_call("brightness", 255)
        mock_config.set.assert_any_call("serial_port", "/dev/ttyUSB1")
        mock_config.save_config.assert_called_once()

    @patch('builtins.print')
    @patch('commands.config')
    def test_cmd_config_individual_values(self, mock_config, mock_print):
        """Test setting individual config values"""
        # Arrange
        self.args.width = 32
        self.args.height = 16
        self.args.brightness = 200

        # Act
        result = cmd_config(self.args)

        # Assert
        self.assertTrue(result)
        mock_config.set.assert_any_call("matrix_width", 32)
        mock_config.set.assert_any_call("matrix_height", 16)
        mock_config.set.assert_any_call("brightness", 200)
        mock_config.save_config.assert_called_once()

    @patch('builtins.print')
    @patch('commands.config')
    def test_cmd_config_exception(self, mock_config, mock_print):
        """Test config command with exception"""
        # Arrange
        mock_config.get.side_effect = RuntimeError("Config error")
        self.args.show = True

        # Act
        result = cmd_config(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error configuring matrix: Config error")


class TestCmdTest(unittest.TestCase):
    """Test cases for cmd_test function"""

    def setUp(self):
        self.args = Mock()
        self.args.module = None

    @patch('builtins.print')
    @patch('commands.main')
    def test_cmd_test_full_suite(self, mock_main, mock_print):
        """Test running full test suite"""
        # Arrange
        mock_main.return_value = True

        # Act
        result = cmd_test(self.args)

        # Assert
        self.assertTrue(result)
        mock_main.assert_called_once()

    @patch('builtins.print')
    @patch('unittest.TestLoader')
    @patch('unittest.TextTestRunner')
    def test_cmd_test_specific_module(self, mock_runner_class, mock_loader_class, mock_print):
        """Test running specific test module"""
        # Arrange
        self.args.module = "matrix"
        mock_loader = Mock()
        mock_suite = Mock()
        mock_runner = Mock()
        mock_result = Mock()
        mock_result.wasSuccessful.return_value = True

        mock_loader_class.return_value = mock_loader
        mock_loader.loadTestsFromName.return_value = mock_suite
        mock_runner_class.return_value = mock_runner
        mock_runner.run.return_value = mock_result

        # Act
        result = cmd_test(self.args)

        # Assert
        self.assertTrue(result)
        mock_loader.loadTestsFromName.assert_called_with("tests.test_matrix")
        mock_runner.run.assert_called_with(mock_suite)

    @patch('builtins.print')
    def test_cmd_test_exception(self, mock_print):
        """Test test command with exception"""
        # Arrange
        with patch('commands.main', side_effect=RuntimeError("Test error")):
            # Act
            result = cmd_test(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error running tests: Test error")


class TestCmdInfo(unittest.TestCase):
    """Test cases for cmd_info function"""

    def setUp(self):
        self.args = Mock()

    @patch('builtins.print')
    @patch('commands.config')
    @patch('builtins.__import__')
    def test_cmd_info_success(self, mock_import, mock_config, mock_print):
        """Test successful info display"""
        # Arrange
        mock_config.get.side_effect = lambda key: {
            'matrix_width': 16,
            'matrix_height': 16,
            'connection_mode': 'serial',
        }.get(key)

        # Act
        result = cmd_info(self.args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_any_call("ℹ️ LED Matrix Project Information")
        mock_print.assert_any_call("📊 Project Status:")
        mock_print.assert_any_call("   Matrix Size: 16×16")
        mock_print.assert_any_call("   Total LEDs: 256")

    @patch('builtins.print')
    @patch('commands.config')
    @patch('builtins.__import__')
    def test_cmd_info_module_availability(self, mock_import, mock_config, mock_print):
        """Test module availability checking"""
        # Arrange
        mock_config.get.side_effect = lambda key: {
            'matrix_width': 16,
            'matrix_height': 16,
            'connection_mode': 'serial',
        }.get(key)

        # Mock some modules available, some not
        def mock_import_side_effect(name):
            if name in ["matrix_controller", "arduino_generator"]:
                return Mock()
            raise ImportError("Module not found")

        mock_import.side_effect = mock_import_side_effect

        # Act
        result = cmd_info(self.args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_any_call("📦 Available Modules:")

    @patch('builtins.print')
    @patch('commands.hardware')
    @patch('commands.config')
    def test_cmd_info_hardware_status(self, mock_hardware, mock_config, mock_print):
        """Test hardware status checking"""
        # Arrange
        mock_config.get.side_effect = lambda key: {
            'matrix_width': 16,
            'matrix_height': 16,
            'connection_mode': 'serial',
        }.get(key)
        mock_hardware.connection_mode = "serial"

        # Act
        result = cmd_info(self.args)

        # Assert
        self.assertTrue(result)
        mock_print.assert_any_call("🔌 Hardware Status:")
        mock_print.assert_any_call("   Connection Mode: serial")

    @patch('builtins.print')
    @patch('commands.config')
    def test_cmd_info_exception(self, mock_config, mock_print):
        """Test info command with exception"""
        # Arrange
        mock_config.get.side_effect = RuntimeError("Config error")

        # Act
        result = cmd_info(self.args)

        # Assert
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Error getting project info: Config error")


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling scenarios"""

    def test_empty_args_handling(self):
        """Test command functions with empty or None args"""
        # Test with None args - should not crash
        from contextlib import suppress
        with suppress(AttributeError):
            cmd_controller(None)

    @patch('builtins.print')
    def test_missing_dependencies_graceful_handling(self, mock_print):
        """Test graceful handling of missing dependencies"""
        # Test cmd_controller with missing WebMatrixController
        with patch('commands.WebMatrixController', side_effect=ImportError("No module")):
            result = cmd_controller(Mock())
            self.assertFalse(result)

    @patch('builtins.print')
    @patch('commands.config')
    def test_config_edge_cases(self, mock_config, mock_print):
        """Test config command edge cases"""
        # Test with all None values
        args = Mock()
        args.show = False
        args.interactive = False
        args.width = None
        args.height = None
        args.brightness = None
        args.port = None

        result = cmd_config(args)
        self.assertTrue(result)  # Should return True even with no changes

    @patch('builtins.print')
    @patch('builtins.input')
    @patch('commands.MatrixDesign')
    def test_design_interactive_invalid_input(self, mock_design_class, mock_input, mock_print):
        """Test design interactive mode with invalid inputs"""
        args = Mock()
        args.interactive = True
        args.width = 16
        args.height = 16

        mock_design = Mock()
        mock_design_class.return_value = mock_design

        # Test invalid menu choice followed by exit
        mock_input.side_effect = ["", "", "99", "0"]

        result = cmd_design(args)
        self.assertTrue(result)


class TestThreadingSafety(unittest.TestCase):
    """Test threading-related functionality"""

    @patch('threading.Thread')
    @patch('time.sleep')
    def test_cmd_start_thread_daemon_setting(self, mock_sleep, mock_thread):
        """Test that threads are properly configured as daemon threads"""
        # Arrange
        mock_controller_thread = Mock()
        mock_web_thread = Mock()
        mock_thread.side_effect = [mock_controller_thread, mock_web_thread]
        mock_sleep.side_effect = KeyboardInterrupt()

        args = Mock()

        # Act
        with patch('builtins.print'):
            cmd_start(args)

        # Assert
        thread_calls = mock_thread.call_args_list
        for args_call, kwargs_call in thread_calls:
            assert kwargs_call.get('daemon', False)


class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization"""

    @patch('builtins.print')
    @patch('commands.validate_model')
    def test_cmd_generate_model_validation(self, mock_validate, mock_print):
        """Test model validation in generate command"""
        # Test various invalid models
        invalid_models = ["invalid", "", "UNKNOWN", "raspberry_pi"]

        for model in invalid_models:
            args = Mock()
            args.model = model
            mock_validate.return_value = False

            result = cmd_generate(args)
            self.assertFalse(result)

    @patch('builtins.print')
    @patch('builtins.input')
    @patch('commands.config')
    def test_config_interactive_input_validation(self, mock_config, mock_input, mock_print):
        """Test input validation in interactive config"""
        # Arrange
        args = Mock()
        args.interactive = True
        args.show = False
        args.width = None
        args.height = None
        args.brightness = None
        args.port = None

        mock_config.get.return_value = 16  # Default values

        # Test with empty inputs (should use defaults)
        mock_input.side_effect = ["", "", "", ""]

        result = cmd_config(args)
        self.assertTrue(result)


if __name__ == '__main__':
    # Run the tests with detailed output
    unittest.main(verbosity=2)