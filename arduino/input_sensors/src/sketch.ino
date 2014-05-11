#define LED_N 3
#define LED_P 2
#define TEMP A5
#define DIST A0

// manually defining packet size to avoid packet format mismatch
#define PACKET_SIZE 3

// kalman filter weights (actual_variance / (actual_variance + sensor_variance))
float temp_actual_var = 11.0;
float temp_sensor_var = 2.0;
float temp_weight = temp_actual_var / (temp_actual_var + temp_sensor_var);
float light_actual_var = 370.0;
float light_sensor_var = 2.0;
float light_weight = light_actual_var / (light_actual_var + light_sensor_var);
float dist_actual_var = 2000.0;
float dist_sensor_var = 100.0;
float dist_weight = dist_actual_var / (dist_actual_var + dist_sensor_var);

// kalman filter guesses (these could be tweaked)
int temp_guess = 20;
int light_guess = 20;
int dist_guess = 230;

void setup() {
    Serial.begin(9600);
}

void loop() {
    // just testing python client for now
    int messages[] = {read_light(), read_temp(), read_distance()};
    send_packet(messages);
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

// charge LED, then reverse voltage and measure time until complete discharge
// this process takes some time (tens/hundreds of ms) but not a big deal.
int read_light() {
    unsigned int j;

    pinMode(LED_N, OUTPUT);
    pinMode(LED_P, OUTPUT);
    digitalWrite(LED_N, HIGH);
    digitalWrite(LED_P, LOW);

    pinMode(LED_N, INPUT);
    digitalWrite(LED_N, LOW);

    for (j = 0; j < 3000; j++) {
        if (digitalRead(LED_N) == 0) break;
        delay(10);
    }

    // kalman filter stuff happens here
    float estimate = (1 - light_weight) * light_guess + light_weight * j;
    float est_variance = (light_actual_var * light_sensor_var) / (light_actual_var + light_sensor_var);

    light_weight = est_variance / (est_variance + light_sensor_var);

    // cast to int for now
    return (int) estimate;
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
