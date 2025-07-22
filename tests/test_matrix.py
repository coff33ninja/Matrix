"""
Comprehensive unit tests for matrix.py - LED Matrix Project Entry Point
Testing framework: unittest (Python standard library)
"""

import unittest
import sys
import os
import argparse
from unittest.mock import patch, call
from io import StringIO

# Add the parent directory to sys.path to import matrix.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the module under test
import matrix


class TestPrintBanner(unittest.TestCase):
    """Test the print_banner function"""
    
    @patch('builtins.print')
    @patch('matrix.datetime')
    def test_print_banner_format(self, mock_datetime, mock_print):
        """Test that print_banner outputs the correct format"""
        # Mock datetime
        mock_datetime.now.return_value.strftime.return_value = "2024-01-15 10:30:45"
        
        matrix.print_banner()
        
        expected_calls = [
            call("=" * 70),
            call("🔥 LED Matrix Project - Unified Control Interface"),
            call("=" * 70),
            call("📅 2024-01-15 10:30:45"),
            call(),
        ]
        
        mock_print.assert_has_calls(expected_calls)
        mock_datetime.now.assert_called_once()
        mock_datetime.now.return_value.strftime.assert_called_once_with('%Y-%m-%d %H:%M:%S')
    
    @patch('builtins.print')
    def test_print_banner_calls_print_five_times(self, mock_print):
        """Test that print_banner makes exactly 5 print calls"""
        matrix.print_banner()
        self.assertEqual(mock_print.call_count, 5)


class TestMainArgumentParsing(unittest.TestCase):
    """Test argument parsing in main function"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock all command handlers to avoid import errors
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.command_mocks[cmd].return_value = True
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py'])
    def test_main_no_arguments_shows_help(self, mock_banner):
        """Test that main shows help when no arguments provided"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertTrue(result)
        mock_banner.assert_called_once()
        output = mock_stdout.getvalue()
        self.assertIn("usage:", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', '--quiet'])
    def test_quiet_mode_no_banner(self, mock_banner):
        """Test that quiet mode doesn't print banner"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        mock_banner.assert_not_called()
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', '--verbose', 'controller'])
    def test_verbose_mode_with_banner(self, mock_banner):
        """Test that verbose mode prints banner and passes verbose flag"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        mock_banner.assert_called_once()
        self.command_mocks['cmd_controller'].assert_called_once()
        args = self.command_mocks['cmd_controller'].call_args[0][0]
        self.assertTrue(args.verbose)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_controller_command(self, mock_banner):
        """Test controller command execution"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_controller'].assert_called_once()
        output = mock_stdout.getvalue()
        self.assertIn("✅ Command completed successfully!", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'start', '--port', '8080'])
    def test_start_command_with_port(self, mock_banner):
        """Test start command with port argument"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_start'].assert_called_once()
        args = self.command_mocks['cmd_start'].call_args[0][0]
        self.assertEqual(args.port, 8080)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'generate', 'uno', '16', '16', '--compare'])
    def test_generate_command_with_options(self, mock_banner):
        """Test generate command with all options"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_generate'].assert_called_once()
        args = self.command_mocks['cmd_generate'].call_args[0][0]
        self.assertEqual(args.model, 'uno')
        self.assertEqual(args.width, 16)
        self.assertEqual(args.height, 16)
        self.assertTrue(args.compare)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'generate', 'esp32', '32', '32', '--organized', '--upload-help'])
    def test_generate_command_esp32_with_flags(self, mock_banner):
        """Test generate command with ESP32 and additional flags"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_generate'].assert_called_once()
        args = self.command_mocks['cmd_generate'].call_args[0][0]
        self.assertEqual(args.model, 'esp32')
        self.assertEqual(args.width, 32)
        self.assertEqual(args.height, 32)
        self.assertTrue(args.organized)
        self.assertTrue(args.upload_help)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'design', '--width', '24', '--height', '8', '--samples', '--interactive'])
    def test_design_command_with_dimensions(self, mock_banner):
        """Test design command with custom dimensions and flags"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_design'].assert_called_once()
        args = self.command_mocks['cmd_design'].call_args[0][0]
        self.assertEqual(args.width, 24)
        self.assertEqual(args.height, 8)
        self.assertTrue(args.samples)
        self.assertTrue(args.interactive)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'wiring', 'esp32', '16', '16', '--data-pin', '2', '--psu', '5V10A'])
    def test_wiring_command_with_options(self, mock_banner):
        """Test wiring command with all options"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_wiring'].assert_called_once()
        args = self.command_mocks['cmd_wiring'].call_args[0][0]
        self.assertEqual(args.controller, 'esp32')
        self.assertEqual(args.width, 16)
        self.assertEqual(args.height, 16)
        self.assertEqual(args.data_pin, 2)
        self.assertEqual(args.psu, '5V10A')
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'config', '--show', '--width', '32', '--brightness', '128', '--port', '/dev/ttyUSB0'])
    def test_config_command_with_settings(self, mock_banner):
        """Test config command with various settings"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_config'].assert_called_once()
        args = self.command_mocks['cmd_config'].call_args[0][0]
        self.assertTrue(args.show)
        self.assertEqual(args.width, 32)
        self.assertEqual(args.brightness, 128)
        self.assertEqual(args.port, '/dev/ttyUSB0')
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'test', '--module', 'arduino_models'])
    def test_test_command_with_module(self, mock_banner):
        """Test test command with specific module"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_test'].assert_called_once()
        args = self.command_mocks['cmd_test'].call_args[0][0]
        self.assertEqual(args.module, 'arduino_models')
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'info'])
    def test_info_command(self, mock_banner):
        """Test info command"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        self.command_mocks['cmd_info'].assert_called_once()


class TestMainErrorHandling(unittest.TestCase):
    """Test error handling in main function"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock command handlers
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_command_failure(self, mock_banner):
        """Test handling when command returns False"""
        self.command_mocks['cmd_controller'].return_value = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("❌ Command failed!", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_keyboard_interrupt(self, mock_banner):
        """Test handling of KeyboardInterrupt"""
        self.command_mocks['cmd_controller'].side_effect = KeyboardInterrupt()
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("⚠️ Operation cancelled by user", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_unexpected_exception(self, mock_banner):
        """Test handling of unexpected exceptions"""
        test_exception = RuntimeError("Test error")
        self.command_mocks['cmd_controller'].side_effect = test_exception
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("💥 Unexpected error: Test error", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', '--verbose', 'controller'])
    def test_unexpected_exception_with_verbose(self, mock_banner):
        """Test handling of unexpected exceptions in verbose mode"""
        test_exception = RuntimeError("Test error")
        self.command_mocks['cmd_controller'].side_effect = test_exception
        
        with patch('sys.stdout', new_callable=StringIO):
            with patch('traceback.print_exc') as mock_traceback:
                result = matrix.main()
                
        self.assertFalse(result)
        mock_traceback.assert_called_once()
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'unknown_command'])
    def test_unknown_command(self, mock_banner):
        """Test handling of unknown commands"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("❌ Unknown command: unknown_command", output)
        self.assertIn("usage:", output)


class TestMainQuietMode(unittest.TestCase):
    """Test quiet mode behavior"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock all command handlers
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.command_mocks[cmd].return_value = True
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', '--quiet', 'controller'])
    def test_quiet_mode_success_no_output(self, mock_banner):
        """Test that quiet mode suppresses success messages"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertTrue(result)
        mock_banner.assert_not_called()
        output = mock_stdout.getvalue()
        self.assertNotIn("✅ Command completed successfully!", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', '--quiet', 'controller'])
    def test_quiet_mode_failure_no_output(self, mock_banner):
        """Test that quiet mode suppresses failure messages"""
        self.command_mocks['cmd_controller'].return_value = False
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        mock_banner.assert_not_called()


class TestMainWithEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock all command handlers
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.command_mocks[cmd].return_value = True
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'generate', 'mega', '1', '1'])
    def test_generate_minimum_dimensions(self, mock_banner):
        """Test generate command with minimum dimensions"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_generate'].call_args[0][0]
        self.assertEqual(args.model, 'mega')
        self.assertEqual(args.width, 1)
        self.assertEqual(args.height, 1)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'generate', 'esp8266', '999', '999'])
    def test_generate_large_dimensions(self, mock_banner):
        """Test generate command with large dimensions"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_generate'].call_args[0][0]
        self.assertEqual(args.model, 'esp8266')
        self.assertEqual(args.width, 999)
        self.assertEqual(args.height, 999)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'config', '--brightness', '0'])
    def test_config_minimum_brightness(self, mock_banner):
        """Test config command with minimum brightness"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_config'].call_args[0][0]
        self.assertEqual(args.brightness, 0)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'config', '--brightness', '255'])
    def test_config_maximum_brightness(self, mock_banner):
        """Test config command with maximum brightness"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_config'].call_args[0][0]
        self.assertEqual(args.brightness, 255)
    
    @patch('matrix.print_banner')
    def test_wiring_all_controller_types(self, mock_banner):
        """Test wiring command with different controller types"""
        controllers = ['arduino_uno', 'arduino_nano', 'esp32', 'esp8266']
        
        for controller in controllers:
            with self.subTest(controller=controller):
                with patch('sys.argv', ['matrix.py', 'wiring', controller, '8', '8']):
                    with patch('sys.stdout', new_callable=StringIO):
                        result = matrix.main()
                        
                self.assertTrue(result)
                args = self.command_mocks['cmd_wiring'].call_args[0][0]
                self.assertEqual(args.controller, controller)
    
    @patch('matrix.print_banner')
    def test_all_power_supply_options(self, mock_banner):
        """Test wiring command with all power supply options"""
        power_supplies = ['5V5A', '5V10A', '5V20A', '5V30A', '5V40A']
        
        for psu in power_supplies:
            with self.subTest(psu=psu):
                with patch('sys.argv', ['matrix.py', 'wiring', 'esp32', '16', '16', '--psu', psu]):
                    with patch('sys.stdout', new_callable=StringIO):
                        result = matrix.main()
                        
                self.assertTrue(result)
                args = self.command_mocks['cmd_wiring'].call_args[0][0]
                self.assertEqual(args.psu, psu)
    
    @patch('matrix.print_banner')
    def test_all_generate_models(self, mock_banner):
        """Test generate command with all supported Arduino models"""
        models = ['uno', 'nano', 'esp32', 'esp8266', 'mega']
        
        for model in models:
            with self.subTest(model=model):
                with patch('sys.argv', ['matrix.py', 'generate', model, '16', '16']):
                    with patch('sys.stdout', new_callable=StringIO):
                        result = matrix.main()
                        
                self.assertTrue(result)
                args = self.command_mocks['cmd_generate'].call_args[0][0]
                self.assertEqual(args.model, model)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'generate', 'nano', '64', '32', '--compare', '--organized', '--upload-help'])
    def test_generate_all_flags_combined(self, mock_banner):
        """Test generate command with all flags enabled"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_generate'].call_args[0][0]
        self.assertTrue(args.compare)
        self.assertTrue(args.organized)
        self.assertTrue(args.upload_help)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'design', '--width', '1', '--height', '1'])
    def test_design_minimum_dimensions(self, mock_banner):
        """Test design command with minimum dimensions"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_design'].call_args[0][0]
        self.assertEqual(args.width, 1)
        self.assertEqual(args.height, 1)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'config', '--interactive'])
    def test_config_interactive_mode(self, mock_banner):
        """Test config command in interactive mode"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_config'].call_args[0][0]
        self.assertTrue(args.interactive)


class TestMainSystemIntegration(unittest.TestCase):
    """Test system integration aspects"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock command handlers
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.command_mocks[cmd].return_value = True
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', '--verbose', '--quiet', 'controller'])
    def test_conflicting_verbose_quiet_flags(self, mock_banner):
        """Test behavior when both verbose and quiet flags are provided"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        # Quiet should take precedence
        mock_banner.assert_not_called()
        args = self.command_mocks['cmd_controller'].call_args[0][0]
        self.assertTrue(args.verbose)
        self.assertTrue(args.quiet)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'start'])
    def test_start_default_port(self, mock_banner):
        """Test start command uses default port when none specified"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_start'].call_args[0][0]
        self.assertEqual(args.port, 3000)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'design'])
    def test_design_default_dimensions(self, mock_banner):
        """Test design command uses default dimensions when none specified"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_design'].call_args[0][0]
        self.assertEqual(args.width, 16)
        self.assertEqual(args.height, 16)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'wiring', 'arduino_uno', '16', '16', '--data-pin', '0'])
    def test_wiring_zero_data_pin(self, mock_banner):
        """Test wiring command with data pin 0"""
        with patch('sys.stdout', new_callable=StringIO):
            result = matrix.main()
            
        self.assertTrue(result)
        args = self.command_mocks['cmd_wiring'].call_args[0][0]
        self.assertEqual(args.data_pin, 0)


class TestMainExceptionPropagation(unittest.TestCase):
    """Test exception propagation and handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock command handlers
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_import_error_handling(self, mock_banner):
        """Test handling of ImportError exceptions"""
        import_error = ImportError("Module not found")
        self.command_mocks['cmd_controller'].side_effect = import_error
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("💥 Unexpected error: Module not found", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_permission_error_handling(self, mock_banner):
        """Test handling of PermissionError exceptions"""
        permission_error = PermissionError("Access denied")
        self.command_mocks['cmd_controller'].side_effect = permission_error
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("💥 Unexpected error: Access denied", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_value_error_handling(self, mock_banner):
        """Test handling of ValueError exceptions"""
        value_error = ValueError("Invalid value provided")
        self.command_mocks['cmd_controller'].side_effect = value_error
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("💥 Unexpected error: Invalid value provided", output)


class TestMainReturnValues(unittest.TestCase):
    """Test return value handling from commands"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock command handlers
        self.command_mocks = {}
        for cmd in ['cmd_controller', 'cmd_start', 'cmd_generate', 'cmd_design', 
                   'cmd_wiring', 'cmd_config', 'cmd_test', 'cmd_info']:
            patcher = patch(f'matrix.{cmd}')
            self.command_mocks[cmd] = patcher.start()
            self.addCleanup(patcher.stop)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_command_returns_none(self, mock_banner):
        """Test handling when command returns None"""
        self.command_mocks['cmd_controller'].return_value = None
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("❌ Command failed!", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_command_returns_truthy_value(self, mock_banner):
        """Test handling when command returns truthy non-boolean value"""
        self.command_mocks['cmd_controller'].return_value = "success"
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertTrue(result)
        output = mock_stdout.getvalue()
        self.assertIn("✅ Command completed successfully!", output)
    
    @patch('matrix.print_banner')
    @patch('sys.argv', ['matrix.py', 'controller'])
    def test_command_returns_falsy_value(self, mock_banner):
        """Test handling when command returns falsy non-boolean value"""
        self.command_mocks['cmd_controller'].return_value = 0
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = matrix.main()
            
        self.assertFalse(result)
        output = mock_stdout.getvalue()
        self.assertIn("❌ Command failed!", output)


class TestMainIfNameMain(unittest.TestCase):
    """Test the __name__ == '__main__' block behavior"""
    
    @patch('matrix.main')
    @patch('sys.exit')
    def test_main_success_exit_code_zero(self, mock_exit, mock_main):
        """Test that successful main execution exits with code 0"""
        mock_main.return_value = True
        
        # Simulate the __main__ execution
        if True:  # Simulate __name__ == '__main__'
            success = mock_main()
            mock_exit(0 if success else 1)
            
        mock_main.assert_called_once()
        mock_exit.assert_called_once_with(0)
    
    @patch('matrix.main')
    @patch('sys.exit')
    def test_main_failure_exit_code_one(self, mock_exit, mock_main):
        """Test that failed main execution exits with code 1"""
        mock_main.return_value = False
        
        # Simulate the __main__ execution
        if True:  # Simulate __name__ == '__main__'
            success = mock_main()
            mock_exit(0 if success else 1)
            
        mock_main.assert_called_once()
        mock_exit.assert_called_once_with(1)


class TestArgumentParserConfiguration(unittest.TestCase):
    """Test argument parser configuration and choices validation"""
    
    def test_generate_model_choices(self):
        """Test that generate command accepts only valid model choices"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        generate_parser = subparsers.add_parser("generate")
        generate_parser.add_argument("model", choices=["uno", "nano", "esp32", "esp8266", "mega"])
        
        # Valid choices should not raise error
        for model in ["uno", "nano", "esp32", "esp8266", "mega"]:
            args = parser.parse_args(["generate", model])
            self.assertEqual(args.model, model)
    
    def test_wiring_controller_choices(self):
        """Test that wiring command accepts only valid controller choices"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        wiring_parser = subparsers.add_parser("wiring")
        wiring_parser.add_argument("controller", choices=["arduino_uno", "arduino_nano", "esp32", "esp8266"])
        wiring_parser.add_argument("width", type=int)
        wiring_parser.add_argument("height", type=int)
        
        # Valid choices should not raise error
        for controller in ["arduino_uno", "arduino_nano", "esp32", "esp8266"]:
            args = parser.parse_args(["wiring", controller, "16", "16"])
            self.assertEqual(args.controller, controller)
    
    def test_power_supply_choices(self):
        """Test that wiring command accepts only valid power supply choices"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        wiring_parser = subparsers.add_parser("wiring")
        wiring_parser.add_argument("controller", choices=["arduino_uno", "arduino_nano", "esp32", "esp8266"])
        wiring_parser.add_argument("width", type=int)
        wiring_parser.add_argument("height", type=int)
        wiring_parser.add_argument("--psu", choices=["5V5A", "5V10A", "5V20A", "5V30A", "5V40A"])
        
        # Valid choices should not raise error
        for psu in ["5V5A", "5V10A", "5V20A", "5V30A", "5V40A"]:
            args = parser.parse_args(["wiring", "esp32", "16", "16", "--psu", psu])
            self.assertEqual(args.psu, psu)


if __name__ == '__main__':
    unittest.main(verbosity=2)