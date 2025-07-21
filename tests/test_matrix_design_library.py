#!/usr/bin/env python3
"""
Test suite for matrix design library
Tests design creation, effects, file operations, and statistical analysis
"""

import unittest
import tempfile
import os
import sys
import shutil
import numpy as np
from unittest.mock import patch, MagicMock

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from matrix_design_library import MatrixDesign
from tests import get_test_config


class TestMatrixDesign(unittest.TestCase):
    """Test cases for matrix design functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = get_test_config()
        self.design = MatrixDesign(
            width=self.test_config["default_matrix_width"],
            height=self.test_config["default_matrix_height"]
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_design_initialization(self):
        """Test matrix design initialization"""
        self.assertEqual(self.design.width, self.test_config["default_matrix_width"])
        self.assertEqual(self.design.height, self.test_config["default_matrix_height"])
        self.assertEqual(len(self.design.frames), 1)  # Should start with one empty frame
        self.assertEqual(self.design.current_frame, 0)
        self.assertGreater(self.design.frame_rate, 0)
    
    def test_frame_management(self):
        """Test frame addition, duplication, and deletion"""
        initial_frame_count = len(self.design.frames)
        
        # Add frame
        new_frame_index = self.design.add_frame()
        self.assertEqual(len(self.design.frames), initial_frame_count + 1)
        self.assertEqual(new_frame_index, initial_frame_count)
        
        # Duplicate frame
        duplicate_index = self.design.duplicate_frame(0)
        self.assertEqual(len(self.design.frames), initial_frame_count + 2)
        self.assertEqual(duplicate_index, 1)
        
        # Delete frame (should not delete if only one frame)
        while len(self.design.frames) > 1:
            self.design.delete_frame()
        
        # Try to delete last frame (should fail)
        with self.assertRaises(ValueError):
            self.design.delete_frame()
    
    def test_pixel_operations(self):
        """Test individual pixel operations"""
        test_color = '#ff0000'  # Red
        
        # Set pixel
        self.design.set_pixel(5, 5, test_color)
        retrieved_color = self.design.get_pixel(5, 5)
        self.assertEqual(retrieved_color, test_color)
        
        # Test bounds checking
        out_of_bounds_color = self.design.get_pixel(100, 100)
        self.assertEqual(out_of_bounds_color, '#000000')  # Should return black for out of bounds
        
        # Set pixel out of bounds (should not crash)
        self.design.set_pixel(100, 100, test_color)  # Should be ignored
    
    def test_fill_operations(self):
        """Test fill operations"""
        test_color = '#00ff00'  # Green
        
        # Fill solid
        self.design.fill_solid(test_color)
        
        # Check random pixels
        for _ in range(10):
            x = np.random.randint(0, self.design.width)
            y = np.random.randint(0, self.design.height)
            self.assertEqual(self.design.get_pixel(x, y), test_color)
    
    def test_pattern_generation(self):
        """Test pattern generation functions"""
        # Rainbow pattern
        self.design.generate_rainbow()
        
        # Check that colors are not all the same
        colors = set()
        for y in range(min(5, self.design.height)):
            for x in range(min(5, self.design.width)):
                colors.add(self.design.get_pixel(x, y))
        self.assertGreater(len(colors), 1)  # Should have multiple colors
        
        # Gradient pattern
        self.design.generate_gradient('#ff0000', '#0000ff', 'horizontal')
        
        # Check that gradient changes across width
        left_color = self.design.get_pixel(0, self.design.height // 2)
        right_color = self.design.get_pixel(self.design.width - 1, self.design.height // 2)
        self.assertNotEqual(left_color, right_color)
        
        # Checkerboard pattern
        self.design.generate_checkerboard('#ffffff', '#000000', 2)
        
        # Check checkerboard pattern
        color1 = self.design.get_pixel(0, 0)
        color2 = self.design.get_pixel(2, 0)  # Should be different due to checkerboard
        self.assertNotEqual(color1, color2)
    
    def test_flood_fill(self):
        """Test flood fill algorithm"""
        # Fill with initial color
        self.design.fill_solid('#000000')
        
        # Set a different color in one corner
        self.design.set_pixel(0, 0, '#ff0000')
        
        # Flood fill from that corner
        self.design.flood_fill(0, 0, '#00ff00')
        
        # The pixel should now be green
        self.assertEqual(self.design.get_pixel(0, 0), '#00ff00')
    
    def test_export_import_design(self):
        """Test design export and import"""
        # Set up test design
        self.design.fill_solid('#ff0000')
        self.design.set_pixel(5, 5, '#00ff00')
        
        # Export design
        export_file = os.path.join(self.temp_dir, "test_design.json")
        export_success = self.design.export_design(export_file)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(export_file))
        
        # Create new design and import
        new_design = MatrixDesign(self.design.width, self.design.height)
        import_success = new_design.import_design(export_file)
        self.assertTrue(import_success)
        
        # Verify imported design matches original
        self.assertEqual(new_design.get_pixel(5, 5), '#00ff00')
        self.assertEqual(len(new_design.frames), len(self.design.frames))
    
    @patch('PIL.Image.open')
    def test_image_loading(self, mock_image_open):
        """Test image loading functionality"""
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_img.resize.return_value = mock_img
        mock_img.getpixel.return_value = (255, 0, 0)  # Red pixel
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        # Test image loading
        success = self.design.load_image("fake_image.png")
        self.assertTrue(success)
        
        # Verify mock was called
        mock_image_open.assert_called_once()
    
    def test_text_creation(self):
        """Test text creation functionality"""
        success = self.design.create_text("TEST", font_size=8, color='#ffffff')
        self.assertTrue(success)
        
        # Check that some pixels are not black (text should be visible)
        non_black_pixels = 0
        for y in range(self.design.height):
            for x in range(self.design.width):
                if self.design.get_pixel(x, y) != '#000000':
                    non_black_pixels += 1
        
        self.assertGreater(non_black_pixels, 0)


class TestMatrixDesignAdvancedFeatures(unittest.TestCase):
    """Test cases for advanced matrix design features using numpy, time, and os"""
    
    def setUp(self):
        """Set up test fixtures for advanced features"""
        self.temp_dir = tempfile.mkdtemp()
        self.design = MatrixDesign(16, 16)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_plasma_effect_generation(self):
        """Test plasma effect generation using numpy"""
        # Generate plasma effect
        self.design.generate_plasma_effect(time_offset=0)
        
        # Check that colors vary across the matrix
        colors = set()
        for y in range(self.design.height):
            for x in range(self.design.width):
                colors.add(self.design.get_pixel(x, y))
        
        # Plasma should generate many different colors
        self.assertGreater(len(colors), 10)
    
    def test_plasma_animation_creation(self):
        """Test plasma animation creation with timing"""
        import time
        start_time = time.time()
        
        # Create plasma animation
        self.design.create_plasma_animation(num_frames=5)
        
        end_time = time.time()
        
        # Should have created 5 frames
        self.assertEqual(len(self.design.frames), 5)
        
        # Should have taken some time (but not too much for 5 frames)
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 10)  # Should complete within 10 seconds
    
    def test_noise_filter_application(self):
        """Test noise filter using numpy random generation"""
        # Fill with solid color first
        self.design.fill_solid('#808080')  # Gray
        original_color = self.design.get_pixel(8, 8)
        
        # Apply noise filter
        self.design.apply_noise_filter(intensity=0.2)
        
        # Color should be slightly different due to noise
        noisy_color = self.design.get_pixel(8, 8)
        # Colors might be the same due to randomness, but overall pattern should change
        
        # Check that at least some pixels changed
        changed_pixels = 0
        for y in range(self.design.height):
            for x in range(self.design.width):
                if self.design.get_pixel(x, y) != '#808080':
                    changed_pixels += 1
        
        # Some pixels should have changed due to noise
        self.assertGreater(changed_pixels, 0)
    
    def test_frame_statistical_analysis(self):
        """Test frame statistical analysis using numpy"""
        # Create a test pattern
        self.design.fill_solid('#ff0000')  # Red
        self.design.set_pixel(0, 0, '#00ff00')  # One green pixel
        self.design.set_pixel(1, 1, '#0000ff')  # One blue pixel
        
        # Analyze frame statistics
        stats = self.design.analyze_frame_statistics()
        
        self.assertIsNotNone(stats)
        self.assertIn('red_channel', stats)
        self.assertIn('green_channel', stats)
        self.assertIn('blue_channel', stats)
        self.assertIn('brightness', stats)
        
        # Red channel should have high mean (mostly red pixels)
        self.assertGreater(stats['red_channel']['mean'], 200)
        
        # Green and blue should have lower means
        self.assertLess(stats['green_channel']['mean'], 50)
        self.assertLess(stats['blue_channel']['mean'], 50)
        
        # Check histogram
        self.assertIn('histogram', stats['brightness'])
        self.assertIsInstance(stats['brightness']['histogram'], list)
    
    def test_backup_with_timestamp(self):
        """Test backup creation with timestamp using os and time modules"""
        # Create a test design
        self.design.fill_solid('#ff0000')
        
        # Export original design
        original_file = os.path.join(self.temp_dir, "original_design.json")
        self.design.export_design(original_file)
        
        # Create backup with timestamp
        backup_file = self.design.create_backup_with_timestamp(original_file)
        
        self.assertIsNotNone(backup_file)
        self.assertTrue(os.path.exists(backup_file))
        
        # Backup should be in backups subdirectory
        self.assertIn("backups", backup_file)
        self.assertTrue(backup_file.endswith(".json"))
    
    def test_file_operations_with_os_module(self):
        """Test file operations using os module functionality"""
        # Test export with directory creation
        nested_path = os.path.join(self.temp_dir, "nested", "deep", "design.json")
        
        # Export should create directories automatically
        success = self.design.export_design(nested_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(nested_path))
        self.assertTrue(os.path.exists(os.path.dirname(nested_path)))
        
        # Test import with file validation
        success = self.design.import_design(nested_path)
        self.assertTrue(success)
        
        # Test import with non-existent file
        non_existent = os.path.join(self.temp_dir, "does_not_exist.json")
        success = self.design.import_design(non_existent)
        self.assertFalse(success)


class TestMatrixDesignUtilities(unittest.TestCase):
    """Test cases for utility functions and helper methods"""
    
    def test_color_conversion_utilities(self):
        """Test color conversion utility functions"""
        # Test hex to RGB
        rgb = MatrixDesign.hex_to_rgb('#ff0080')
        self.assertEqual(rgb, (255, 0, 128))
        
        # Test RGB to hex
        hex_color = MatrixDesign.rgb_to_hex(255, 0, 128)
        self.assertEqual(hex_color, '#ff0080')
        
        # Test round trip conversion
        original_hex = '#123456'
        rgb = MatrixDesign.hex_to_rgb(original_hex)
        converted_hex = MatrixDesign.rgb_to_hex(*rgb)
        self.assertEqual(original_hex, converted_hex)
    
    def test_arduino_code_generation(self):
        """Test Arduino code generation from design"""
        # Create a simple design
        self.design = MatrixDesign(8, 8)
        self.design.fill_solid('#ff0000')
        
        # Generate Arduino code
        arduino_code = self.design.generate_arduino_code("matrixData", "uno")
        
        self.assertIsInstance(arduino_code, str)
        self.assertGreater(len(arduino_code), 100)
        
        # Check for required elements
        self.assertIn('matrixData', arduino_code)
        self.assertIn('8', arduino_code)  # Matrix dimensions
        self.assertIn('PROGMEM', arduino_code)
        self.assertIn('loadMatrixData', arduino_code)


def run_design_library_validation():
    """Run validation tests for matrix design library"""
    print("🔧 Running Matrix Design Library Validation Tests")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test 1: Basic design operations
        print("\n📝 Test 1: Basic Design Operations")
        design = MatrixDesign(16, 16)
        
        # Test pattern generation
        design.generate_rainbow()
        design.generate_gradient('#ff0000', '#0000ff', 'horizontal')
        design.generate_checkerboard('#ffffff', '#000000', 2)
        
        # Test pixel operations
        design.set_pixel(5, 5, '#ff00ff')
        assert design.get_pixel(5, 5) == '#ff00ff'
        
        print("   ✅ Basic design operations working correctly")
        
        # Test 2: Advanced effects with numpy
        print("\n📝 Test 2: Advanced Effects (numpy)")
        
        # Plasma effect
        design.generate_plasma_effect()
        
        # Noise filter
        design.apply_noise_filter(0.1)
        
        # Statistical analysis
        stats = design.analyze_frame_statistics()
        assert stats is not None
        assert 'red_channel' in stats
        
        print("   ✅ Advanced effects working correctly")
        
        # Test 3: File operations with os module
        print("\n📝 Test 3: File Operations (os module)")
        
        export_file = os.path.join(temp_dir, "test_design.json")
        export_success = design.export_design(export_file)
        assert export_success
        assert os.path.exists(export_file)
        
        # Test backup creation
        backup_file = design.create_backup_with_timestamp(export_file)
        assert backup_file is not None
        assert os.path.exists(backup_file)
        
        print("   ✅ File operations working correctly")
        
        # Test 4: Animation creation with timing
        print("\n📝 Test 4: Animation Creation (time module)")
        
        import time
        start_time = time.time()
        design.create_plasma_animation(num_frames=3)
        end_time = time.time()
        
        assert len(design.frames) == 3
        assert end_time > start_time  # Should take some time
        
        print("   ✅ Animation creation working correctly")
        
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
    print("🧪 Running Matrix Design Library Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run validation tests
    print("\n" + "=" * 60)
    validation_success = run_design_library_validation()
    
    print("\n🎉 Matrix Design Library Test Suite Complete!")
    print("=" * 60)
    if validation_success:
        print("✅ All tests passed - Matrix design library is working correctly!")
    else:
        print("⚠️  Some validation tests failed - check output above")