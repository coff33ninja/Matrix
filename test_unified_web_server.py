#!/usr/bin/env python3
"""
Test suite for the unified web server implementation
Tests route handling, file serving, API proxy, and navigation functionality
"""

import unittest
import requests
import threading
import time
import tempfile
import os
from pathlib import Path
import json

# Import the unified web server
try:
    from modules.web_server import UnifiedMatrixWebServer
except ImportError:
    print("❌ Could not import UnifiedMatrixWebServer. Make sure modules/web_server.py exists.")
    exit(1)

class TestUnifiedWebServer(unittest.TestCase):
    """Test cases for the unified web server"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test server"""
        cls.test_port = 3001  # Use different port for testing
        cls.server = UnifiedMatrixWebServer(port=cls.test_port)
        cls.base_url = f"http://localhost:{cls.test_port}"
        
        # Start server in background thread
        cls.server_thread = threading.Thread(target=cls.server.start, daemon=True)
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Verify server is running
        try:
            response = requests.get(cls.base_url, timeout=5)
            if response.status_code != 200:
                raise Exception(f"Server not responding properly: {response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to start test server: {e}")
    
    def test_landing_page(self):
        """Test that landing page loads correctly"""
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("LED Matrix Control Center", response.text)
        self.assertIn("Control Interface", response.text)
        self.assertIn("Documentation", response.text)
        self.assertIn("/control", response.text)
        self.assertIn("/docs", response.text)
    
    def test_control_interface_routing(self):
        """Test that control interface routes correctly"""
        # Test /control redirect to /control/
        response = requests.get(f"{self.base_url}/control")
        self.assertEqual(response.status_code, 200)
        
        # Test /control/ loads index.html
        response = requests.get(f"{self.base_url}/control/")
        self.assertEqual(response.status_code, 200)
        # Should contain control interface content
        self.assertIn("LED Matrix Control Center", response.text)
    
    def test_docs_interface_routing(self):
        """Test that documentation interface routes correctly"""
        # Test /docs redirect to /docs/
        response = requests.get(f"{self.base_url}/docs")
        self.assertEqual(response.status_code, 200)
        
        # Test /docs/ loads index.html
        response = requests.get(f"{self.base_url}/docs/")
        self.assertEqual(response.status_code, 200)
        # Should contain documentation content
        self.assertIn("LED Matrix Project", response.text)
    
    def test_404_handling(self):
        """Test that 404 errors are handled properly"""
        response = requests.get(f"{self.base_url}/nonexistent")
        self.assertEqual(response.status_code, 404)
        self.assertIn("404 - Page Not Found", response.text)
        self.assertIn("Control Interface", response.text)
        self.assertIn("Documentation", response.text)
    
    def test_api_proxy_unavailable(self):
        """Test API proxy when controller is not running"""
        response = requests.get(f"{self.base_url}/api/status")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Service Unavailable", response.text)
        self.assertIn("Python controller not running", response.text)
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = requests.get(self.base_url)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
    
    def test_mime_types(self):
        """Test that proper MIME types are served"""
        # Test HTML
        response = requests.get(self.base_url)
        self.assertTrue(response.headers["Content-Type"].startswith("text/html"))
        
        # Test CSS (if available)
        try:
            response = requests.get(f"{self.base_url}/control/style.css")
            if response.status_code == 200:
                self.assertTrue(response.headers["Content-Type"].startswith("text/css"))
        except:
            pass  # CSS file might not exist
    
    def test_navigation_links(self):
        """Test that navigation links are properly updated"""
        # Check control interface has navigation to docs
        response = requests.get(f"{self.base_url}/control")
        self.assertIn("/docs", response.text)
        self.assertIn("Documentation", response.text)
        
        # Check docs interface has navigation to control
        response = requests.get(f"{self.base_url}/docs")
        self.assertIn("/control", response.text)
        self.assertIn("Control Interface", response.text)
    
    def test_security_path_traversal(self):
        """Test that path traversal attacks are prevented"""
        # Try to access files outside the sites directory
        response = requests.get(f"{self.base_url}/control/../../../etc/passwd")
        self.assertEqual(response.status_code, 404)
        
        response = requests.get(f"{self.base_url}/docs/../../matrix.py")
        self.assertEqual(response.status_code, 404)

class TestNavigationIntegration(unittest.TestCase):
    """Test navigation integration between interfaces"""
    
    def setUp(self):
        self.base_url = "http://localhost:3001"  # Use test server
    
    def test_cross_interface_navigation(self):
        """Test navigation between control and documentation"""
        # Start at landing page
        response = requests.get(self.base_url)
        self.assertIn("/control", response.text)
        self.assertIn("/docs", response.text)
        
        # Navigate to control interface
        response = requests.get(f"{self.base_url}/control")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Documentation", response.text)
        
        # Navigate to documentation
        response = requests.get(f"{self.base_url}/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Control Interface", response.text)

class TestPerformance(unittest.TestCase):
    """Test performance aspects of the unified server"""
    
    def setUp(self):
        self.base_url = "http://localhost:3001"  # Use test server
    
    def test_response_times(self):
        """Test that response times are reasonable"""
        start_time = time.time()
        response = requests.get(self.base_url)
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        def make_request():
            response = requests.get(self.base_url)
            return response.status_code
        
        # Make 10 concurrent requests
        threads = []
        results = []
        
        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        for status_code in results:
            self.assertEqual(status_code, 200)

def run_tests():
    """Run all tests"""
    print("🧪 Starting Unified Web Server Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestUnifiedWebServer))
    suite.addTests(loader.loadTestsFromTestCase(TestNavigationIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        print(f"📊 Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"📊 Ran {result.testsRun} tests")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"⚠️  Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)