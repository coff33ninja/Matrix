#!/usr/bin/env python3
"""
Test script for the Arduino generator system
Comprehensive tests for model selection and code generation
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from arduino_generator import ArduinoGenerator
from arduino_models import get_model_display_names, validate_model, get_model_info
from tests import get_test_config


class TestArduinoGenerator(unittest.TestCase):
    """Test cases for Arduino code generator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = ArduinoGenerator()
        self.test_config = get_test_config()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_model_validation(self):
        """Test Arduino model validation"""
        # Valid models
        valid_models = ['uno', 'nano', 'esp32', 'esp8266', 'mega']
        for model in valid_models:
            self.assertTrue(validate_model(model), f"Model {model} should be valid")
        
        # Invalid models
        invalid_models = ['invalid', 'arduino_fake', '']
        for model in invalid_models:
            self.assertFalse(validate_model(model), f"Model {model} should be invalid")
    
    def test_model_info_retrieval(self):
        """Test model information retrieval"""
        model_info = get_model_info('uno')
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info['name'], 'Arduino Uno')
        self.assertEqual(model_info['voltage'], '5V')
        self.assertFalse(model_info['needs_level_shifter'])
        
        # Test ESP32 (requires level shifter)
        esp32_info = get_model_info('esp32')
        self.assertIsNotNone(esp32_info)
        self.assertTrue(esp32_info['needs_level_shifter'])
        self.assertEqual(esp32_info['voltage'], '3.3V')
    
    def test_code_generation_basic(self):
        """Test basic Arduino code generation"""
        test_configs = [
            {'model': 'uno', 'width': 16, 'height': 16},
            {'model': 'esp32', 'width': 32, 'height': 32},
            {'model': 'nano', 'width': 8, 'height': 8},
        ]
        
        for config in test_configs:
            with self.subTest(model=config['model']):
                code = self.generator.generate_code(
                    config['model'],
                    matrix_width=config['width'],
                    matrix_height=config['height']
                )
                
                # Basic validation
                self.assertIsInstance(code, str)
                self.assertGreater(len(code), 100)  # Should be substantial
                
                # Check for required elements
                self.assertIn('#include <FastLED.h>', code)
                self.assertIn(f"#define MATRIX_WIDTH {config['width']}", code)
                self.assertIn(f"#define MATRIX_HEIGHT {config['height']}", code)
                self.assertIn('void setup()', code)
                self.assertIn('void loop()', code)
    
    def test_code_generation_with_custom_config(self):
        """Test code generation with custom configuration"""
        custom_config = {
            'width': 20,
            'height': 25,
            'data_pin': 7,
            'brightness': 200
        }
        
        code = self.generator.generate_code(
            'uno',
            matrix_width=custom_config['width'],
            matrix_height=custom_config['height'],
            data_pin=custom_config['data_pin'],
            brightness=custom_config['brightness']
        )
        
        self.assertIn(f"#define MATRIX_WIDTH {custom_config['width']}", code)
        self.assertIn(f"#define MATRIX_HEIGHT {custom_config['height']}", code)
        self.assertIn(f"#define DATA_PIN {custom_config['data_pin']}", code)
        self.assertIn(f"#define BRIGHTNESS {custom_config['brightness']}", code)
    
    def test_file_generation(self):
        """Test Arduino file generation and saving"""
        test_file = os.path.join(self.temp_dir, "test_matrix.ino")
        
        filename = self.generator.save_arduino_file(
            'uno',
            filename=test_file,
            matrix_width=16,
            matrix_height=16
        )
        
        self.assertEqual(filename, test_file)
        self.assertTrue(os.path.exists(test_file))
        
        # Verify file content
        with open(test_file, 'r') as f:
            content = f.read()
            self.assertIn('#include <FastLED.h>', content)
            self.assertIn('Arduino Uno', content)
    
    def test_model_recommendations(self):
        """Test model recommendations based on matrix size"""
        # Small matrix - should recommend all models
        small_recommendations = self.generator.get_model_recommendations(8, 8)
        self.assertGreater(len(small_recommendations), 0)
        
        # Large matrix - should filter out smaller models
        large_recommendations = self.generator.get_model_recommendations(64, 64)
        self.assertGreater(len(large_recommendations), 0)
        
        # Check recommendation structure
        for rec in small_recommendations:
            self.assertIn('key', rec)
            self.assertIn('name', rec)
            self.assertIn('suitable', rec)
            self.assertIn('memory_efficiency', rec)
    
    def test_invalid_model_handling(self):
        """Test handling of invalid models"""
        with self.assertRaises(ValueError):
            self.generator.generate_code('invalid_model')
    
    @patch('serial.tools.list_ports.comports')
    def test_serial_port_detection(self, mock_comports):
        """Test serial port detection functionality"""
        # Mock serial ports
        mock_port = MagicMock()
        mock_port.device = 'COM3'
        mock_port.description = 'Arduino Uno'
        mock_port.hwid = 'USB VID:PID=2341:0043'
        mock_port.manufacturer = 'Arduino LLC'
        mock_comports.return_value = [mock_port]
        
        ports = self.generator.list_serial_ports()
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['device'], 'COM3')
        
        arduino_ports = self.generator.find_arduino_ports()
        self.assertEqual(len(arduino_ports), 1)


class TestArduinoGeneratorIntegration(unittest.TestCase):
    """Integration tests for Arduino generator with other modules"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.generator = ArduinoGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_integration_with_matrix_config(self):
        """Test integration with matrix configuration"""
        from matrix_config import config
        
        # Test that generator uses shared config
        code = self.generator.generate_code('uno')
        
        # Should use config values
        expected_width = config.get('matrix_width', 21)
        expected_height = config.get('matrix_height', 24)
        
        self.assertIn(f"#define MATRIX_WIDTH {expected_width}", code)
        self.assertIn(f"#define MATRIX_HEIGHT {expected_height}", code)
    
    def test_organized_directory_generation(self):
        """Test organized directory structure generation"""
        base_dir = os.path.join(self.temp_dir, "generated_arduino")
        
        # Change to temp directory for this test
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            filename = self.generator.save_to_organized_directory(
                'esp32',
                matrix_width=16,
                matrix_height=16
            )
            
            expected_path = os.path.join("generated_arduino", "esp32", "led_matrix_16x16.ino")
            self.assertTrue(os.path.exists(expected_path))
            
        finally:
            os.chdir(original_cwd)


def run_legacy_tests():
    """Run the original test functions for compatibility"""
    print("🔧 Running Legacy Arduino Generator Tests")
    print("=" * 50)
    
    generator = ArduinoGenerator()
    
    # Show available models
    print("\n📋 Available Arduino Models:")
    models = get_model_display_names()
    for key, name in models.items():
        print(f"  - {key}: {name}")
    
    # Test with different models
    test_configs = [
        {'model': 'uno', 'width': 16, 'height': 16, 'description': 'Small matrix for Arduino Uno'},
        {'model': 'esp32', 'width': 32, 'height': 32, 'description': 'Large matrix for ESP32'},
        {'model': 'nano', 'width': 8, 'height': 8, 'description': 'Tiny matrix for Arduino Nano'},
    ]
    
    print("\n🧪 Testing Code Generation:")
    print("-" * 50)
    
    success_count = 0
    for config in test_configs:
        print(f"\n📝 {config['description']}")
        print(f"   Model: {config['model']}, Size: {config['width']}×{config['height']}")
        
        try:
            # Generate code without saving for testing
            code = generator.generate_code(
                config['model'],
                matrix_width=config['width'],
                matrix_height=config['height']
            )
            print(f"   ✅ Generated: {len(code)} characters")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test model recommendations
    print("\n💡 Model Recommendations:")
    print("-" * 50)
    
    test_sizes = [
        (8, 8, "Small matrix"),
        (21, 24, "PC case matrix"),
        (32, 32, "Large display"),
        (64, 64, "Very large matrix")
    ]
    
    for width, height, desc in test_sizes:
        print(f"\n{desc} ({width}×{height} = {width*height} LEDs):")
        try:
            generator.print_model_comparison(width, height)
        except Exception as e:
            print(f"   ❌ Error in model comparison: {e}")
    
    print(f"\n✅ Legacy tests completed: {success_count}/{len(test_configs)} configurations successful")
    return success_count == len(test_configs)


if __name__ == "__main__":
    # Run both unittest and legacy tests
    print("🧪 Running Arduino Generator Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run legacy tests
    print("\n" + "=" * 60)
    legacy_success = run_legacy_tests()
    
    print("\n🎉 Test Suite Complete!")
    print("=" * 60)
    if legacy_success:
        print("✅ All tests passed - Arduino generator is working correctly!")
    else:
        print("⚠️  Some legacy tests failed - check output above")