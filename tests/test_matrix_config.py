#!/usr/bin/env python3
"""
Comprehensive unit tests for MatrixConfig class
Testing framework: unittest (Python standard library)
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch
import time
from unittest import TestCase
import contextlib

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from matrix_config import MatrixConfig


class TestMatrixConfig(TestCase):
    """Test suite for MatrixConfig class"""
    
    def setUp(self) -> None:
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.test_dir, "test_config.json")
        self.valid_config = {
            "matrix_width": 32,
            "matrix_height": 32,
            "brightness": 200,
            "serial_port": "COM4",
        }
        
    def tearDown(self) -> None:
        """Clean up test environment after each test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_default_config_values(self) -> None:
        """Test that DEFAULT_CONFIG contains expected values"""
        expected_keys = [
            "matrix_width", "matrix_height", "leds_per_meter", "wiring_pattern",
            "serial_port", "baud_rate", "brightness", "connection_mode",
            "esp32_ip", "web_port", "web_server_port", "physical_width",
            "physical_height", "data_pin",
        ]
        
        for key in expected_keys:
            assert key in MatrixConfig.DEFAULT_CONFIG
        
        # Test specific default values
        assert MatrixConfig.DEFAULT_CONFIG["matrix_width"] == 21
        assert MatrixConfig.DEFAULT_CONFIG["matrix_height"] == 24
        assert MatrixConfig.DEFAULT_CONFIG["brightness"] == 128
        assert MatrixConfig.DEFAULT_CONFIG["baud_rate"] == 500000

    def test_init_with_nonexistent_config_file(self) -> None:
        """Test initialization when config file doesn't exist"""
        with patch('builtins.print') as mock_print:
            config = MatrixConfig(self.test_config_file)
            assert config.config == MatrixConfig.DEFAULT_CONFIG
            mock_print.assert_called_with(f"Config file {self.test_config_file} not found, using defaults")

    def test_init_with_valid_config_file(self) -> None:
        """Test initialization with a valid config file"""
        # Create a valid config file
        with open(self.test_config_file, 'w') as f:
            json.dump(self.valid_config, f)
        
        with patch('builtins.print') as mock_print:
            config = MatrixConfig(self.test_config_file)
            
            # Should merge with defaults
            expected_config = {**MatrixConfig.DEFAULT_CONFIG, **self.valid_config}
            assert config.config == expected_config
            mock_print.assert_called_with(f"Loaded config from {os.path.abspath(self.test_config_file)}")

    def test_init_with_empty_config_file(self) -> None:
        """Test initialization with an empty config file"""
        # Create empty file
        open(self.test_config_file, 'w').close()
        
        with patch('builtins.print') as mock_print:
            config = MatrixConfig(self.test_config_file)
            assert config.config == MatrixConfig.DEFAULT_CONFIG
            mock_print.assert_called_with(f"Config file {self.test_config_file} is empty, using defaults")

    def test_init_with_invalid_json(self) -> None:
        """Test initialization with invalid JSON in config file"""
        with open(self.test_config_file, 'w') as f:
            f.write("invalid json content")
        
        with patch('builtins.print') as mock_print:
            config = MatrixConfig(self.test_config_file)
            assert config.config == MatrixConfig.DEFAULT_CONFIG
            # Should print error message containing "Error loading config"
            assert any("Error loading config" in str(call) for call in mock_print.call_args_list)

    @patch('os.access')
    def test_init_with_unreadable_file(self, mock_access) -> None:
        """Test initialization with unreadable config file"""
        # Create file first
        with open(self.test_config_file, 'w') as f:
            json.dump(self.valid_config, f)
        
        # Mock file as unreadable
        mock_access.return_value = False
        
        with patch('builtins.print') as mock_print:
            config = MatrixConfig(self.test_config_file)
            assert config.config == MatrixConfig.DEFAULT_CONFIG
            mock_print.assert_called_with(f"Config file {self.test_config_file} is not readable")

    def test_ensure_directories(self) -> None:
        """Test that ensure_directories creates required directories"""
        config_file = os.path.join(self.test_dir, "subdir", "config.json")
        config = MatrixConfig(config_file)
        
        # Check that directories were created
        assert os.path.exists(config.config_dir)
        assert os.path.exists(config.backup_dir)

    def test_get_method(self) -> None:
        """Test the get method for retrieving config values"""
        config = MatrixConfig(self.test_config_file)
        
        # Test getting existing key
        assert config.get("matrix_width") == 21
        
        # Test getting non-existent key with default
        assert config.get("non_existent", "default") == "default"
        
        # Test getting non-existent key without default
        assert config.get("non_existent") is None

    def test_set_method(self) -> None:
        """Test the set method for updating config values"""
        config = MatrixConfig(self.test_config_file)
        
        config.set("matrix_width", 64)
        assert config.get("matrix_width") == 64
        
        # Test setting new key
        config.set("new_key", "new_value")
        assert config.get("new_key") == "new_value"

    def test_update_method(self) -> None:
        """Test the update method for bulk updates"""
        config = MatrixConfig(self.test_config_file)
        
        updates = {
            "matrix_width": 48,
            "matrix_height": 48,
            "brightness": 255,
            "new_setting": "test_value",
        }
        
        config.update(updates)
        
        for key, value in updates.items():
            assert config.get(key) == value

    def test_update_method_with_none_values(self) -> None:
        """Test that update method filters out None values"""
        config = MatrixConfig(self.test_config_file)
        original_width = config.get("matrix_width")
        
        updates = {
            "matrix_width": None,
            "brightness": 255,
            "new_setting": None,
        }
        
        config.update(updates)
        
        # None values should be filtered out
        assert config.get("matrix_width") == original_width
        assert config.get("brightness") == 255
        assert config.get("new_setting") is None

    def test_save_config_new_file(self) -> None:
        """Test saving configuration to a new file"""
        config = MatrixConfig(self.test_config_file)
        config.set("test_key", "test_value")
        
        with patch('builtins.print') as mock_print:
            config.save_config()
            
            # Check file was created and contains correct data
            assert os.path.exists(self.test_config_file)
            
            with open(self.test_config_file) as f:
                saved_config = json.load(f)
                assert saved_config["test_key"] == "test_value"
            
            mock_print.assert_called_with(f"Config saved to {os.path.abspath(self.test_config_file)}")

    def test_save_config_with_backup(self) -> None:
        """Test saving configuration creates backup of existing file"""
        # Create initial config file
        with open(self.test_config_file, 'w') as f:
            json.dump({"old_key": "old_value"}, f)
        
        config = MatrixConfig(self.test_config_file)
        config.set("new_key", "new_value")
        
        with patch.object(config, 'create_backup') as mock_backup:
            config.save_config()
            mock_backup.assert_called_once()

    @patch('os.rename')
    @patch('os.remove')
    def test_save_config_windows_atomic_operation(self, mock_remove, mock_rename) -> None:
        """Test atomic save operation on Windows"""
        with patch('os.name', 'nt'), \
             patch('os.path.exists', side_effect=lambda x: x == self.test_config_file):
            
            config = MatrixConfig(self.test_config_file)
            config.save_config()
            
            # On Windows, existing file should be removed before rename
            mock_remove.assert_called_once_with(self.test_config_file)
            mock_rename.assert_called_once()

    @patch('builtins.open', side_effect=OSError("Disk full"))
    def test_save_config_io_error(self, _mock_open) -> None:
        """Test save_config handles IO errors gracefully"""
        config = MatrixConfig(self.test_config_file)
        
        with patch('builtins.print') as mock_print, \
             patch('os.path.exists', return_value=False), \
             patch('os.remove') as mock_remove:
            
            config.save_config()
            
            # Should print error message
            mock_print.assert_called_with("Error saving config: Disk full")
            # Should attempt to clean up temp file
            mock_remove.assert_called()

    def test_create_backup(self) -> None:
        """Test backup creation functionality"""
        # Create initial config file
        with open(self.test_config_file, 'w') as f:
            json.dump(self.valid_config, f)
        
        config = MatrixConfig(self.test_config_file)
        
        with patch('time.strftime', return_value="20231201_120000"), \
             patch('builtins.print') as mock_print, \
             patch.object(config, 'cleanup_old_backups') as mock_cleanup:
            
            config.create_backup()
            
            # Check backup was created
            expected_backup = os.path.join(config.backup_dir, "matrix_config_backup_20231201_120000.json")
            assert os.path.exists(expected_backup)
            
            # Verify backup content
            with open(expected_backup) as f:
                backup_content = json.load(f)
                assert backup_content == self.valid_config
            
            mock_print.assert_called_with(f"Backup created: {expected_backup}")
            mock_cleanup.assert_called_once()

    def test_create_backup_no_original_file(self) -> None:
        """Test create_backup when original file doesn't exist"""
        config = MatrixConfig(self.test_config_file)
        
        # Should return early if file doesn't exist
        with patch('builtins.print') as mock_print:
            config.create_backup()
            mock_print.assert_not_called()

    @patch('shutil.copy2', side_effect=OSError("Permission denied"))
    def test_create_backup_io_error(self, _mock_copy) -> None:
        """Test create_backup handles IO errors"""
        with open(self.test_config_file, 'w') as f:
            json.dump(self.valid_config, f)
        
        config = MatrixConfig(self.test_config_file)
        
        with patch('builtins.print') as mock_print:
            config.create_backup()
            mock_print.assert_called_with("Error creating backup: Permission denied")

    def test_cleanup_old_backups(self) -> None:
        """Test cleanup of old backup files"""
        config = MatrixConfig(self.test_config_file)
        
        # Create multiple backup files with different timestamps
        backup_files = []
        for i in range(15):  # More than keep_count=10
            filename = f"matrix_config_backup_2023120{i:02d}_120000.json"
            filepath = os.path.join(config.backup_dir, filename)
            with open(filepath, 'w') as f:
                json.dump({f"key_{i}": f"value_{i}"}, f)
            
            # Set different modification times
            timestamp = time.time() - (i * 3600)  # Each file 1 hour older
            os.utime(filepath, (timestamp, timestamp))
            backup_files.append(filepath)
        
        with patch('builtins.print') as mock_print:
            config.cleanup_old_backups(keep_count=10)
            
            # Should keep only 10 most recent files
            remaining_files = [f for f in os.listdir(config.backup_dir) 
                             if f.startswith("matrix_config_backup_")]
            assert len(remaining_files) == 10
            
            # Should have printed removal messages
            assert any("Removed old backup:" in str(call) for call in mock_print.call_args_list)

    def test_cleanup_old_backups_no_backup_dir(self) -> None:
        """Test cleanup when backup directory doesn't exist"""
        config = MatrixConfig(self.test_config_file)
        shutil.rmtree(config.backup_dir)  # Remove backup directory
        
        # Should handle gracefully
        config.cleanup_old_backups()

    def test_get_config_info(self) -> None:
        """Test get_config_info returns comprehensive information"""
        config = MatrixConfig(self.test_config_file)
        info = config.get_config_info()
        
        # Test required keys are present
        required_keys = [
            "config_file", "config_dir", "backup_dir", "file_exists",
            "current_working_dir", "platform", "backup_count",
        ]
        for key in required_keys:
            assert key in info
        
        # Test specific values
        assert info["config_file"] == os.path.abspath(self.test_config_file)
        assert info["file_exists"] == os.path.exists(self.test_config_file)
        assert isinstance(info["backup_count"], int)

    def test_get_config_info_with_existing_file(self) -> None:
        """Test get_config_info with existing config file"""
        with open(self.test_config_file, 'w') as f:
            json.dump(self.valid_config, f)
        
        config = MatrixConfig(self.test_config_file)
        info = config.get_config_info()
        
        # Should include file stats
        assert "file_size_bytes" in info
        assert "last_modified" in info
        assert "is_readable" in info
        assert "is_writable" in info
        
        assert info["file_exists"]
        assert info["file_size_bytes"] > 0

    def test_restore_from_backup_with_filename(self) -> None:
        """Test restoring from a specific backup file"""
        # Create original config and backup
        with open(self.test_config_file, 'w') as f:
            json.dump({"original": "config"}, f)
        
        config = MatrixConfig(self.test_config_file)
        config.create_backup()
        
        # Modify current config
        config.set("modified", "value")
        config.save_config()
        
        # Get backup filename
        backup_files = os.listdir(config.backup_dir)
        backup_filename = next(f for f in backup_files if f.startswith("matrix_config_backup_"))
        
        with patch('builtins.print') as mock_print:
            result = config.restore_from_backup(backup_filename)
            
            assert result
            assert config.get("original") == "config"
            assert config.get("modified") is None  # Should be gone after restore
            
            mock_print.assert_called_with(f"Configuration restored from backup: {backup_filename}")

    def test_restore_from_backup_most_recent(self) -> None:
        """Test restoring from most recent backup when no filename specified"""
        # Create multiple backups
        config = MatrixConfig(self.test_config_file)
        
        # Create first backup
        config.set("version", 1)
        config.save_config()
        config.create_backup()
        time.sleep(0.1)  # Ensure different timestamps
        
        # Create second backup (more recent)
        config.set("version", 2)
        config.save_config()
        config.create_backup()
        
        # Modify current config
        config.set("version", 3)
        config.save_config()
        
        # Restore without specifying filename (should get most recent)
        result = config.restore_from_backup()
        
        assert result
        # Should restore version 2 (most recent backup)
        assert config.get("version") == 2

    def test_restore_from_backup_no_backups(self) -> None:
        """Test restore when no backup files exist"""
        config = MatrixConfig(self.test_config_file)
        
        with patch('builtins.print') as mock_print:
            result = config.restore_from_backup()
            
            assert not result
            mock_print.assert_called_with("No backup files found")

    def test_restore_from_backup_no_backup_dir(self) -> None:
        """Test restore when backup directory doesn't exist"""
        config = MatrixConfig(self.test_config_file)
        shutil.rmtree(config.backup_dir)
        
        with patch('builtins.print') as mock_print:
            result = config.restore_from_backup()
            
            assert not result
            mock_print.assert_called_with("No backup directory found")

    def test_restore_from_backup_invalid_file(self) -> None:
        """Test restore with invalid backup file"""
        config = MatrixConfig(self.test_config_file)
        
        with patch('builtins.print') as mock_print:
            result = config.restore_from_backup("nonexistent_backup.json")
            
            assert not result
            expected_path = os.path.join(config.backup_dir, "nonexistent_backup.json")
            mock_print.assert_called_with(f"Backup file not found: {expected_path}")

    def test_export_config(self) -> None:
        """Test exporting configuration to file"""
        config = MatrixConfig(self.test_config_file)
        config.set("export_test", "test_value")
        
        export_path = os.path.join(self.test_dir, "exported_config.json")
        
        with patch('builtins.print') as mock_print:
            result = config.export_config(export_path)
            
            assert result
            assert os.path.exists(export_path)
            
            # Verify exported content
            with open(export_path) as f:
                exported_config = json.load(f)
                assert exported_config["export_test"] == "test_value"
            
            mock_print.assert_called_with(f"Configuration exported to: {os.path.abspath(export_path)}")

    def test_export_config_creates_directory(self) -> None:
        """Test export creates directory if it doesn't exist"""
        config = MatrixConfig(self.test_config_file)
        
        export_dir = os.path.join(self.test_dir, "new_subdir")
        export_path = os.path.join(export_dir, "config.json")
        
        result = config.export_config(export_path)
        
        assert result
        assert os.path.exists(export_dir)
        assert os.path.exists(export_path)

    @patch('builtins.open', side_effect=OSError("Permission denied"))
    def test_export_config_io_error(self, _mock_open) -> None:
        """Test export handles IO errors"""
        config = MatrixConfig(self.test_config_file)
        export_path = os.path.join(self.test_dir, "export.json")
        
        with patch('builtins.print') as mock_print:
            result = config.export_config(export_path)
            
            assert not result
            mock_print.assert_called_with("Error exporting config: Permission denied")

    def test_import_config(self) -> None:
        """Test importing configuration from file"""
        # Create import file
        import_data = {"imported_key": "imported_value", "brightness": 64}
        import_path = os.path.join(self.test_dir, "import_config.json")
        
        with open(import_path, 'w') as f:
            json.dump(import_data, f)
        
        config = MatrixConfig(self.test_config_file)
        original_width = config.get("matrix_width")  # Should be preserved
        
        with patch('builtins.print') as mock_print:
            result = config.import_config(import_path)
            
            assert result
            assert config.get("imported_key") == "imported_value"
            assert config.get("brightness") == 64  # Should be updated
            assert config.get("matrix_width") == original_width  # Should be preserved
            
            mock_print.assert_called_with(f"Configuration imported from: {os.path.abspath(import_path)}")

    def test_import_config_nonexistent_file(self) -> None:
        """Test import with nonexistent file"""
        config = MatrixConfig(self.test_config_file)
        import_path = os.path.join(self.test_dir, "nonexistent.json")
        
        with patch('builtins.print') as mock_print:
            result = config.import_config(import_path)
            
            assert not result
            mock_print.assert_called_with(f"Import file not found: {import_path}")

    @patch('os.access')
    def test_import_config_unreadable_file(self, mock_access) -> None:
        """Test import with unreadable file"""
        import_path = os.path.join(self.test_dir, "unreadable.json")
        with open(import_path, 'w') as f:
            json.dump({"test": "data"}, f)
        
        mock_access.return_value = False
        
        config = MatrixConfig(self.test_config_file)
        
        with patch('builtins.print') as mock_print:
            result = config.import_config(import_path)
            
            assert not result
            mock_print.assert_called_with(f"Import file not readable: {import_path}")

    def test_import_config_invalid_json(self) -> None:
        """Test import with invalid JSON file"""
        import_path = os.path.join(self.test_dir, "invalid.json")
        with open(import_path, 'w') as f:
            f.write("invalid json content")
        
        config = MatrixConfig(self.test_config_file)
        
        with patch('builtins.print') as mock_print:
            result = config.import_config(import_path)
            
            assert not result
            assert any("Error importing config" in str(call) for call in mock_print.call_args_list)

    def test_import_config_creates_backup(self) -> None:
        """Test import creates backup of existing config"""
        # Create existing config
        with open(self.test_config_file, 'w') as f:
            json.dump({"existing": "config"}, f)
        
        # Create import file
        import_path = os.path.join(self.test_dir, "import.json")
        with open(import_path, 'w') as f:
            json.dump({"imported": "data"}, f)
        
        config = MatrixConfig(self.test_config_file)
        
        with patch.object(config, 'create_backup') as mock_backup:
            config.import_config(import_path)
            mock_backup.assert_called_once()

    def test_global_config_instance(self) -> None:
        """Test that global config instance is created"""
        # This test imports the module to test the global instance
        import matrix_config
        
        assert isinstance(matrix_config.config, MatrixConfig)
        assert matrix_config.config.config_file == "matrix_config.json"

    def test_edge_case_empty_updates(self) -> None:
        """Test update method with empty dictionary"""
        config = MatrixConfig(self.test_config_file)
        original_config = config.config.copy()
        
        config.update({})
        
        assert config.config == original_config

    def test_edge_case_large_config_values(self) -> None:
        """Test handling of large configuration values"""
        config = MatrixConfig(self.test_config_file)
        
        large_string = "x" * 10000
        large_number = 2**32
        
        config.set("large_string", large_string)
        config.set("large_number", large_number)
        
        assert config.get("large_string") == large_string
        assert config.get("large_number") == large_number

    def test_edge_case_special_characters_in_values(self) -> None:
        """Test handling of special characters in config values"""
        config = MatrixConfig(self.test_config_file)
        
        special_values = {
            "unicode_string": "Testing unicode: åäö αβγ 中文",
            "path_with_backslashes": "C:\\Windows\\System32",
            "json_special_chars": '{"nested": "json", "array": [1,2,3]}',
            "newlines_and_tabs": "Line 1\nLine 2\tTabbed",
        }
        
        for key, value in special_values.items():
            config.set(key, value)
            assert config.get(key) == value

    def test_concurrent_access_simulation(self) -> None:
        """Test behavior under simulated concurrent access"""
        # This tests the atomic save operation
        config = MatrixConfig(self.test_config_file)
        
        # Simulate interruption during save
        with patch('os.rename', side_effect=[OSError("Interrupted"), None]), \
             patch('builtins.print'):
            with contextlib.suppress(BaseException):
                config.save_config()
            
            # Second attempt should work
            config.save_config()

    def test_backup_filename_format(self) -> None:
        """Test backup filename format and uniqueness"""
        config = MatrixConfig(self.test_config_file)
        
        # Create config file
        with open(self.test_config_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        with patch('time.strftime', return_value="20231201_143052"):
            config.create_backup()
            
            expected_filename = "matrix_config_backup_20231201_143052.json"
            expected_path = os.path.join(config.backup_dir, expected_filename)
            
            assert os.path.exists(expected_path)

    def test_config_directory_edge_cases(self) -> None:
        """Test configuration with various directory scenarios"""
        # Test with relative path
        relative_config = MatrixConfig("./test_config.json")
        assert os.path.isabs(relative_config.config_dir)
        
        # Test with just filename (no directory)
        filename_only_config = MatrixConfig("config.json")
        assert filename_only_config.config_dir == "."
        
        # Clean up
        for config_obj in [relative_config, filename_only_config]:
            if os.path.exists(config_obj.backup_dir):
                shutil.rmtree(config_obj.backup_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)