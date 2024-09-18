import time
from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Control table addresses
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

# Protocol version
PROTOCOL_VERSION = 2.0  # For Dynamixel X-Series (MX, AX, etc.)

# Default settings
DXL_ID = 1  # ID of your Dynamixel (update if using a different ID)
BAUDRATE =  9600  # Baudrate for your motor
DEVICENAME = '/dev/ttyACM0'  # Port to which your Open RB 150 is connected (update if different)

TORQUE_ENABLE = 1  # Value for enabling torque
TORQUE_DISABLE = 0  # Value for disabling torque
XL430_MIN_POSITION = 1024  # 90 degrees for hinge motor
XL430_MAX_POSITION = 3072  # 270 degrees for hinge motor
DXL_MIN_POSITION = 0  # 0 degrees for servo motor
DXL_MAX_POSITION = 4095  # 360 degrees for servo motor


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

# Enable Dynamixel torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
if dxl_comm_result != COMM_SUCCESS:
    print(f"Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
elif dxl_error != 0:
    print(f"Error: {packetHandler.getRxPacketError(dxl_error)}")
else:
    print("Torque enabled for Dynamixel.")

# Move motor between two positions
for goal_position in [DXL_MIN_POSITION, DXL_MAX_POSITION]:
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"Error: {packetHandler.getRxPacketError(dxl_error)}")
    else:
        print(f"Goal position {goal_position} sent successfully.")
    
    time.sleep(2)

# Disable Dynamixel torque when done
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
if dxl_comm_result != COMM_SUCCESS:
    print(f"Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
elif dxl_error != 0:
    print(f"Error: {packetHandler.getRxPacketError(dxl_error)}")
else:
    print("Torque disabled.")

# Close port
portHandler.closePort()