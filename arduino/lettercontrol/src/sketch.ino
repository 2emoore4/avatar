/**
 * Control the pump over serial using 'a' - 'z' letters.
 */
#include "TimerOne.h"

const int PIN_PUMP_PWM = 9;
int pump_power = 0; // [0, 1024]
int letter_val = 0; // [0, 25]

void setup() {
  Serial.begin(9600);
  // Serial.println("Hello.");
  pinMode(PIN_PUMP_PWM, OUTPUT);
  Timer1.initialize(20);
}

void loop() {
  // Serial.println(pump_power);
  read_letter(&letter_val);
  pump_power = map(letter_val, 0, 25, 0, 1024);
  set_pump(pump_power);
  delay(10);
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
