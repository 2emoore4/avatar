#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"

#define LED_N 3
#define TEMP A3
#define DIST A0
#define POT A2

// manually defining packet size to avoid packet format mismatch
#define PACKET_SIZE 4

// IMU device, with related fields and methods
MPU6050 mpu;
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

Quaternion q;           // [w, x, y, z]         quaternion container
float euler[3];         // [psi, theta, phi]    Euler angle container

volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high
void dmpDataReady() {
    mpuInterrupt = true;
}

// kalman filter weights (actual_variance / (actual_variance + sensor_variance))
float temp_actual_var = 11.0;
float temp_sensor_var = 2.0;
float temp_weight = temp_actual_var / (temp_actual_var + temp_sensor_var);
float light_actual_var = 600.0;
float light_sensor_var = 15.0;
float light_weight = light_actual_var / (light_actual_var + light_sensor_var);
float dist_actual_var = 2000.0;
float dist_sensor_var = 100.0;
float dist_weight = dist_actual_var / (dist_actual_var + dist_sensor_var);

// kalman filter guesses (these could be tweaked)
int temp_guess = 20;
int light_guess = 150;
int dist_guess = 230;

int led_start;
int led_elapsed = 0;

void setup() {
    Serial.begin(115200);

    init_led();
//    init_imu();
}

void loop() {
    // just testing python client for now
    int messages[] = {read_light(), read_temp(), read_distance(), read_pot()};
    send_packet(messages);

    Serial.println("");
//    read_imu();
}

// send packet containing int messages
// message example "a2 23 46 "
// "a" start of packet
// "2" number of messages contained in packet
// "23"/"46" int messages
// delimited by spaces
void send_packet(int messages[]) {
    Serial.print("a");
    Serial.print(PACKET_SIZE);
    Serial.print(" ");

    for (int i = 0; i < PACKET_SIZE; i++) {
        Serial.print(messages[i]);
        Serial.print(" ");
    }
}

// apply charge to led then remove charge
void init_led() {
    // charge LED pin and start timer
    pinMode(LED_N, OUTPUT);
    digitalWrite(LED_N, HIGH);
    led_start = millis();

    // remove charge
    pinMode(LED_N, INPUT);
    digitalWrite(LED_N, LOW);
}

// if LED is discharged, then record discharge time and reset
// return most recently recorded discharge time
int read_light() {
    // LED is fully discharged
    if (digitalRead(LED_N) == 0) {
        led_elapsed = millis() - led_start;

        pinMode(LED_N, OUTPUT);
        digitalWrite(LED_N, HIGH);
        led_start = millis();

        pinMode(LED_N, INPUT);
        digitalWrite(LED_N, LOW);
    }

    // kalman filter stuff happens here
    float estimate = (1 - light_weight) * light_guess + light_weight * led_elapsed;
    float est_variance = (light_actual_var * light_sensor_var) / (light_actual_var + light_sensor_var);

    light_weight = est_variance / (est_variance + light_sensor_var);

    // cast to int for now
    return estimate;
}

// read sensor, convert to millivolts (reading * 4.9 mv/unit)
// convert millivolts to degrees celsius and return
int read_temp() {
    pinMode(TEMP, INPUT);
    float millivolts = analogRead(TEMP) * 4.9;
    float degrees_celsius = (millivolts - 500) / 10.0;

    // kalman filter stuff happens here
    float estimate = (1 - temp_weight) * temp_guess + temp_weight * degrees_celsius;
    float est_variance = (temp_actual_var * temp_sensor_var) / (temp_actual_var + temp_sensor_var);

    temp_weight = est_variance / (est_variance + temp_sensor_var);

    // cast to int for now
    return (int) estimate;
}

// read value from range sensor
int read_distance() {
    pinMode(DIST, INPUT);
    float millivolts = analogRead(DIST) * 4.9;

    // kalman filter stuff happens here
    float estimate = (1 - dist_weight) * dist_guess + dist_weight * millivolts;
    float est_variance = (dist_actual_var * dist_sensor_var) / (dist_actual_var + dist_sensor_var);

    dist_weight = est_variance / (est_variance + dist_sensor_var);

    // cast to int for now
    return (int) estimate;
}

// read value from potentiometer
int read_pot() {
    pinMode(POT, INPUT);
    return analogRead(POT);
}

// IMU initialization
int init_imu() {
    Wire.begin();
    while (!Serial);

    // initialize device
    Serial.println(F("Initializing I2C devices..."));
    mpu.initialize();

    // verify connection
    Serial.println(F("Testing device connections..."));
    Serial.println(mpu.testConnection() ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));

    // wait for ready
    Serial.println(F("\nSend any character to begin DMP programming and demo: "));
    while (Serial.available() && Serial.read()); // empty buffer

    // load and configure the DMP
    Serial.println(F("Initializing DMP..."));
    devStatus = mpu.dmpInitialize();

    // make sure it worked (returns 0 if so)
    if (devStatus == 0) {
        // turn on the DMP, now that it's ready
        Serial.println(F("Enabling DMP..."));
        mpu.setDMPEnabled(true);

        // enable Arduino interrupt detection
        Serial.println(F("Enabling interrupt detection (Arduino external interrupt 0)..."));
        attachInterrupt(0, dmpDataReady, RISING);
        mpuIntStatus = mpu.getIntStatus();

        // set our DMP Ready flag so the main loop() function knows it's okay to use it
        Serial.println(F("DMP ready! Waiting for first interrupt..."));
        dmpReady = true;

        // get expected DMP packet size for later comparison
        packetSize = mpu.dmpGetFIFOPacketSize();

        return 1;
    } else {
        // ERROR!
        // 1 = initial memory load failed
        // 2 = DMP configuration updates failed
        // (if it's going to break, usually the code will be 1)
        Serial.print(F("DMP Initialization failed (code "));
        Serial.print(devStatus);
        Serial.println(F(")"));
        return 0;
    }
}

int read_imu() {
    // if programming failed, don't try to do anything
    if (!dmpReady) return 0;

    // wait for MPU interrupt or extra packet(s) available
    while (!mpuInterrupt && fifoCount < packetSize) {

    }

    // reset interrupt flag and get INT_STATUS byte
    mpuInterrupt = false;
    mpuIntStatus = mpu.getIntStatus();

    // get current FIFO count
    fifoCount = mpu.getFIFOCount();

    // check for overflow (this should never happen unless our code is too inefficient)
    if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
        // reset so we can continue cleanly
        mpu.resetFIFO();
        Serial.println(F("FIFO overflow!"));

    // otherwise, check for DMP data ready interrupt (this should happen frequently)
    } else if (mpuIntStatus & 0x02) {
        // wait for correct available data length, should be a VERY short wait
        while (fifoCount < packetSize) fifoCount = mpu.getFIFOCount();

        // read a packet from FIFO
        mpu.getFIFOBytes(fifoBuffer, packetSize);

        // track FIFO count here in case there is > 1 packet available
        // (this lets us immediately read more without waiting for an interrupt)
        fifoCount -= packetSize;

        // display Euler angles in degrees
        mpu.dmpGetQuaternion(&q, fifoBuffer);
        mpu.dmpGetEuler(euler, &q);
        Serial.print(euler[0] * 180/M_PI);
        Serial.print("\t");
        Serial.print(euler[1] * 180/M_PI);
        Serial.print("\t");
        Serial.println(euler[2] * 180/M_PI);
    }

    return 1;
}
