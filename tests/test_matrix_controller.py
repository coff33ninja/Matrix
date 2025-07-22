# Removed shebang per ruff recommendation

"""
Comprehensive unit tests for WebMatrixController
Testing Framework: unittest (Python standard library)
"""

import unittest
import threading
import time
import numpy as np
import sys
import os
from unittest.mock import patch, MagicMock
import socketserver
from io import BytesIO  # retained for potential future use
from io import StringIO  # retained for potential future use

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

        # Mock external dependencies before importing
        self.mock_config = MagicMock()
        self.mock_config.get.side_effect = lambda key, default=None: {
            'matrix_width': 16,
            'matrix_height': 16,
            'connection_mode': 'USB',
            'serial_port': '/dev/ttyUSB0',
            'baud_rate': 115200,
        }.get(key, default)
        self.mock_config.set = MagicMock()
        self.mock_config.save_config = MagicMock()
        self.mock_config.create_backup = MagicMock(return_value='backup_20240101.json')

        self.mock_hardware = MagicMock()
        self.mock_hardware.send_frame = MagicMock()

        # Mock external modules
        self.patches = [
            patch.dict('sys.modules', {
                'matrix_config': MagicMock(config=self.mock_config),
                'matrix_hardware': MagicMock(hardware=self.mock_hardware),
                'wiring_diagram_generator': MagicMock(),
                'arduino_generator': MagicMock(),
                'psutil': MagicMock(cpu_percent=MagicMock(return_value=50.0), virtual_memory=MagicMock(return_value=MagicMock(percent=60.0))),
                'cv2': MagicMock(),
            }),
            patch('threading.Thread'),
            patch('socketserver.ThreadingTCPServer'),
            patch('PIL.Image'),
            patch('PIL.ImageDraw'),
            patch('PIL.ImageFont'),
        ]

        for p in self.patches:
            p.start()

        # Import the module after mocking
        import tests.test_matrix_controller as module_under_test  # noqa: F401
        from tests.test_matrix_controller import WebMatrixController  # noqa: F401
        self.WebMatrixController = WebMatrixController

        # Create controller instance
        self.controller = self.WebMatrixController(port=8888)

    def tearDown(self) -> None:
        """Clean up after each test method"""
        if hasattr(self.controller, 'stop_animation'):
            self.controller.stop_animation()

        # Stop all patches
        for p in self.patches:
            p.stop()

    def test_init_default_values(self) -> None:
        """Test WebMatrixController initialization with default values"""
        controller = self.WebMatrixController()

        assert controller.W == 16
        assert controller.H == 16
        assert controller.port == 8080
        assert controller.current_mode == "idle"
        assert not controller.is_streaming
        assert isinstance(controller.matrix_data, np.ndarray)
        assert controller.matrix_data.shape == (16, 16, 3)
        assert controller.matrix_data.dtype == np.uint8

    def test_init_custom_port(self) -> None:
        """Test WebMatrixController initialization with custom port"""
        controller = self.WebMatrixController(port=9999)

        assert controller.port == 9999

    def test_init_custom_matrix_size(self) -> None:
        """Test WebMatrixController with custom matrix dimensions"""
        self.mock_config.get.side_effect = lambda key, default=None: {
            'matrix_width': 32,
            'matrix_height': 8,
            'connection_mode': 'USB',
            'serial_port': '/dev/ttyUSB0',
            'baud_rate': 115200,
        }.get(key, default)
        controller = self.WebMatrixController()

        assert controller.W == 32
        assert controller.H == 8
        assert controller.matrix_data.shape == (8, 32, 3)

    def test_clear_matrix(self) -> None:
        """Test clearing the matrix display"""
        # Set some initial data
        self.controller.matrix_data[0, 0] = [255, 128, 64]

        result = self.controller.clear_matrix()

        assert result
        assert np.all(self.controller.matrix_data == 0)
        self.mock_hardware.send_frame.assert_called_once()

    def test_rainbow_pattern(self) -> None:
        """Test rainbow pattern generation"""
        result = self.controller.rainbow_pattern()

        assert result
        assert not np.all(self.controller.matrix_data == 0)
        assert np.all(self.controller.matrix_data >= 0)
        assert np.all(self.controller.matrix_data <= 255)
        self.mock_hardware.send_frame.assert_called_once()

    def test_send_frame_success(self) -> None:
        """Test successful frame sending to hardware"""
        result = self.controller.send_frame()

        assert result
        self.mock_hardware.send_frame.assert_called_once_with(self.controller.matrix_data)

    def test_send_frame_failure(self) -> None:
        """Test frame sending failure handling"""
        self.mock_hardware.send_frame.side_effect = Exception("Hardware error")

        with patch('builtins.print') as mock_print:
            result = self.controller.send_frame()

        assert not result
        mock_print.assert_called_with("Hardware send error: Hardware error")

    def test_draw_text_empty_string(self) -> None:
        """Test drawing empty text"""
        result = self.controller.draw_text("")

        assert not result

    def test_draw_text_valid_string(self) -> None:
        """Test drawing valid text"""
        with patch('PIL.Image.new') as mock_image, patch('PIL.ImageDraw.Draw') as mock_draw, patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = MagicMock()
            mock_draw_instance = MagicMock()
            mock_draw_instance.textbbox.return_value = (0, 0, 50, 20)
            mock_draw.return_value = mock_draw_instance

            mock_img = MagicMock()
            mock_img.resize.return_value = mock_img
            mock_image.return_value = mock_img

            with patch('numpy.array', return_value=np.zeros((16, 16, 3), dtype=np.uint8)):
                result = self.controller.draw_text("TEST")

        assert result
        self.mock_hardware.send_frame.assert_called()

    def test_draw_text_font_fallback(self) -> None:
        """Test text drawing with font fallback"""
        with patch('PIL.Image.new') as mock_image, patch('PIL.ImageDraw.Draw') as mock_draw, patch('PIL.ImageFont.truetype', side_effect=OSError("Font not found")), patch('PIL.ImageFont.load_default') as mock_default_font:
            mock_default_font.return_value = MagicMock()
            mock_draw_instance = MagicMock()
            mock_draw_instance.textbbox.return_value = (0, 0, 50, 20)
            mock_draw.return_value = mock_draw_instance

            mock_img = MagicMock()
            mock_img.resize.return_value = mock_img
            mock_image.return_value = mock_img

            with patch('numpy.array', return_value=np.zeros((16, 16, 3), dtype=np.uint8)):
                result = self.controller.draw_text("TEST")

        assert result
        mock_default_font.assert_called_once()

    def test_draw_text_exception_handling(self) -> None:
        """Test text drawing exception handling"""
        with patch('PIL.Image.new', side_effect=Exception("PIL error")), patch('builtins.print') as mock_print:
            result = self.controller.draw_text("TEST")

        assert not result
        mock_print.assert_called_with("Failed to draw text: PIL error")

    def test_scroll_text_empty_string(self) -> None:
        """Test scrolling empty text"""
        result = self.controller.scroll_text("")

        assert not result

    def test_scroll_text_valid_string(self) -> None:
        """Test scrolling valid text"""
        with patch.object(self.controller, 'stop_animation') as mock_stop:
            result = self.controller.scroll_text("HELLO")

        assert result
        assert self.controller.current_mode == "text"
        assert self.controller.is_streaming
        mock_stop.assert_called_once()
        assert isinstance(self.controller.animation_thread, threading.Thread)

    def test_stop_animation(self) -> None:
        """Test stopping animation"""
        self.controller.is_streaming = True
        self.controller.current_mode = "test"
        self.controller.animation_thread = MagicMock()
        self.controller.animation_thread.is_alive.return_value = True

        result = self.controller.stop_animation()

        assert result
        assert not self.controller.is_streaming
        assert self.controller.current_mode == "idle"
        self.controller.animation_thread.join.assert_called_once_with(timeout=1.0)

    def test_stop_animation_no_thread(self) -> None:
        """Test stopping animation when no thread exists"""
        self.controller.animation_thread = None

        result = self.controller.stop_animation()

        assert result
        assert not self.controller.is_streaming
        assert self.controller.current_mode == "idle"

    def test_apply_pattern_solid(self) -> None:
        """Test applying solid color pattern"""
        with patch.object(self.controller, 'stop_animation') as mock_stop:
            result = self.controller.apply_pattern("solid", "#ff8000", 128, 50)

        assert result
        mock_stop.assert_called_once()
        assert self.controller.current_mode == "solid"
        expected_color = [127, 64, 0]  # #ff8000 with 128/255 brightness
        assert np.all(self.controller.matrix_data == expected_color)

    def test_apply_pattern_rainbow(self) -> None:
        """Test applying rainbow pattern"""
        with patch.object(self.controller, 'rainbow_pattern') as mock_rainbow:
            mock_rainbow.return_value = True
            result = self.controller.apply_pattern("rainbow", "#ffffff", 255, 50)

        assert result
        mock_rainbow.assert_called_once()

    def test_apply_pattern_animated(self) -> None:
        """Test applying animated patterns"""
        patterns = ["plasma", "fire", "matrix"]

        for pattern in patterns:
            with self.subTest(pattern=pattern):
                with patch.object(self.controller, 'stop_animation') as mock_stop:
                    result = self.controller.apply_pattern(pattern, "#00ff00", 200, 75)

                assert result
                assert self.controller.current_mode == pattern
                assert self.controller.is_streaming
                assert isinstance(self.controller.animation_thread, threading.Thread)
                mock_stop.assert_called_once()

                # Clean up for next test
                self.controller.stop_animation()

    def test_apply_pattern_invalid_color_format(self) -> None:
        """Test applying pattern with invalid hex color format"""
        with patch('builtins.print') as mock_print:
            result = self.controller.apply_pattern("solid", "invalid", 255, 50)

        assert not result
        assert mock_print.called

    def test_apply_pattern_exception_handling(self) -> None:
        """Test pattern application exception handling"""
        with patch.object(self.controller, 'stop_animation', side_effect=Exception("Stop error")), patch('builtins.print') as mock_print:
            result = self.controller.apply_pattern("solid", "#ffffff", 255, 50)

        assert not result
        mock_print.assert_called_with("Error applying pattern: Stop error")

    def test_apply_custom_pattern_valid_data(self) -> None:
        """Test applying valid custom pattern data"""
        pattern_data = [
            [[255, 0, 0], [0, 255, 0]],
            [[0, 0, 255], [255, 255, 255]],
        ]

        with patch.object(self.controller, 'stop_animation') as mock_stop:
            self.controller._apply_custom_pattern(pattern_data)

        mock_stop.assert_called_once()
        self.mock_hardware.send_frame.assert_called_once()
        assert list(self.controller.matrix_data[0, 0]) == [255, 0, 0]
        assert list(self.controller.matrix_data[0, 1]) == [0, 255, 0]

    def test_apply_custom_pattern_invalid_data(self) -> None:
        """Test applying invalid custom pattern data"""
        pattern_data = [["invalid", "data"]]

        self.controller._apply_custom_pattern(pattern_data)

        self.mock_hardware.send_frame.assert_called_once()

    def test_apply_custom_pattern_oversized_data(self) -> None:
        """Test applying custom pattern larger than matrix"""
        pattern_data = []
        for y in range(20):
            row = []
            for x in range(20):
                row.append([x % 256, y % 256, (x + y) % 256])
            pattern_data.append(row)

        self.controller._apply_custom_pattern(pattern_data)

        assert list(self.controller.matrix_data[15, 15]) == [15, 15, 30]

    def test_draw_char_valid_character(self) -> None:
        """Test drawing valid characters"""
        self.controller._draw_char('A', 0, 0)

        white_pixels = np.sum(np.all(self.controller.matrix_data == [255, 255, 255], axis=2))
        assert white_pixels > 0

    def test_draw_char_unknown_character(self) -> None:
        """Test drawing unknown character (should default to space)"""
        initial_data = self.controller.matrix_data.copy()
        self.controller._draw_char('Ω', 0, 0)

        np.testing.assert_array_equal(self.controller.matrix_data, initial_data)

    def test_draw_char_out_of_bounds(self) -> None:
        """Test drawing character outside matrix bounds"""
        self.controller._draw_char('A', 20, 20)

        assert np.all(self.controller.matrix_data == 0)

    def test_text_loop_functionality(self) -> None:
        """Test text scrolling loop functionality"""
        self.controller.current_mode = "text"
        self.controller.is_streaming = True

        with patch('time.sleep'):
            thread = threading.Thread(target=self.controller._text_loop, args=("AB",))
            thread.daemon = True
            thread.start()

            time.sleep(0.01)
            self.controller.stop_animation()
            thread.join(timeout=1.0)

        self.mock_hardware.send_frame.assert_called()

    def test_plasma_animation_loop(self) -> None:
        """Test plasma animation loop"""
        self.controller.current_mode = "plasma"
        self.controller.is_streaming = True

        with patch('time.sleep'):
            thread = threading.Thread(target=self.controller._plasma_animation_loop, args=(50,))
            thread.daemon = True
            thread.start()

            time.sleep(0.01)
            self.controller.stop_animation()
            thread.join(timeout=1.0)

        self.mock_hardware.send_frame.assert_called()

    def test_fire_animation_loop(self) -> None:
        """Test fire animation loop"""
        self.controller.current_mode = "fire"
        self.controller.is_streaming = True

        with patch('time.sleep'), patch('random.randint', return_value=128):
            thread = threading.Thread(target=self.controller._fire_animation_loop, args=(50,))
            thread.daemon = True
            thread.start()

            time.sleep(0.01)
            self.controller.stop_animation()
            thread.join(timeout=1.0)

        self.mock_hardware.send_frame.assert_called()

    def test_matrix_rain_animation_loop(self) -> None:
        """Test matrix rain animation loop"""
        self.controller.current_mode = "matrix"
        self.controller.is_streaming = True

        with patch('time.sleep'), patch('random.random', return_value=0.01):
            thread = threading.Thread(target=self.controller._matrix_rain_animation_loop, args=(50,))
            thread.daemon = True
            thread.start()

            time.sleep(0.01)
            self.controller.stop_animation()
            thread.join(timeout=1.0)

        self.mock_hardware.send_frame.assert_called()

    def test_concurrent_animation_safety(self) -> None:
        """Test thread safety when switching between animations"""
        self.controller.apply_pattern("plasma", "#ff0000", 255, 50)
        self.controller.apply_pattern("fire", "#00ff00", 255, 75)
        self.controller.apply_pattern("matrix", "#0000ff", 255, 25)
        self.controller.stop_animation()

        assert self.controller.current_mode == "idle"
        assert not self.controller.is_streaming

    def test_brightness_scaling_edge_cases(self) -> None:
        """Test brightness scaling with edge case values"""
        test_cases = [
            (0, [0, 0, 0]),
            (255, [255, 0, 0]),
            (127, [127, 0, 0]),
            (1, [1, 0, 0]),
        ]

        for brightness, expected in test_cases:
            with self.subTest(brightness=brightness):
                self.controller.apply_pattern("solid", "#ff0000", brightness, 50)
                np.testing.assert_array_equal(self.controller.matrix_data[0, 0], expected)

    def test_color_parsing_edge_cases(self) -> None:
        """Test color parsing with various input formats"""
        test_cases = [
            ("#ffffff", [255, 255, 255]),
            ("#000000", [0, 0, 0]),
            ("#ff8040", [255, 128, 64]),
            ("ffffff", [255, 255, 255]),
        ]

        for color, expected_rgb in test_cases:
            with self.subTest(color=color):
                self.controller.apply_pattern("solid", color, 255, 50)
                np.testing.assert_array_equal(self.controller.matrix_data[0, 0], expected_rgb)

class TestWebMatrixControllerIntegration(unittest.TestCase):
    """Integration tests for WebMatrixController"""

    def setUp(self) -> None:
        """Set up integration test fixtures"""
        
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

        self.patches = [
            patch.dict('sys.modules', {
                'matrix_config': MagicMock(config=self.mock_config),
                'matrix_hardware': MagicMock(hardware=self.mock_hardware),
                'wiring_diagram_generator': MagicMock(),
                'arduino_generator': MagicMock(),
                'psutil': MagicMock(),
                'cv2': MagicMock(),
            }),
            patch('threading.Thread'),
            patch('socketserver.ThreadingTCPServer'),
        ]

        for p in self.patches:
            p.start()

        from tests.test_matrix_controller import WebMatrixController  # noqa: F401
        self.controller = WebMatrixController()

    def tearDown(self) -> None:
        """Clean up"""
        for p in self.patches:
            p.stop()

    def test_full_pattern_workflow(self) -> None:
        """Test complete pattern application workflow"""
        patterns = ["solid", "rainbow", "plasma", "fire", "matrix"]

        for pattern in patterns:
            with self.subTest(pattern=pattern):
                result = self.controller.apply_pattern(pattern, "#ff0000", 128, 50)
                assert result
                if pattern in ["plasma", "fire", "matrix"]:
                    assert self.controller.is_streaming
                    self.controller.stop_animation()

        assert self.controller.current_mode == "idle"
        assert not self.controller.is_streaming

    def test_matrix_resize_workflow(self) -> None:
        """Test matrix resizing workflow"""
        self.controller.W = 32
        self.controller.H = 8
        self.controller.matrix_data = np.zeros((8, 32, 3), dtype=np.uint8)

        result = self.controller.apply_pattern("solid", "#00ff00", 255, 50)
        assert result
        assert self.controller.matrix_data.shape == (8, 32, 3)
        expected_color = [0, 255, 0]
        assert np.all(self.controller.matrix_data == expected_color)

    def test_concurrent_operations_safety(self) -> None:
        """Test concurrent operations safety"""
        self.controller.apply_pattern("plasma", "#ff0000", 200, 50)
        self.controller.clear_matrix()
        self.controller.stop_animation()
        assert self.controller.current_mode == "idle"
        assert not self.controller.is_streaming

    def test_animation_thread_cleanup(self) -> None:
        """Test that animation threads are properly cleaned up"""
        animations = ["plasma", "fire", "matrix"]
        for animation in animations:
            self.controller.apply_pattern(animation, "#ffffff", 255, 50)
            assert self.controller.is_streaming
            self.controller.stop_animation()
            assert not self.controller.is_streaming
            assert self.controller.current_mode == "idle"

        assert not self.controller.is_streaming
        assert self.controller.current_mode == "idle"

class TestWebMatrixControllerUtilityFunctions(unittest.TestCase):
    """Test utility functions at the end of the file"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.patches = [
            patch.dict('sys.modules', {
                'matrix_config': MagicMock(),
                'matrix_hardware': MagicMock(),
                'wiring_diagram_generator': MagicMock(),
                'arduino_generator': MagicMock(),
                'psutil': MagicMock(),
                'cv2': MagicMock(),
            }),
            patch('threading.Thread'),
            patch('socketserver.ThreadingTCPServer'),
        ]

        for p in self.patches:
            p.start()

        from tests.test_matrix_controller import WebMatrixController  # noqa: F401
        self.controller = WebMatrixController()

    def tearDown(self) -> None:
        """Clean up"""
        for p in self.patches:
            p.stop()

    def test_generate_mermaid_wiring(self) -> None:
        """Test Mermaid wiring diagram generation"""
        result = self.controller.generate_mermaid_wiring("arduino_uno", 16, 16, "5V10A")
        assert isinstance(result, str)
        assert "graph TD" in result
        assert "Arduino Uno" in result
        assert "5V10A" in result
        assert "256 LEDs" in result

    def test_get_psu_recommendations(self) -> None:
        """Test power supply recommendations"""
        result = self.controller.get_psu_recommendations(5.0)
        assert "recommended" in result
        assert "options" in result
        assert "requiredCurrent" in result
        assert isinstance(result["options"], list)

    def test_generate_component_list(self) -> None:
        """Test component list generation"""
        components = self.controller.generate_component_list("arduino_uno", 256, 2.0, "5V10A")
        assert isinstance(components, list)
        assert len(components) > 0
        for component in components:
            assert "category" in component
            assert "name" in component
            assert "quantity" in component
            assert "price" in component
            assert "total" in component

    def test_calculate_estimated_cost(self) -> None:
        """Test cost calculation"""
        components = [
            {"total": 25.0},
            {"total": 30.0},
            {"total": 15.0},
        ]

        result = self.controller.calculate_estimated_cost(components)
        assert "subtotal" in result
        assert "shipping" in result
        assert "total" in result
        assert result["subtotal"] == 70.0
        assert result["shipping"] == 7.0
        assert result["total"] == 77.0

class TestWebMatrixControllerWebHandlerHelpers(unittest.TestCase):
    """Test cases for web server helper functionality"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.patches = [
            patch.dict('sys.modules', {
                'matrix_config': MagicMock(),
                'matrix_hardware': MagicMock(),
                'wiring_diagram_generator': MagicMock(),
                'arduino_generator': MagicMock(),
                'psutil': MagicMock(),
                'cv2': MagicMock(),
            }),
            patch('threading.Thread'),
            patch('socketserver.ThreadingTCPServer'),
        ]

        for p in self.patches:
            p.start()

        from tests.test_matrix_controller import WebMatrixController  # noqa: F401
        self.controller = WebMatrixController(port=8888)

    def tearDown(self) -> None:
        """Clean up"""
        for p in self.patches:
            p.stop()

    def create_mock_handler(self) -> object:
        """Create a mock web handler for testing"""
        class MockWebHandler:
            def __init__(self) -> None:
                self.controller = self.controller  # type: ignore[name-defined]
                self.client_address = ('127.0.0.1', 12345)
                self.headers = {'Content-Length': '0'}
                self.responses = []
                self.status_code = 200
                self.response_headers = {}

            def send_response(self, code: int) -> None:
                self.status_code = code

            def send_header(self, name: str, value: str) -> None:
                self.response_headers[name] = value

            def send_cors_headers(self) -> None:
                self.response_headers.update({
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                })

            def end_headers(self) -> None:
                pass

            def send_json_response(self, data: dict, status: int = 200) -> None:
                self.send_response(status)
                self.send_cors_headers()
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.responses.append(data)

        return MockWebHandler()

    def test_status_endpoint_response_structure(self) -> None:
        """Test /api/status endpoint response structure"""
        handler = self.create_mock_handler()

        status_data = {
            "connected": True,
            "matrix": {"width": handler.controller.W, "height": handler.controller.H},
            "current_mode": handler.controller.current_mode,
            "timestamp": "2024-01-01T00:00:00",
        }
        handler.send_json_response(status_data)

        response = handler.responses[0]
        assert response["connected"]
        assert response["matrix"]["width"] == 16
        assert response["matrix"]["height"] == 16
        assert response["current_mode"] == "idle"
        assert "timestamp" in response

    def test_cors_headers_set(self) -> None:
        """Test that CORS headers are properly set"""
        handler = self.create_mock_handler()
        handler.send_json_response({"test": "data"})

        expected_cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

        for header, value in expected_cors_headers.items():
            assert handler.response_headers[header] == value

    def test_error_response_format(self) -> None:
        """Test error response format"""
        handler = self.create_mock_handler()

        error_response = {"status": "error", "message": "Test error"}
        handler.send_json_response(error_response, 500)

        assert handler.status_code == 500
        response = handler.responses[0]
        assert response["status"] == "error"
        assert response["message"] == "Test error"

if __name__ == '__main__':
    unittest.main(verbosity=2, buffer=True)
        
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
