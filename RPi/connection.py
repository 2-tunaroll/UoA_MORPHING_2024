from dynamixel_sdk import *  # Uses Dynamixel SDK library
import time

# Control table addresses for XL430 and XC330 motors
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
ADDR_OPERATING_MODE = 11
ADDR_GOAL_VELOCITY = 104

# Control constants
OP_VELOCITY = 1
OP_POSITION = 3

# Protocol version
PROTOCOL_VERSION = 2.0  # For Dynamixel X-Series motors

# Motor IDs
LR_WHEG = 1
LM_WHEG = 2
LF_WHEG = 3
RR_WHEG = 4
RM_WHEG = 5
RF_WHEG = 6
FRONT_PIVOT = 7
REAR_PIVOT = 8

# Baudrate and device
BAUDRATE = 57600
DEVICENAME = '/dev/ttyACM0'  # Adjust as needed

# Initialize PortHandler and PacketHandler instances
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port
if portHandler.openPort():
    print("Succeeded in opening the port.")
else:
    print("Failed to open the port.")
    quit()

# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded in setting the baudrate.")
else:
    print("Failed to set the baudrate.")
    quit()

# Enable torque and set operating mode for each motor
def set_motor_operating_mode(motor_id, mode):
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_OPERATING_MODE, mode)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Failed to set operating mode for motor {motor_id}: {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"Error setting operating mode for motor {motor_id}: {packetHandler.getRxPacketError(dxl_error)}")
    else:
        print(f"Operating mode set for motor {motor_id}")

def enable_torque(motor_id):
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_TORQUE_ENABLE, 1)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Failed to enable torque for motor {motor_id}: {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"Error enabling torque for motor {motor_id}: {packetHandler.getRxPacketError(dxl_error)}")
    else:
        print(f"Torque enabled for motor {motor_id}")

# Set motor modes
for motor_id in [LR_WHEG, LM_WHEG, LF_WHEG, RR_WHEG, RM_WHEG, RF_WHEG]:
    set_motor_operating_mode(motor_id, OP_VELOCITY)
for motor_id in [FRONT_PIVOT, REAR_PIVOT]:
    set_motor_operating_mode(motor_id, OP_POSITION)

# Enable torque for all motors
for motor_id in [LR_WHEG, LM_WHEG, LF_WHEG, RR_WHEG, RM_WHEG, RF_WHEG, FRONT_PIVOT, REAR_PIVOT]:
    enable_torque(motor_id)

# Set goal positions and velocities
def set_goal_position(motor_id, position):
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, motor_id, ADDR_GOAL_POSITION, position)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Failed to set goal position for motor {motor_id}: {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"Error setting goal position for motor {motor_id}: {packetHandler.getRxPacketError(dxl_error)}")

def set_goal_velocity(motor_id, velocity):
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, motor_id, ADDR_GOAL_VELOCITY, velocity)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Failed to set goal velocity for motor {motor_id}: {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"Error setting goal velocity for motor {motor_id}: {packetHandler.getRxPacketError(dxl_error)}")

# Example: Set pivot positions to 180 degrees and wheg velocities to -5 RPM
set_goal_position(FRONT_PIVOT, 2048)  # 180 degrees
set_goal_position(REAR_PIVOT, 2048)  # 180 degrees
for motor_id in [LR_WHEG, LM_WHEG, LF_WHEG, RR_WHEG, RM_WHEG, RF_WHEG]:
    set_goal_velocity(motor_id, -5)  # -5 RPM

time.sleep(2)

# Close port when done
portHandler.closePort()
