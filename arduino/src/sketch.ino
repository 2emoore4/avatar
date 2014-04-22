void setup() {
    Serial.begin(9600);
}

char incoming_char = -1;
int timer;

void loop() {
    if (Serial.available() > 0) {
        incoming_char = Serial.read();

        switch (incoming_char) {
        case 'c':
            delay(5);
            Serial.print("y");
            break;
        }
    }
}
