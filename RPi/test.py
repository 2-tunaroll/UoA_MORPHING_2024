from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Motor IDs (Based on your working Arduino setup)
motor_ids = [1, 2, 3, 4, 5, 6, 7, 8]

# Control table addresses
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
ADDR_OPERATING_MODE = 11
ADDR_GOAL_VELOCITY = 104

# Protocol version
PROTOCOL_VERSION = 2.0  # For Dynamixel X-Series motors

# Baudrate and device
BAUDRATE = 57600  # Assuming this is correct based on Arduino setup
DEVICENAME = '/dev/ttyACM0'  # Serial port for OpenRB 150

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
    print(f"Succeeded in setting the baudrate to {BAUDRATE}.")
else:
    print(f"Failed to set the baudrate to {BAUDRATE}.")
    quit()

# Ping each motor and display the result
for motor_id in motor_ids:
    try:
        model_number, dxl_comm_result, dxl_error = packetHandler.pingGetModelNum(portHandler, motor_id)
        if dxl_comm_result == COMM_SUCCESS:
            print(f"Motor {motor_id} responded successfully. Model Number: {model_number}")
        elif dxl_error != 0:
            print(f"Error pinging motor {motor_id}: {packetHandler.getRxPacketError(dxl_error)}")
        else:
            print(f"Failed to ping motor {motor_id}: {packetHandler.getTxRxResult(dxl_comm_result)}")
    except Exception as e:
        print(f"EXCEPTION: Could not ping motor {motor_id} - {e}")

# Close port when done
portHandler.closePort()
