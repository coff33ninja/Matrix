#!/usr/bin/env python3
"""
Test runner for the complete LED Matrix Project test suite
Runs all tests and provides comprehensive reporting
"""

import unittest
import sys
import os
import time
import importlib
from io import StringIO

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from tests import setup_test_environment, get_test_config


class TestResult:
    """Custom test result tracking"""
    
    def __init__(self):
        self.tests_run = 0
        self.failures = 0
        self.errors = 0
        self.skipped = 0
        self.success = 0
        self.start_time = None
        self.end_time = None
        self.test_results = []
    
    def start_timer(self):
        self.start_time = time.time()
    
    def stop_timer(self):
        self.end_time = time.time()
    
    def get_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def add_result(self, test_name, status, duration, details=None):
        self.test_results.append({
            'name': test_name,
            'status': status,
            'duration': duration,
            'details': details
        })
        
        if status == 'PASS':
            self.success += 1
        elif status == 'FAIL':
            self.failures += 1
        elif status == 'ERROR':
            self.errors += 1
        elif status == 'SKIP':
            self.skipped += 1
        
        self.tests_run += 1


def run_test_module(module_name, result_tracker):
    """Run tests from a specific module"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {module_name}")
    print(f"{'='*60}")
    
    module_start = time.time()
    
    try:
        # Import the test module
        test_module = importlib.import_module(f"tests.{module_name}")
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests with custom result handling
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        test_result = runner.run(suite)
        
        # Calculate results
        module_duration = time.time() - module_start
        tests_run = test_result.testsRun
        failures = len(test_result.failures)
        errors = len(test_result.errors)
        skipped = len(test_result.skipped)
        success = tests_run - failures - errors - skipped
        
        # Update tracker
        status = 'PASS' if (failures == 0 and errors == 0) else 'FAIL'
        result_tracker.add_result(
            module_name, 
            status, 
            module_duration,
            {
                'tests_run': tests_run,
                'success': success,
                'failures': failures,
                'errors': errors,
                'skipped': skipped
            }
        )
        
        # Print summary
        print(f"\n📊 {module_name} Results:")
        print(f"   Tests Run: {tests_run}")
        print(f"   ✅ Passed: {success}")
        if failures > 0:
            print(f"   ❌ Failed: {failures}")
        if errors > 0:
            print(f"   💥 Errors: {errors}")
        if skipped > 0:
            print(f"   ⏭️  Skipped: {skipped}")
        print(f"   ⏱️  Duration: {module_duration:.2f}s")
        
        # Print failure details if any
        if failures > 0 or errors > 0:
            print(f"\n❌ Failure Details for {module_name}:")
            for failure in test_result.failures:
                print(f"   FAIL: {failure[0]}")
                print(f"         {failure[1].split('AssertionError:')[-1].strip()}")
            
            for error in test_result.errors:
                print(f"   ERROR: {error[0]}")
                print(f"          {error[1].split('Exception:')[-1].strip()}")
        
        return status == 'PASS'
        
    except Exception as e:
        print(f"❌ Failed to run {module_name}: {e}")
        result_tracker.add_result(module_name, 'ERROR', time.time() - module_start, str(e))
        return False


def run_legacy_validation_tests(result_tracker):
    """Run legacy validation tests from individual modules"""
    print(f"\n{'='*60}")
    print("� Runninng Legacy Validation Tests")
    print(f"{'='*60}")
    
    validation_start = time.time()
    validation_results = []
    
    # Test modules that have validation functions
    validation_modules = [
        ('test_arduino_generator', 'run_legacy_tests'),
        ('test_matrix_config', 'run_config_validation_tests'),
        ('test_arduino_models', 'run_arduino_models_validation'),
        ('test_matrix_design_library', 'run_design_library_validation'),
        ('test_wiring_diagram_generator', 'run_wiring_diagram_validation'),
        ('test_integration', 'run_integration_validation')
    ]
    
    for module_name, function_name in validation_modules:
        print(f"\n📝 Running {module_name}.{function_name}()")
        
        try:
            test_module = importlib.import_module(f"tests.{module_name}")
            validation_function = getattr(test_module, function_name)
            
            func_start = time.time()
            success = validation_function()
            func_duration = time.time() - func_start
            
            status = 'PASS' if success else 'FAIL'
            validation_results.append((module_name, status, func_duration))
            
            print(f"   {'✅' if success else '❌'} {module_name} validation: {status} ({func_duration:.2f}s)")
            
        except Exception as e:
            print(f"   ❌ {module_name} validation failed: {e}")
            validation_results.append((module_name, 'ERROR', 0))
    
    # Summary
    validation_duration = time.time() - validation_start
    passed = sum(1 for _, status, _ in validation_results if status == 'PASS')
    total = len(validation_results)
    
    overall_status = 'PASS' if passed == total else 'FAIL'
    result_tracker.add_result(
        'legacy_validation', 
        overall_status, 
        validation_duration,
        {
            'total': total,
            'passed': passed,
            'failed': total - passed
        }
    )
    
    print("\n📊 Legacy Validation Summary:")
    print(f"   Total: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {total - passed}")
    print(f"   ⏱️  Duration: {validation_duration:.2f}s")
    
    return overall_status == 'PASS'


def print_final_report(result_tracker):
    """Print comprehensive final test report"""
    print(f"\n{'='*80}")
    print(f"🎉 FINAL TEST REPORT")
    print(f"{'='*80}")
    
    # Overall statistics
    total_duration = result_tracker.get_duration()
    print("\n📊 Overall Statistics:")
    print(f"   Total Test Suites: {len(result_tracker.test_results)}")
    print(f"   ✅ Passed: {result_tracker.success}")
    print(f"   ❌ Failed: {result_tracker.failures}")
    print(f"   💥 Errors: {result_tracker.errors}")
    print(f"   ⏭️  Skipped: {result_tracker.skipped}")
    print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
    
    # Success rate
    if result_tracker.tests_run > 0:
        success_rate = (result_tracker.success / result_tracker.tests_run) * 100
        print(f"   📈 Success Rate: {success_rate:.1f}%")
    
    # Detailed results
    print("\n📋 Detailed Results:")
    print(f"{'Test Suite':<30} {'Status':<8} {'Duration':<10} {'Details'}")
    print(f"{'-'*70}")
    
    for result in result_tracker.test_results:
        status_icon = {
            'PASS': '✅',
            'FAIL': '❌',
            'ERROR': '💥',
            'SKIP': '⏭️'
        }.get(result['status'], '❓')
        
        details = ""
        if result['details'] and isinstance(result['details'], dict):
            if 'tests_run' in result['details']:
                details = f"{result['details']['success']}/{result['details']['tests_run']} tests"
            elif 'passed' in result['details']:
                details = f"{result['details']['passed']}/{result['details']['total']} validations"
        
        print(f"{result['name']:<30} {status_icon} {result['status']:<6} {result['duration']:<8.2f}s {details}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if result_tracker.failures == 0 and result_tracker.errors == 0:
        print("   🎉 All tests passed! The LED Matrix Project is working correctly.")
        print("   🚀 Ready for production use.")
    else:
        print("   ⚠️  Some tests failed. Please review the failure details above.")
        print("   🔧 Fix failing tests before deploying to production.")
        
        if result_tracker.errors > 0:
            print("   💥 Errors indicate serious issues that need immediate attention.")
    
    # Performance insights
    slowest_test = max(result_tracker.test_results, key=lambda x: x['duration'])
    fastest_test = min(result_tracker.test_results, key=lambda x: x['duration'])
    
    print("\n⚡ Performance Insights:")
    print(f"   Slowest: {slowest_test['name']} ({slowest_test['duration']:.2f}s)")
    print(f"   Fastest: {fastest_test['name']} ({fastest_test['duration']:.2f}s)")
    
    return result_tracker.failures == 0 and result_tracker.errors == 0


def main():
    """Main test runner function"""
    print("🧪 LED Matrix Project - Comprehensive Test Suite")
    print("=" * 80)
    
    # Setup test environment
    setup_success = setup_test_environment()
    if not setup_success:
        print("❌ Failed to setup test environment")
        return False
    
    test_config = get_test_config()
    print(f"📋 Test Configuration:")
    print(f"   Matrix Size: {test_config['default_matrix_width']}×{test_config['default_matrix_height']}")
    print(f"   Test Brightness: {test_config['test_brightness']}")
    print(f"   Test Timeout: {test_config['test_timeout']}s")
    
    # Initialize result tracker
    result_tracker = TestResult()
    result_tracker.start_timer()
    
    # Test modules to run
    test_modules = [
        'test_arduino_models',
        'test_matrix_config', 
        'test_arduino_generator',
        'test_matrix_design_library',
        'test_wiring_diagram_generator',
        'test_integration'
    ]
    
    # Run each test module
    all_passed = True
    for module in test_modules:
        module_passed = run_test_module(module, result_tracker)
        all_passed = all_passed and module_passed
    
    # Run legacy validation tests
    legacy_passed = run_legacy_validation_tests(result_tracker)
    all_passed = all_passed and legacy_passed
    
    # Stop timer and generate final report
    result_tracker.stop_timer()
    final_success = print_final_report(result_tracker)
    
    # Return overall success
    return final_success and all_passed


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        
        print(f"\n{'='*80}")
        if success:
            print("🎉 ALL TESTS PASSED! LED Matrix Project is ready for use.")
        else:
            print("❌ SOME TESTS FAILED! Please review and fix issues above.")
        print(f"{'='*80}")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)