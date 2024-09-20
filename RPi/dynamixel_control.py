from dynamixel_sdk import *  # Uses Dynamixel SDK library

class DynamixelController:
    def __init__(self, device_name, baudrate, protocol_version=2.0):
        self.port_handler = PortHandler(device_name)
        self.packet_handler = PacketHandler(protocol_version)

        # Open the port
        if not self.port_handler.openPort():
            raise Exception("Failed to open the port")

        # Set baudrate
        if not self.port_handler.setBaudRate(baudrate):
            raise Exception("Failed to set baudrate")

    def set_operating_mode(self, motor_id, mode):
        """
        Set the operating mode of the motor. 
        Available modes: 'position', 'velocity'
        """
        OPERATING_MODE_ADDR = 11  # Address for operating mode in Control Table
        OPERATING_MODES = {
            'position': 3,  # Operating mode value for position control
            'velocity': 1   # Operating mode value for velocity control
        }

        if mode not in OPERATING_MODES:
            raise ValueError(f"Invalid operating mode: {mode}")

        mode_value = OPERATING_MODES[mode]
        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR, mode_value)
        if result != COMM_SUCCESS:
            print(f"Failed to set operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            print(f"Error setting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def torque_on(self, motor_id):
        """Enable the torque on a motor."""
        TORQUE_ENABLE_ADDR = 64  # Torque enable address in the Control Table
        TORQUE_ENABLE = 1

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE_ADDR, TORQUE_ENABLE)
        if result != COMM_SUCCESS:
            print(f"Failed to enable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            print(f"Error enabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def torque_off(self, motor_id):
        """Disable the torque on a motor."""
        TORQUE_ENABLE_ADDR = 64  # Torque enable address in the Control Table
        TORQUE_DISABLE = 0

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE_ADDR, TORQUE_DISABLE)
        if result != COMM_SUCCESS:
            print(f"Failed to disable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            print(f"Error disabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def set_goal_velocity(self, motor_id, velocity):
        """Set the velocity goal for a motor."""
        VELOCITY_GOAL_ADDR = 104  # Velocity goal address in Control Table

        # Convert velocity to the appropriate value (sign handling for forward/reverse)
        velocity_value = int(velocity)  # Ensure the value is an integer

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, VELOCITY_GOAL_ADDR, velocity_value)
        if result != COMM_SUCCESS:
            print(f"Failed to set goal velocity for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            print(f"Error setting goal velocity for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def set_goal_position(self, motor_id, position):
        """Set the goal position for a motor."""
        """Ensure motors are set to position control mode before using this function."""
        self.set_operating_mode(motor_id, 'position') #Change to position control mode

        POSITION_GOAL_ADDR = 116  # Position goal address in Control Table

        position_value = int(position)  # Ensure the position value is an integer
        position_value = int((position_value / 360) * 4096)   # Convert position value from degrees to encoder ticks
        position_value = position_value % 4096 # Ensure the position value is within 0-4095 ticks

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, POSITION_GOAL_ADDR, position_value)
        if result != COMM_SUCCESS:
            print(f"Failed to set goal position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            print(f"Error setting goal position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        print("Goal position", position, "position set for motor", motor_id)

    def get_present_position(self, motor_id):
        """Get the current position of the motor."""
        PRESENT_POSITION_ADDR = 132  # Present position address in Control Table

        position, result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, PRESENT_POSITION_ADDR)
        if result != COMM_SUCCESS:
            print(f"Failed to get position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            print(f"Error getting position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

        position = int((position / 4096) * 360) # Convert from encoder ticks to degrees
        position = position % 360 # Ensure the position is within 0-359 degrees

        return position

    def close(self):
        """Close the port and clean up resources."""
        self.port_handler.closePort()
