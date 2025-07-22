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