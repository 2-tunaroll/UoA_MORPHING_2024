
void setup() {
  
  Serial.begin(9600);  // Set baud rate to match Raspberry Pi
  Serial.setTimeout(100);  // Set timeout for reading serial data
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int values[11];
    parseData(data, values);
    Serial.print("Received: ");
    for (int i = 0; i < 11; i++) {
      Serial.print(values[i]);
      Serial.print(" ");
    }
    Serial.println();
  }
}

void parseData(String data, int* values) {
  int index = 0;
  int start = 0;
  int end = data.indexOf(',');

  while (end != -1 && index < 11) {
    values[index++] = data.substring(start, end).toInt();
    start = end + 1;
    end = data.indexOf(',', start);
  }

  // Get the last value
  if (index < 11) {
    values[index] = data.substring(start).toInt();
  }
}
