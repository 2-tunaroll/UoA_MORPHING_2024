#include <Dynamixel2Arduino.h>

#define DXL_SERIAL Serial1  // Use Serial1 for the OpenRB-150
#define DEBUG_SERIAL Serial  // Use Serial for debugging
const int DXL_DIR_PIN = -1;  // Direction pin not used

// Motor IDs and control parameters
const uint8_t LR_WHEG = 1;
const uint8_t LM_WHEG = 2;
const uint8_t LF_WHEG = 3;
const uint8_t RR_WHEG = 4;
const uint8_t RM_WHEG = 5;
const uint8_t RF_WHEG = 6;
const uint8_t FRONT_PIVOT = 7;
const uint8_t REAR_PIVOT = 8;
const float DXL_PROTOCOL_VERSION = 2.0;

void setup() {
  Serial.begin(115200);  // For debugging
  Serial2.begin(57600);  // Use Serial2 for communication with Raspberry Pi
}

void loop() {
  if (Serial2.available()) {
    int incomingByte = Serial2.read();
    Serial.print("I received: ");
    Serial.println(incomingByte, DEC);
  } else {
    Serial.println("DEBUG: No data available on Serial2.");
  }
  delay(500);
}
