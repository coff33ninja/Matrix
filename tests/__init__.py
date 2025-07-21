#!/usr/bin/env python3
"""
LED Matrix Project Test Suite
Comprehensive tests for all modules and functionality
"""

__version__ = "1.0.0"
__author__ = "LED Matrix Project"

# Test configuration
TEST_CONFIG = {
    "default_matrix_width": 16,
    "default_matrix_height": 16,
    "test_brightness": 128,
    "test_data_pin": 6,
    "mock_serial_port": "COM_TEST",
    "test_timeout": 5.0
}

# Test utilities
def get_test_config():
    """Get test configuration dictionary"""
    return TEST_CONFIG.copy()

def setup_test_environment():
    """Setup test environment with mock configurations"""
    import sys
    import os
    
    # Add parent directory to path for imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Add modules directory to path for imports
    modules_dir = os.path.join(parent_dir, 'modules')
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)
    
    return True

# Import test modules
try:
    setup_test_environment()
    print("✅ Test environment setup complete")
except Exception as e:
    print(f"❌ Test environment setup failed: {e}")