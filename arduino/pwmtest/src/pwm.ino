#include "TimerOne.h"

const int PIN_PWM = 9;
int pwm_val = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("Hello.");
  pinMode(PIN_PWM, OUTPUT);
  Timer1.initialize(10);
}

void loop() {
  Serial.println(pwm_val);
  Timer1.pwm(PIN_PWM, pwm_val);
  delay(10);

  pwm_val += 1;
  if (pwm_val == 1024)
    pwm_val = 0;
}
