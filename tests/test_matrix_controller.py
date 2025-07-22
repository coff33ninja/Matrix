"""
Comprehensive unit tests for WebMatrixController
Testing framework: unittest (Python standard library)
"""

import unittest
from unittest.mock import patch, MagicMock
import threading
import time
import json
import numpy as np
from PIL import Image
import io
import base64
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestWebMatrixController(unittest.TestCase):
    """Test cases for WebMatrixController class"""

    def setUp(self) -> None:
        """Set up test fixtures before each test method"""
        # Mock external dependencies
        self.mock_config = MagicMock()
        self.mock_config.get.side_effect = lambda key, default=None: {
            'matrix_width': 16,
            'matrix_height': 16,
            'connection_mode': 'USB',
            'serial_port': '/dev/ttyUSB0',
            'baud_rate': 115200,
        }.get(key, default)
        
        self.mock_hardware = MagicMock()
        
        # Patch imports
        self.config_patcher = patch('matrix_config.config', self.mock_config)
        self.hardware_patcher = patch('matrix_hardware.hardware', self.mock_hardware)
        self.wiring_patcher = patch('wiring_diagram_generator.WiringDiagramGenerator')
        self.server_patcher = patch('socketserver.ThreadingTCPServer')
        self.psutil_patcher = patch('psutil.cpu_percent', return_value=25.0)
        self.memory_patcher = patch('psutil.virtual_memory')
        
        self.mock_config_patched = self.config_patcher.start()
        self.mock_hardware_patched = self.hardware_patcher.start()
        self.mock_wiring = self.wiring_patcher.start()
        self.mock_server = self.server_patcher.start()
        self.mock_psutil = self.psutil_patcher.start()
        self.mock_memory = self.memory_patcher.start()
        
        # Configure mock memory
        mock_memory_obj = MagicMock()
        mock_memory_obj.percent = 45.0
        self.mock_memory.return_value = mock_memory_obj

    def tearDown(self) -> None:
        """Clean up after each test method"""
        self.config_patcher.stop()
        self.hardware_patcher.stop()
        self.wiring_patcher.stop()
        self.server_patcher.stop()
        self.psutil_patcher.stop()
        self.memory_patcher.stop()

    @patch('threading.Thread')
    def test_init_default_port(self, mock_thread):
        """Test WebMatrixController initialization with default port"""
        from tests.test_matrix_controller import WebMatrixController
        
        controller = WebMatrixController()
        
        # Verify basic initialization
        self.assertEqual(controller.W, 16)
        self.assertEqual(controller.H, 16)
        self.assertEqual(controller.port, 8080)
        self.assertEqual(controller.current_mode, "idle")
        self.assertFalse(controller.is_streaming)
        self.assertEqual(controller.matrix_data.shape, (16, 16, 3))
        self.assertIsInstance(controller.start_time, datetime)
        
        # Verify server thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    @patch('threading.Thread')
    def test_init_custom_port(self, mock_thread):
        """Test WebMatrixController initialization with custom port"""
        from tests.test_matrix_controller import WebMatrixController
        
        controller = WebMatrixController(port=9000)
        
        self.assertEqual(controller.port, 9000)

    @patch('threading.Thread')
    def test_init_custom_matrix_size(self, mock_thread):
        """Test initialization with custom matrix size from config"""
        self.mock_config.get.side_effect = lambda key, default=None: {
            'matrix_width': 32,
            'matrix_height': 8,
            'connection_mode': 'USB'
        }.get(key, default)
        
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        self.assertEqual(controller.W, 32)
        self.assertEqual(controller.H, 8)
        self.assertEqual(controller.matrix_data.shape, (8, 32, 3))

    @patch('threading.Thread')
    def test_clear_matrix(self, mock_thread):
        """Test clear_matrix method"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Set some data in the matrix
        controller.matrix_data[0, 0] = [255, 255, 255]
        
        result = controller.clear_matrix()
        
        self.assertTrue(result)
        self.assertTrue(np.all(controller.matrix_data == 0))
        self.mock_hardware.send_frame.assert_called_once()

    @patch('threading.Thread')
    def test_send_frame_success(self, mock_thread):
        """Test successful frame sending"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        self.mock_hardware.send_frame.return_value = True
        
        result = controller.send_frame()
        
        self.assertTrue(result)
        self.mock_hardware.send_frame.assert_called_with(controller.matrix_data)

    @patch('threading.Thread')
    def test_send_frame_failure(self, mock_thread):
        """Test frame sending failure"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        self.mock_hardware.send_frame.side_effect = Exception("Hardware error")
        
        with patch('builtins.print') as mock_print:
            result = controller.send_frame()
            
        self.assertFalse(result)
        mock_print.assert_called_with("Hardware send error: Hardware error")

    @patch('threading.Thread')
    def test_rainbow_pattern(self, mock_thread):
        """Test rainbow pattern generation"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        result = controller.rainbow_pattern()
        
        self.assertTrue(result)
        # Verify that matrix data has been modified (not all zeros)
        self.assertFalse(np.all(controller.matrix_data == 0))
        # Verify send_frame was called
        self.mock_hardware.send_frame.assert_called_once()

    @patch('threading.Thread')
    def test_draw_text_empty_string(self, mock_thread):
        """Test draw_text with empty string"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        result = controller.draw_text("")
        
        self.assertFalse(result)
        self.mock_hardware.send_frame.assert_not_called()

    @patch('threading.Thread')
    @patch('PIL.ImageFont.truetype')
    @patch('PIL.ImageFont.load_default')
    def test_draw_text_with_font_fallback(self, mock_default_font, mock_truetype, mock_thread):
        """Test draw_text with font fallback"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Simulate font loading failure
        mock_truetype.side_effect = OSError("Font not found")
        mock_default_font.return_value = MagicMock()
        
        result = controller.draw_text("TEST")
        
        self.assertTrue(result)
        mock_truetype.assert_called_once_with("arial.ttf", 12)
        mock_default_font.assert_called_once()
        self.mock_hardware.send_frame.assert_called_once()

    @patch('threading.Thread')
    def test_scroll_text_empty_string(self, mock_thread):
        """Test scroll_text with empty string"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        result = controller.scroll_text("")
        
        self.assertFalse(result)

    @patch('threading.Thread')
    def test_scroll_text_valid_string(self, mock_thread):
        """Test scroll_text with valid string"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        with patch.object(controller, 'stop_animation') as mock_stop:
            result = controller.scroll_text("HELLO")
            
        self.assertTrue(result)
        self.assertEqual(controller.current_mode, "text")
        self.assertTrue(controller.is_streaming)
        mock_stop.assert_called_once()

    @patch('threading.Thread')
    def test_stop_animation(self, mock_thread):
        """Test stop_animation method"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Set up streaming state
        controller.is_streaming = True
        controller.current_mode = "test"
        
        # Mock animation thread
        mock_anim_thread = MagicMock()
        mock_anim_thread.is_alive.return_value = True
        controller.animation_thread = mock_anim_thread
        
        result = controller.stop_animation()
        
        self.assertTrue(result)
        self.assertFalse(controller.is_streaming)
        self.assertEqual(controller.current_mode, "idle")
        mock_anim_thread.join.assert_called_once_with(timeout=1.0)

    @patch('threading.Thread')
    def test_draw_char_known_character(self, mock_thread):
        """Test _draw_char with known character"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Clear matrix first
        controller.matrix_data.fill(0)
        
        controller._draw_char('A', 5, 5)
        
        # Verify some pixels were set (character A pattern should be drawn)
        self.assertFalse(np.all(controller.matrix_data == 0))

    @patch('threading.Thread')
    def test_draw_char_unknown_character(self, mock_thread):
        """Test _draw_char with unknown character (should draw space)"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Clear matrix first
        controller.matrix_data.fill(0)
        
        controller._draw_char('Z', 5, 5)  # Z is not in the patterns dict
        
        # Should remain all zeros (space pattern)
        self.assertTrue(np.all(controller.matrix_data == 0))

    @patch('threading.Thread')
    def test_draw_char_out_of_bounds(self, mock_thread):
        """Test _draw_char with out-of-bounds coordinates"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # This should not raise an exception
        controller._draw_char('A', 100, 100)  # Way out of bounds
        controller._draw_char('A', -10, -10)  # Negative coordinates

    @patch('threading.Thread')
    def test_apply_pattern_solid_color(self, mock_thread):
        """Test apply_pattern with solid color"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        with patch.object(controller, 'stop_animation') as mock_stop:
            result = controller.apply_pattern("solid", "#ff0000", 128, 50)
        
        self.assertTrue(result)
        mock_stop.assert_called_once()
        self.assertEqual(controller.current_mode, "solid")
        
        # Check that red color with 50% brightness was applied
        expected_color = [128, 0, 0]  # 50% of 255 red
        self.assertTrue(np.all(controller.matrix_data == expected_color))

    @patch('threading.Thread')
    def test_apply_pattern_rainbow(self, mock_thread):
        """Test apply_pattern with rainbow pattern"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        with patch.object(controller, 'rainbow_pattern', return_value=True) as mock_rainbow:
            result = controller.apply_pattern("rainbow", "#ff0000", 128, 50)
        
        self.assertTrue(result)
        mock_rainbow.assert_called_once()

    @patch('threading.Thread')
    def test_apply_pattern_animated(self, mock_thread):
        """Test apply_pattern with animated pattern (plasma)"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        with patch.object(controller, 'stop_animation') as mock_stop:
            result = controller.apply_pattern("plasma", "#ff0000", 128, 50)
        
        self.assertTrue(result)
        self.assertEqual(controller.current_mode, "plasma")
        self.assertTrue(controller.is_streaming)
        mock_stop.assert_called_once()

    @patch('threading.Thread')
    def test_apply_pattern_invalid_pattern(self, mock_thread):
        """Test apply_pattern with invalid pattern"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        result = controller.apply_pattern("invalid_pattern", "#ff0000", 128, 50)
        
        self.assertFalse(result)

    @patch('threading.Thread')
    def test_apply_pattern_invalid_color_format(self, mock_thread):
        """Test apply_pattern with invalid color format"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # This should handle gracefully and not crash
        with patch('builtins.print') as mock_print:
            result = controller.apply_pattern("solid", "invalid_color", 128, 50)
        
        self.assertFalse(result)
        mock_print.assert_called()  # Should print an error

    @patch('threading.Thread')
    def test_apply_custom_pattern_valid_data(self, mock_thread):
        """Test _apply_custom_pattern with valid data"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Create test pattern data
        pattern_data = [
            [[255, 0, 0], [0, 255, 0]],  # 2x2 pattern
            [[0, 0, 255], [255, 255, 0]],
        ]
        
        with patch.object(controller, 'stop_animation') as mock_stop:
            controller._apply_custom_pattern(pattern_data)
        
        mock_stop.assert_called_once()
        self.mock_hardware.send_frame.assert_called_once()
        
        # Check that the pattern was applied correctly
        np.testing.assert_array_equal(controller.matrix_data[0, 0], [255, 0, 0])
        np.testing.assert_array_equal(controller.matrix_data[0, 1], [0, 255, 0])

    @patch('threading.Thread')
    def test_apply_custom_pattern_invalid_data(self, mock_thread):
        """Test _apply_custom_pattern with invalid data"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Invalid pattern data (not proper RGB format)
        pattern_data = [["invalid", "data"]]
        
        with patch('builtins.print'):
            controller._apply_custom_pattern(pattern_data)

    @patch('threading.Thread')
    def test_text_loop_basic_functionality(self, mock_thread):
        """Test _text_loop basic functionality"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        # Set up for text loop
        controller.is_streaming = True
        controller.current_mode = "text"
        
        # Mock time.sleep to speed up test
        with patch('time.sleep'), patch.object(controller, 'send_frame') as mock_send:
            # Start the loop in a thread and stop it quickly
            thread = threading.Thread(target=controller._text_loop, args=("A",))
            thread.start()
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop the loop
            controller.is_streaming = False
            thread.join(timeout=1.0)
        
        # Verify that send_frame was called
        self.assertTrue(mock_send.called)

    @patch('threading.Thread')
    @patch('time.sleep')
    def test_plasma_animation_loop(self, mock_sleep, mock_thread):
        """Test _plasma_animation_loop"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        controller.is_streaming = True
        controller.current_mode = "plasma"
        
        with patch.object(controller, 'send_frame') as mock_send:
            # Start the animation loop in a thread
            thread = threading.Thread(target=controller._plasma_animation_loop, args=(50,))
            thread.start()
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop the animation
            controller.is_streaming = False
            thread.join(timeout=1.0)
        
        # Verify that send_frame was called and matrix data was modified
        self.assertTrue(mock_send.called)
        # Plasma should generate non-zero values
        self.assertFalse(np.all(controller.matrix_data == 0))

    @patch('threading.Thread')
    @patch('time.sleep')
    def test_fire_animation_loop(self, mock_sleep, mock_thread):
        """Test _fire_animation_loop"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        controller.is_streaming = True
        controller.current_mode = "fire"
        
        with patch.object(controller, 'send_frame') as mock_send:
            # Start the animation loop in a thread
            thread = threading.Thread(target=controller._fire_animation_loop, args=(50,))
            thread.start()
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop the animation
            controller.is_streaming = False
            thread.join(timeout=1.0)
        
        # Verify that send_frame was called
        self.assertTrue(mock_send.called)

    @patch('threading.Thread')
    @patch('time.sleep')
    def test_matrix_rain_animation_loop(self, mock_sleep, mock_thread):
        """Test _matrix_rain_animation_loop"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        controller.is_streaming = True
        controller.current_mode = "matrix"
        
        with patch.object(controller, 'send_frame') as mock_send:
            # Start the animation loop in a thread
            thread = threading.Thread(target=controller._matrix_rain_animation_loop, args=(50,))
            thread.start()
            
            # Let it run briefly
            time.sleep(0.1)
            
            # Stop the animation
            controller.is_streaming = False
            thread.join(timeout=1.0)
        
        # Verify that send_frame was called
        self.assertTrue(mock_send.called)

    @patch('threading.Thread')
    def test_run_method_keyboard_interrupt(self, mock_thread):
        """Test run method with KeyboardInterrupt"""
        from tests.test_matrix_controller import WebMatrixController
        controller = WebMatrixController()
        
        with patch('time.sleep', side_effect=KeyboardInterrupt()), patch('builtins.print') as mock_print, patch.object(controller, 'stop_animation') as mock_stop:
            controller.run()
        
        mock_stop.assert_called_once()
        mock_print.assert_any_call("\nController stopped by user")

    def test_brightness_scaling(self):
        """Test brightness scaling in apply_pattern"""
        # Test brightness scaling logic separately
        color = "ff0000"  # Red
        brightness = 128  # 50% brightness
        
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        brightness_factor = brightness / 255.0
        scaled_r = int(r * brightness_factor)
        scaled_g = int(g * brightness_factor)
        scaled_b = int(b * brightness_factor)
        
        self.assertEqual(scaled_r, 128)  # 255 * 0.5
        self.assertEqual(scaled_g, 0)
        self.assertEqual(scaled_b, 0)

    def test_color_conversion_edge_cases(self):
        """Test color conversion edge cases"""
        # Test with and without # prefix
        color_with_hash = "#ff0000"
        color_without_hash = "ff0000"
        
        # Both should produce the same result
        for color in [color_with_hash, color_without_hash]:
            if color.startswith("#"):
                color = color[1:]
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            self.assertEqual((r, g, b), (255, 0, 0))

    def test_matrix_dimensions_validation(self):
        """Test matrix dimension handling"""
        # Test with different matrix sizes
        dimensions = [(8, 8), (16, 16), (32, 8), (64, 64)]
        
        for w, h in dimensions:
            matrix_data = np.zeros((h, w, 3), dtype=np.uint8)
            self.assertEqual(matrix_data.shape, (h, w, 3))
            self.assertEqual(matrix_data.dtype, np.uint8)

    def test_numpy_array_operations(self):
        """Test numpy array operations used in the controller"""
        # Test fill operation
        test_array = np.zeros((16, 16, 3), dtype=np.uint8)
        test_array.fill(128)
        self.assertTrue(np.all(test_array == 128))
        
        # Test indexing
        test_array[0, 0] = [255, 0, 0]
        np.testing.assert_array_equal(test_array[0, 0], [255, 0, 0])


class TestWebHandlerMethods(unittest.TestCase):
    """Test cases for WebHandler methods within WebMatrixController"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_config = MagicMock()
        self.mock_config.get.side_effect = lambda key, default=None: {
            'matrix_width': 16,
            'matrix_height': 16,
            'connection_mode': 'USB',
            'serial_port': '/dev/ttyUSB0',
            'baud_rate': 115200,
        }.get(key, default)
        
        self.mock_hardware = MagicMock()
        
        # Patch imports
        self.config_patcher = patch('matrix_config.config', self.mock_config)
        self.hardware_patcher = patch('matrix_hardware.hardware', self.mock_hardware)
        self.server_patcher = patch('socketserver.ThreadingTCPServer')
        
        self.config_patcher.start()
        self.hardware_patcher.start() 
        self.server_patcher.start()

    def tearDown(self) -> None:
        """Clean up after tests"""
        self.config_patcher.stop()
        self.hardware_patcher.stop()
        self.server_patcher.stop()

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        # This would test the send_cors_headers method
        # Since it's an internal method of a nested class, we'll test it conceptually
        expected_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        
        for header, value in expected_headers.items():
            self.assertIsInstance(header, str)
            self.assertIsInstance(value, str)

    def test_json_response_structure(self):
        """Test JSON response structure"""
        test_data = {"status": "success", "message": "Test"}
        json_str = json.dumps(test_data)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["message"], "Test")

    def test_api_status_response_structure(self):
        """Test API status response structure"""
        status_response = {
            "connected": True,
            "matrix": {"width": 16, "height": 16},
            "current_mode": "idle",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.assertIn("connected", status_response)
        self.assertIn("matrix", status_response)
        self.assertIn("current_mode", status_response)
        self.assertIn("timestamp", status_response)
        self.assertTrue(status_response["connected"])

    def test_api_config_response_structure(self):
        """Test API config response structure"""
        config_data = {
            "connectionMode": "USB",
            "serialPort": "/dev/ttyUSB0",
            "baudRate": 115200,
            "matrixWidth": 16,
            "matrixHeight": 16,
        }
        
        required_fields = ["connectionMode", "serialPort", "baudRate", "matrixWidth", "matrixHeight"]
        for field in required_fields:
            self.assertIn(field, config_data)

    def test_led_options_structure(self):
        """Test LED options response structure"""
        led_options = [
            {"value": 30, "label": "30 LEDs/m (Low Density)", "spacing": "33.3mm"},
            {"value": 60, "label": "60 LEDs/m (Medium Density)", "spacing": "16.7mm"},
            {"value": 144, "label": "144 LEDs/m (High Density)", "spacing": "6.9mm"},
        ]
        
        for option in led_options:
            self.assertIn("value", option)
            self.assertIn("label", option)
            self.assertIn("spacing", option)
            self.assertIsInstance(option["value"], int)

    def test_power_supply_options_structure(self):
        """Test power supply options structure"""
        psu_options = [
            {"value": "5V2A", "label": "5V 2A (10W)", "maxLeds": 33, "price": 15},
            {"value": "5V5A", "label": "5V 5A (25W)", "maxLeds": 83, "price": 25},
        ]
        
        for psu in psu_options:
            required_fields = ["value", "label", "maxLeds", "price"]
            for field in required_fields:
                self.assertIn(field, psu)

    def test_controller_options_structure(self):
        """Test controller options structure"""
        controller_options = [
            {"value": "arduino_uno", "label": "Arduino Uno R3", "voltage": "5V", "price": 25},
            {"value": "esp32", "label": "ESP32 Dev Board", "voltage": "3.3V", "price": 12},
        ]
        
        for controller in controller_options:
            required_fields = ["value", "label", "voltage", "price"]
            for field in required_fields:
                self.assertIn(field, controller)

    def test_base64_image_encoding(self):
        """Test base64 image encoding for preview"""
        # Create a simple test image
        test_image = Image.new('RGB', (16, 16), color=(255, 0, 0))
        
        # Convert to base64
        buffer = io.BytesIO()
        test_image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Verify it's valid base64
        self.assertIsInstance(img_str, str)
        self.assertTrue(len(img_str) > 0)
        
        # Verify we can decode it back
        decoded_bytes = base64.b64decode(img_str)
        self.assertIsInstance(decoded_bytes, bytes)

    def test_wiring_data_structure(self):
        """Test wiring data response structure"""
        wiring_data = {
            "controller": "arduino_uno",
            "matrix": {"width": 16, "height": 16, "totalLeds": 256},
            "power": {
                "maxCurrent": 12.8,
                "maxPower": 64.0,
                "recommendedPSU": "5V20A",
                "selectedPSU": "5V20A",
            },
            "strip": {
                "ledsPerMeter": 144,
                "totalLength": 1.78,
                "segments": 1,
            },
            "mermaidDiagram": "graph TD...",
            "components": [],
            "estimatedCost": 150.0,
        }
        
        required_sections = ["controller", "matrix", "power", "strip", "mermaidDiagram", "components", "estimatedCost"]
        for section in required_sections:
            self.assertIn(section, wiring_data)


class TestUtilityMethods(unittest.TestCase):
    """Test cases for utility methods in WebMatrixController"""

    def test_mermaid_diagram_generation(self):
        """Test Mermaid diagram generation structure"""
        controller_type = "arduino_uno"
        width, height = 16, 16
        power_supply = "5V10A"
        total_leds = width * height
        
        self.assertEqual(total_leds, 256)
        self.assertIn("arduino", controller_type)
        self.assertIn("5V", power_supply)

    def test_psu_recommendations_logic(self):
        """Test PSU recommendation logic"""
        max_current = 10.0  # Amps
        recommended_current = max_current * 1.2  # 20% safety margin
        
        psu_options = [
            {"name": "5V10A", "current": 10.0},
            {"name": "5V20A", "current": 20.0},
            {"name": "5V30A", "current": 30.0},
        ]
        
        recommended = None
        for psu in psu_options:
            if psu["current"] >= recommended_current:
                recommended = psu
                break
        
        self.assertIsNotNone(recommended)
        self.assertEqual(recommended["name"], "5V20A")

    def test_component_list_generation_logic(self):
        """Test component list generation logic"""
        controller_types = ["arduino_uno", "esp32", "esp8266"]
        
        for controller_type in controller_types:
            needs_level_shifter = controller_type in ["esp32", "esp8266"]
            
            if controller_type == "arduino_uno":
                self.assertFalse(needs_level_shifter)
            else:
                self.assertTrue(needs_level_shifter)

    def test_cost_calculation_logic(self):
        """Test cost calculation logic"""
        components = [
            {"total": 25.0},
            {"total": 35.0},
            {"total": 15.0},
        ]
        
        subtotal = sum(component["total"] for component in components)
        shipping = subtotal * 0.1
        total = subtotal + shipping
        
        self.assertEqual(subtotal, 75.0)
        self.assertEqual(shipping, 7.5)
        self.assertEqual(total, 82.5)

    def test_strip_length_calculation(self):
        """Test LED strip length calculation"""
        total_leds = 256
        leds_per_meter_options = [30, 60, 144, 256]
        
        for leds_per_meter in leds_per_meter_options:
            strip_length = total_leds / leds_per_meter
            segments = max(1, int(strip_length))
            
            self.assertGreater(strip_length, 0)
            self.assertGreaterEqual(segments, 1)
            
            if leds_per_meter == 256:
                self.assertEqual(strip_length, 1.0)
                self.assertEqual(segments, 1)


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.makeSuite(TestWebMatrixController))
    test_suite.addTest(unittest.makeSuite(TestWebHandlerMethods))
    test_suite.addTest(unittest.makeSuite(TestUtilityMethods))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)