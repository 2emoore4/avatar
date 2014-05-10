#define LED_N 3
#define LED_P 2
#define TEMP A0

// manually defining packet size to avoid packet format mismatch
#define PACKET_SIZE 2

void setup() {
    Serial.begin(9600);
}

void loop() {
    // just testing python client for now
    int messages[] = {read_light(), read_temp()};
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

    return j;
}

// read sensor, convert to millivolts (reading * 4.9 mv/unit)
// convert millivolts to degrees celsius and return
int read_temp() {
    pinMode(TEMP, INPUT);
    int millivolts = analogRead(TEMP) * 4.9;
    return (millivolts - 500) / 10;
}
