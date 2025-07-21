/*
 * LED Matrix Controller for Arduino Uno
 * Generated on: 2025-07-20 14:49:36
 * 
 * Matrix Configuration:
 * - Size: 16×16 = 256 LEDs
 * - Data Pin: 6
 * - Brightness: 128/255
 * - Controller: Arduino Uno (5V)
 * - Level Shifter Required: No
 * 
 * Memory Usage Estimate:
 * - LED Array: 768 bytes
 * - Available SRAM: 2048 bytes
 * - Memory Efficiency: 62.5%
 */

#include <FastLED.h>
// Matrix Configuration - Update these values for your setup
#define MATRIX_WIDTH 16
#define MATRIX_HEIGHT 16
#define NUM_LEDS (MATRIX_WIDTH * MATRIX_HEIGHT)  // 256 LEDs
#define DATA_PIN 6
#define BRIGHTNESS 128

CRGB leds[NUM_LEDS];
void setup() {
  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  Serial.begin(500000);
  
  // Clear all LEDs on startup
  FastLED.clear();
  FastLED.show();
}// XY coordinate mapping (serpentine wiring pattern)
uint16_t XY(byte x, byte y) {
  return (y & 1) ? (y * MATRIX_WIDTH + (MATRIX_WIDTH - 1 - x)) : (y * MATRIX_WIDTH + x);
}
void loop() {
  if (Serial.available() >= NUM_LEDS * 3) {
    for (uint16_t i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(Serial.read(), Serial.read(), Serial.read());
    }
    FastLED.show();
  }
}