/**
 * Control the pump over serial using 'a' - 'z' letters.
 * Wait for a '*' as the sync byte.
 */
#include "TimerOne.h"

const int PIN_PUMP_PWM = 9;
const int PIN_LED_R_PWM = 6;
const int PIN_LED_G_PWM = 5;
const int PIN_LED_B_PWM = 3;

int letter_val = 0; // [0, 25]
int pump_power = 0; // [0, 1024]
int led_r_val = 0;  // [0, 255]
int led_g_val = 0;  // [0, 255]
int led_b_val = 0;  // [0, 255]

void setup() {
  Serial.begin(9600);
  Serial.println("Hello.");
  pinMode(PIN_PUMP_PWM, OUTPUT);
  Timer1.initialize(20);
  set_pump(0);
}

void loop() {
  Serial.println(pump_power);
  wait_for_sync();
  read_letter_blocking(&letter_val);
  pump_power = map(letter_val, 0, 25, 0, 1024);
  read_letter_blocking(&letter_val);
  led_r_val = map(letter_val, 0, 25, 0, 255);
  read_letter_blocking(&letter_val);
  led_g_val = map(letter_val, 0, 25, 0, 255);
  read_letter_blocking(&letter_val);
  led_b_val = map(letter_val, 0, 25, 0, 255);

  // set stuff
  set_pump(pump_power);
  set_led(PIN_LED_R_PWM, led_r_val);
  set_led(PIN_LED_G_PWM, led_g_val);
  set_led(PIN_LED_B_PWM, led_b_val);
  delay(10);
}

// Set an led brightness.
// takes number in [0, 255]
void set_led(int pin, int brightness) {
  int pwm_val = 255 - brightness;
  analogWrite(pin, pwm_val);
}

// Set the pump power.
// takes number in [0, 1024]
void set_pump(int power) {
  int pwm_val = 1024 - power;
  Timer1.pwm(PIN_PUMP_PWM, 1024 - power);
}

// Read a letter a-z from serial.
// If there is nothing in the serial queue, this is a no-op.
// If there is something to read, read it and ignore if not a letter.
// Place the new value in val.
void read_letter(int *val) {
  if (Serial.available()) {
    int inByte = Serial.read();
    if ('a' <= inByte && inByte <= 'z') {
      *val = inByte - (int) 'a';
    }
  }
}

// Same as read_letter
// But blocks until a char is available.
void read_letter_blocking(int *val) {
  while (!Serial.available()) {}

  int inByte = Serial.read();
  if ('a' <= inByte && inByte <= 'z') {
    *val = inByte - (int) 'a';
  }
}

// Block until a '*' is received
void wait_for_sync() {
  int inByte;
  while (true) {
    while (!Serial.available()) {}

    inByte = Serial.read();
    if (inByte == '*') {
      return;
    }
  }
}
