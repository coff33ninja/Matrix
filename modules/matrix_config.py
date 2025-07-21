#!/usr/bin/env python3
"""
Centralized Matrix Configuration
Single source of truth for all matrix settings
"""

import json
import os


class MatrixConfig:
    """Centralized configuration management"""

    DEFAULT_CONFIG = {
        "matrix_width": 21,
        "matrix_height": 24,
        "leds_per_meter": 144,
        "wiring_pattern": "serpentine",
        "serial_port": "COM3",
        "baud_rate": 500000,
        "brightness": 128,
        "connection_mode": "USB",
        "esp32_ip": "192.168.4.1",
        "web_port": 8080,
        "physical_width": 146,
        "physical_height": 167,
        "data_pin": 6,
    }

    def __init__(self, config_file="matrix_config.json"):
        self.config_file = config_file
        self.config_dir = os.path.dirname(os.path.abspath(config_file)) or "."
        self.backup_dir = os.path.join(self.config_dir, "backups")
        self.ensure_directories()
        self.config = self.load_config()

    def ensure_directories(self):
        """Ensure required directories exist using os functions"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)

    def load_config(self):
        """Load configuration with defaults and file validation"""
        try:
            # Check if config file exists and is readable
            if not os.path.exists(self.config_file):
                print(f"Config file {self.config_file} not found, using defaults")
                return self.DEFAULT_CONFIG.copy()

            # Check file permissions
            if not os.access(self.config_file, os.R_OK):
                print(f"Config file {self.config_file} is not readable")
                return self.DEFAULT_CONFIG.copy()

            # Get file stats for validation
            file_stats = os.stat(self.config_file)
            if file_stats.st_size == 0:
                print(f"Config file {self.config_file} is empty, using defaults")
                return self.DEFAULT_CONFIG.copy()

            with open(self.config_file, "r") as f:
                config = json.load(f)
                print(f"Loaded config from {os.path.abspath(self.config_file)}")
                return {**self.DEFAULT_CONFIG, **config}

        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            print(f"Error loading config: {e}, using defaults")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save current configuration with backup"""
        try:
            # Create backup if original file exists
            if os.path.exists(self.config_file):
                self.create_backup()

            # Ensure directory exists
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            # Write config with atomic operation (write to temp, then rename)
            temp_file = self.config_file + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(self.config, f, indent=2)

            # Atomic rename (safer than direct write)
            if os.name == "nt":  # Windows
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
            os.rename(temp_file, self.config_file)

            print(f"Config saved to {os.path.abspath(self.config_file)}")

        except (IOError, OSError) as e:
            print(f"Error saving config: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value

    def update(self, updates):
        """Update multiple configuration values"""
        self.config.update({k: v for k, v in updates.items() if v is not None})

    def create_backup(self):
        """Create timestamped backup of current config"""
        if not os.path.exists(self.config_file):
            return

        try:
            # Generate timestamp for backup filename
            import time

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"matrix_config_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            # Copy current config to backup
            import shutil

            shutil.copy2(self.config_file, backup_path)
            print(f"Backup created: {backup_path}")

            # Clean old backups (keep only last 10)
            self.cleanup_old_backups()

        except (IOError, OSError) as e:
            print(f"Error creating backup: {e}")

    def cleanup_old_backups(self, keep_count=10):
        """Remove old backup files, keeping only the most recent ones"""
        try:
            if not os.path.exists(self.backup_dir):
                return

            # Get all backup files
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("matrix_config_backup_") and filename.endswith(
                    ".json"
                ):
                    filepath = os.path.join(self.backup_dir, filename)
                    if os.path.isfile(filepath):
                        backup_files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            for filepath, _ in backup_files[keep_count:]:
                os.remove(filepath)
                print(f"Removed old backup: {os.path.basename(filepath)}")

        except (IOError, OSError) as e:
            print(f"Error cleaning up backups: {e}")

    def get_config_info(self):
        """Get detailed information about config file and system"""
        info = {
            "config_file": os.path.abspath(self.config_file),
            "config_dir": os.path.abspath(self.config_dir),
            "backup_dir": os.path.abspath(self.backup_dir),
            "file_exists": os.path.exists(self.config_file),
            "current_working_dir": os.getcwd(),
            "platform": os.name,
        }

        if os.path.exists(self.config_file):
            try:
                stat_info = os.stat(self.config_file)
                info.update(
                    {
                        "file_size_bytes": stat_info.st_size,
                        "last_modified": stat_info.st_mtime,
                        "is_readable": os.access(self.config_file, os.R_OK),
                        "is_writable": os.access(self.config_file, os.W_OK),
                    }
                )
            except OSError:
                pass

        # Count backup files
        backup_count = 0
        if os.path.exists(self.backup_dir):
            try:
                backup_count = len(
                    [
                        f
                        for f in os.listdir(self.backup_dir)
                        if f.startswith("matrix_config_backup_") and f.endswith(".json")
                    ]
                )
            except OSError:
                pass

        info["backup_count"] = backup_count
        return info

    def restore_from_backup(self, backup_filename=None):
        """Restore configuration from a backup file"""
        try:
            if backup_filename is None:
                # Find the most recent backup
                if not os.path.exists(self.backup_dir):
                    print("No backup directory found")
                    return False

                backup_files = []
                for filename in os.listdir(self.backup_dir):
                    if filename.startswith(
                        "matrix_config_backup_"
                    ) and filename.endswith(".json"):
                        filepath = os.path.join(self.backup_dir, filename)
                        if os.path.isfile(filepath):
                            backup_files.append((filename, os.path.getmtime(filepath)))

                if not backup_files:
                    print("No backup files found")
                    return False

                # Get most recent backup
                backup_files.sort(key=lambda x: x[1], reverse=True)
                backup_filename = backup_files[0][0]

            backup_path = os.path.join(self.backup_dir, backup_filename)

            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_path}")
                return False

            # Load backup and validate
            with open(backup_path, "r") as f:
                backup_config = json.load(f)

            # Create backup of current config before restoring
            if os.path.exists(self.config_file):
                self.create_backup()

            # Restore from backup
            self.config = {**self.DEFAULT_CONFIG, **backup_config}
            self.save_config()

            print(f"Configuration restored from backup: {backup_filename}")
            return True

        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Error restoring from backup: {e}")
            return False

    def export_config(self, export_path):
        """Export current configuration to specified path"""
        try:
            # Ensure export directory exists
            export_dir = os.path.dirname(export_path)
            if export_dir and not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

            with open(export_path, "w") as f:
                json.dump(self.config, f, indent=2)

            print(f"Configuration exported to: {os.path.abspath(export_path)}")
            return True

        except (IOError, OSError) as e:
            print(f"Error exporting config: {e}")
            return False

    def import_config(self, import_path):
        """Import configuration from specified path"""
        try:
            if not os.path.exists(import_path):
                print(f"Import file not found: {import_path}")
                return False

            if not os.access(import_path, os.R_OK):
                print(f"Import file not readable: {import_path}")
                return False

            with open(import_path, "r") as f:
                imported_config = json.load(f)

            # Create backup before importing
            if os.path.exists(self.config_file):
                self.create_backup()

            # Merge with defaults and current config
            self.config = {**self.DEFAULT_CONFIG, **imported_config}
            self.save_config()

            print(f"Configuration imported from: {os.path.abspath(import_path)}")
            return True

        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Error importing config: {e}")
            return False


# Global config instance
config = MatrixConfig()
