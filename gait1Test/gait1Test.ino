/*******************************************************************************
* Copyright 2016 ROBOTIS CO., LTD.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/

#include <Dynamixel2Arduino.h>
#define DXL_SERIAL Serial1
#define DEBUG_SERIAL Serial
const int DXL_DIR_PIN = -1;

// SET DYNAMIXEL IDS
const uint8_t LR_WHEG= 1;
const uint8_t LM_WHEG= 2;
const uint8_t LF_WHEG= 3;
const uint8_t RR_WHEG= 4;
const uint8_t RM_WHEG= 5;
const uint8_t RF_WHEG= 6;
const uint8_t FRONT_PIVOT= 7;
const uint8_t REAR_PIVOT= 8;
const float DXL_PROTOCOL_VERSION = 2.0;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

//This namespace is required to use Control table item names
using namespace ControlTableItem;

void setup() {
  // put your setup code here, to run once:
  
  // Use UART port of DYNAMIXEL Shield to debug.
  DEBUG_SERIAL.begin(115200);
  
  // Set Port baudrate to 57600bps. This has to match with DYNAMIXEL baudrate.
  dxl.begin(57600);
  // Set Port Protocol Version. This has to match with DYNAMIXEL protocol version.
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  // Get DYNAMIXEL information
  dxl.ping(LR_WHEG);
  dxl.ping(LM_WHEG);
  dxl.ping(LF_WHEG);
  dxl.ping(RR_WHEG);
  dxl.ping(RM_WHEG);
  dxl.ping(RF_WHEG);
  dxl.ping(FRONT_PIVOT);
  dxl.ping(REAR_PIVOT);

  // Turn off torque when configuring items in EEPROM area
  dxl.torqueOff(LR_WHEG);
  dxl.torqueOff(LM_WHEG);
  dxl.torqueOff(LF_WHEG);
  dxl.torqueOff(RR_WHEG);
  dxl.torqueOff(RM_WHEG);
  dxl.torqueOff(RF_WHEG);
  dxl.torqueOff(FRONT_PIVOT);
  dxl.torqueOff(REAR_PIVOT);

  // Set operating mode
  dxl.setOperatingMode(LR_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(LM_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(LF_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(RR_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(RM_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(RF_WHEG, OP_VELOCITY);
  dxl.setOperatingMode(FRONT_PIVOT, OP_POSITION);
  dxl.setOperatingMode(REAR_PIVOT, OP_POSITION);

  // Turn Whegs on
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
  // put your main code here, to run repeatedly:
  
  // Please refer to e-Manual(http://emanual.robotis.com) for available range of value.   
  int RPM=-5;

  dxl.setGoalPosition(FRONT_PIVOT, 180, UNIT_DEGREE);
  dxl.setGoalPosition(REAR_PIVOT, 180, UNIT_DEGREE);

  // Set Goal Velocity using RPM
  dxl.setGoalVelocity(LR_WHEG, RPM, UNIT_RPM);
  dxl.setGoalVelocity(LM_WHEG, RPM, UNIT_RPM);
  dxl.setGoalVelocity(LF_WHEG, RPM, UNIT_RPM);
  dxl.setGoalVelocity(RR_WHEG, RPM, UNIT_RPM);
  dxl.setGoalVelocity(RM_WHEG, RPM, UNIT_RPM);
  dxl.setGoalVelocity(RF_WHEG, RPM, UNIT_RPM);

  for (int i=0; i<10; i++){
    //DEBUG_SERIAL.println(dxl.getPresentPosition(LR_WHEG, UNIT_DEGREE));
    delay(500);
  }
  //DEBUG_SERIAL.println(dxl.getPresentPosition(REAR_PIVOT, UNIT_DEGREE));



  dxl.setGoalVelocity(LR_WHEG, 0, UNIT_RPM);
  dxl.setGoalVelocity(LM_WHEG, 0, UNIT_RPM);
  dxl.setGoalVelocity(LF_WHEG, 0, UNIT_RPM);
  dxl.setGoalVelocity(RR_WHEG, 0, UNIT_RPM);
  dxl.setGoalVelocity(RM_WHEG, 0, UNIT_RPM);
  dxl.setGoalVelocity(RF_WHEG, 0, UNIT_RPM);
  delay(6000);

//Ronan done something here

}
