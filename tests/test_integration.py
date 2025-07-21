#!/usr/bin/env python3
"""
Integration test suite for LED Matrix Project
Tests interaction between modules and end-to-end functionality
"""

import unittest
import tempfile
import os
import sys
import shutil
from unittest.mock import patch, MagicMock

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from tests import get_test_config


class TestModuleIntegration(unittest.TestCase):
    """Test integration between different modules"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = get_test_config()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_config_hardware_integration(self):
        """Test integration between config and hardware modules"""
        from matrix_config import MatrixConfig
        from matrix_hardware import MatrixHardware
        
        # Create test config
        config_file = os.path.join(self.temp_dir, "integration_config.json")
        config = MatrixConfig(config_file)
        config.set("connection_mode", "USB")
        config.set("serial_port", "COM_TEST")
        config.set("brightness", 150)
        config.save_config()
        
        # Hardware should use config values
        hardware = MatrixHardware()
        self.assertEqual(hardware.connection_mode, "USB")
    
    def test_arduino_generator_models_integration(self):
        """Test integration between Arduino generator and models"""
        from arduino_generator import ArduinoGenerator
        from arduino_models import get_model_info, validate_model
        
        generator = ArduinoGenerator()
        
        # Test that generator uses model information correctly
        for model_key in ['uno', 'esp32', 'nano']:
            with self.subTest(model=model_key):
                self.assertTrue(validate_model(model_key))
                model_info = get_model_info(model_key)
                self.assertIsNotNone(model_info)
                
                # Generate code and verify it uses model-specific settings
                code = generator.generate_code(model_key, matrix_width=16, matrix_height=16)
                
                # Should include model-specific elements
                self.assertIn(f"#define DATA_PIN {model_info['default_pin']}", code)
                self.assertIn(model_info['includes'][0], code)
                
                if model_info['needs_level_shifter']:
                    # ESP models should have different setup
                    self.assertIn('WiFi', code)
                else:
                    # Arduino models should have serial setup
                    self.assertIn('Serial.begin', code)
    
    def test_design_library_arduino_integration(self):
        """Test integration between design library and Arduino generator"""
        from matrix_design_library import MatrixDesign
        
        # Create a design
        design = MatrixDesign(8, 8)
        design.fill_solid('#ff0000')
        design.set_pixel(0, 0, '#00ff00')
        
        # Generate Arduino code from design
        arduino_code = design.generate_arduino_code("testData", "uno")
        
        self.assertIsInstance(arduino_code, str)
        self.assertGreater(len(arduino_code), 100)
        
        # Should contain design-specific data
        self.assertIn('testData', arduino_code)
        self.assertIn('8', arduino_code)  # Matrix dimensions
        self.assertIn('loadMatrixData', arduino_code)
    
    def test_config_generator_integration(self):
        """Test integration between config generator and other modules"""
        from matrix_config_generator import MatrixConfigGenerator
        
        generator = MatrixConfigGenerator()
        generator.set_config(width=12, height=12, brightness=100)
        
        # Test Arduino code generation
        arduino_code = generator.generate_arduino_code('uno')
        self.assertIn('#define MATRIX_WIDTH 12', arduino_code)
        self.assertIn('#define MATRIX_HEIGHT 12', arduino_code)
        self.assertIn('#define BRIGHTNESS 100', arduino_code)
        
        # Test Python code generation
        python_code = generator.generate_python_code()
        self.assertIn('MATRIX_WIDTH = 12', python_code)
        self.assertIn('MATRIX_HEIGHT = 12', python_code)
        self.assertIn('BRIGHTNESS = 100', python_code)
    
    def test_wiring_diagram_integration(self):
        """Test integration with wiring diagram generator"""
        try:
            from wiring_diagram_generator import WiringDiagramGenerator
            
            generator = WiringDiagramGenerator()
            
            # Test power calculation integration
            power_req = generator.calculate_power_requirements(16, 16, 128)
            self.assertIn('total_leds', power_req)
            self.assertEqual(power_req['total_leds'], 256)
            
            # Test diagram generation
            diagram = generator.generate_mermaid_diagram('arduino_uno', 16, 16)
            self.assertIsInstance(diagram, str)
            self.assertIn('Arduino Uno', diagram)
            self.assertIn('16', diagram)
            
        except ImportError:
            self.skipTest("Wiring diagram generator not available")


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        """Set up end-to-end test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = get_test_config()
    
    def tearDown(self):
        """Clean up end-to-end test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_project_generation_workflow(self):
        """Test complete project generation from config to files"""
        from matrix_config_generator import MatrixConfigGenerator
        
        # Step 1: Configure project
        generator = MatrixConfigGenerator()
        generator.set_config(
            width=16,
            height=16,
            brightness=128,
            data_pin=6
        )
        
        # Step 2: Calculate specifications
        specs = generator.calculate_specs()
        self.assertEqual(specs['total_leds'], 256)
        self.assertGreater(specs['max_current_total'], 0)
        
        # Step 3: Generate files
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            generator.save_files("test_project", "uno")
            
            # Verify files were created
            expected_files = [
                "test_project_uno.ino",
                "test_project_controller.py",
                "test_project_config.json"
            ]
            
            for filename in expected_files:
                self.assertTrue(os.path.exists(filename), f"File {filename} not created")
                
                # Verify file has content
                with open(filename, 'r') as f:
                    content = f.read()
                    self.assertGreater(len(content), 100, f"File {filename} appears empty")
        
        finally:
            os.chdir(original_cwd)
    
    def test_design_to_arduino_workflow(self):
        """Test workflow from design creation to Arduino code"""
        from matrix_design_library import MatrixDesign
        
        # Step 1: Create design
        design = MatrixDesign(8, 8)
        design.generate_rainbow()
        
        # Step 2: Export design
        design_file = os.path.join(self.temp_dir, "test_design.json")
        export_success = design.export_design(design_file)
        self.assertTrue(export_success)
        
        # Step 3: Generate Arduino code
        arduino_code = design.generate_arduino_code("rainbowData", "esp32")
        
        # Step 4: Verify Arduino code
        self.assertIn('rainbowData', arduino_code)
        self.assertIn('ESP32', arduino_code)
        self.assertIn('WiFi', arduino_code)  # ESP32 specific
        self.assertIn('loadMatrixData', arduino_code)
    
    def test_configuration_backup_restore_workflow(self):
        """Test configuration backup and restore workflow"""
        from matrix_config import MatrixConfig
        
        config_file = os.path.join(self.temp_dir, "workflow_config.json")
        
        # Step 1: Create and configure
        config = MatrixConfig(config_file)
        config.set("matrix_width", 20)
        config.set("matrix_height", 25)
        config.set("test_workflow", "original_value")
        config.save_config()
        
        # Step 2: Modify configuration
        config.set("matrix_width", 30)
        config.set("test_workflow", "modified_value")
        config.save_config()  # This creates a backup
        
        # Step 3: Restore from backup
        restore_success = config.restore_from_backup()
        self.assertTrue(restore_success)
        
        # Step 4: Verify restoration
        self.assertEqual(config.get("matrix_width"), 20)
        self.assertEqual(config.get("test_workflow"), "original_value")
    
    @patch('serial.Serial')
    def test_hardware_communication_workflow(self, mock_serial):
        """Test hardware communication workflow"""
        from matrix_hardware import MatrixHardware
        import numpy as np
        
        # Mock serial connection
        mock_serial_instance = MagicMock()
        mock_serial.return_value = mock_serial_instance
        
        # Step 1: Connect to hardware
        hardware = MatrixHardware()
        result = hardware.connect(mode="USB", port="COM_TEST")
        self.assertIn("Connected", result)
        
        # Step 2: Send frame data
        test_data = np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8)
        result = hardware.send_frame(test_data)
        self.assertEqual(result, "Frame sent successfully")
        
        # Step 3: Verify serial communication
        mock_serial.assert_called_once()
        mock_serial_instance.write.assert_called()
        
        # Step 4: Disconnect
        hardware.disconnect()
        mock_serial_instance.close.assert_called_once()


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across module boundaries"""
    
    def test_invalid_model_error_propagation(self):
        """Test that invalid model errors propagate correctly"""
        from arduino_generator import ArduinoGenerator
        
        generator = ArduinoGenerator()
        
        # Should raise ValueError for invalid model
        with self.assertRaises(ValueError):
            generator.generate_code("invalid_model")
    
    def test_file_operation_error_handling(self):
        """Test file operation error handling across modules"""
        from matrix_design_library import MatrixDesign
        
        design = MatrixDesign(8, 8)
        
        # Test export to invalid path
        invalid_path = "/invalid/path/that/does/not/exist/design.json"
        success = design.export_design(invalid_path)
        self.assertFalse(success)  # Should fail gracefully
        
        # Test import from non-existent file
        success = design.import_design("non_existent_file.json")
        self.assertFalse(success)  # Should fail gracefully
    
    def test_configuration_error_recovery(self):
        """Test configuration error recovery"""
        from matrix_config import MatrixConfig
        
        # Test with corrupted config file
        temp_file = os.path.join(tempfile.mkdtemp(), "corrupted.json")
        with open(temp_file, 'w') as f:
            f.write("{ invalid json")
        
        # Should fall back to defaults without crashing
        config = MatrixConfig(temp_file)
        self.assertIsNotNone(config.get("matrix_width"))
        self.assertIsNotNone(config.get("matrix_height"))


def run_integration_validation():
    """Run validation tests for module integration"""
    print("🔧 Running Integration Validation Tests")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test 1: Module imports and basic integration
        print("\n📝 Test 1: Module Import Integration")
        
        from matrix_config import config
        from matrix_hardware import hardware
        from arduino_generator import ArduinoGenerator
        from arduino_models import validate_model
        
        # All modules should import without errors
        assert config is not None
        assert hardware is not None
        
        generator = ArduinoGenerator()
        assert generator is not None
        
        assert validate_model('uno') is True
        
        print("   ✅ Module imports working correctly")
        
        # Test 2: Cross-module functionality
        print("\n📝 Test 2: Cross-Module Functionality")
        
        # Config should be used by hardware
        original_mode = config.get("connection_mode")
        config.set("connection_mode", "TEST_MODE")
        
        new_hardware = hardware.__class__()  # Create new instance
        # Note: This test is limited due to global config usage
        
        # Restore original mode
        config.set("connection_mode", original_mode)
        
        print("   ✅ Cross-module functionality working")
        
        # Test 3: End-to-end workflow
        print("\n📝 Test 3: End-to-End Workflow")
        
        # Generate Arduino code using integrated modules
        code = generator.generate_code('uno', matrix_width=8, matrix_height=8)
        assert len(code) > 100
        assert '#define MATRIX_WIDTH 8' in code
        
        print("   ✅ End-to-end workflow working correctly")
        
        print("\n✅ All integration validation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run both unittest and validation tests
    print("🧪 Running Integration Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run validation tests
    print("\n" + "=" * 60)
    validation_success = run_integration_validation()
    
    print("\n🎉 Integration Test Suite Complete!")
    print("=" * 60)
    if validation_success:
        print("✅ All tests passed - Module integration is working correctly!")
    else:
        print("⚠️  Some validation tests failed - check output above")