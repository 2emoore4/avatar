#define LED_N 2
#define LED_P 3

void setup() {
    Serial.begin(9600);
}

void loop() {
    // just testing python client for now
    int messages[] = {read_light(), 33, 46};
    send_packet(messages);
}

// send packet containing int messages
// message example "a2 23 46 "
// "a" start of packet
// "2" number of messages contained in packet
// "23"/"46" int messages
// delimited by spaces
void send_packet(int messages[]) {
    int packet_size = sizeof(messages) + 1;
    Serial.print("a");
    Serial.print(packet_size);
    Serial.print(" ");

    for (int i = 0; i < packet_size; i++) {
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
