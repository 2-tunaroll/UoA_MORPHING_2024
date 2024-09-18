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

// Dynamixel controller instance
Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

void setup() {
  // Start serial communication
  DEBUG_SERIAL.begin(115200);  // For debugging
  DXL_SERIAL.begin(57600);     // Dynamixel baud rate

  // Initialize the Dynamixel controller
  dxl.begin(57600);  // Must match with DYNAMIXEL baud rate
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  // Set operating mode for motors
  dxl.setOperatingMode(LR_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(LM_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(LF_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(RR_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(RM_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(RF_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(FRONT_PIVOT, OP_POSITION);
  dxl.setOperatingMode(REAR_PIVOT, OP_POSITION);

  // Enable torque for all motors
  enableAllMotors();
}

void enableAllMotors() {
  dxl.torqueOn(LR_WHEG);
  dxl.torqueOn(LM_WHEG);
  dxl.torqueOn(LF_WHEG);
  dxl.torqueOn(RR_WHEG);
  dxl.torqueOn(RM_WHEG);
  dxl.torqueOn(RF_WHEG);
  dxl.torqueOn(FRONT_PIVOT);
  dxl.torqueOn(REAR_PIVOT);
}

void loop() {
  // Check if data is available from the Raspberry Pi
  if (DXL_SERIAL.available()) {
    // Read motor ID, command type, and value from the serial buffer
    uint8_t motor_id = DXL_SERIAL.read();      // Motor ID
    uint8_t command_type = DXL_SERIAL.read();  // Command type (1: position, 2: velocity)
    int value = DXL_SERIAL.parseInt();         // Value (e.g., position or velocity)

    // Perform the appropriate action
    if (command_type == 1) {
      // Set goal position
      setMotorPosition(motor_id, value);
    } else if (command_type == 2) {
      // Set goal velocity
      setMotorVelocity(motor_id, value);
    }
  }
}

void setMotorPosition(uint8_t motor_id, int position) {
  dxl.setGoalPosition(motor_id, position, UNIT_DEGREE);  // Position in degrees
  DEBUG_SERIAL.print("Motor ID: ");
  DEBUG_SERIAL.print(motor_id);
  DEBUG_SERIAL.print(" set to position: ");
  DEBUG_SERIAL.println(position);
}

void setMotorVelocity(uint8_t motor_id, int velocity) {
  dxl.setGoalVelocity(motor_id, velocity, UNIT_RPM);  // Velocity in RPM
  DEBUG_SERIAL.print("Motor ID: ");
  DEBUG_SERIAL.print(motor_id);
  DEBUG_SERIAL.print(" set to velocity: ");
  DEBUG_SERIAL.println(velocity);
}