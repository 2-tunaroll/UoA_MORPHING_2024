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

    def set_operating_mode(self, motor_id, mode):
        """
        Set the operating mode of the motor. Available modes: 'position', 'velocity'
        """
        OPERATING_MODE_ADDR = 11  # Address for operating mode in Control Table
        OPERATING_MODES = {
            'position': 3,  # Operating mode value for position control
            'velocity': 1   # Operating mode value for velocity control
        }

        # Disable torque before changing the operating mode
        self.torque_off(motor_id)

        if mode not in OPERATING_MODES:
            logging.error(f"Invalid operating mode: {mode}")
            return  # Don't raise exceptions, just log the error

        mode_value = OPERATING_MODES[mode]
        result, error = self.packet_handler.write1ByteTxRx(self.port_handler, motor_id, OPERATING_MODE_ADDR, mode_value)
        
        if result != COMM_SUCCESS:
            logging.error(f"Failed to set operating mode for motor {motor_id}: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            logging.error(f"Error setting operating mode for motor {motor_id}: {self.packet_handler.getRxPacketError(error)}")
        else:
            logging.info(f"Operating mode set to {mode} for motor {motor_id}")

        # Re-enable torque after setting the operating mode
        self.torque_on(motor_id)

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
            return 'position'
        elif operating_mode == 1:
            return 'velocity'
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

    def rotate_by_degrees(self, motor_id, degrees, tolerance=1):
        """
        Rotate the motor by a specified number of degrees relative to its current position,
        and wait until the motor reaches the target position before continuing.
        
        :param motor_id: ID of the motor to rotate
        :param degrees: Degrees to rotate relative to the current position
        :param tolerance: Acceptable range (in degrees) within which the motor is considered to have reached the target
        """
        POSITION_GOAL_ADDR = 116  # Position goal address in Control Table

        # Get the current position in degrees
        current_position_degrees = self.get_present_position(motor_id)

        # Calculate the new position by adding the rotation
        new_position_degrees = current_position_degrees + degrees

        # Convert the new position to encoder units
        new_position_value = int((new_position_degrees / 360) * 4096)  # Convert degrees to encoder ticks

        # Send the new goal position to the motor
        result, error = self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, POSITION_GOAL_ADDR, new_position_value)

        if result != COMM_SUCCESS:
            logging.error(f"Failed to rotate motor {motor_id} by {degrees} degrees: {self.packet_handler.getTxRxResult(result)}")
            return False
        elif error != 0:
            logging.error(f"Error rotating motor {motor_id} by {degrees} degrees: {self.packet_handler.getRxPacketError(error)}")
            return False
        else:
            logging.info(f"Motor {motor_id} rotated by {degrees} degrees (new target position: {new_position_degrees} degrees)")

        # Wait until the motor reaches the target position within the specified tolerance
        while True:
            current_position = self.get_present_position(motor_id)
            position_error = abs(current_position - new_position_degrees) % 360  # Handle wrapping around 0-360 degrees

            # If the current position is within the tolerance range, consider the position reached
            if position_error <= tolerance:
                logging.info(f"Motor {motor_id} reached target position: {current_position} degrees (within {tolerance} degrees tolerance)")
                break

            # Optional: add a short delay to prevent busy-waiting
            time.sleep(0.05)

        return True


    def close(self):
        """Close the port and clean up resources."""
        self.port_handler.closePort()
        logging.info("Port closed")

    """ Functionality for group control of motors """
    def create_motor_group(self, group_name, motor_ids):
        """Create a group of motors for easier control."""
        self.motor_groups[group_name] = motor_ids
        logging.info(f"Motor group '{group_name}' created with motors: {motor_ids}")

    def sync_write_position(self, group_name, positions):
        """Sync write goal positions for a group of motors."""
        if group_name not in self.motor_groups:
            logging.error(f"Motor group {group_name} not found")
            return
        
        groupSyncWrite = GroupSyncWrite(self.port_handler, self.packet_handler, 116, 4)  # Goal position address and size
        
        for i, motor_id in enumerate(self.motor_groups[group_name]):
            pos = positions
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

    def increment_group_position(self, group_name, degrees, profile_velocity):
        """
        Increment the position of all motors in a group by a specified number of degrees, 
        adding the increment to their current position and setting a velocity limit (Profile Velocity).
        
        :param group_name: Name of the motor group
        :param degrees: Degrees to increment
        :param profile_velocity: Profile velocity in RPM (this will be set for each motor in the group)
        """
        if group_name not in self.motor_groups:
            logging.error(f"Motor group '{group_name}' not found")
            return

        # Set profile velocity for all motors in the group
        self.set_group_profile_velocity(group_name, profile_velocity)

        groupSyncWrite = GroupSyncWrite(self.port_handler, self.packet_handler, 116, 4)  # Position goal address and size

        # Convert the degree increment into encoder ticks
        increment_ticks = int((degrees / 360) * 4096)  # 4096 ticks per 360 degrees

        for motor_id in self.motor_groups[group_name]:
            # Get current position in ticks
            current_position_ticks = self.get_entire_position(motor_id)
            if current_position_ticks is None:
                logging.error(f"Could not retrieve position for motor {motor_id}")
                return
            
            # Calculate the new target position
            new_position_value = (current_position_ticks + increment_ticks) % 4096  # Ensure wrapping within 0-4095

            # Prepare the goal position parameters for the motor
            param_goal_position = [
                DXL_LOBYTE(DXL_LOWORD(new_position_value)),
                DXL_HIBYTE(DXL_LOWORD(new_position_value)),
                DXL_LOBYTE(DXL_HIWORD(new_position_value)),
                DXL_HIBYTE(DXL_HIWORD(new_position_value))
            ]

            # Add the motor's new position to the sync write group
            result = groupSyncWrite.addParam(motor_id, param_goal_position)
            if not result:
                logging.error(f"Failed to add motor {motor_id} to GroupSyncWrite")
                return

        # Transmit the position command to all motors in the group
        result = groupSyncWrite.txPacket()
        if result != COMM_SUCCESS:
            logging.error(f"Failed to increment positions for group '{group_name}': {self.packet_handler.getTxRxResult(result)}")
        else:
            logging.info(f"Incremented position for all motors in group '{group_name}' by {degrees} degrees")

        # Clear the parameters for the next bulk write
        groupSyncWrite.clearParam()
