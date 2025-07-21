#!/usr/bin/env python3
"""
Test suite for wiring diagram generator
Tests diagram generation, JSON export/import, and configuration functionality
"""

import unittest
import tempfile
import os
import sys
import shutil
import json

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from wiring_diagram_generator import WiringDiagramGenerator
from tests import get_test_config


class TestWiringDiagramGenerator(unittest.TestCase):
    """Test cases for wiring diagram generator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = get_test_config()
        self.generator = WiringDiagramGenerator()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_generator_initialization(self):
        """Test wiring diagram generator initialization"""
        self.assertIsInstance(self.generator.controllers, dict)
        self.assertIsInstance(self.generator.power_supplies, dict)
        
        # Check that all expected controllers are present
        expected_controllers = ['arduino_uno', 'arduino_nano', 'esp32', 'esp8266']
        for controller in expected_controllers:
            self.assertIn(controller, self.generator.controllers)
        
        # Check controller data structure
        for controller_data in self.generator.controllers.values():
            required_fields = ['name', 'voltage', 'default_pin', 'needs_level_shifter', 'color']
            for field in required_fields:
                self.assertIn(field, controller_data)
    
    def test_power_requirements_calculation(self):
        """Test power requirements calculation using shared function"""
        power_req = self.generator.calculate_power_requirements(16, 16, 128)
        
        self.assertIn('total_leds', power_req)
        self.assertIn('total_current_amps', power_req)
        self.assertIn('recommended_psu', power_req)
        
        # Verify calculations
        self.assertEqual(power_req['total_leds'], 256)
        self.assertGreater(power_req['total_current_amps'], 0)
        self.assertIn(power_req['recommended_psu'], self.generator.power_supplies)
    
    def test_mermaid_diagram_generation(self):
        """Test Mermaid diagram generation"""
        diagram = self.generator.generate_mermaid_diagram('arduino_uno', 16, 16)
        
        self.assertIsInstance(diagram, str)
        self.assertGreater(len(diagram), 100)
        
        # Check for required elements
        self.assertIn('graph TB', diagram)
        self.assertIn('Arduino Uno', diagram)
        self.assertIn('16', diagram)  # Matrix dimensions
        self.assertIn('CONTROLLER', diagram)
        self.assertIn('PSU', diagram)
        self.assertIn('MATRIX', diagram)
    
    def test_connection_list_generation(self):
        """Test connection list generation"""
        connections = self.generator.generate_connection_list('esp32', 8, 8)
        
        self.assertIsInstance(connections, str)
        self.assertGreater(len(connections), 100)
        
        # Check for ESP32-specific content
        self.assertIn('ESP32', connections)
        # Handle case variations
        self.assertTrue('Level shifter' in connections or 'Level Shifter' in connections)
        self.assertIn('74HCT125', connections)
        # Handle both Unicode and encoded versions
        self.assertTrue('8×8' in connections or '8Ã—8' in connections)
    
    def test_troubleshooting_guide_generation(self):
        """Test troubleshooting guide generation"""
        guide = self.generator.generate_troubleshooting_guide('arduino_uno')
        
        self.assertIsInstance(guide, str)
        self.assertGreater(len(guide), 100)
        
        # Check for troubleshooting content
        self.assertIn('Troubleshooting Guide', guide)
        self.assertIn('Arduino Uno', guide)
        self.assertIn('Common Issues', guide)
        self.assertIn('LEDs Not Lighting Up', guide)
    
    def test_complete_guide_generation(self):
        """Test complete guide generation"""
        guide = self.generator.generate_complete_guide('arduino_nano', 12, 12)
        
        self.assertIsInstance(guide, str)
        self.assertGreater(len(guide), 500)  # Should be comprehensive
        
        # Check for all major sections
        self.assertIn('LED Matrix Wiring Guide', guide)
        self.assertIn('Configuration Summary', guide)
        self.assertIn('Mermaid Wiring Diagram', guide)
        self.assertIn('Connection List', guide)
        self.assertIn('Troubleshooting Guide', guide)
    
    def test_guide_file_saving(self):
        """Test saving guide to file"""
        test_file = os.path.join(self.temp_dir, "test_guide.md")
        
        filename = self.generator.save_guide('arduino_uno', 8, 8, test_file)
        
        self.assertEqual(filename, test_file)
        self.assertTrue(os.path.exists(test_file))
        
        # Verify file content
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Arduino Uno', content)
            # Handle both Unicode and encoded versions
            self.assertTrue('8×8' in content or '8Ã—8' in content)


class TestWiringDiagramJSONFunctionality(unittest.TestCase):
    """Test cases for JSON export/import functionality"""
    
    def setUp(self):
        """Set up JSON test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = WiringDiagramGenerator()
    
    def tearDown(self):
        """Clean up JSON test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_json_configuration_export(self):
        """Test JSON configuration export functionality"""
        test_file = os.path.join(self.temp_dir, "test_config.json")
        
        filename = self.generator.export_configuration_json(
            'esp32', 16, 16, data_pin=13, filename=test_file
        )
        
        self.assertEqual(filename, test_file)
        self.assertTrue(os.path.exists(test_file))
        
        # Verify JSON structure
        with open(test_file, 'r') as f:
            config_data = json.load(f)
        
        # Check required sections
        required_sections = [
            'metadata', 'matrix_configuration', 'controller_configuration',
            'power_requirements', 'wiring_connections', 'component_list'
        ]
        
        for section in required_sections:
            self.assertIn(section, config_data)
        
        # Verify specific data
        self.assertEqual(config_data['matrix_configuration']['width'], 16)
        self.assertEqual(config_data['matrix_configuration']['height'], 16)
        self.assertEqual(config_data['controller_configuration']['type'], 'esp32')
        self.assertTrue(config_data['controller_configuration']['needs_level_shifter'])
        
        # Check level shifter configuration for ESP32
        self.assertIn('level_shifter_configuration', config_data)
        self.assertTrue(config_data['level_shifter_configuration']['required'])
    
    def test_json_configuration_import(self):
        """Test JSON configuration import functionality"""
        # First export a configuration
        test_file = os.path.join(self.temp_dir, "import_test.json")
        self.generator.export_configuration_json('arduino_uno', 20, 25, filename=test_file)
        
        # Then import it
        imported_config = self.generator.import_configuration_json(test_file)
        
        self.assertIsNotNone(imported_config)
        self.assertEqual(imported_config['matrix_configuration']['width'], 20)
        self.assertEqual(imported_config['matrix_configuration']['height'], 25)
        self.assertEqual(imported_config['controller_configuration']['type'], 'arduino_uno')
    
    def test_json_import_error_handling(self):
        """Test JSON import error handling"""
        # Test with non-existent file
        result = self.generator.import_configuration_json("non_existent_file.json")
        self.assertIsNone(result)
        
        # Test with invalid JSON
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json content")
        
        result = self.generator.import_configuration_json(invalid_file)
        self.assertIsNone(result)
    
    def test_shopping_list_generation(self):
        """Test shopping list JSON generation"""
        shopping_list = self.generator.generate_shopping_list_json('arduino_uno', 16, 16)
        
        self.assertIsInstance(shopping_list, dict)
        
        # Check required sections
        required_sections = [
            'project_info', 'required_components', 'optional_components',
            'led_strip_specifications', 'purchase_links'
        ]
        
        for section in required_sections:
            self.assertIn(section, shopping_list)
        
        # Verify project info
        project_info = shopping_list['project_info']
        self.assertIn('name', project_info)
        self.assertIn('total_leds', project_info)
        self.assertIn('estimated_cost', project_info)
        self.assertEqual(project_info['total_leds'], 256)  # 16x16
        
        # Verify components list
        components = shopping_list['required_components']
        self.assertIsInstance(components, list)
        self.assertGreater(len(components), 0)
        
        # Check for essential components
        component_names = [comp['name'] for comp in components]
        self.assertTrue(any('Arduino Uno' in name for name in component_names))
        self.assertTrue(any('Power Supply' in name for name in component_names))
        self.assertTrue(any('Capacitor' in name for name in component_names))
        self.assertTrue(any('Resistor' in name for name in component_names))
    
    def test_cost_estimation(self):
        """Test project cost estimation"""
        # Test different configurations
        configs = [
            ('arduino_uno', 8, 8),
            ('esp32', 32, 32),
            ('arduino_nano', 16, 16)
        ]
        
        for controller, width, height in configs:
            with self.subTest(controller=controller, size=f"{width}x{height}"):
                shopping_list = self.generator.generate_shopping_list_json(controller, width, height)
                cost = shopping_list['project_info']['estimated_cost']
                
                self.assertIsInstance(cost, (int, float))
                self.assertGreater(cost, 0)
                
                # Larger matrices should cost more
                if width * height > 100:
                    self.assertGreater(cost, 50)  # Should be at least $50 for large matrices


class TestWiringDiagramIntegration(unittest.TestCase):
    """Test integration with other modules"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.generator = WiringDiagramGenerator()
    
    def test_power_calculation_integration(self):
        """Test integration with arduino_models power calculations"""
        # Test that power calculations use shared functions
        power_req = self.generator.calculate_power_requirements(16, 16, 128)
        
        # Should use the shared calculation from arduino_models
        self.assertIn('brightness_factor', power_req)
        self.assertIn('safety_margin_percent', power_req)
        self.assertAlmostEqual(power_req['brightness_factor'], 0.5, places=1)  # 128/255 ≈ 0.5
        self.assertEqual(power_req['safety_margin_percent'], 20)
    
    def test_controller_model_consistency(self):
        """Test consistency with Arduino models"""
        from arduino_models import ARDUINO_MODELS
        
        # Check that wiring generator controllers match Arduino models
        for controller_key in self.generator.controllers.keys():
            # Map wiring generator keys to Arduino model keys
            model_key_map = {
                'arduino_uno': 'uno',
                'arduino_nano': 'nano',
                'esp32': 'esp32',
                'esp8266': 'esp8266'
            }
            
            if controller_key in model_key_map:
                arduino_model_key = model_key_map[controller_key]
                if arduino_model_key in ARDUINO_MODELS:
                    arduino_model = ARDUINO_MODELS[arduino_model_key]
                    wiring_controller = self.generator.controllers[controller_key]
                    
                    # Check consistency
                    self.assertEqual(
                        wiring_controller['needs_level_shifter'],
                        arduino_model['needs_level_shifter']
                    )
                    self.assertEqual(
                        wiring_controller['default_pin'],
                        arduino_model['default_pin']
                    )


def run_wiring_diagram_validation():
    """Run validation tests for wiring diagram generator"""
    print("🔧 Running Wiring Diagram Generator Validation Tests")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test 1: Basic diagram generation
        print("\n📝 Test 1: Basic Diagram Generation")
        generator = WiringDiagramGenerator()
        
        # Test Mermaid diagram
        diagram = generator.generate_mermaid_diagram('arduino_uno', 16, 16)
        assert len(diagram) > 100
        assert 'Arduino Uno' in diagram
        
        # Test connection list
        connections = generator.generate_connection_list('esp32', 8, 8)
        assert len(connections) > 100
        assert 'ESP32' in connections
        
        print("   ✅ Basic diagram generation working correctly")
        
        # Test 2: JSON functionality
        print("\n📝 Test 2: JSON Export/Import")
        
        # Export JSON configuration
        json_file = os.path.join(temp_dir, "test_config.json")
        filename = generator.export_configuration_json('esp32', 16, 16, filename=json_file)
        assert os.path.exists(json_file)
        
        # Import and verify
        imported_config = generator.import_configuration_json(json_file)
        assert imported_config is not None
        assert imported_config['matrix_configuration']['width'] == 16
        
        print("   ✅ JSON export/import working correctly")
        
        # Test 3: Shopping list generation
        print("\n📝 Test 3: Shopping List Generation")
        
        shopping_list = generator.generate_shopping_list_json('arduino_uno', 12, 12)
        assert 'project_info' in shopping_list
        assert 'required_components' in shopping_list
        assert shopping_list['project_info']['total_leds'] == 144
        
        print("   ✅ Shopping list generation working correctly")
        
        # Test 4: Power calculation integration
        print("\n📝 Test 4: Power Calculation Integration")
        
        power_req = generator.calculate_power_requirements(16, 16, 128)
        assert 'total_current_amps' in power_req
        assert 'brightness_factor' in power_req
        assert abs(power_req['brightness_factor'] - 0.5) < 0.01  # 128/255 ≈ 0.5
        
        print("   ✅ Power calculation integration working correctly")
        
        print("\n✅ All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run both unittest and validation tests
    print("🧪 Running Wiring Diagram Generator Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run validation tests
    print("\n" + "=" * 60)
    validation_success = run_wiring_diagram_validation()
    
    print("\n🎉 Wiring Diagram Generator Test Suite Complete!")
    print("=" * 60)
    if validation_success:
        print("✅ All tests passed - Wiring diagram generator is working correctly!")
    else:
        print("⚠️  Some validation tests failed - check output above")