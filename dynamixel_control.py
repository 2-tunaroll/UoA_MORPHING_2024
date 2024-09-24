""" This script uses the dynamixel_sdk library to control Dynamixel motors connected to the Raspberry Pi via an Open RB15 motor controller board. It uses sync write and bulk write commands to control multiple motors simultaneously. """
from dynamixel_sdk import *  # Uses Dynamixel SDK library
import logging
import yaml

class DynamixelController:
    def __init__(self, config_path='config.yaml', device_name=None, baudrate=None, protocol_version=2.0):
        # Load configuration from the YAML file
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

        # Dynamically set the device_name and baudrate from config or passed arguments
        self.device_name = device_name or self.config['controller']['device_name']
        self.baudrate = baudrate or self.config['controller']['baudrate']
        
        # Set up motor groups and control table from config
        self.motor_groups = self.config['motor_groups']
        self.control_table = self.config['control_table']
        self.motor_ids = self.config['motor_ids']

        self.port_handler = PortHandler(self.device_name)
        self.packet_handler = PacketHandler(protocol_version)

        # Open the port
        if not self.port_handler.openPort():
            logging.error("Failed to open the port")
            raise Exception("Failed to open the port")
        logging.info(f"Port {self.device_name} opened successfully")

        # Set baudrate
        if not self.port_handler.setBaudRate(self.baudrate):
            logging.error("Failed to set baudrate")
            raise Exception("Failed to set baudrate")
        logging.info(f"Baudrate set to {self.baudrate}")

        # Automatically set up motor groups
        self.setup_motor_groups()

    def create_motor_group(self, group_name, motor_ids):
        """Create a group of motors for easier control."""
        self.motor_groups[group_name] = motor_ids
        logging.info(f"Motor group '{group_name}' created with motors: {motor_ids}")

    def setup_motor_groups(self):
        """Setup all motor groups from the YAML config."""
        motor_groups = self.config['motor_groups']  # Access motor groups from config
        motor_ids = self.config['motor_ids']  # Access motor IDs from config

        for group_name, motor_names in motor_groups.items():
            # Get motor IDs by looking up motor names in motor_ids (whegs and pivots)
            motor_ids_list = [
                motor_ids['whegs'].get(name, motor_ids['pivots'].get(name)) for name in motor_names
            ]
            self.create_motor_group(group_name, motor_ids_list)

    def get_control_table_address(self, key):
        """Get the address for a control table key."""
        if key in self.control_table:
            return self.control_table[key]
        else:
            logging.error(f"Control table key '{key}' not found")
            raise ValueError(f"Control table key '{key}' not found")
         
    def get_homing_offset(self, motor_id):
        """
        Get the current homing offset for the motor.
        """
        HOMING_OFFSET_ADDR = 20  # Address for homing offset in Control Table

        homing_offset, result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, HOMING_OFFSET_ADDR)
        
        if result != COMM_SUCCESS:
            logging.error(f"Failed to read homing offset for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            return None
        if error != 0:
            logging.error(f"Error reading homing offset for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
            return None
        
        logging.info(f"Homing offset for motor {motor_id} is {homing_offset}")
    
    def set_homing_offset(self, motor_id, offset):
        """
        Set the homing offset for the motor to reverse its position direction.
        """
        HOMING_OFFSET_ADDR = 20  # Address for homing offset in Control Table

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, HOMING_OFFSET_ADDR, offset)
        
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set homing offset for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error setting homing offset for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Homing offset set to {offset} for motor {motor_id}")
            print(f"Homing offset set to {offset} for motor {motor_id}")

    # Removed as it has been replaced with a sync write function
    # def set_operating_mode(self, motor_id, mode):
    #     """
    #     Set the operating mode of the motor.
    #     Available modes: 'position', 'velocity', 'multi_turn'
    #     """
    #     OPERATING_MODE_ADDR = 11  # Address for operating mode in Control Table
    #     OPERATING_MODES = {
    #         'position': 3,   # Position control mode
    #         'velocity': 1,   # Velocity control mode
    #         'multi_turn': 4  # Multi-turn mode for continuous rotation
    #     }

    #     if mode not in OPERATING_MODES: 
    #         logging.error(f"Invalid operating mode: {mode}")
    #         return

    #     # Disable torque before changing the mode
    #     self.torque_off(motor_id)

    #     mode_value = OPERATING_MODES[mode]
    #     result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR, mode_value)

    #     if result != COMM_SUCCESS:
    #         logging.error(f"Failed to set operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
    #     elif error != 0:
    #         logging.error(f"Error setting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
    #     else:
    #         logging.info(f"Operating mode set to {mode} for motor {motor_id}")

    #     # Re-enable torque after setting the mode
    #     self.torque_on(motor_id)

    #     if mode == 'velocity':  # Apply velocity limit if in velocity mode
    #         logging.debug(f"Setting velocity limit for motor {motor_id} in velocity mode")
    #         self.set_group_velocity_limit(motor_id, 10)
    #     else:  # Apply velocity profile if in position or multi-turn mode
    #         logging.debug(f"Setting profile velocity for motor {motor_id} in {mode} mode")
    #         self.set_group_profile_velocity(motor_id, 10)



    def check_operating_mode(self, motor_id):
        """
        Check the operating mode of the motor.
        Returns the operating mode as a string.
        Available modes: 'position', 'velocity', 'multi_turn'
        """
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
        elif operating_mode == 4:
            return 'multi_turn'
        logging.debug(f"Operating mode for motor {motor_id} is {operating_mode}")
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
        else:
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
        else:
            logging.info(f"Torque disabled for motor {motor_id}")

    def set_goal_velocity(self, motor_id, velocity):
        """Set the velocity goal for a motor."""
        VELOCITY_GOAL_ADDR = 104  # Velocity goal address in Control Table

        velocity_value = int(velocity)  # Ensure the value is an integer

        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, VELOCITY_GOAL_ADDR, velocity_value)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set goal velocity for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error setting goal velocity for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Goal velocity set to {velocity} for motor {motor_id}")

    def set_goal_position(self, motor_id, position):
        """Set the goal position for a motor, but log only if the position changes."""
        POSITION_GOAL_ADDR = 116  # Position goal address in Control Table

        # Get the current position to avoid unnecessary logging
        current_position = self.get_present_position(motor_id)
        
        # Only log if the new position differs from the current position
        if current_position != position:
            position_value = int((position / 360) * 4096)   # Convert position value from degrees to encoder ticks
            position_value = position_value % 4096  # Ensure the position value is within 0-4095 ticks

            result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, POSITION_GOAL_ADDR, position_value)
            if result != COMM_SUCCESS:
                logging.error(f"Failed to set goal position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            if error != 0:
                logging.error(f"Error setting goal position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
            else:
                logging.info(f"Goal position {position} set for motor {motor_id}")

    def get_present_position(self, motor_id):
        """Get the current position of the motor."""
        PRESENT_POSITION_ADDR = 132  # Present position address in Control Table

        position, result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, PRESENT_POSITION_ADDR)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to get position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error getting position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")

        position = int((position / 4096) * 360)  # Convert from encoder ticks to degrees
        position = position % 360  # Ensure the position is within 0-359 degrees

        logging.debug(f"Current position for motor {motor_id} is {position} degrees")
        return position

    def get_entire_position(self, motor_id):
        """
        Get the current raw position of the motor in encoder units (ticks).
        Returns the raw encoder value without converting to degrees.
        
        :param motor_id: The ID of the motor
        :return: Raw encoder value (0-4095 ticks)
        """
        PRESENT_POSITION_ADDR = 132  # Present position address in Control Table

        # Read the raw 4-byte position value from the motor
        position, result, error = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, PRESENT_POSITION_ADDR)
        
        if result != COMM_SUCCESS:
            logging.error(f"Failed to get raw position for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            return None
        if error != 0:
            logging.error(f"Error getting raw position for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
            return None
        
        return position  # Return the raw encoder value (ticks)

    def set_velocity_limit(self, motor_id, velocity_rpm):
        """Set the velocity limit for an individual motor."""
        velocity_limit_in_encoder_units = int(velocity_rpm / 0.229)  # Convert RPM to encoder units (based on 0.229 factor)

        ADDR_VELOCITY_LIMIT = 44
        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, ADDR_VELOCITY_LIMIT, velocity_limit_in_encoder_units)
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set velocity limit for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        if error != 0:
            logging.error(f"Error setting velocity limit for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Velocity limit of {velocity_rpm} RPM set for motor {motor_id}")
    
    def set_profile_velocity(self, motor_id, velocity_rpm):
        """
        Set the profile velocity (speed) in position control mode.
        The motor will move to the goal position at this speed.
        """
        # Convert RPM to encoder units (0.229 factor for XM and XL motors)
        velocity_limit_in_encoder_units = int(velocity_rpm / 0.229)
        
        ADDR_PROFILE_VELOCITY = 112  # Profile velocity address in the control table
        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, ADDR_PROFILE_VELOCITY, velocity_limit_in_encoder_units)

        if result != COMM_SUCCESS:
            logging.error(f"Failed to set profile velocity for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error setting profile velocity for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Profile velocity set to {velocity_rpm} RPM for motor {motor_id}")

    def set_profile_acceleration(self, motor_id, acceleration_rpmps):
        """
        Set the profile acceleration (how fast the motor accelerates) in position control mode.
        The motor will accelerate at this rate to reach its profile velocity.
        """
        # Convert acceleration to encoder units (based on 0.229 factor for XM/XL motors)
        acceleration_in_encoder_units = int(acceleration_rpmps / 0.229)
        
        ADDR_PROFILE_ACCELERATION = 108  # Profile acceleration address in the control table
        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, ADDR_PROFILE_ACCELERATION, acceleration_in_encoder_units)

        if result != COMM_SUCCESS:
            logging.error(f"Failed to set profile acceleration for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error setting profile acceleration for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Profile acceleration set to {acceleration_rpmps} RPM/s for motor {motor_id}")

    def close(self):
        """Close the port and clean up resources."""
        self.port_handler.closePort()
        logging.info("Port closed")

    def sync_write_position(self, group_name, position):
        """Sync write goal positions for a group of motors."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        # Check if the motors are in multi-turn mode, if not, set them to multi-turn mode
        for motor_id in self.motor_groups[group_name]:
            current_mode = self.check_operating_mode(motor_id)
            if current_mode != 'position':
                self.set_operating_mode_group(group_name, 'position')

        # Update position from degrees to encoder ticks
        pos = int((position / 360) * 4096)  # Convert position to encoder ticks
        
        groupSyncWrite = GroupSyncWrite(self.port_handler, self.packet_handler, 116, 4)  # Goal position address and size
        
        for i, motor_id in enumerate(self.motor_groups[group_name]):
            param_goal_position = [DXL_LOBYTE(DXL_LOWORD(pos)),
                                   DXL_HIBYTE(DXL_LOWORD(pos)),
                                   DXL_LOBYTE(DXL_HIWORD(pos)),
                                   DXL_HIBYTE(DXL_HIWORD(pos))]
            groupSyncWrite.addParam(motor_id, param_goal_position)

        result = groupSyncWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to sync write positions for group {group_name}: {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Sync write goal positions set for group {group_name}")
        groupSyncWrite.clearParam()

    def bulk_write_velocity(self, group_name, velocities):
        """Bulk write velocities for a group of motors."""
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
        
        result = groupBulkWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to bulk write velocities for group {group_name}: {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Bulk write velocities set for group {group_name}")
        groupBulkWrite.clearParam()

    def torque_on_group(self, group_name):
        """Enable torque for all motors in a group."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        for motor_id in self.motor_groups[group_name]:
            result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, 64, 1)  # Torque enable address
            if result != COMM_SUCCESS:
                logging.error(f"Failed to enable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            elif error != 0:
                logging.error(f"Error enabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        
        logging.info(f"Torque enabled for all motors in group '{group_name}'")

    def torque_off_group(self, group_name):
        """Disable torque for all motors in a group."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        for motor_id in self.motor_groups[group_name]:
            result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, 64, 0)  # Torque disable address
            if result != COMM_SUCCESS:
                logging.error(f"Failed to disable torque for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
            elif error != 0:
                logging.error(f"Error disabling torque for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        
        logging.info(f"Torque disabled for all motors in group '{group_name}'")

    def set_group_velocity_limit(self, group_name, velocity_rpm):
        """Set the velocity limit for all motors in a group using bulk write."""

        if group_name not in self.motor_groups:
            logging.error(f"Motor group '{group_name}' not found")
            return

        groupBulkWrite = GroupBulkWrite(self.port_handler, self.packet_handler)

        velocity_limit_in_encoder_units = int(velocity_rpm / 0.229)  # Convert RPM to encoder units

        param_goal_velocity = [
            DXL_LOBYTE(DXL_LOWORD(velocity_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_LOWORD(velocity_limit_in_encoder_units)),
            DXL_LOBYTE(DXL_HIWORD(velocity_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_HIWORD(velocity_limit_in_encoder_units))
        ]

        for motor_id in self.motor_groups[group_name]:
            result = groupBulkWrite.addParam(motor_id, 44, 4, param_goal_velocity)  # Velocity limit register address 44
            if not result:
                logging.error(f"Failed to add motor {motor_id} to bulk write")

        result = groupBulkWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to bulk write velocity limit for group '{group_name}': {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Velocity limit of {velocity_rpm} RPM set for all motors in group '{group_name}'")
        groupBulkWrite.clearParam()

    def set_group_profile_velocity(self, group_name, velocity_rpm):
        """
        Set the profile velocity (speed) for a group of motors in position control mode.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group '{group_name}' not found")
            return

        groupBulkWrite = GroupBulkWrite(self.port_handler, self.packet_handler)

        # Convert the velocity limit from RPM to encoder units
        velocity_limit_in_encoder_units = int(velocity_rpm / 0.229)

        # Prepare velocity data for each motor in the group
        param_profile_velocity = [
            DXL_LOBYTE(DXL_LOWORD(velocity_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_LOWORD(velocity_limit_in_encoder_units)),
            DXL_LOBYTE(DXL_HIWORD(velocity_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_HIWORD(velocity_limit_in_encoder_units))
        ]

        for motor_id in self.motor_groups[group_name]:
            result = groupBulkWrite.addParam(motor_id, 112, 4, param_profile_velocity)
            if not result:
                logging.error(f"Failed to add motor {motor_id} to bulk write")

        # Execute the bulk write
        result = groupBulkWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to bulk write profile velocity for group '{group_name}': {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Profile velocity of {velocity_rpm} RPM set for all motors in group '{group_name}'")

        groupBulkWrite.clearParam()

    def set_group_profile_acceleration(self, group_name, acceleration_rpm2):
        """
        Set the profile acceleration for a group of motors in position control mode.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group '{group_name}' not found")
            return

        groupBulkWrite = GroupBulkWrite(self.port_handler, self.packet_handler)

        # Convert the acceleration limit from RPM^2 to encoder units (Dynamixel uses 214.577 units/RPM^2 for conversion)
        acceleration_limit_in_encoder_units = int(acceleration_rpm2 / 0.916)

        # Prepare acceleration data for each motor in the group
        param_profile_acceleration = [
            DXL_LOBYTE(DXL_LOWORD(acceleration_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_LOWORD(acceleration_limit_in_encoder_units)),
            DXL_LOBYTE(DXL_HIWORD(acceleration_limit_in_encoder_units)),
            DXL_HIBYTE(DXL_HIWORD(acceleration_limit_in_encoder_units))
        ]

        for motor_id in self.motor_groups[group_name]:
            result = groupBulkWrite.addParam(motor_id, 108, 4, param_profile_acceleration)  # 108 is the address for profile acceleration in most Dynamixel motors
            if not result:
                logging.error(f"Failed to add motor {motor_id} to bulk write")

        # Execute the bulk write
        result = groupBulkWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to bulk write profile acceleration for group '{group_name}': {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Profile acceleration of {acceleration_rpm2} RPM^2 set for all motors in group '{group_name}'")

        groupBulkWrite.clearParam()

    def increment_group_position(self, group_name, increment):
        """ 
        Increment the goal position for a group of motors, applying negative increment for right-side motors (IDs 4, 5, 6).
        
        :param group_name: The name of the motor group to increment.
        :param increment: Degrees to increment the position.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group '{group_name}' not found")
            return

        # Check if the motors are in multi-turn mode, if not, set them to multi-turn mode
        for motor_id in self.motor_groups[group_name]:
            current_mode = self.check_operating_mode(motor_id)
            if current_mode != 'multi_turn':
                self.set_operating_mode_group(group_name, 'multi_turn')

        increment_ticks = int((increment / 360) * 4096)  # Convert increment to encoder ticks
        groupSyncWrite = GroupSyncWrite(self.port_handler, self.packet_handler, 116, 4)  # Position goal address and size

        # List of right-side motor IDs (for which we reverse the increment)
        right_wheg_ids = [4, 5, 6]

        for motor_id in self.motor_groups[group_name]:
            # Get the current position of the motor in ticks
            current_position = self.get_entire_position(motor_id)
            
            # Reverse increment for right-side motors
            if motor_id in right_wheg_ids:
                new_position = current_position - increment_ticks  # Reverse increment for right-side motors
            else:
                new_position = current_position + increment_ticks  # Normal increment for left or other motors

            param_goal_position = [
                DXL_LOBYTE(DXL_LOWORD(new_position)),
                DXL_HIBYTE(DXL_LOWORD(new_position)),
                DXL_LOBYTE(DXL_HIWORD(new_position)),
                DXL_HIBYTE(DXL_HIWORD(new_position))
            ]

            # Add the motor's goal position to the sync write group
            result = groupSyncWrite.addParam(motor_id, param_goal_position)
            if not result:
                logging.error(f"Failed to add motor {motor_id} to GroupSyncWrite")
                return

        # Transmit the sync write command to all motors in the group
        result = groupSyncWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to sync write positions for group '{group_name}': {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Sync write goal positions set for group '{group_name}'")

        # Clear the parameters for the next sync write
        groupSyncWrite.clearParam()

    def set_operating_mode_group(self, group_name, mode):
        """
        Set the operating mode for a group of motors using sync write.
        Available modes: 'position', 'velocity', 'multi_turn'
        """
        OPERATING_MODE_ADDR = 11  # Address for operating mode in Control Table
        OPERATING_MODES = {
            'position': 3,   # Position control mode
            'velocity': 1,   # Velocity control mode
            'multi_turn': 4  # Multi-turn mode for continuous rotation
        }

        if mode not in OPERATING_MODES:
            logging.error(f"Invalid operating mode: {mode}")
            return

        # Ensure the group exists
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        mode_value = OPERATING_MODES[mode]
        groupSyncWrite = GroupSyncWrite(self.port_handler, self.packet_handler, OPERATING_MODE_ADDR, 1)  # 1 byte for operating mode

        # Disable torque for the entire group before changing the mode
        self.torque_off_group(group_name)

        # Prepare sync write parameters for each motor in the group
        for motor_id in self.motor_groups[group_name]:
            param_operating_mode = [mode_value]
            result = groupSyncWrite.addParam(motor_id, param_operating_mode)
            if not result:
                logging.error(f"Failed to add motor {motor_id} to sync write")

        # Transmit the sync write command
        result = groupSyncWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to sync write operating modes for group {group_name}: {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Operating mode set to '{mode}' for group {group_name}")
        
        groupSyncWrite.clearParam()

        # Re-enable torque for the entire group after setting the mode
        self.torque_on_group(group_name)

        # Apply specific configuration for velocity and position modes
        if mode == 'velocity':
            logging.debug(f"Setting velocity limit for motors in group {group_name}")
            self.set_group_velocity_limit(group_name, 10)
        else:
            logging.debug(f"Setting profile velocity for motors in group {group_name}")
            self.set_group_profile_velocity(group_name, 10)
