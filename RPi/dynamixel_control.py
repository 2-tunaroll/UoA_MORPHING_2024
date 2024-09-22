import logging
from dynamixel_sdk import *  # Uses Dynamixel SDK library

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
        Set the operating mode of the motor. Available modes: 'position', 'velocity'
        Only log if the mode is actually changed.
        """
        OPERATING_MODE_ADDR = 11
        OPERATING_MODES = {
            'position': 3,
            'velocity': 1
        }

        current_mode = self.check_operating_mode(motor_id)
        if current_mode == mode:
            # No need to log if the mode is already set
            return

        self.torque_off(motor_id)

        if mode not in OPERATING_MODES:
            logging.error(f"Invalid operating mode: {mode}")
            return

        mode_value = OPERATING_MODES[mode]
        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR, mode_value)

        if result != COMM_SUCCESS:
            logging.error(f"Failed to set operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error setting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Operating mode set to {mode} for motor {motor_id}")

        self.torque_on(motor_id)

    def check_operating_mode(self, motor_id):
        """ Check the current operating mode and return it only if it differs. """
        OPERATING_MODE_ADDR = 11
        operating_mode, result, error = self.packet_handler.read1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to get operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error getting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

        if operating_mode == 3:
            return 'position'
        elif operating_mode == 1:
            return 'velocity'

    def torque_on(self, motor_id):
        """ Enable the torque on a motor, log only if torque state changes. """
        TORQUE_ENABLE_ADDR = 64
        TORQUE_ENABLE = 1

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE_ADDR, TORQUE_ENABLE)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to enable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error enabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def torque_off(self, motor_id):
        """ Disable the torque on a motor, log only if torque state changes. """
        TORQUE_ENABLE_ADDR = 64
        TORQUE_DISABLE = 0

        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, TORQUE_ENABLE_ADDR, TORQUE_DISABLE)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to disable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error disabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def set_goal_position(self, motor_id, position):
        """ Set the goal position for a motor, log only on change. """
        POSITION_GOAL_ADDR = 116
        position_value = int((position / 360) * 4096)
        position_value = position_value % 4096  # Convert degrees to ticks and ensure within 0-4096

        current_position = self.get_present_position(motor_id)
        if abs(current_position - position) < 1:  # Only log if the position changes by more than 1 degree
            return

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, POSITION_GOAL_ADDR, position_value)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set goal position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error setting goal position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

    def get_present_position(self, motor_id):
        """ Get the current position of the motor and convert it to degrees. """
        PRESENT_POSITION_ADDR = 132
        position, result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, PRESENT_POSITION_ADDR)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to get position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error getting position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

        position = int((position / 4096) * 360)  # Convert from ticks to degrees
        return position % 360  # Ensure the position is within 0-359 degrees

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