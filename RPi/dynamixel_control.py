from dynamixel_sdk import *  # Uses Dynamixel SDK library
import logging

class DynamixelController:
    def __init__(self, device_name, baudrate, protocol_version=2.0):
        self.port_handler = PortHandler(device_name)
        self.packet_handler = PacketHandler(protocol_version)

        # Open the port
        if not self.port_handler.openPort():
            logging.error("Failed to open the port")
            raise Exception("Failed to open the port")
        logging.info(f"Port {device_name} opened successfully")

        # Set baudrate
        if not self.port_handler.setBaudRate(baudrate):
            logging.error("Failed to set baudrate")
            raise Exception("Failed to set baudrate")
        logging.info(f"Baudrate set to {baudrate}")

        self.motor_groups = {}  # Dictionary to store motor groups

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
            logging.error(f"Invalid operating mode: {mode}")
            raise ValueError(f"Invalid operating mode: {mode}")

        mode_value = OPERATING_MODES[mode]
        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR, mode_value)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error setting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        logging.info(f"Operating mode set to {mode} for motor {motor_id}")
    
    def check_operating_mode(self, motor_id):
        """
        Check the operating mode of the motor.
        Returns the operating mode as a string.
        Available modes: 'position', 'velocity'
        """
        OPERATING_MODE_ADDR = 11
        operating_mode, result, error = self.packet_handler.read1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to get operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error getting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        if operating_mode == 3:
            operating_mode = 'position'
        elif operating_mode == 1:
            operating_mode = 'velocity'
        logging.info(f"Operating mode for motor {motor_id} is {operating_mode}")
        return operating_mode
    
    def torque_on(self, motor_id):
        """Enable the torque on a motor."""
        TORQUE_ENABLE_ADDR = 64  # Torque enable address in the Control Table
        TORQUE_ENABLE = 1

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE_ADDR, TORQUE_ENABLE)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to enable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error enabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        logging.info(f"Torque enabled for motor {motor_id}")

    def torque_off(self, motor_id):
        """Disable the torque on a motor."""
        TORQUE_ENABLE_ADDR = 64  # Torque enable address in the Control Table
        TORQUE_DISABLE = 0

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE_ADDR, TORQUE_DISABLE)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to disable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error disabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        logging.info(f"Torque disabled for motor {motor_id}")

    def set_goal_velocity(self, motor_id, velocity):
        """Set the velocity goal for a motor."""
        VELOCITY_GOAL_ADDR = 104  # Velocity goal address in Control Table

        # Convert velocity to the appropriate value (sign handling for forward/reverse)
        velocity_value = int(velocity)  # Ensure the value is an integer

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, VELOCITY_GOAL_ADDR, velocity_value)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set goal velocity for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error setting goal velocity for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        logging.info(f"Goal velocity set to {velocity} for motor {motor_id}")

    def set_goal_position(self, motor_id, position):
        """Set the goal position for a motor."""
        POSITION_GOAL_ADDR = 116  # Position goal address in Control Table

        position_value = int(position)  # Ensure the position value is an integer
        position_value = int((position_value / 360) * 4096)   # Convert position value from degrees to encoder ticks
        position_value = position_value % 4096 # Ensure the position value is within 0-4095 ticks

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, POSITION_GOAL_ADDR, position_value)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set goal position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error setting goal position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        logging.info(f"Goal position {position} set for motor {motor_id}")

    def get_present_position(self, motor_id):
        """Get the current position of the motor."""
        PRESENT_POSITION_ADDR = 132  # Present position address in Control Table

        position, result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, PRESENT_POSITION_ADDR)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to get position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error getting position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

        position = int((position / 4096) * 360) # Convert from encoder ticks to degrees
        position = position % 360 # Ensure the position is within 0-359 degrees

        logging.info(f"Current position for motor {motor_id} is {position} degrees")
        return position

    def set_velocity_limit(self, motor_id, velocity_rpm):
        # Set the velocity limit for an individual motor
        # Convert RPM to encoder units (based on 0.229 factor for XM and XL motors)
        velocity_limit_in_encoder_units = int(velocity_rpm / 0.229)
        # Set the velocity limit for the motor
        ADDR_VELOCITY_LIMIT = 44
        self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, ADDR_VELOCITY_LIMIT, velocity_limit_in_encoder_units)

    def close(self):
        """Close the port and clean up resources."""
        self.port_handler.closePort()
        logging.info("Port closed")

    """ Functionality for group control of motors"""
    def create_motor_group(self, group_name, motor_ids):
        # Create a group of motors for easier control
        self.motor_groups[group_name] = motor_ids
        
    def sync_write_position(self, group_name, positions):
        # Sync write goal positions for a group of motors
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        groupSyncWrite = GroupSyncWrite(self.port_handler, self.packet_handler, 116, 4)  # Goal position address and size
        
        for i, motor_id in enumerate(self.motor_groups[group_name]):
            pos = positions[i]
            param_goal_position = [DXL_LOBYTE(DXL_LOWORD(pos)),
                                   DXL_HIBYTE(DXL_LOWORD(pos)),
                                   DXL_LOBYTE(DXL_HIWORD(pos)),
                                   DXL_HIBYTE(DXL_HIWORD(pos))]
            groupSyncWrite.addParam(motor_id, param_goal_position)

        groupSyncWrite.txPacket()
        groupSyncWrite.clearParam()

    def bulk_write_velocity(self, group_name, velocities):
        # Bulk write velocities for a group of motors
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        groupBulkWrite = GroupBulkWrite(self.port_handler, self.packet_handler)
        
        for i, motor_id in enumerate(self.motor_groups[group_name]):
            vel = velocities[i]
            param_goal_velocity = [DXL_LOBYTE(DXL_LOWORD(vel)),
                                   DXL_HIBYTE(DXL_LOWORD(vel)),
                                   DXL_LOBYTE(DXL_HIWORD(vel)),
                                   DXL_HIBYTE(DXL_HIWORD(vel))]
            groupBulkWrite.addParam(motor_id, 104, 4, param_goal_velocity)  # Velocity address
        
        groupBulkWrite.txPacket()
        groupBulkWrite.clearParam()

    def torque_on_group(self, group_name):
        # Enable torque for all motors in a group
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        for motor_id in self.motor_groups[group_name]:
            self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, 64, 1)  # Torque enable address

    def torque_off_group(self, group_name):
        # Disable torque for all motors in a group
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        for motor_id in self.motor_groups[group_name]:
            self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, 64, 0)  # Torque disable

    def set_group_velocity_limit(self, group_name, velocity_rpm):
        # Set the velocity limit for all motors in a group using bulk write
        if group_name not in self.motor_groups:
            logging.error(f"Motor group '{group_name}' not found")
            return

        groupBulkWrite = GroupBulkWrite(self.port_handler, self.packet_handler)

        # Convert the desired velocity limit in RPM to encoder units
        velocity_limit_in_encoder_units = int(velocity_rpm / 0.229)

        # Prepare velocity data for each motor in the group
        param_goal_velocity = [
            DXL_LOBYTE(DXL_LOWORD(velocity_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_LOWORD(velocity_limit_in_encoder_units)),
            DXL_LOBYTE(DXL_HIWORD(velocity_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_HIWORD(velocity_limit_in_encoder_units))
        ]

        for motor_id in self.motor_groups[group_name]:
            # Add velocity limit for each motor to bulk write
            result = groupBulkWrite.addParam(motor_id, 44, 4, param_goal_velocity)  # Velocity limit register address 44
            if not result:
                logging.error(f"Failed to add motor {motor_id} to bulk write")
        
        # Execute the bulk write
        result = groupBulkWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to bulk write velocity limit for group '{group_name}': {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Velocity limit of {velocity_rpm} RPM set for all motors in group '{group_name}'")

        groupBulkWrite.clearParam()