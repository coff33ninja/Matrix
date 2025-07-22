import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from web_server import get_env_config, ServerConfig, UnifiedMatrixWebServer, setup_signal_handlers, main

class TestGetEnvConfig(unittest.TestCase):
    """Test environment configuration function"""

    @patch.dict('os.environ', {
        'WEB_SERVER_PORT': '3001',
        'WEB_SERVER_HOST': 'testhost',
        'API_PROXY_PORT': '8081',
        'ENABLE_CORS': 'false',
        'ENABLE_CACHING': 'true',
        'SITES_DIR': '/test/sites',
        'AUTOCREATE_DIRS': 'true',
        'PYTHONPATH': '/test/python',
        'PATH': '/usr/bin:/bin',
    })
    def test_get_env_config_with_all_vars(self):
        """Test get_env_config with all environment variables set"""
        config = get_env_config()

        expected_keys = [
            'WEB_SERVER_PORT', 'WEB_SERVER_HOST', 'API_PROXY_PORT',
            'ENABLE_CORS', 'ENABLE_CACHING', 'SITES_DIR',
            'AUTOCREATE_DIRS', 'PYTHONPATH', 'PATH',
        ]

        for key in expected_keys:
            self.assertIn(key, config)

        self.assertEqual(config['WEB_SERVER_PORT'], '3001')
        self.assertEqual(config['WEB_SERVER_HOST'], 'testhost')
        self.assertEqual(config['API_PROXY_PORT'], '8081')
        self.assertEqual(config['ENABLE_CORS'], 'false')
        self.assertEqual(config['PATH'], '/usr/bin:/bin')

    @patch.dict('os.environ', {
        'WEB_SERVER_PORT': '3000',
        'PATH': 'a' * 150,  # Long path to test truncation
    }, clear=True)
    def test_get_env_config_path_truncation(self):
        """Test that long PATH values are truncated"""
        config = get_env_config()

        self.assertIn('PATH', config)
        self.assertTrue(config['PATH'].endswith('...'))
        self.assertEqual(len(config['PATH']), 103)  # 100 chars + '...'

    @patch.dict('os.environ', {}, clear=True)
    def test_get_env_config_empty_env(self):
        """Test get_env_config with no environment variables set"""
        config = get_env_config()
        self.assertEqual(config, {})

    @patch.dict('os.environ', {'WEB_SERVER_PORT': '3000', 'UNDEFINED_VAR': None}, clear=True)
    def test_get_env_config_filters_none_values(self):
        """Test that None values are filtered out"""
        config = get_env_config()

        self.assertIn('WEB_SERVER_PORT', config)
        self.assertNotIn('UNDEFINED_VAR', config)


class TestServerConfig(unittest.TestCase):
    """Test ServerConfig dataclass"""

    @patch.dict('os.environ', {}, clear=True)
    def test_server_config_defaults(self):
        """Test ServerConfig uses correct default values"""
        config = ServerConfig()

        self.assertEqual(config.port, 3000)
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.control_path, "sites/control")
        self.assertEqual(config.docs_path, "sites/docs")
        self.assertEqual(config.api_proxy_port, 8080)
        self.assertTrue(config.enable_cors)
        self.assertTrue(config.enable_caching)

    @patch.dict('os.environ', {
        'WEB_SERVER_PORT': '4000',
        'WEB_SERVER_HOST': '0.0.0.0',
        'CONTROL_PATH': 'custom/control',
        'DOCS_PATH': 'custom/docs',
        'API_PROXY_PORT': '9090',
        'ENABLE_CORS': 'false',
        'ENABLE_CACHING': 'false',
    })
    def test_server_config_from_env(self):
        """Test ServerConfig reads from environment variables"""
        config = ServerConfig()

        self.assertEqual(config.port, 4000)
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.control_path, "custom/control")
        self.assertEqual(config.docs_path, "custom/docs")
        self.assertEqual(config.api_proxy_port, 9090)
        self.assertFalse(config.enable_cors)
        self.assertFalse(config.enable_caching)

    @patch.dict('os.environ', {'ENABLE_CORS': 'TRUE', 'ENABLE_CACHING': 'False'})
    def test_server_config_boolean_parsing(self):
        """Test that boolean environment variables are parsed correctly"""
        config = ServerConfig()

        self.assertTrue(config.enable_cors)  # 'TRUE' -> True
        self.assertFalse(config.enable_caching)  # 'False' -> False

    def test_server_config_custom_port(self):
        """Test ServerConfig with custom port parameter"""
        config = ServerConfig(port=5000)
        self.assertEqual(config.port, 5000)


class TestUnifiedMatrixWebServerInit(unittest.TestCase):
    """Test UnifiedMatrixWebServer initialization"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    @patch.dict('os.environ', {'SITES_DIR': '/custom/sites'}, clear=True)
    def test_init_custom_sites_dir(self):
        """Test initialization with custom sites directory"""
        server = UnifiedMatrixWebServer(port=3001)

        self.assertEqual(server.config.port, 3001)
        self.assertEqual(str(server.sites_dir), '/custom/sites')
        self.assertEqual(str(server.control_dir), '/custom/sites/control')
        self.assertEqual(str(server.docs_dir), '/custom/sites/docs')
        self.assertEqual(str(server.errors_dir), '/custom/sites/errors')

    @patch.dict('os.environ', {'WEB_SERVER_PORT': '4000'})
    def test_init_port_from_env(self):
        """Test that port is read from environment when not passed"""
        server = UnifiedMatrixWebServer()
        self.assertEqual(server.config.port, 4000)

    def test_init_default_port(self):
        """Test initialization with default port"""
        with patch.dict('os.environ', {}, clear=True):
            server = UnifiedMatrixWebServer()
            self.assertEqual(server.config.port, 3000)

    @patch('os.makedirs')
    @patch.dict('os.environ', {'AUTOCREATE_DIRS': 'true'})
    def test_init_autocreate_dirs_enabled(self, mock_makedirs):
        """Test that directories are created when AUTOCREATE_DIRS is true"""
        server = UnifiedMatrixWebServer()

        expected_calls = [
            call(server.control_dir, exist_ok=True),
            call(server.docs_dir, exist_ok=True),
            call(server.errors_dir, exist_ok=True),
        ]
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

    @patch('os.makedirs')
    @patch.dict('os.environ', {'AUTOCREATE_DIRS': 'false'})
    def test_init_autocreate_dirs_disabled(self, mock_makedirs):
        """Test that directories are not created when AUTOCREATE_DIRS is false"""
        UnifiedMatrixWebServer()
        mock_makedirs.assert_not_called()

    @patch('builtins.print')
    def test_init_missing_directories_warning(self, mock_print):
        """Test that warnings are printed for missing directories"""
        with patch.object(Path, 'exists', return_value=False):
            UnifiedMatrixWebServer()

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        control_warning = any("Control directory not found" in msg for msg in print_calls)
        docs_warning = any("Documentation directory not found" in msg for msg in print_calls)
        errors_warning = any("Error pages directory not found" in msg for msg in print_calls)

        self.assertTrue(control_warning)
        self.assertTrue(docs_warning)
        self.assertTrue(errors_warning)


class TestCreateLandingPage(unittest.TestCase):
    """Test landing page creation"""

    def setUp(self):
        self.server = UnifiedMatrixWebServer()

    def test_create_landing_page_returns_html(self):
        """Test that create_landing_page returns valid HTML"""
        html = self.server.create_landing_page()

        self.assertIsInstance(html, str)
        self.assertTrue(html.startswith('<!DOCTYPE html>'))
        self.assertIn('<html lang="en">', html)
        self.assertIn('</html>', html)

    def test_create_landing_page_contains_navigation(self):
        """Test that landing page contains expected navigation elements"""
        html = self.server.create_landing_page()

        self.assertIn('LED Matrix Control Center', html)
        self.assertIn('Control Interface', html)
        self.assertIn('Documentation', html)
        self.assertIn('/control', html)
        self.assertIn('/docs', html)

    def test_create_landing_page_contains_status_check(self):
        """Test that landing page contains status checking functionality"""
        html = self.server.create_landing_page()

        self.assertIn('checkControllerStatus', html)
        self.assertIn('/api/status', html)
        self.assertIn('controller-status', html)

    def test_create_landing_page_contains_css(self):
        """Test that landing page contains CSS styling"""
        html = self.server.create_landing_page()

        self.assertIn('<style>', html)
        self.assertIn('</style>', html)
        self.assertIn('--primary:', html)
        self.assertIn('--secondary:', html)


class TestRequestHandlerRouting(unittest.TestCase):
    """Test HTTP request handler routing logic"""

    def setUp(self):
        self.server = UnifiedMatrixWebServer()
        self.handler_class = self.server.create_custom_handler()

    def create_mock_handler(self, path, method='GET'):
        """Create a mock request handler for testing"""
        handler = MagicMock(spec=self.handler_class)
        handler.path = path
        handler.command = method
        handler.client_address = ['127.0.0.1', 12345]
        handler.headers = {'Content-Type': 'application/json'}

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.handle_request = actual_handler.__class__.handle_request.__get__(handler)
        handler.serve_landing_page = MagicMock()
        handler.serve_control_interface = MagicMock()
        handler.serve_docs_interface = MagicMock()
        handler.proxy_api_request = MagicMock()
        handler.serve_404 = MagicMock()
        handler.serve_500 = MagicMock()

        return handler

    def test_handle_request_root_path(self):
        """Test that root path serves landing page"""
        handler = self.create_mock_handler('/')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/'
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.serve_landing_page.assert_called_once()

    def test_handle_request_empty_path(self):
        """Test that empty path serves landing page"""
        handler = self.create_mock_handler('')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = ''
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.serve_landing_page.assert_called_once()

    def test_handle_request_control_path(self):
        """Test that control paths are routed correctly"""
        handler = self.create_mock_handler('/control/index.html')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/control/index.html'
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.serve_control_interface.assert_called_once_with('/control/index.html')

    def test_handle_request_docs_path(self):
        """Test that docs paths are routed correctly"""
        handler = self.create_mock_handler('/docs/getting-started.html')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/docs/getting-started.html'
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.serve_docs_interface.assert_called_once_with('/docs/getting-started.html')

    def test_handle_request_api_path(self):
        """Test that API paths are proxied"""
        handler = self.create_mock_handler('/api/status')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/api/status'
            mock_parse.return_value.query = 'test=1'

            handler.handle_request()
            handler.proxy_api_request.assert_called_once_with('/api/status', 'test=1')

    def test_handle_request_control_api_path(self):
        """Test that control API paths are proxied"""
        handler = self.create_mock_handler('/control/api/config')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/control/api/config'
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.proxy_api_request.assert_called_once_with('/control/api/config', '')

    def test_handle_request_unknown_path(self):
        """Test that unknown paths return 404"""
        handler = self.create_mock_handler('/unknown/path')

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/unknown/path'
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.serve_404.assert_called_once()

    def test_handle_request_exception_handling(self):
        """Test that exceptions in request handling are caught and return 500"""
        handler = self.create_mock_handler('/control')
        handler.serve_control_interface.side_effect = Exception("Test error")

        with patch('urllib.parse.urlparse') as mock_parse:
            mock_parse.return_value.path = '/control'
            mock_parse.return_value.query = ''

            handler.handle_request()
            handler.serve_500.assert_called_once_with("Test error")


class TestStaticFileServing(unittest.TestCase):
    """Test static file serving functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.server = UnifiedMatrixWebServer()
        self.handler_class = self.server.create_custom_handler()

    def create_mock_handler_for_static(self):
        """Create a mock handler for static file testing"""
        handler = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        handler.serve_404 = MagicMock()
        handler.serve_500 = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.serve_static_file = actual_handler.__class__.serve_static_file.__get__(handler)
        handler.send_cors_headers = MagicMock()

        return handler

    def test_serve_static_file_existing_file(self):
        """Test serving an existing static file"""
        test_file_path = Path(self.temp_dir) / "test.html"
        test_content = "<html><body>Test Content</body></html>"
        with open(test_file_path, 'w') as f:
            f.write(test_content)

        handler = self.create_mock_handler_for_static()
        handler.serve_static_file(Path(self.temp_dir), "test.html")

        handler.send_response.assert_called_once_with(200)
        handler.send_header.assert_any_call('Content-Type', 'text/html')
        handler.end_headers.assert_called_once()
        handler.wfile.write.assert_called_once_with(test_content.encode('utf-8'))

    def test_serve_static_file_nonexistent_file(self):
        """Test serving a nonexistent file returns 404"""
        handler = self.create_mock_handler_for_static()
        handler.serve_static_file(Path(self.temp_dir), "nonexistent.html")

        handler.serve_404.assert_called_once()
        handler.send_response.assert_not_called()

    def test_serve_static_file_directory_traversal_protection(self):
        """Test that directory traversal attacks are prevented"""
        handler = self.create_mock_handler_for_static()
        handler.serve_static_file(Path(self.temp_dir), "../../../etc/passwd")

        handler.serve_404.assert_called_once()

    def test_serve_static_file_mime_type_detection(self):
        """Test that MIME types are detected correctly"""
        test_files = {
            "test.css": ("text/css", "body { color: red; }"),
            "test.js": ("text/javascript", "console.log('test');"),
            "test.json": ("application/json", '{"test": true}'),
            "test.png": ("image/png", b"\x89PNG\r\n\x1a\n"),  # PNG header
            "test.unknown": ("application/octet-stream", "unknown content"),
        }

        for filename, (expected_mime, content) in test_files.items():
            test_file_path = Path(self.temp_dir) / filename
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(test_file_path, mode) as f:
                f.write(content)

            handler = self.create_mock_handler_for_static()
            handler.serve_static_file(Path(self.temp_dir), filename)

            handler.send_header.assert_any_call('Content-Type', expected_mime)

    def test_serve_static_file_caching_headers(self):
        """Test that caching headers are added when enabled"""
        test_file_path = Path(self.temp_dir) / "test.html"
        with open(test_file_path, 'w') as f:
            f.write("<html></html>")

        handler = self.create_mock_handler_for_static()
        self.server.config.enable_caching = True

        handler.serve_static_file(Path(self.temp_dir), "test.html")

        handler.send_header.assert_any_call('Cache-Control', 'public, max-age=3600')

    def test_serve_control_interface_path_processing(self):
        """Test that control interface paths are processed correctly"""
        handler = MagicMock()
        handler.serve_static_file = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.serve_control_interface = actual_handler.__class__.serve_control_interface.__get__(handler)

        test_cases = [
            ('/control', '/index.html'),
            ('/control/', '/index.html'),
            ('/control/app.js', '/app.js'),
            ('/control/css/style.css', '/css/style.css'),
        ]

        for input_path, expected_file_path in test_cases:
            handler.serve_control_interface(input_path)
            handler.serve_static_file.assert_called_with(self.server.control_dir, expected_file_path)

    def test_serve_docs_interface_path_processing(self):
        """Test that docs interface paths are processed correctly"""
        handler = MagicMock()
        handler.serve_static_file = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.serve_docs_interface = actual_handler.__class__.serve_docs_interface.__get__(handler)

        test_cases = [
            ('/docs', '/index.html'),
            ('/docs/', '/index.html'),
            ('/docs/guide.html', '/guide.html'),
            ('/docs/images/diagram.png', '/images/diagram.png'),
        ]

        for input_path, expected_file_path in test_cases:
            handler.serve_docs_interface(input_path)
            handler.serve_static_file.assert_called_with(self.server.docs_dir, expected_file_path)


class TestAPIProxy(unittest.TestCase):
    """Test API proxy functionality"""

    def setUp(self):
        self.server = UnifiedMatrixWebServer()
        self.handler_class = self.server.create_custom_handler()

    def create_mock_handler_for_api(self, method='GET'):
        """Create a mock handler for API testing"""
        handler = MagicMock()
        handler.command = method
        handler.headers = {'Content-Type': 'application/json', 'Content-Length': '0'}
        handler.rfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        handler.serve_404 = MagicMock()
        handler.serve_500 = MagicMock()
        handler.serve_503 = MagicMock()
        handler.send_cors_headers = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.proxy_api_request = actual_handler.__class__.proxy_api_request.__get__(handler)

        return handler

    @patch('web_server.requests')
    def test_proxy_api_request_get(self, mock_requests):
        """Test proxying GET API requests"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"status": "ok"}'
        mock_requests.get.return_value = mock_response

        handler = self.create_mock_handler_for_api('GET')
        handler.proxy_api_request('/api/status', 'param=value')

        expected_url = f'http://localhost:{self.server.config.api_proxy_port}/api/status?param=value'
        mock_requests.get.assert_called_once_with(expected_url, timeout=5)

        handler.send_response.assert_called_once_with(200)
        handler.wfile.write.assert_called_once_with(b'{"status": "ok"}')

    @patch('web_server.requests')
    def test_proxy_api_request_post(self, mock_requests):
        """Test proxying POST API requests"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"created": true}'
        mock_requests.post.return_value = mock_response

        handler = self.create_mock_handler_for_api('POST')
        handler.headers['Content-Length'] = '20'
        handler.rfile.read.return_value = b'{"data": "test"}'

        handler.proxy_api_request('/api/create', '')

        expected_url = f'http://localhost:{self.server.config.api_proxy_port}/api/create'
        mock_requests.post.assert_called_once_with(
            expected_url,
            data=b'{"data": "test"}',
            headers={'Content-Type': 'application/json'},
            timeout=5,
        )

    @patch('web_server.requests')
    def test_proxy_api_request_control_api_path_conversion(self, mock_requests):
        """Test that /control/api paths are converted to /api"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'success'
        mock_requests.get.return_value = mock_response

        handler = self.create_mock_handler_for_api('GET')
        handler.proxy_api_request('/control/api/config', '')

        expected_url = f'http://localhost:{self.server.config.api_proxy_port}/api/config'
        mock_requests.get.assert_called_once_with(expected_url, timeout=5)

    @patch('web_server.requests')
    def test_proxy_api_request_connection_error(self, mock_requests):
        """Test handling of connection errors in API proxy"""
        import requests
        mock_requests.get.side_effect = requests.exceptions.ConnectionError()
        mock_requests.exceptions = requests.exceptions

        handler = self.create_mock_handler_for_api('GET')
        handler.proxy_api_request('/api/status', '')

        handler.serve_503.assert_called_once_with("Python controller not running on port 8080")

    @patch('web_server.requests')
    def test_proxy_api_request_timeout_error(self, mock_requests):
        """Test handling of timeout errors in API proxy"""
        import requests
        mock_requests.get.side_effect = requests.exceptions.Timeout()
        mock_requests.exceptions = requests.exceptions

        handler = self.create_mock_handler_for_api('GET')
        handler.proxy_api_request('/api/status', '')

        handler.serve_503.assert_called_once_with("Controller request timeout")

    def test_proxy_api_request_no_requests_library(self):
        """Test API proxy behavior when requests library is not available"""
        handler = self.create_mock_handler_for_api('GET')

        with patch('web_server.requests', None):
            handler.proxy_api_request('/api/status', '')

        handler.serve_503.assert_called_once_with("Requests library not available")

    @patch('web_server.requests')
    def test_proxy_api_request_unsupported_method(self, mock_requests):
        """Test handling of unsupported HTTP methods"""
        handler = self.create_mock_handler_for_api('DELETE')
        handler.proxy_api_request('/api/resource', '')

        handler.serve_404.assert_called_once()
        mock_requests.get.assert_not_called()
        mock_requests.post.assert_not_called()


class TestErrorPages(unittest.TestCase):
    """Test error page serving functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.server = UnifiedMatrixWebServer()
        self.server.errors_dir = Path(self.temp_dir)
        self.handler_class = self.server.create_custom_handler()

    def create_mock_handler_for_errors(self):
        """Create a mock handler for error page testing"""
        handler = MagicMock()
        handler.path = '/test/path'
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        handler.send_cors_headers = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.serve_404 = actual_handler.__class__.serve_404.__get__(handler)
        handler.serve_500 = actual_handler.__class__.serve_500.__get__(handler)
        handler.serve_503 = actual_handler.__class__.serve_503.__get__(handler)

        return handler

    def test_serve_404_with_custom_page(self):
        """Test serving 404 error with custom error page"""
        custom_404_content = "<html><body><h1>Custom 404 Page</h1></body></html>"
        error_page_path = Path(self.temp_dir) / "404.html"
        with open(error_page_path, 'w') as f:
            f.write(custom_404_content)

        handler = self.create_mock_handler_for_errors()
        handler.serve_404()

        handler.send_response.assert_called_once_with(404)
        handler.send_header.assert_any_call('Content-Type', 'text/html; charset=utf-8')
        handler.wfile.write.assert_called_once_with(custom_404_content.encode('utf-8'))

    def test_serve_404_with_fallback_page(self):
        """Test serving 404 error with fallback page when custom page doesn't exist"""
        handler = self.create_mock_handler_for_errors()
        handler.serve_404()

        handler.send_response.assert_called_once_with(404)
        handler.send_header.assert_any_call('Content-Type', 'text/html; charset=utf-8')

        write_call_args = handler.wfile.write.call_args[0][0]
        decoded_content = write_call_args.decode('utf-8')
        self.assertIn('404 - Page Not Found', decoded_content)
        self.assertIn('Return Home', decoded_content)

    def test_serve_500_with_custom_page_and_placeholder(self):
        """Test serving 500 error with custom page and error message placeholder"""
        custom_500_content = "<html><body><h1>Server Error</h1><p>{{ERROR_MESSAGE}}</p></body></html>"
        error_page_path = Path(self.temp_dir) / "500.html"
        with open(error_page_path, 'w') as f:
            f.write(custom_500_content)

        handler = self.create_mock_handler_for_errors()
        handler.serve_500("Database connection failed")

        handler.send_response.assert_called_once_with(500)

        write_call_args = handler.wfile.write.call_args[0][0]
        decoded_content = write_call_args.decode('utf-8')
        self.assertIn('Database connection failed', decoded_content)
        self.assertNotIn('{{ERROR_MESSAGE}}', decoded_content)

    def test_serve_503_with_custom_page(self):
        """Test serving 503 error with custom error page"""
        custom_503_content = "<html><body><h1>Service Unavailable</h1><p>{{ERROR_MESSAGE}}</p></body></html>"
        error_page_path = Path(self.temp_dir) / "503.html"
        with open(error_page_path, 'w') as f:
            f.write(custom_503_content)

        handler = self.create_mock_handler_for_errors()
        handler.serve_503("Controller not responding")

        handler.send_response.assert_called_once_with(503)

        write_call_args = handler.wfile.write.call_args[0][0]
        decoded_content = write_call_args.decode('utf-8')
        self.assertIn('Controller not responding', decoded_content)

    def test_serve_404_connection_aborted(self):
        """Test that connection aborted errors are handled gracefully in 404"""
        handler = self.create_mock_handler_for_errors()
        handler.wfile.write.side_effect = ConnectionAbortedError()

        with patch('builtins.print') as mock_print:
            handler.serve_404()

            mock_print.assert_called_once()
            print_msg = mock_print.call_args[0][0]
            self.assertIn('Client disconnected', print_msg)

    def test_serve_500_broken_pipe(self):
        """Test that broken pipe errors are handled gracefully in 500"""
        handler = self.create_mock_handler_for_errors()
        handler.wfile.write.side_effect = BrokenPipeError()

        with patch('builtins.print') as mock_print:
            handler.serve_500("Test error")

            mock_print.assert_called_once()
            print_msg = mock_print.call_args[0][0]
            self.assertIn('Client disconnected', print_msg)


class TestCORSHeaders(unittest.TestCase):
    """Test CORS headers functionality"""

    def setUp(self):
        self.server = UnifiedMatrixWebServer()
        self.handler_class = self.server.create_custom_handler()

    def create_mock_handler_for_cors(self):
        """Create a mock handler for CORS testing"""
        handler = MagicMock()
        handler.send_header = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.send_cors_headers = actual_handler.__class__.send_cors_headers.__get__(handler)

        return handler

    def test_send_cors_headers_enabled(self):
        """Test that CORS headers are sent when enabled"""
        self.server.config.enable_cors = True
        handler = self.create_mock_handler_for_cors()

        handler.send_cors_headers()

        expected_calls = [
            call('Access-Control-Allow-Origin', '*'),
            call('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            call('Access-Control-Allow-Headers', 'Content-Type'),
        ]
        handler.send_header.assert_has_calls(expected_calls)

    def test_send_cors_headers_disabled(self):
        """Test that CORS headers are not sent when disabled"""
        self.server.config.enable_cors = False
        handler = self.create_mock_handler_for_cors()

        handler.send_cors_headers()

        handler.send_header.assert_not_called()

    def test_do_OPTIONS_method(self):
        """Test that OPTIONS requests are handled correctly"""
        handler = MagicMock()
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()
        handler.send_cors_headers = MagicMock()

        actual_handler = self.handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.do_OPTIONS = actual_handler.__class__.do_OPTIONS.__get__(handler)

        handler.do_OPTIONS()

        handler.send_response.assert_called_once_with(200)
        handler.send_cors_headers.assert_called_once()
        handler.end_headers.assert_called_once()


class TestServerStart(unittest.TestCase):
    """Test server start functionality"""

    def setUp(self):
        self.server = UnifiedMatrixWebServer(port=0)  # Use port 0 for testing

    @patch('socketserver.TCPServer')
    @patch('builtins.print')
    def test_start_server_success(self, mock_print, mock_tcp_server):
        """Test successful server start"""
        mock_httpd = MagicMock()
        mock_tcp_server.return_value.__enter__.return_value = mock_httpd

        def mock_serve_forever():
            raise KeyboardInterrupt

        mock_httpd.serve_forever.side_effect = mock_serve_forever

        result = self.server.start()

        self.assertTrue(result)
        mock_httpd.serve_forever.assert_called_once()

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        startup_msgs = [msg for msg in print_calls if 'LED Matrix Unified Web Server' in msg]
        self.assertTrue(len(startup_msgs) > 0)

    @patch('socketserver.TCPServer')
    def test_start_server_port_in_use(self, mock_tcp_server):
        """Test server start when port is already in use"""
        mock_tcp_server.side_effect = OSError(98, "Address already in use")

        with patch('builtins.print') as mock_print:
            result = self.server.start()

        self.assertFalse(result)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_msgs = [msg for msg in print_calls if 'already in use' in msg]
        self.assertTrue(len(error_msgs) > 0)

    @patch('socketserver.TCPServer')
    def test_start_server_other_os_error(self, mock_tcp_server):
        """Test server start with other OS errors"""
        mock_tcp_server.side_effect = OSError(13, "Permission denied")

        with patch('builtins.print') as mock_print:
            result = self.server.start()

        self.assertFalse(result)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_msgs = [msg for msg in print_calls if 'OS error' in msg]
        self.assertTrue(len(error_msgs) > 0)

    @patch('socketserver.TCPServer')
    def test_start_server_generic_exception(self, mock_tcp_server):
        """Test server start with generic exceptions"""
        mock_tcp_server.side_effect = ValueError("Invalid configuration")

        with patch('builtins.print') as mock_print:
            result = self.server.start()

        self.assertFalse(result)

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_msgs = [msg for msg in print_calls if 'server error' in msg]
        self.assertTrue(len(error_msgs) > 0)

    @patch('os.name', 'nt')  # Windows
    @patch('socket.socket')
    def test_start_server_windows_port_check(self, mock_socket):
        """Test port availability check on Windows"""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0  # Port in use

        with patch('socketserver.TCPServer') as mock_tcp_server:
            mock_httpd = MagicMock()
            mock_tcp_server.return_value.__enter__.return_value = mock_httpd
            mock_httpd.serve_forever.side_effect = KeyboardInterrupt

            with patch('builtins.print') as mock_print:
                self.server.start()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            warning_msgs = [msg for msg in print_calls if 'appears to be in use' in msg]
            self.assertTrue(len(warning_msgs) > 0)

        mock_sock.close.assert_called_once()


class TestSignalHandlers(unittest.TestCase):
    """Test signal handler setup"""

    @patch('signal.signal')
    @patch('os._exit')
    def test_setup_signal_handlers(self, mock_signal, mock_exit):
        """Test that signal handlers are set up correctly"""
        import signal

        with patch.object(signal, 'SIGTERM', 15), \
             patch.object(signal, 'SIGINT', 2):
            setup_signal_handlers()

        assert mock_signal.call_count == 2

    @patch('signal.signal')
    @patch('os._exit')
    @patch('builtins.print')
    def test_signal_handler_function(self, mock_signal, mock_exit, mock_print):
        """Test that the signal handler function works correctly"""
        import signal

        with patch.object(signal, 'SIGTERM', 15):
            setup_signal_handlers()

            sig_handler = mock_signal.call_args_list[0][0][1]
            sig_handler(15, None)

            self.assertEqual(mock_print.call_args_list[0][0][0], "\n🔔 Received signal 15")
            self.assertIn("🛑 Shutting down gracefully...", [c[0][0] for c in mock_print.call_args_list])
            mock_exit.assert_called_once_with(0)


class TestMainFunction(unittest.TestCase):
    """Test main function"""

    @patch('web_server.setup_signal_handlers')
    @patch('web_server.UnifiedMatrixWebServer')
    def test_main_function_normal_flow(self, mock_server_class, mock_setup_signals):
        """Test main function normal execution flow"""
        mock_server = MagicMock()
        mock_server_class.return_value = mock_server

        with patch.dict('os.environ', {}, clear=True):
            main()

        mock_setup_signals.assert_called_once()
        mock_server_class.assert_called_once()
        mock_server.start.assert_called_once()

    @patch('web_server.setup_signal_handlers')
    @patch('web_server.UnifiedMatrixWebServer')
    @patch('web_server.get_env_config')
    @patch('builtins.print')
    def test_main_function_debug_mode(self, mock_print, mock_get_env, mock_server_class, mock_setup_signals):
        """Test main function with debug mode enabled"""
        mock_server = MagicMock()
        mock_server_class.return_value = mock_server
        mock_get_env.return_value = {'TEST_VAR': 'test_value'}

        with patch.dict('os.environ', {'DEBUG': 'true'}):
            main()

        debug_msgs = [m for m in [c[0][0] for c in mock_print.call_args_list] if 'Debug mode enabled' in m]
        env_msgs = [m for m in [c[0][0] for c in mock_print.call_args_list] if 'Environment configuration' in m]
        assert debug_msgs
        assert env_msgs


class TestLoggingConfiguration(unittest.TestCase):
    """Test logging configuration"""

    def test_logger_configuration(self):
        """Test that logger is configured correctly"""
        import logging

        test_logger = logging.getLogger('WebServer')

        assert test_logger.name == 'WebServer'
        assert len(test_logger.handlers) >= 0  # May have handlers from module import


class TestIntegrationScenarios(unittest.TestCase):
    """Integration-style tests for complex scenarios"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    @patch.dict('os.environ', {
        'SITES_DIR': None,
        'AUTOCREATE_DIRS': 'true',
    }, clear=True)
    def test_full_server_initialization_with_autocreate(self):
        """Test full server initialization with directory auto-creation"""
        with patch('os.makedirs') as mock_makedirs:
            UnifiedMatrixWebServer()
            self.assertEqual(mock_makedirs.call_count, 3)  # control, docs, errors

    def test_request_routing_integration(self):
        """Test that request routing works end-to-end"""
        server = UnifiedMatrixWebServer()
        handler_class = server.create_custom_handler()

        request = MagicMock()
        client_address = ('127.0.0.1', 12345)
        server_instance = MagicMock()

        handler = handler_class(request, client_address, server_instance)

        assert hasattr(handler, 'do_GET')
        assert hasattr(handler, 'do_POST')
        assert hasattr(handler, 'do_OPTIONS')
        assert hasattr(handler, 'handle_request')


    @patch('web_server.requests')
    def test_api_proxy_end_to_end(self, mock_requests):
        """Test API proxy functionality end-to-end"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"result": "success"}'
        mock_requests.get.return_value = mock_response

        server = UnifiedMatrixWebServer()
        handler_class = server.create_custom_handler()

        handler = MagicMock()
        handler.command = 'GET'
        handler.headers = {'Content-Type': 'application/json'}
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()
        handler.send_cors_headers = MagicMock()

        actual_handler = handler_class(MagicMock(), MagicMock(), MagicMock())
        handler.proxy_api_request = actual_handler.__class__.proxy_api_request.__get__(handler)

        handler.proxy_api_request('/api/test', '')

        expected_url = f'http://localhost:{server.config.api_proxy_port}/api/test'
        mock_requests.get.assert_called_once_with(expected_url, timeout=5)

        handler.send_response.assert_called_once_with(200)
        handler.wfile.write.assert_called_once_with(b'{"result": "success"}')


if __name__ == '__main__':
    unittest.main()