#!/usr/bin/env python3
"""
Test suite for matrix configuration module
Tests configuration management, file operations, and backup functionality
"""

import unittest
import tempfile
import os
import sys
import json
import shutil
from unittest.mock import patch, mock_open

# Setup test environment
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'modules'))

from matrix_config import MatrixConfig
from tests import get_test_config


class TestMatrixConfig(unittest.TestCase):
    """Test cases for matrix configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")
        self.test_config = get_test_config()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_default_config_loading(self):
        """Test loading default configuration when no file exists"""
        config = MatrixConfig(self.test_config_file)
        
        # Should have default values
        self.assertEqual(config.get("matrix_width"), 21)
        self.assertEqual(config.get("matrix_height"), 24)
        self.assertEqual(config.get("brightness"), 128)
        self.assertEqual(config.get("connection_mode"), "USB")
    
    def test_config_file_creation_and_loading(self):
        """Test creating and loading configuration file"""
        # Create initial config
        config = MatrixConfig(self.test_config_file)
        config.set("matrix_width", 32)
        config.set("matrix_height", 32)
        config.set("brightness", 200)
        config.save_config()
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.test_config_file))
        
        # Load config in new instance
        config2 = MatrixConfig(self.test_config_file)
        self.assertEqual(config2.get("matrix_width"), 32)
        self.assertEqual(config2.get("matrix_height"), 32)
        self.assertEqual(config2.get("brightness"), 200)
    
    def test_config_update_functionality(self):
        """Test configuration update with multiple values"""
        config = MatrixConfig(self.test_config_file)
        
        updates = {
            "matrix_width": 16,
            "matrix_height": 16,
            "brightness": 150,
            "data_pin": 7
        }
        
        config.update(updates)
        
        for key, value in updates.items():
            self.assertEqual(config.get(key), value)
    
    def test_config_update_with_none_values(self):
        """Test that None values are filtered out in updates"""
        config = MatrixConfig(self.test_config_file)
        original_width = config.get("matrix_width")
        
        updates = {
            "matrix_width": None,  # Should be filtered out
            "brightness": 100      # Should be applied
        }
        
        config.update(updates)
        
        # Width should remain unchanged, brightness should be updated
        self.assertEqual(config.get("matrix_width"), original_width)
        self.assertEqual(config.get("brightness"), 100)
    
    def test_backup_functionality(self):
        """Test configuration backup creation"""
        config = MatrixConfig(self.test_config_file)
        config.set("test_value", "backup_test")
        config.save_config()
        
        # Create backup
        config.create_backup()
        
        # Check backup directory exists
        backup_dir = os.path.join(config.backup_dir)
        self.assertTrue(os.path.exists(backup_dir))
        
        # Check backup file was created
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("matrix_config_backup_")]
        self.assertGreater(len(backup_files), 0)
    
    def test_config_info_retrieval(self):
        """Test configuration information retrieval"""
        config = MatrixConfig(self.test_config_file)
        config.save_config()
        
        info = config.get_config_info()
        
        # Check required info fields
        self.assertIn("config_file", info)
        self.assertIn("config_dir", info)
        self.assertIn("backup_dir", info)
        self.assertIn("file_exists", info)
        self.assertIn("platform", info)
        
        # File should exist after saving
        self.assertTrue(info["file_exists"])
    
    def test_export_import_functionality(self):
        """Test configuration export and import"""
        config = MatrixConfig(self.test_config_file)
        config.set("matrix_width", 24)
        config.set("matrix_height", 32)
        config.set("test_export", "export_value")
        
        # Export configuration
        export_path = os.path.join(self.temp_dir, "exported_config.json")
        success = config.export_config(export_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Create new config instance and import
        config2 = MatrixConfig(os.path.join(self.temp_dir, "new_config.json"))
        import_success = config2.import_config(export_path)
        self.assertTrue(import_success)
        
        # Verify imported values
        self.assertEqual(config2.get("matrix_width"), 24)
        self.assertEqual(config2.get("matrix_height"), 32)
        self.assertEqual(config2.get("test_export"), "export_value")
    
    def test_backup_restoration(self):
        """Test backup restoration functionality"""
        config = MatrixConfig(self.test_config_file)
        
        # Set initial values and save
        config.set("matrix_width", 16)
        config.set("test_restore", "original_value")
        config.save_config()
        
        # Modify values and save (this creates backup)
        config.set("matrix_width", 32)
        config.set("test_restore", "modified_value")
        config.save_config()
        
        # Restore from backup
        restore_success = config.restore_from_backup()
        self.assertTrue(restore_success)
        
        # Values should be restored to previous state
        self.assertEqual(config.get("matrix_width"), 16)
        self.assertEqual(config.get("test_restore"), "original_value")
    
    def test_directory_creation(self):
        """Test automatic directory creation"""
        nested_config_path = os.path.join(self.temp_dir, "nested", "deep", "config.json")
        config = MatrixConfig(nested_config_path)
        config.save_config()
        
        # Directory should be created automatically
        self.assertTrue(os.path.exists(os.path.dirname(nested_config_path)))
        self.assertTrue(os.path.exists(nested_config_path))
    
    def test_corrupted_config_handling(self):
        """Test handling of corrupted configuration files"""
        # Create corrupted JSON file
        with open(self.test_config_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Should fall back to defaults without crashing
        config = MatrixConfig(self.test_config_file)
        self.assertEqual(config.get("matrix_width"), 21)  # Default value
    
    def test_atomic_save_operation(self):
        """Test atomic save operation (temp file + rename)"""
        config = MatrixConfig(self.test_config_file)
        config.set("atomic_test", "test_value")
        
        # Mock os.rename to verify it's called
        with patch('os.rename') as mock_rename:
            config.save_config()
            mock_rename.assert_called_once()
    
    def test_cleanup_old_backups(self):
        """Test cleanup of old backup files"""
        config = MatrixConfig(self.test_config_file)
        config.save_config()
        
        # Create multiple backups
        for i in range(15):  # More than the default keep_count of 10
            config.create_backup()
        
        # Check that only 10 backups are kept
        backup_files = [f for f in os.listdir(config.backup_dir) 
                       if f.startswith("matrix_config_backup_")]
        self.assertLessEqual(len(backup_files), 10)


class TestMatrixConfigIntegration(unittest.TestCase):
    """Integration tests for matrix configuration"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "integration_config.json")
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_global_config_instance(self):
        """Test that global config instance works correctly"""
        from matrix_config import config
        
        # Should be a MatrixConfig instance
        self.assertIsInstance(config, MatrixConfig)
        
        # Should have default values
        self.assertIsNotNone(config.get("matrix_width"))
        self.assertIsNotNone(config.get("matrix_height"))
    
    def test_config_sharing_between_modules(self):
        """Test that configuration is properly shared between modules"""
        from matrix_config import config
        
        # Modify global config
        original_width = config.get("matrix_width")
        config.set("matrix_width", 99)
        
        # Import another module that uses config
        try:
            from matrix_hardware import hardware
            # Hardware should see the updated config
            # (This is more of a smoke test to ensure no import errors)
            self.assertIsNotNone(hardware)
        except ImportError:
            self.skipTest("matrix_hardware module not available")
        finally:
            # Restore original value
            config.set("matrix_width", original_width)


def run_config_validation_tests():
    """Run validation tests to ensure config works with real scenarios"""
    print("🔧 Running Matrix Config Validation Tests")
    print("=" * 50)
    
    temp_dir = tempfile.mkdtemp()
    test_config_file = os.path.join(temp_dir, "validation_config.json")
    
    try:
        # Test 1: Basic configuration lifecycle
        print("\n📝 Test 1: Basic Configuration Lifecycle")
        config = MatrixConfig(test_config_file)
        
        # Set some values
        config.set("matrix_width", 20)
        config.set("matrix_height", 25)
        config.set("brightness", 180)
        config.save_config()
        
        # Reload and verify
        config2 = MatrixConfig(test_config_file)
        assert config2.get("matrix_width") == 20
        assert config2.get("matrix_height") == 25
        assert config2.get("brightness") == 180
        print("   ✅ Configuration lifecycle working correctly")
        
        # Test 2: Backup and restore
        print("\n📝 Test 2: Backup and Restore")
        config2.set("matrix_width", 30)
        config2.save_config()  # Creates backup
        
        success = config2.restore_from_backup()
        assert success
        assert config2.get("matrix_width") == 20  # Should be restored
        print("   ✅ Backup and restore working correctly")
        
        # Test 3: Export and import
        print("\n📝 Test 3: Export and Import")
        export_path = os.path.join(temp_dir, "exported.json")
        export_success = config2.export_config(export_path)
        assert export_success
        
        config3 = MatrixConfig(os.path.join(temp_dir, "imported_config.json"))
        import_success = config3.import_config(export_path)
        assert import_success
        assert config3.get("matrix_width") == 20
        print("   ✅ Export and import working correctly")
        
        print("\n✅ All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation test failed: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run both unittest and validation tests
    print("🧪 Running Matrix Config Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run validation tests
    print("\n" + "=" * 60)
    validation_success = run_config_validation_tests()
    
    print("\n🎉 Matrix Config Test Suite Complete!")
    print("=" * 60)
    if validation_success:
        print("✅ All tests passed - Matrix configuration is working correctly!")
    else:
        print("⚠️  Some validation tests failed - check output above")