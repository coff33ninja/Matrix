/*
 * LED Matrix Controller for ESP32 Dev Board
 * Generated on: 2025-07-20 14:50:15
 * 
 * Matrix Configuration:
 * - Size: 32×32 = 1024 LEDs
 * - Data Pin: 13
 * - Brightness: 128/255
 * - Controller: ESP32 Dev Board (3.3V)
 * - Level Shifter Required: Yes
 * 
 * Memory Usage Estimate:
 * - LED Array: 3072 bytes
 * - Available SRAM: 520000 bytes
 * - Memory Efficiency: 99.4%
 */

#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <FastLED.h>
// Matrix Configuration - Update these values for your setup
#define MATRIX_WIDTH 32
#define MATRIX_HEIGHT 32
#define NUM_LEDS (MATRIX_WIDTH * MATRIX_HEIGHT)  // 1024 LEDs
#define DATA_PIN 13
#define BRIGHTNESS 128

CRGB leds[NUM_LEDS];
// WiFi Configuration
const char *ssid = "PC-Matrix";
const char *pass = "12345678";
AsyncWebServer server(80);
void setup() {
  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  WiFi.softAP(ssid, pass);
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();
  
  server.on("/frame", HTTP_POST,
    [](AsyncWebServerRequest *r){},
    NULL,
    [](AsyncWebServerRequest *r, uint8_t *data, size_t len, size_t, size_t){
      memcpy(leds, data, min(len, sizeof(leds)));
      FastLED.show();
      r->send(200, "text/plain", "OK");
    });
  server.begin();
}// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}

// Helper function to set individual pixels
void setPixel(uint8_t x, uint8_t y, CRGB color) {
  if (x < MATRIX_WIDTH && y < MATRIX_HEIGHT) {
    leds[XY(x, y)] = color;
  }
}
void loop() {
  // ESP32 handles requests via web server callbacks
  // Main loop can be empty or used for other tasks
  delay(10);
}