#!/usr/bin/env python3
"""
Quick test for async matrix controller functionality
"""

import sys
import os

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from matrix_controller import WebMatrixController
        print("✅ WebMatrixController imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import WebMatrixController: {e}")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp available - async mode supported")
        async_available = True
    except ImportError:
        print("⚠️  aiohttp not available - will use sync mode")
        async_available = False
    
    try:
        import asyncio
        print("✅ asyncio available")
    except ImportError:
        print("❌ asyncio not available")
        return False
    
    return True, async_available

def test_controller_creation():
    """Test creating the controller instance"""
    print("\n🏗️  Testing controller creation...")
    
    try:
        from matrix_controller import WebMatrixController
        
        # Test with async mode
        controller = WebMatrixController(port=8081, use_async=True)
        print("✅ Async controller created successfully")
        
        # Test with sync mode
        controller_sync = WebMatrixController(port=8082, use_async=False)
        print("✅ Sync controller created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create controller: {e}")
        return False

def main():
    """Run basic tests"""
    print("🚀 LED Matrix Async Controller Test")
    print("=" * 50)
    
    # Test imports
    import_result = test_imports()
    if not import_result:
        print("\n❌ Import tests failed")
        return False
    
    imports_ok, async_available = import_result
    
    # Test controller creation
    if not test_controller_creation():
        print("\n❌ Controller creation tests failed")
        return False
    
    print("\n✅ All tests passed!")
    print("\n📋 Summary:")
    print(f"   • Imports: ✅ Working")
    print(f"   • Async support: {'✅ Available' if async_available else '⚠️  Not available'}")
    print(f"   • Controller creation: ✅ Working")
    
    if async_available:
        print("\n🎉 Ready to use async features!")
        print("   Start with: python matrix.py controller")
    else:
        print("\n⚠️  Install aiohttp for async features:")
        print("   pip install aiohttp aiofiles websockets")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)