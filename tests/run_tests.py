#!/usr/bin/env python3
"""
Legacy test runner - redirects to unified entry point
Use: python matrix.py test
"""

import sys
import os

print("⚠️  This test runner has been replaced by the unified entry point.")
print("Please use: python matrix.py test")
print()

# Redirect to unified entry point
sys.argv = ['matrix.py', 'test'] + sys.argv[1:]

try:
    from matrix import main
    success = main()
    sys.exit(0 if success else 1)
except Exception as e:
    print(f"❌ Error running unified entry point: {e}")
    print("Falling back to direct test execution...")
    
    # Fallback to direct execution
    try:
        from tests.run_all_tests import main as test_main
        success = test_main()
        sys.exit(0 if success else 1)
    except Exception as e2:
        print(f"💥 Fallback also failed: {e2}")
        sys.exit(1)