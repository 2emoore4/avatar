#define LED_N 2
#define LED_P 3

void setup() {
    Serial.begin(9600);
}

void loop() {
    //Serial.println(read_light());
    Serial.print("a");
    Serial.print("b");
    Serial.print("c");
}

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
