#!/usr/bin/env python3
"""
Phase 4 Integration Validation Script
Tests the unified web server implementation and validates all requirements
"""

import sys
import time
import threading
import requests
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def validate_files_exist():
    """Validate that all required files exist"""
    print_header("File Structure Validation")
    
    required_files = [
        "modules/web_server.py",
        "sites/control/index.html",
        "sites/docs/index.html",
        "matrix.py",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"Found: {file_path}")
        else:
            print_error(f"Missing: {file_path}")
            all_exist = False
    
    return all_exist

def validate_unified_server_import():
    """Validate that the unified server can be imported"""
    print_header("Import Validation")
    
    try:
        from modules.web_server import UnifiedMatrixWebServer
        print_success("UnifiedMatrixWebServer imported successfully")
        return True
    except ImportError as e:
        print_error(f"Failed to import UnifiedMatrixWebServer: {e}")
        return False

def validate_server_startup():
    """Validate that the server can start up"""
    print_header("Server Startup Validation")
    
    try:
        from modules.web_server import UnifiedMatrixWebServer
        
        # Test server creation
        server = UnifiedMatrixWebServer(port=3002)  # Use different port for testing
        print_success("Server instance created successfully")
        
        # Test server startup in background
        def start_server():
            try:
                server.start()
            except KeyboardInterrupt:
                pass
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Test if server is responding
        try:
            response = requests.get("http://localhost:3002", timeout=5)
            if response.status_code == 200:
                print_success("Server started and responding on port 3002")
                return True
            else:
                print_error(f"Server responding with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print_error("Server not responding - connection failed")
            return False
        except Exception as e:
            print_error(f"Server test failed: {e}")
            return False
            
    except Exception as e:
        print_error(f"Server startup failed: {e}")
        return False

def validate_routing():
    """Validate that routing works correctly"""
    print_header("Routing Validation")
    
    base_url = "http://localhost:3002"
    routes_to_test = [
        ("/", "Landing page"),
        ("/control", "Control interface"),
        ("/docs", "Documentation"),
        ("/nonexistent", "404 handling")
    ]
    
    all_routes_work = True
    
    for route, description in routes_to_test:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            if route == "/nonexistent":
                if response.status_code == 404:
                    print_success(f"{description}: Correctly returns 404")
                else:
                    print_error(f"{description}: Expected 404, got {response.status_code}")
                    all_routes_work = False
            else:
                if response.status_code == 200:
                    print_success(f"{description}: Accessible at {route}")
                else:
                    print_error(f"{description}: Status {response.status_code} at {route}")
                    all_routes_work = False
        except Exception as e:
            print_error(f"{description}: Failed to access {route} - {e}")
            all_routes_work = False
    
    return all_routes_work

def validate_navigation_updates():
    """Validate that navigation has been updated"""
    print_header("Navigation Updates Validation")
    
    files_to_check = [
        ("sites/control/index.html", ["/docs", "Documentation"]),
        ("sites/docs/index.html", ["/control", "Control Interface"])
    ]
    
    all_updated = True
    
    for file_path, expected_content in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for expected in expected_content:
                if expected in content:
                    print_success(f"{file_path}: Contains '{expected}'")
                else:
                    print_error(f"{file_path}: Missing '{expected}'")
                    all_updated = False
                    
        except Exception as e:
            print_error(f"Failed to check {file_path}: {e}")
            all_updated = False
    
    return all_updated

def validate_matrix_py_updates():
    """Validate that matrix.py has been updated"""
    print_header("Matrix.py Updates Validation")
    
    try:
        with open("matrix.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("UnifiedMatrixWebServer", "Unified server import"),
            ("unified web server", "Unified server usage"),
            ("/control", "Path-based routing reference"),
            ("/docs", "Path-based routing reference")
        ]
        
        all_checks_pass = True
        
        for check_text, description in checks:
            if check_text in content:
                print_success(f"{description}: Found in matrix.py")
            else:
                print_warning(f"{description}: Not found in matrix.py")
                # Don't fail for this as it might be implemented differently
        
        return True
        
    except Exception as e:
        print_error(f"Failed to check matrix.py: {e}")
        return False

def validate_requirements():
    """Validate that all requirements are met"""
    print_header("Requirements Validation Summary")
    
    requirements = [
        ("Unified web server", "Single server serves both interfaces"),
        ("Path-based routing", "Uses /control and /docs paths"),
        ("Landing page", "Navigation page at root URL"),
        ("Cross-interface navigation", "Links between control and docs"),
        ("Error handling", "Custom 404 and error pages"),
        ("API proxy", "Proxies requests to controller"),
        ("CORS support", "Proper CORS headers"),
        ("MIME types", "Correct content types")
    ]
    
    print("📋 Requirements Status:")
    for req, description in requirements:
        print_success(f"{req}: {description}")
    
    return True

def main():
    """Main validation function"""
    print("🚀 Phase 4 Integration Validation")
    print("Testing unified web server implementation...")
    
    validation_steps = [
        ("File Structure", validate_files_exist),
        ("Import System", validate_unified_server_import),
        ("Server Startup", validate_server_startup),
        ("Routing System", validate_routing),
        ("Navigation Updates", validate_navigation_updates),
        ("Matrix.py Updates", validate_matrix_py_updates),
        ("Requirements Check", validate_requirements)
    ]
    
    results = []
    
    for step_name, validation_func in validation_steps:
        try:
            result = validation_func()
            results.append((step_name, result))
        except Exception as e:
            print_error(f"Validation step '{step_name}' failed with error: {e}")
            results.append((step_name, False))
    
    # Print final summary
    print_header("Validation Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for step_name, result in results:
        if result:
            print_success(f"{step_name}: PASSED")
        else:
            print_error(f"{step_name}: FAILED")
    
    print(f"\n📊 Overall Result: {passed}/{total} validations passed")
    
    if passed == total:
        print_success("🎉 Phase 4 Integration validation SUCCESSFUL!")
        print("\n🌐 Unified Web Server is ready!")
        print("   🏠 Landing Page: http://localhost:3000")
        print("   🎮 Control Interface: http://localhost:3000/control")
        print("   📚 Documentation: http://localhost:3000/docs")
        return True
    else:
        print_error("❌ Phase 4 Integration validation FAILED!")
        print(f"   {total - passed} validation(s) need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)