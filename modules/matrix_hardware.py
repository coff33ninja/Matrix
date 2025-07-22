#!/usr/bin/env python3
"""
Shared Hardware Communication Module
DRY implementation for serial and WiFi communication
"""

import serial
import requests
import struct
import itertools
import numpy as np
from matrix_config import config


class MatrixHardware:
    """Unified hardware communication interface"""

    def __init__(self):
        self.ser = None
        self.connection_mode = config.get("connection_mode", "USB")

    def connect(self, mode=None, port=None, esp32_ip=None):
        """Connect to matrix hardware"""
        if mode is not None:
            self.connection_mode = mode

        try:
            if self.connection_mode == "USB":
                port = port or config.get("serial_port")
                baud_rate = config.get("baud_rate") or 115200  # Ensure integer default
                self.ser = serial.Serial(port, baud_rate, timeout=1)
                return f"Connected via USB to {port}"
            else:
                esp32_ip = esp32_ip or str(config.get("esp32_ip", "192.168.4.1"))
                response = requests.get(f"http://{esp32_ip}/", timeout=2)
                if response.status_code == 200:
                    return f"Connected via Wi-Fi to {esp32_ip}"
                else:
                    return f"Wi-Fi connection issue: HTTP {response.status_code}"
        except Exception as e:
            raise ConnectionError(f"Connection failed: {str(e)}")

    def disconnect(self):
        """Disconnect from hardware"""
        if self.ser:
            self.ser.close()
            self.ser = None

    def send_frame(self, matrix_data):
        """Send frame data to hardware"""
        try:
            # Apply brightness
            brightness_value = config.get("brightness", 128)
            brightness = (
                brightness_value if brightness_value is not None else 128
            ) / 255.0
            data = (matrix_data * brightness).astype(np.uint8)

            # Pack data efficiently
            frame_data = b"".join(
                struct.pack("BBB", r, g, b)
                for r, g, b in itertools.chain.from_iterable(data)
            )

            if self.connection_mode == "USB" and self.ser:
                self.ser.write(frame_data)
            elif self.connection_mode == "WIFI":
                esp32_ip = config.get("esp32_ip")
                requests.post(
                    f"http://{esp32_ip}/frame",
                    data=frame_data,
                    timeout=1,
                )

            return "Frame sent successfully"
        except Exception as e:
            raise RuntimeError(f"Send error: {str(e)}")


# Global hardware instance
hardware = MatrixHardware()
