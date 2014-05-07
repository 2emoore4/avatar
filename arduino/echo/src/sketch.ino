int val = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println(val);
  read_letter(&val);
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
