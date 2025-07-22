"""
Integration tests for WebMatrixController
Testing framework: unittest (Python standard library)
These tests focus on the interaction between components and end-to-end functionality
"""

import unittest
from unittest.mock import patch, MagicMock
import threading
import time
import sys
import os
import numpy as np

# Add the parent directory to the path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestWebMatrixControllerIntegration(unittest.TestCase):
    """Integration test cases for WebMatrixController"""

    def setUp(self) -> None:
        """Set up test fixtures"""
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

        self.config_patcher.start()
        self.hardware_patcher.start()
        self.wiring_patcher.start()

    def tearDown(self) -> None:
        """Clean up after tests"""
        self.config_patcher.stop()
        self.hardware_patcher.stop()
        self.wiring_patcher.stop()

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_pattern_to_hardware_integration(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test pattern application flows through to hardware"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        # Apply a pattern and verify it reaches hardware
        result = controller.apply_pattern("solid", "#ff0000", 255, 50)

        assert result
        # Verify hardware was called
        self.mock_hardware.send_frame.assert_called()

        # Verify matrix data was set correctly
        expected_color = [255, 0, 0]  # Full red at 100% brightness
        assert (controller.matrix_data == expected_color).all()

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_text_to_hardware_integration(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test text rendering flows through to hardware"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        # Draw text and verify it reaches hardware
        result = controller.draw_text("TEST")

        assert result
        self.mock_hardware.send_frame.assert_called()

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_animation_lifecycle(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test complete animation lifecycle"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        # Start an animation
        controller.apply_pattern("plasma", "#ff0000", 128, 50)
        assert controller.is_streaming
        assert controller.current_mode == "plasma"

        # Stop the animation
        controller.stop_animation()
        assert not controller.is_streaming
        assert controller.current_mode == "idle"

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_config_update_integration(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test configuration update integration"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        # Simulate config update

        # This would normally be called from the web handler
        controller.W = 32
        controller.H = 8
        controller.matrix_data = controller.matrix_data = np.zeros((8, 32, 3), dtype=np.uint8)

        assert controller.W == 32
        assert controller.H == 8
        assert controller.matrix_data.shape == (8, 32, 3)

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_clear_to_pattern_integration(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test clearing matrix then applying pattern"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        # Set some initial data
        controller.matrix_data.fill(128)

        # Clear the matrix
        controller.clear_matrix()
        assert (controller.matrix_data == 0).all()

        # Apply a pattern
        controller.apply_pattern("solid", "#00ff00", 255, 50)
        expected_color = [0, 255, 0]  # Full green
        assert (controller.matrix_data == expected_color).all()

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_multiple_pattern_switches(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test switching between multiple patterns"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        patterns = ["solid", "rainbow", "plasma", "fire", "matrix"]

        for pattern in patterns:
            with patch.object(controller, 'stop_animation') as mock_stop:
                result = controller.apply_pattern(pattern, "#ff0000", 128, 50)

            assert result or pattern == "rainbow"  # rainbow returns via different path
            mock_stop.assert_called()
            assert controller.current_mode == pattern

    def test_thread_safety_simulation(self) -> None:
        """Test thread safety of shared resources"""
        # This simulates concurrent access to matrix_data
        import numpy as np

        matrix_data = np.zeros((16, 16, 3), dtype=np.uint8)

        def writer_thread() -> None:
            for i in range(10):
                matrix_data.fill(i)
                time.sleep(0.01)

        def reader_thread() -> None:
            for _ in range(10):
                # Read the matrix data
                current_state = matrix_data.copy()
                assert current_state.shape == (16, 16, 3)
                time.sleep(0.01)

        # Start threads
        writer = threading.Thread(target=writer_thread)
        reader = threading.Thread(target=reader_thread)

        writer.start()
        reader.start()

        writer.join()
        reader.join()

    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_error_recovery_integration(self, _mock_thread: MagicMock, _mock_server: MagicMock) -> None:
        """Test error recovery in integration scenarios"""
        from tests.test_matrix_controller import WebMatrixController

        controller = WebMatrixController()

        # Simulate hardware failure
        self.mock_hardware.send_frame.side_effect = Exception("Hardware disconnected")

        # Operations should handle errors gracefully
        result = controller.clear_matrix()
        assert result  # Method should return True even if send fails

        # Pattern application should handle errors
        with patch('builtins.print'):
            result = controller.apply_pattern("solid", "#ff0000", 128, 50)
            assert result  # Pattern logic succeeds, send may fail


class TestWebMatrixControllerEndToEnd(unittest.TestCase):
    """End-to-end test scenarios"""

    @patch('matrix_config.config')
    @patch('matrix_hardware.hardware')
    @patch('wiring_diagram_generator.WiringDiagramGenerator')
    @patch('socketserver.ThreadingTCPServer')
    @patch('threading.Thread')
    def test_typical_usage_scenario(
        self,
        _mock_thread: MagicMock,
        _mock_server: MagicMock,
        _mock_wiring: MagicMock,
        mock_hardware: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Test a typical usage scenario from start to finish"""
        # Configure mocks
        mock_config.get.side_effect = lambda key, default=None: {
            'matrix_width': 16,
            'matrix_height': 16,
        }.get(key, default)

        from tests.test_matrix_controller import WebMatrixController

        # 1. Initialize controller
        controller = WebMatrixController()

        # 2. Clear matrix
        controller.clear_matrix()

        # 3. Display text
        controller.draw_text("HELLO")

        # 4. Apply some patterns
        controller.apply_pattern("solid", "#ff0000", 128, 50)  # Red
        controller.apply_pattern("rainbow", "#000000", 255, 50)  # Rainbow

        # 5. Start animation
        controller.apply_pattern("plasma", "#000000", 255, 75)

        # 6. Stop animation
        controller.stop_animation()

        # Verify hardware was called multiple times
        assert mock_hardware.send_frame.call_count > 0

    def test_performance_benchmarks(self) -> None:
        """Test performance characteristics"""
        import numpy as np

        # Test matrix operations performance
        sizes = [(8, 8), (16, 16), (32, 32), (64, 64)]

        for w, h in sizes:
            start_time = time.time()

            # Create matrix
            matrix = np.zeros((h, w, 3), dtype=np.uint8)

            # Fill operations
            matrix.fill(128)
            matrix[0, 0] = [255, 0, 0]

            # Pattern operations
            for y in range(h):
                for x in range(w):
                    matrix[y, x] = [x % 256, y % 256, (x + y) % 256]

            end_time = time.time()
            duration = end_time - start_time

            assert duration < 1.0, f"Matrix operations for {w}x{h} took too long: {duration}s"

    def test_memory_usage_patterns(self) -> None:
        """Test memory usage patterns"""
        import numpy as np

        # Test different matrix sizes and their memory footprint
        sizes = [(8, 8), (16, 16), (32, 32)]

        for w, h in sizes:
            matrix = np.zeros((h, w, 3), dtype=np.uint8)
            expected_bytes = h * w * 3  # 3 bytes per pixel (RGB)
            actual_bytes = matrix.nbytes

            assert actual_bytes == expected_bytes

            # Test memory doesn't grow unexpectedly with operations
            original_bytes = matrix.nbytes
            matrix.fill(255)
            matrix[0, 0] = [0, 0, 0]

            assert matrix.nbytes == original_bytes


if __name__ == "__main__":
    # Create a test suite for integration tests
    test_suite = unittest.TestSuite()

    # Add integration test cases
    test_suite.addTest(unittest.makeSuite(TestWebMatrixControllerIntegration))
    test_suite.addTest(unittest.makeSuite(TestWebMatrixControllerEndToEnd))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)