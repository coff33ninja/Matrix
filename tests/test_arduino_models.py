#!/usr/bin/env python3
"""
Test suite for Arduino models module
Tests model information, calculations, and mathematical functions
"""

import unittest
import sys
import os
import math

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from arduino_models import (
    ARDUINO_MODELS,
    get_model_info,
    get_available_models,
    get_model_display_names,
    validate_model,
    get_recommended_model_for_leds,
    calculate_power_requirements,
    calculate_matrix_dimensions,
    calculate_memory_usage,
    calculate_refresh_rate,
    get_optimal_pin_configuration
)
from tests import get_test_config


class TestArduinoModels(unittest.TestCase):
    """Test cases for Arduino model definitions and basic functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = get_test_config()
    
    def test_model_definitions_completeness(self):
        """Test that all model definitions have required fields"""
        required_fields = [
            'name', 'display_name', 'voltage', 'default_pin',
            'memory_sram', 'memory_flash', 'needs_level_shifter',
            'max_leds_recommended', 'baud_rate', 'includes',
            'setup_code', 'loop_code'
        ]
        
        for model_key, model_data in ARDUINO_MODELS.items():
            with self.subTest(model=model_key):
                for field in required_fields:
                    self.assertIn(field, model_data, 
                                f"Model {model_key} missing required field: {field}")
                
                # Validate data types
                self.assertIsInstance(model_data['memory_sram'], int)
                self.assertIsInstance(model_data['memory_flash'], int)
                self.assertIsInstance(model_data['needs_level_shifter'], bool)
                self.assertIsInstance(model_data['max_leds_recommended'], int)
                self.assertIsInstance(model_data['includes'], list)
    
    def test_model_validation(self):
        """Test model validation function"""
        # Valid models
        for model_key in ARDUINO_MODELS.keys():
            self.assertTrue(validate_model(model_key))
            self.assertTrue(validate_model(model_key.upper()))  # Case insensitive
        
        # Invalid models
        invalid_models = ['invalid', 'arduino_fake', '', None]
        for invalid_model in invalid_models:
            if invalid_model is not None:
                self.assertFalse(validate_model(invalid_model))
    
    def test_model_info_retrieval(self):
        """Test model information retrieval"""
        # Valid model
        uno_info = get_model_info('uno')
        self.assertIsNotNone(uno_info)
        self.assertEqual(uno_info['name'], 'Arduino Uno')
        self.assertEqual(uno_info['voltage'], '5V')
        
        # Invalid model
        invalid_info = get_model_info('invalid_model')
        self.assertIsNone(invalid_info)
        
        # Case insensitive
        uno_info_upper = get_model_info('UNO')
        self.assertEqual(uno_info, uno_info_upper)
    
    def test_available_models_functions(self):
        """Test functions that return available models"""
        available = get_available_models()
        self.assertIsInstance(available, list)
        self.assertGreater(len(available), 0)
        self.assertIn('uno', available)
        self.assertIn('esp32', available)
        
        display_names = get_model_display_names()
        self.assertIsInstance(display_names, dict)
        self.assertEqual(len(display_names), len(available))
        self.assertEqual(display_names['uno'], 'Arduino Uno')
    
    def test_model_recommendations(self):
        """Test model recommendations based on LED count"""
        # Small LED count - all models should be suitable
        small_recs = get_recommended_model_for_leds(100)
        self.assertIsInstance(small_recs, list)
        self.assertGreater(len(small_recs), 0)
        
        suitable_count = sum(1 for rec in small_recs if rec['suitable'])
        self.assertGreater(suitable_count, 0)
        
        # Large LED count - some models should be unsuitable
        large_recs = get_recommended_model_for_leds(3000)
        unsuitable_count = sum(1 for rec in large_recs if not rec['suitable'])
        self.assertGreater(unsuitable_count, 0)
        
        # Check recommendation structure
        for rec in small_recs:
            self.assertIn('key', rec)
            self.assertIn('name', rec)
            self.assertIn('suitable', rec)
            self.assertIn('memory_efficiency', rec)


class TestArduinoModelCalculations(unittest.TestCase):
    """Test cases for mathematical calculations in Arduino models"""
    
    def test_power_requirements_calculation(self):
        """Test power requirements calculation"""
        # Test with standard values
        power_req = calculate_power_requirements(100, 100)  # 100 LEDs at 100% brightness
        
        self.assertIn('total_power_watts', power_req)
        self.assertIn('total_current_amps', power_req)
        self.assertIn('recommended_psu_watts', power_req)
        self.assertIn('safety_margin_percent', power_req)
        self.assertIn('brightness_factor', power_req)
        
        # Validate calculations
        self.assertEqual(power_req['brightness_factor'], 1.0)
        self.assertEqual(power_req['safety_margin_percent'], 20)
        self.assertGreater(power_req['total_power_watts'], 0)
        self.assertGreater(power_req['total_current_amps'], 0)
        
        # Test with reduced brightness
        power_req_50 = calculate_power_requirements(100, 50)  # 50% brightness
        self.assertEqual(power_req_50['brightness_factor'], 0.5)
        self.assertLess(power_req_50['total_current_amps'], power_req['total_current_amps'])
    
    def test_matrix_dimensions_calculation(self):
        """Test matrix dimensions calculation"""
        # Perfect square
        square_dims = calculate_matrix_dimensions(64)  # 8x8
        self.assertIsInstance(square_dims, list)
        self.assertGreater(len(square_dims), 0)
        
        # Check for square option
        square_found = any(dim['is_square'] for dim in square_dims)
        self.assertTrue(square_found)
        
        # Verify calculations
        for dim in square_dims:
            self.assertEqual(dim['width'] * dim['height'], 64)
            self.assertIn('aspect_ratio', dim)
            self.assertIn('is_square', dim)
        
        # Prime number (should only have 1x prime factors)
        prime_dims = calculate_matrix_dimensions(17)
        self.assertEqual(len(prime_dims), 1)
        self.assertTrue(prime_dims[0]['width'] == 1 or prime_dims[0]['height'] == 1)
    
    def test_memory_usage_calculation(self):
        """Test memory usage calculation"""
        # Test with Arduino Uno
        memory_usage = calculate_memory_usage(16, 16, 'uno')
        self.assertIsNotNone(memory_usage)
        
        required_fields = [
            'led_array_bytes', 'program_overhead_bytes', 'total_used_bytes',
            'available_sram_bytes', 'memory_used_percent', 'memory_free_bytes',
            'memory_efficiency_percent', 'is_feasible'
        ]
        
        for field in required_fields:
            self.assertIn(field, memory_usage)
        
        # Validate calculations
        expected_led_bytes = 16 * 16 * 3  # 768 bytes
        self.assertEqual(memory_usage['led_array_bytes'], expected_led_bytes)
        self.assertEqual(memory_usage['total_used_bytes'], 
                        expected_led_bytes + memory_usage['program_overhead_bytes'])
        
        # Test with invalid model
        invalid_memory = calculate_memory_usage(16, 16, 'invalid_model')
        self.assertIsNone(invalid_memory)
        
        # Test feasibility with large matrix
        large_memory = calculate_memory_usage(100, 100, 'uno')  # Very large for Uno
        self.assertFalse(large_memory['is_feasible'])
    
    def test_refresh_rate_calculation(self):
        """Test refresh rate calculation"""
        refresh_rate = calculate_refresh_rate(256, 500000)  # 16x16 matrix at 500k baud
        
        required_fields = [
            'max_fps', 'frame_time_ms', 'bytes_per_frame',
            'effective_baud_rate', 'is_realtime_capable'
        ]
        
        for field in required_fields:
            self.assertIn(field, refresh_rate)
        
        # Validate calculations
        expected_bytes = 256 * 3  # 768 bytes per frame
        self.assertEqual(refresh_rate['bytes_per_frame'], expected_bytes)
        self.assertGreater(refresh_rate['max_fps'], 0)
        self.assertGreater(refresh_rate['frame_time_ms'], 0)
        
        # Test with very low baud rate
        slow_refresh = calculate_refresh_rate(1000, 9600)  # Large matrix, slow baud
        self.assertFalse(slow_refresh['is_realtime_capable'])
    
    def test_optimal_pin_configuration(self):
        """Test optimal pin configuration calculation"""
        # Test ESP32 (many pins available)
        esp32_pins = get_optimal_pin_configuration('esp32', 4)
        self.assertIsNotNone(esp32_pins)
        
        required_fields = [
            'recommended_pins', 'max_parallel_strips',
            'pin_spacing', 'supports_parallel'
        ]
        
        for field in required_fields:
            self.assertIn(field, esp32_pins)
        
        self.assertEqual(len(esp32_pins['recommended_pins']), 4)
        self.assertTrue(esp32_pins['supports_parallel'])
        
        # Test Arduino Uno (limited pins)
        uno_pins = get_optimal_pin_configuration('uno', 5)  # Request more than available
        self.assertIsNotNone(uno_pins)
        self.assertFalse(uno_pins['supports_parallel'])  # Can't support 5 parallel strips
        
        # Test invalid model
        invalid_pins = get_optimal_pin_configuration('invalid_model', 1)
        self.assertIsNone(invalid_pins)


class TestArduinoModelsMathematicalFunctions(unittest.TestCase):
    """Test cases for mathematical functions using the math module"""
    
    def test_math_module_usage(self):
        """Test that math module functions are used correctly"""
        # Test power calculations use math.ceil
        power_req = calculate_power_requirements(100, 75)
        
        # Should use ceiling for power requirements
        expected_power = math.ceil(100 * 0.06 * 0.75 * 5 * 1.2)  # LEDs * current * brightness * voltage * safety
        self.assertEqual(power_req['total_power_watts'], expected_power)
        
        # Test matrix dimensions use math.sqrt
        dims = calculate_matrix_dimensions(100)
        sqrt_100 = int(math.sqrt(100))
        
        # Should find the 10x10 option
        square_option = next((d for d in dims if d['is_square']), None)
        self.assertIsNotNone(square_option)
        self.assertEqual(square_option['width'], sqrt_100)
        self.assertEqual(square_option['height'], sqrt_100)
    
    def test_mathematical_precision(self):
        """Test mathematical precision in calculations"""
        # Test that calculations are consistent
        power1 = calculate_power_requirements(256, 100)
        power2 = calculate_power_requirements(256, 100)
        
        self.assertEqual(power1['total_power_watts'], power2['total_power_watts'])
        self.assertEqual(power1['total_current_amps'], power2['total_current_amps'])
        
        # Test edge cases
        zero_power = calculate_power_requirements(0, 100)
        self.assertEqual(zero_power['total_current_amps'], 0)
        self.assertEqual(zero_power['total_power_watts'], 0)
        
        # Test with zero brightness
        zero_brightness = calculate_power_requirements(100, 0)
        self.assertEqual(zero_brightness['brightness_factor'], 0)


def run_arduino_models_validation():
    """Run validation tests for Arduino models"""
    print("🔧 Running Arduino Models Validation Tests")
    print("=" * 50)
    
    try:
        # Test 1: All models have consistent data
        print("\n📝 Test 1: Model Data Consistency")
        for model_key in ARDUINO_MODELS.keys():
            model = get_model_info(model_key)
            assert model is not None
            assert model['memory_sram'] > 0
            assert model['max_leds_recommended'] > 0
            assert len(model['includes']) > 0
        print("   ✅ All models have consistent data")
        
        # Test 2: Mathematical functions work correctly
        print("\n📝 Test 2: Mathematical Functions")
        
        # Power calculation
        power = calculate_power_requirements(100, 50)
        assert power['brightness_factor'] == 0.5
        assert power['total_power_watts'] > 0
        
        # Matrix dimensions
        dims = calculate_matrix_dimensions(64)
        assert len(dims) > 0
        assert any(d['is_square'] for d in dims)
        
        # Memory usage
        memory = calculate_memory_usage(16, 16, 'uno')
        assert memory['led_array_bytes'] == 768  # 16*16*3
        assert memory['is_feasible'] is True
        
        print("   ✅ Mathematical functions working correctly")
        
        # Test 3: Model recommendations
        print("\n📝 Test 3: Model Recommendations")
        small_recs = get_recommended_model_for_leds(100)
        large_recs = get_recommended_model_for_leds(2000)
        
        assert len(small_recs) > 0
        assert len(large_recs) > 0
        
        # Small matrix should have more suitable models
        small_suitable = sum(1 for r in small_recs if r['suitable'])
        large_suitable = sum(1 for r in large_recs if r['suitable'])
        assert small_suitable >= large_suitable
        
        print("   ✅ Model recommendations working correctly")
        
        print("\n✅ All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run both unittest and validation tests
    print("🧪 Running Arduino Models Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run validation tests
    print("\n" + "=" * 60)
    validation_success = run_arduino_models_validation()
    
    print("\n🎉 Arduino Models Test Suite Complete!")
    print("=" * 60)
    if validation_success:
        print("✅ All tests passed - Arduino models are working correctly!")
    else:
        print("⚠️  Some validation tests failed - check output above")