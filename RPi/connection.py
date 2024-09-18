from dynamixel_sdk import *  # Uses Dynamixel SDK library
import time

# Control table addresses
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

# Protocol version (2.0 for X-series motors like XL430 and XC330)
PROTOCOL_VERSION = 2.0

# Default settings
DXL_ID = 254  # Broadcast ID to test if communication works
BAUDRATE = 57600  # Try 57600 or 1000000
DEVICENAME = '/dev/ttyACM0'  # Adjust if needed, e.g., /dev/ttyUSB0

TORQUE_ENABLE = 1  # Value for enabling torque
TORQUE_DISABLE = 0  # Value for disabling torque
DXL_MIN_POSITION = 0  # Min position value
DXL_MAX_POSITION = 4095  # Max position value

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
