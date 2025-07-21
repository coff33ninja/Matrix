#!/usr/bin/env python3
import math

"""
Arduino Models Configuration
Centralized dictionary of Arduino models with their specifications and code templates
"""

ARDUINO_MODELS = {
    "uno": {
        "name": "Arduino Uno",
        "display_name": "Arduino Uno",
        "voltage": "5V",
        "default_pin": 6,
        "memory_sram": 2048,  # bytes
        "memory_flash": 32768,  # bytes
        "needs_level_shifter": False,
        "max_leds_recommended": 500,
        "baud_rate": 500000,
        "includes": ["<FastLED.h>"],
        "setup_code": """FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  Serial.begin({baud_rate});
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();""",
        "loop_code": """if (Serial.available() >= NUM_LEDS * 3) {
    for (uint16_t i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(Serial.read(), Serial.read(), Serial.read());
    }
    FastLED.show();
  }""",
        "additional_functions": """// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}""",
    },
    "nano": {
        "name": "Arduino Nano",
        "display_name": "Arduino Nano",
        "voltage": "5V",
        "default_pin": 6,
        "memory_sram": 2048,  # bytes
        "memory_flash": 32768,  # bytes
        "needs_level_shifter": False,
        "max_leds_recommended": 500,
        "baud_rate": 500000,
        "includes": ["<FastLED.h>"],
        "setup_code": """FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  Serial.begin({baud_rate});
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();""",
        "loop_code": """if (Serial.available() >= NUM_LEDS * 3) {
    for (uint16_t i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(Serial.read(), Serial.read(), Serial.read());
    }
    FastLED.show();
  }""",
        "additional_functions": """// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}""",
    },
    "esp32": {
        "name": "ESP32",
        "display_name": "ESP32 Dev Board",
        "voltage": "3.3V",
        "default_pin": 13,
        "memory_sram": 520000,  # bytes
        "memory_flash": 4194304,  # bytes
        "needs_level_shifter": True,
        "max_leds_recommended": 2000,
        "baud_rate": 115200,
        "includes": ["<WiFi.h>", "<ESPAsyncWebServer.h>", "<FastLED.h>"],
        "additional_defines": """
// WiFi Configuration
const char *ssid = "PC-Matrix";
const char *pass = "12345678";
AsyncWebServer server(80);""",
        "setup_code": """FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  WiFi.softAP(ssid, pass);
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();
  
  server.on("/frame", HTTP_POST,
    [](AsyncWebServerRequest *r){{}},
    NULL,
    [](AsyncWebServerRequest *r, uint8_t *data, size_t len, size_t, size_t){{
      memcpy(leds, data, min(len, sizeof(leds)));
      FastLED.show();
      r->send(200, "text/plain", "OK");
    }});
  server.begin();""",
        "loop_code": """// ESP32 handles requests via web server callbacks
  // Main loop can be empty or used for other tasks
  delay(10);""",
        "additional_functions": """// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}

// Helper function to set individual pixels
void setPixel(uint8_t x, uint8_t y, CRGB color) {
  if (x < MATRIX_WIDTH && y < MATRIX_HEIGHT) {
    leds[XY(x, y)] = color;
  }
}""",
    },
    "esp8266": {
        "name": "ESP8266",
        "display_name": "ESP8266 NodeMCU",
        "voltage": "3.3V",
        "default_pin": 2,
        "memory_sram": 80000,  # bytes
        "memory_flash": 4194304,  # bytes
        "needs_level_shifter": True,
        "max_leds_recommended": 800,
        "baud_rate": 115200,
        "includes": ["<ESP8266WiFi.h>", "<ESPAsyncWebServer.h>", "<FastLED.h>"],
        "additional_defines": """
// WiFi Configuration
const char *ssid = "PC-Matrix";
const char *pass = "12345678";
AsyncWebServer server(80);""",
        "setup_code": """FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  WiFi.softAP(ssid, pass);
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();
  
  server.on("/frame", HTTP_POST,
    [](AsyncWebServerRequest *r){{}},
    NULL,
    [](AsyncWebServerRequest *r, uint8_t *data, size_t len, size_t, size_t){{
      memcpy(leds, data, min(len, sizeof(leds)));
      FastLED.show();
      r->send(200, "text/plain", "OK");
    }});
  server.begin();""",
        "loop_code": """// ESP8266 handles requests via web server callbacks
  // Main loop can be empty or used for other tasks
  delay(10);""",
        "additional_functions": """// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}

// Helper function to set individual pixels
void setPixel(uint8_t x, uint8_t y, CRGB color) {
  if (x < MATRIX_WIDTH && y < MATRIX_HEIGHT) {
    leds[XY(x, y)] = color;
  }
}""",
    },
    "mega": {
        "name": "Arduino Mega",
        "display_name": "Arduino Mega 2560",
        "voltage": "5V",
        "default_pin": 6,
        "memory_sram": 8192,  # bytes
        "memory_flash": 262144,  # bytes
        "needs_level_shifter": False,
        "max_leds_recommended": 2000,
        "baud_rate": 500000,
        "includes": ["<FastLED.h>"],
        "setup_code": """FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  Serial.begin({baud_rate});
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();""",
        "loop_code": """if (Serial.available() >= NUM_LEDS * 3) {
    for (uint16_t i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(Serial.read(), Serial.read(), Serial.read());
    }
    FastLED.show();
  }""",
        "additional_functions": """// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}

// Helper function for large matrices
void clearMatrix() {
  FastLED.clear();
  FastLED.show();
}""",
    },
}


def get_model_info(model_key):
    """Get information for a specific Arduino model"""
    return ARDUINO_MODELS.get(model_key.lower())


def get_available_models():
    """Get list of available Arduino models"""
    return list(ARDUINO_MODELS.keys())


def get_model_display_names():
    """Get dictionary of model keys to display names"""
    return {key: model["display_name"] for key, model in ARDUINO_MODELS.items()}


def validate_model(model_key):
    """Validate if a model key exists"""
    return model_key.lower() in ARDUINO_MODELS


def get_recommended_model_for_leds(num_leds):
    """Get recommended Arduino model based on LED count"""
    recommendations = []

    for key, model in ARDUINO_MODELS.items():
        if num_leds <= model["max_leds_recommended"]:
            recommendations.append(
                {
                    "key": key,
                    "name": model["display_name"],
                    "memory_efficiency": (model["memory_sram"] - (num_leds * 3))
                    / model["memory_sram"],
                    "suitable": True,
                }
            )
        else:
            recommendations.append(
                {
                    "key": key,
                    "name": model["display_name"],
                    "memory_efficiency": 0,
                    "suitable": False,
                }
            )

    # Sort by memory efficiency (higher is better)
    recommendations.sort(key=lambda x: x["memory_efficiency"], reverse=True)
    return recommendations


def calculate_power_requirements(num_leds, brightness_percent=100):
    """Calculate power requirements for LED matrix using math functions"""
    # Each WS2812B LED can draw up to 60mA at full brightness (20mA per color channel)
    max_current_per_led = 0.06  # 60mA in Amps
    voltage = 5.0  # 5V supply

    # Calculate actual current based on brightness
    brightness_factor = brightness_percent / 100.0
    actual_current_per_led = max_current_per_led * brightness_factor

    # Total current and power calculations
    total_current = num_leds * actual_current_per_led
    total_power = voltage * total_current

    # Calculate recommended PSU capacity (add 20% safety margin)
    safety_factor = 1.2
    recommended_psu_power = total_power * safety_factor

    # Use math functions for calculations
    power_watts = math.ceil(recommended_psu_power)  # Round up to nearest watt
    current_amps = math.ceil(total_current * 10) / 10  # Round up to nearest 0.1A

    return {
        "total_power_watts": power_watts,
        "total_current_amps": current_amps,
        "recommended_psu_watts": power_watts,
        "safety_margin_percent": 20,
        "brightness_factor": brightness_factor,
    }


def calculate_matrix_dimensions(num_leds):
    """Calculate optimal matrix dimensions for given LED count"""
    # Find factors of num_leds to suggest rectangular matrices
    factors = []
    sqrt_leds = int(math.sqrt(num_leds))

    for i in range(1, sqrt_leds + 1):
        if num_leds % i == 0:
            width = i
            height = num_leds // i
            aspect_ratio = max(width, height) / min(width, height)
            factors.append(
                {
                    "width": width,
                    "height": height,
                    "aspect_ratio": round(aspect_ratio, 2),
                    "is_square": width == height,
                }
            )

    # Sort by aspect ratio (closer to square is better)
    factors.sort(key=lambda x: x["aspect_ratio"])
    return factors


def calculate_memory_usage(width, height, model_key="uno"):
    """Calculate memory usage for matrix configuration"""
    num_leds = width * height
    model = get_model_info(model_key)

    if not model:
        return None

    # Calculate memory requirements
    led_array_bytes = num_leds * 3  # 3 bytes per LED (RGB)
    program_overhead = 1024  # Estimated program overhead in bytes
    available_sram = model["memory_sram"]

    # Calculate percentages using math functions
    memory_used_percent = math.ceil(
        (led_array_bytes + program_overhead) / available_sram * 100
    )
    memory_free_bytes = available_sram - led_array_bytes - program_overhead
    memory_efficiency = max(0, math.floor((memory_free_bytes / available_sram) * 100))

    return {
        "led_array_bytes": led_array_bytes,
        "program_overhead_bytes": program_overhead,
        "total_used_bytes": led_array_bytes + program_overhead,
        "available_sram_bytes": available_sram,
        "memory_used_percent": memory_used_percent,
        "memory_free_bytes": memory_free_bytes,
        "memory_efficiency_percent": memory_efficiency,
        "is_feasible": memory_used_percent < 90,  # Leave 10% safety margin
    }


def calculate_refresh_rate(num_leds, baud_rate=500000):
    """Calculate theoretical maximum refresh rate for LED matrix"""
    # Each LED requires 3 bytes (RGB), plus protocol overhead
    bytes_per_frame = num_leds * 3
    protocol_overhead = 0.1  # 10% overhead for serial protocol

    # Calculate effective data rate
    effective_baud = baud_rate * (1 - protocol_overhead)
    bytes_per_second = effective_baud / 8  # Convert bits to bytes

    # Calculate maximum FPS using math functions
    max_fps = math.floor(bytes_per_second / bytes_per_frame)
    frame_time_ms = math.ceil(1000 / max_fps) if max_fps > 0 else float("inf")

    return {
        "max_fps": max_fps,
        "frame_time_ms": frame_time_ms,
        "bytes_per_frame": bytes_per_frame,
        "effective_baud_rate": int(effective_baud),
        "is_realtime_capable": max_fps >= 30,  # 30 FPS for smooth animation
    }


def get_optimal_pin_configuration(model_key, num_parallel_strips=1):
    """Get optimal pin configuration for multi-strip setups"""
    model = get_model_info(model_key)
    if not model:
        return None

    # Calculate optimal pin spacing using math
    if model_key in ["esp32"]:
        # ESP32 has many GPIO pins, use optimal spacing
        base_pin = model["default_pin"]
        pin_spacing = max(2, math.ceil(math.log2(num_parallel_strips)))
        pins = [base_pin + (i * pin_spacing) for i in range(num_parallel_strips)]
    elif model_key in ["mega"]:
        # Arduino Mega has many digital pins
        pins = [6, 7, 8, 9, 10, 11, 12, 13][:num_parallel_strips]
    else:
        # Limited pins on Uno/Nano
        pins = [model["default_pin"]]
        if num_parallel_strips > 1:
            pins.extend([7, 8, 9][: num_parallel_strips - 1])

    return {
        "recommended_pins": pins[:num_parallel_strips],
        "max_parallel_strips": len(pins),
        "pin_spacing": pin_spacing if "pin_spacing" in locals() else 1,
        "supports_parallel": len(pins) >= num_parallel_strips,
    }
