""" This script uses the dynamixel_sdk library to control Dynamixel motors connected to the Raspberry Pi via an Open RB15 motor controller board. It uses sync write and bulk write commands to control multiple motors simultaneously. """
from dynamixel_sdk import *  # Uses Dynamixel SDK library
import logging
import yaml
import time

class DynamixelController:
    def __init__(self, config_path='config.yaml', device_name=None, baudrate=None, protocol_version=2.0):
        """Initialize the controller with YAML config and setup motor groups."""
        # Load configuration
        self.load_config(config_path)
        
        # Dynamically set the device_name and baudrate from config or passed arguments
        self.device_name = device_name or self.config['controller'].get('device_name')
        self.baudrate = baudrate or self.config['controller'].get('baudrate')

        # Check if device_name or baudrate are not set
        if not self.device_name:
            logging.error("Device name not provided and not found in config")
            raise ValueError("Device name must be provided either as an argument or in the config file")
        
        if not self.baudrate:
            logging.error("Baudrate not provided and not found in config")
            raise ValueError("Baudrate must be provided either as an argument or in the config file")

        # Initialize SDK handlers
        self.port_handler = PortHandler(self.device_name)
        self.packet_handler = PacketHandler(protocol_version)

        # Open the port and set the baudrate
        self.open_port()
        
        # Set up motor groups and control table from config
        self.motor_groups = {}  # Initialize as an empty dictionary
        self.load_control_table()
        self.setup_motor_groups()

    def load_config(self, config_path):
        """Load configuration from a YAML file."""
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            logging.info("Configuration loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            raise
    
    def open_port(self):
        """Open the port and set baudrate."""
        if not self.port_handler.openPort():
            logging.error("Failed to open the port")
            raise Exception("Failed to open the port")
        logging.info(f"Port {self.device_name} opened successfully")
        
        if not self.port_handler.setBaudRate(self.baudrate):
            logging.error("Failed to set baudrate")
            raise Exception("Failed to set baudrate")
        logging.info(f"Baudrate set to {self.baudrate}")
        
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

    def load_control_table(self):
        """Load control table from the configuration file."""
        self.control_table = self.config.get('control_table', {})
        if not self.control_table:
            logging.error("Control table missing or empty in configuration.")
            raise Exception("Control table not defined in config.")
        
        # Verify each control table entry has both 'address' and 'length'
        for entry, value in self.control_table.items():
            if 'address' not in value or 'length' not in value:
                logging.error(f"Control table entry '{entry}' is missing 'address' or 'length'.")
                raise Exception(f"Control table entry '{entry}' is incomplete.")
        
        logging.info("Control table loaded successfully.")

    def get_control_table_address(self, key):
        """Get the address for a control table key."""
        if key in self.control_table:
            return self.control_table[key]
        else:
            logging.error(f"Control table key '{key}' not found")
            raise ValueError(f"Control table key '{key}' not found")
    
    def position_to_degrees(self, position_value):
        """Convert a raw motor position value (0-4095) to degrees (0-360)."""
        if position_value is None:
            logging.error("Invalid position value: None")
            return None
        return (position_value / 4095.0) * 360.0
    
    def degrees_to_position(self, degrees):
        """Convert degrees to a raw motor position value (0-4095)."""
        if degrees is None:
            logging.error("Invalid degrees value: None")
            return None
        return int((degrees / 360.0) * 4095)

    def set_status_return_level(self, group_name, level=1):
        """Set the status return level for a group of motors."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        # Set the status return level for all motors in the group
        status_levels = {motor_id: level for motor_id in self.motor_groups[group_name]}
        self.sync_write_group(group_name, 'status_return_level', status_levels)

        logging.info(f"Status return level set to {level} for group {group_name}")

    def sync_write_group(self, group_name, parameter_name, param_dict):
        """
        Sync write command for a group of motors with different values.
        
        :param group_name: The name of the motor group (from config) to which the command will be sent.
        :param parameter_name: The control table parameter to write (e.g., 'position_goal', 'velocity_goal').
        :param param_dict: A dictionary mapping motor_id to the target value for each motor.
        """
        motor_ids = self.motor_groups.get(group_name, [])
        if not motor_ids:
            logging.warning(f"No motors found for group '{group_name}'")
            return
        
        # Retrieve the control table address and length for the given parameter
        control_item = self.control_table.get(parameter_name)
        if not control_item:
            logging.error(f"Control table entry '{parameter_name}' not found.")
            raise Exception(f"Control table entry '{parameter_name}' not found.")
        
        address = control_item['address']
        length = control_item['length']
        
        # Create a GroupSyncWrite instance
        sync_write = GroupSyncWrite(self.port_handler, self.packet_handler, address, length)
        
        # Prepare sync write data for each motor
        for motor_id in motor_ids:
            param = param_dict.get(motor_id)
            if param is not None:
                # Convert the value to the appropriate byte format (little endian)
                if length == 1:
                    param_data = [DXL_LOBYTE(param)]
                elif length == 2:
                    param_data = [DXL_LOBYTE(param), DXL_HIBYTE(param)]
                elif length == 4:
                    param_data = [
                        DXL_LOBYTE(DXL_LOWORD(param)),
                        DXL_HIBYTE(DXL_LOWORD(param)),
                        DXL_LOBYTE(DXL_HIWORD(param)),
                        DXL_HIBYTE(DXL_HIWORD(param))
                    ]
                else:
                    logging.error(f"Unsupported data length {length} for parameter '{parameter_name}'.")
                    raise Exception(f"Unsupported data length {length}.")

                # Add the parameter to the sync write for the specific motor
                if not sync_write.addParam(motor_id, bytes(param_data)):
                    logging.error(f"Failed to add parameter for motor {motor_id}.")
                    raise Exception(f"Failed to add parameter for motor {motor_id}.")
        
        # Execute the sync write command
        result = sync_write.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Sync write failed with error: {self.packet_handler.getTxRxResult(result)}")

        # Clear the parameters after the sync write
        sync_write.clearParam()

    def bulk_read_group(self, motor_ids, parameters):
        """
        Bulk read command to read multiple parameters from multiple motors.

        :param motor_ids: List of motor IDs to read from.
        :param parameters: List of parameters to read (e.g., ['present_position', 'present_velocity']).
        :return: Dictionary where keys are motor_ids and values are dictionaries of parameter data.
        """
        bulk_read = GroupBulkRead(self.port_handler, self.packet_handler)

        for motor_id in motor_ids:
            for parameter_name in parameters:
                control_item = self.control_table.get(parameter_name)
                if not control_item:
                    logging.error(f"Control table entry '{parameter_name}' not found.")
                    raise Exception(f"Control table entry '{parameter_name}' not found.")
                
                # Get the control table address and length for the parameter
                address = control_item['address']
                length = control_item['length']

                if not bulk_read.addParam(motor_id, address, length):
                    logging.error(f"Failed to add motor {motor_id} for parameter '{parameter_name}'.")
                    raise Exception(f"Failed to add motor {motor_id} for parameter '{parameter_name}'.")

        result = bulk_read.txRxPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Bulk read failed with error: {self.packet_handler.getTxRxResult(result)}")
            return None

        motor_data = {}
        for motor_id in motor_ids:
            motor_data[motor_id] = {}
            for parameter_name in parameters:
                control_item = self.control_table.get(parameter_name)
                length = control_item['length']
                
                data = bulk_read.getData(motor_id, control_item['address'], length)

                if data is None:
                    logging.error(f"No data received for motor {motor_id}.")
                    motor_data[motor_id][parameter_name] = None
                else:
                    # Handle position data conversion to degrees
                    if parameter_name == 'present_position':
                        position_value = data
                        degrees = self.position_to_degrees(position_value)
                        motor_data[motor_id]['position_degrees'] = degrees
                    else:
                        motor_data[motor_id][parameter_name] = data

        bulk_read.clearParam()

        return motor_data

    def set_operating_mode_group(self, group_name, mode):
        """
        Set the operating mode for a group of motors using sync write.
        Available modes: 'position', 'velocity', 'multi_turn'
        :param group_name: The name of the motor group to set the operating mode for.
        :param mode: The operating mode to set ('position', 'velocity', 'multi_turn').
        """
        OPERATING_MODES = {
            'position': 3,   # Position control mode
            'velocity': 1,   # Velocity control mode
            'multi_turn': 4  # Multi-turn mode for continuous rotation
        }

        # Validate operating mode
        if mode not in OPERATING_MODES:
            logging.error(f"Invalid operating mode: {mode}")
            return

        # Ensure the motor group exists
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        mode_value = OPERATING_MODES[mode]

        # Disable torque for the entire group before changing the mode
        self.torque_off_group(group_name)

        # Use sync_write_group to set the operating mode for each motor in the group
        operating_mode_params = {motor_id: mode_value for motor_id in self.motor_groups[group_name]}
        self.sync_write_group(group_name, 'operating_mode', operating_mode_params)

        logging.info(f"Operating mode set to '{mode}' for group {group_name}")

        # Re-enable torque for the entire group after setting the mode
        self.torque_on_group(group_name)

        # Apply specific configuration for velocity and position modes
        if mode == 'velocity':
            logging.debug(f"Setting velocity limit for motors in group {group_name}")
            self.set_group_velocity_limit(group_name)
        else:
            logging.debug(f"Setting profile velocity for motors in group {group_name}")
            self.set_group_profile_velocity(group_name)

    def set_group_velocity_limit(self, group_name):
        """
        Set velocity limit for a group of motors based on config.yaml or the hard velocity limit.
        
        :param group_name: The name of the motor group to set the velocity limit for.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        # Get hard velocity limit from config.yaml
        hard_velocity_limit = self.config.get('hard_velocity_limit', None)
        if hard_velocity_limit is None:
            logging.error(f"Hard velocity limit not found in config.yaml")
            return

        # Get velocity limit from config.yaml
        velocity_limit = self.config.get('velocity_limits', {}).get(group_name, None)
        if velocity_limit is None:
            logging.error(f"Velocity limit for group {group_name} not found in config.yaml")
            return

        # Check if the velocity limit exceeds the hard limit
        if velocity_limit > hard_velocity_limit:
            logging.warning(f"Velocity limit {velocity_limit} exceeds hard limit {hard_velocity_limit}. Limiting to {hard_velocity_limit}.")
            velocity_limit = hard_velocity_limit

        # Apply velocity limit using sync write
        velocity_limits = {motor_id: velocity_limit for motor_id in self.motor_groups[group_name]}
        self.sync_write_group(group_name, 'velocity_limit', velocity_limits)

        logging.info(f"Velocity limit set to {velocity_limit} for group {group_name}")

    def set_group_profile_velocity(self, group_name, profile_velocity=None):
        """
        Set profile velocity for a group of motors based on config.yaml or a provided value.
        
        :param group_name: The name of the motor group to set the profile velocity for.
        :param profile_velocity: Optional, if provided will override the value from config.yaml.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        # Get hard profile velocity limit from config.yaml
        hard_profile_velocity_limit = self.config.get('hard_profile_velocity_limit', None)
        if hard_profile_velocity_limit is None:
            logging.error(f"Hard profile velocity limit not found in config.yaml")
            return

        # Get profile velocity from config.yaml if not provided
        if profile_velocity is None:
            profile_velocity = self.config.get('profile_velocities', {}).get(group_name, None)
            if profile_velocity is None:
                logging.error(f"Profile velocity for group {group_name} not found in config.yaml and no value was provided.")
                return

        # Check if the profile velocity is zero (infinite velocity) and log a warning
        if profile_velocity == 0:
            logging.warning(f"Profile velocity of 0 (infinite) is not allowed. Limiting to hard profile velocity limit {hard_profile_velocity_limit}.")
            profile_velocity = 1  # Limit it to 1 instead

        # Check if the profile velocity exceeds the hard limit
        if profile_velocity > hard_profile_velocity_limit:
            logging.warning(f"Profile velocity {profile_velocity} exceeds hard limit {hard_profile_velocity_limit}. Limiting to {hard_profile_velocity_limit}.")
            profile_velocity = hard_profile_velocity_limit

        # Apply profile velocity using sync write
        profile_velocities = {motor_id: profile_velocity for motor_id in self.motor_groups[group_name]}
        self.sync_write_group(group_name, 'profile_velocity', profile_velocities)

        logging.info(f"Profile velocity set to {profile_velocity} for group {group_name}")

    def torque_off_group(self, group_name):
        """Disable torque for all motors in the group."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        # Disable torque for each motor
        torque_values = {motor_id: 0 for motor_id in self.motor_groups[group_name]}
        self.sync_write_group(group_name, 'torque_enable', torque_values)
        logging.info(f"Torque disabled for group {group_name}")

    def torque_on_group(self, group_name):
        """Enable torque for all motors in the group."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        # Enable torque for each motor
        torque_values = {motor_id: 1 for motor_id in self.motor_groups[group_name]}
        self.sync_write_group(group_name, 'torque_enable', torque_values)
        logging.info(f"Torque enabled for group {group_name}")

    def set_position_group(self, group_name, positions_dict):
        """
        Set target positions (in degrees) for a group of motors.
        
        :param group_name: The motor group name (from config)
        :param positions_dict: Dictionary with motor_id as key and target position in degrees as value.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return

        # Ensure the group is in position control mode
        self.set_operating_mode_group(group_name, 'position')

        # Convert degrees to raw position values (0-4095 range) using degrees_to_position
        position_goals = {motor_id: self.degrees_to_position(degrees) for motor_id, degrees in positions_dict.items()}

        try:
            self.sync_write_group(group_name, 'position_goal', position_goals)
            logging.info(f"Target positions set for group {group_name}: {positions_dict}")
        except Exception as e:
            logging.error(f"Failed to set positions for group {group_name}: {e}")


    def set_velocity_group(self, group_name, velocities_dict):
        """
        Set target velocities for a group of motors.
        
        :param group_name: The motor group name (from config)
        :param velocities_dict: Dictionary with motor_id as key and target velocity as value.
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        # Ensure the group is in velocity control mode
        self.set_operating_mode_group(group_name, 'velocity')

        # Ensure torque is enabled after mode change
        self.torque_on_group(group_name)

        # Check if any velocity exceeds the hard velocity limit
        hard_velocity_limit = self.config.get('hard_velocity_limit', None)
        if hard_velocity_limit is None:
            logging.error(f"Hard velocity limit not found in config.yaml")
            return

        for motor_id, velocity in velocities_dict.items():
            if velocity > hard_velocity_limit:
                logging.warning(f"Velocity {velocity} for motor {motor_id} exceeds hard limit {hard_velocity_limit}. Limiting to {hard_velocity_limit}.")
                velocities_dict[motor_id] = hard_velocity_limit

        try:
            self.sync_write_group(group_name, 'velocity_goal', velocities_dict)
            logging.info(f"Target velocities set for group {group_name}: {velocities_dict}")
        except Exception as e:
            logging.error(f"Failed to set velocities for group {group_name}: {e}")

    def set_drive_mode_group(self, group_name, reverse_direction=False):
        """
        Set the drive mode for a group of motors.
        
        :param self: The motor controller instance.
        :param group_name: The motor group to modify (e.g., 'Right_Side').
        :param reverse_direction: Set to True to reverse direction, False for normal.
        """
        try:
            # Define the drive mode value (Bit 0)
            drive_mode_value = 1 if reverse_direction else 0

            # Get the motor IDs for the group
            if group_name not in self.motor_groups:
                logging.error(f"Motor group {group_name} not found")
                return

            # Set drive mode for each motor in the group
            drive_modes = {motor_id: drive_mode_value for motor_id in self.motor_groups[group_name]}
            
            # Sync write to set drive mode
            self.sync_write_group(group_name, 'drive_mode', drive_modes)
            logging.info(f"Drive mode set for group {group_name} with reverse_direction={reverse_direction}")
            
        except Exception as e:
            logging.error(f"Failed to set drive mode for group {group_name}: {e}")

    def increment_motor_position_by_degrees(self, group_name, degrees_increment):
        """
        Increment the position of motors in a group by a specified number of degrees in extended position mode.

        :param self: The motor controller instance.
        :param group_name: The motor group to modify (e.g., 'Wheg_Group').
        :param degrees_increment: The number of degrees to increment the position by.
        """
        try:
            # Ensure the motors are in Extended Position Control Mode
            self.set_operating_mode_group(group_name, 'multi_turn')
            logging.info(f"Operating mode set to Extended Position Control Mode for {group_name}.")

            # Retrieve the current position for each motor
            motor_ids = self.motor_groups[group_name]
            motor_data = self.bulk_read_group(motor_ids, ['present_position'])
            
            if motor_data is None:
                logging.error("Bulk read (positions) failed: No data returned")
                return

            # Calculate the new target position for each motor
            target_positions = {}
            for motor_id, data in motor_data.items():
                current_position_raw = data.get('present_position')
                if current_position_raw is not None:
                    # Convert degrees to raw motor value (0-4095 represents 360 degrees)
                    position_increment_raw = self.degreestoposition(degrees_increment)
                    
                    # Calculate the new target position in extended position mode
                    new_position_raw = current_position_raw + position_increment_raw
                    
                    target_positions[motor_id] = new_position_raw
                    logging.info(f"Motor {motor_id} new target position (raw): {new_position_raw}")

            # Send the new target positions to the motors
            self.sync_write_group(group_name, 'position_goal', target_positions)
            logging.info(f"Positions incremented by {degrees_increment} degrees for group {group_name}.")
            
        except Exception as e:
            logging.error(f"Failed to increment motor positions for group {group_name}: {e}")
