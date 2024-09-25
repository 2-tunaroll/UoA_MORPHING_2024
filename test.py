import logging
from dynamixel_control import DynamixelController
import time

# Initialize logging for console output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def test_dynamixel_controller():
    # Step 1: Initialize the controller with the config.yaml path
    logging.debug("Test Case: Initialize DynamixelController")
    try:
        controller = DynamixelController(config_path='config.yaml')
        logging.info("DynamixelController initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize DynamixelController: {e}")
        return
    
    # Step 2: Test opening the port and baudrate
    logging.debug("Test Case: Open port and set baudrate")
    try:
        controller.open_port()
        logging.info(f"Port {controller.device_name} opened with baudrate {controller.baudrate}.")
    except Exception as e:
        logging.error(f"Failed to open port: {e}")
        return

    # Step 3: Test motor group setup
    logging.debug("Test Case: Setup motor groups")
    try:
        controller.setup_motor_groups()
        logging.info("Motor groups set up successfully.")
    except Exception as e:
        logging.error(f"Motor group setup failed: {e}")
        return

    # Step 4: Test Torque OFF
    logging.debug("Test Case: Torque OFF for Wheg_Group")
    try:
        controller.torque_off_group('Wheg_Group')
        logging.info("Torque disabled for Wheg_Group.")
        time.sleep(1)  # Give time for the command to propagate
    except Exception as e:
        logging.error(f"Torque off test failed: {e}")
        return

    # Step 5: Test Torque ON
    logging.debug("Test Case: Torque ON for Wheg_Group")
    try:
        controller.torque_on_group('Wheg_Group')
        logging.info("Torque enabled for Wheg_Group.")
        time.sleep(1)  # Give time for the command to propagate
    except Exception as e:
        logging.error(f"Torque on test failed: {e}")
        return

    # Step 6: Test sync write (set motors to some initial position)
    logging.debug("Test Case: Sync Write - Set initial motor positions")
    try:
        initial_positions = {motor_id: 2048 for motor_id in controller.motor_groups['Wheg_Group']}
        controller.sync_write_group('Wheg_Group', 'position_goal', initial_positions)
        logging.info("Sync write (position_goal) executed successfully.")
    except Exception as e:
        logging.error(f"Sync write test failed: {e}")
        return

    # Wait for motors to move to the desired position
    time.sleep(2)

    # Step 7: Test bulk read (read positions)
    logging.debug("Test Case: Bulk Read - Read motor positions (in degrees)")
    try:
        motor_ids = controller.motor_groups['Wheg_Group']
        motor_positions = controller.bulk_read_group(motor_ids, ['present_position'])
        for motor_id, data in motor_positions.items():
            logging.info(f"Motor {motor_id} Position (Degrees): {data['position_degrees']:.2f}")
    except Exception as e:
        logging.error(f"Bulk read test failed: {e}")
        return

    # Step 8: Test setting operating mode to velocity control
    logging.debug("Test Case: Set operating mode to velocity control")
    try:
        controller.set_operating_mode_group('Wheg_Group', 'velocity')
        logging.info("Operating mode set to 'velocity' successfully.")
    except Exception as e:
        logging.error(f"Setting operating mode failed: {e}")
        return

    # Step 9: Test setting velocity limit
    logging.debug("Test Case: Set velocity limit for Wheg_Group")
    try:
        controller.set_group_velocity_limit('Wheg_Group')
        logging.info("Velocity limit set successfully.")
    except Exception as e:
        logging.error(f"Setting velocity limit failed: {e}")
        return

    # Step 10: Test setting profile velocity
    logging.debug("Test Case: Set profile velocity for Wheg_Group")
    try:
        controller.set_group_profile_velocity('Wheg_Group')
        logging.info("Profile velocity set successfully.")
    except Exception as e:
        logging.error(f"Setting profile velocity failed: {e}")
        return
    
    # Step 11: Test Set Position
    logging.debug("Test Case: Set target positions")
    try:
        positions = {motor_id: 180.0 for motor_id in controller.motor_groups['Wheg_Group']}  # Set to 180 degrees
        controller.set_position_group('Wheg_Group', positions)
        logging.info(f"Positions set to {positions}")
        time.sleep(2)  # Give time for motors to move
    except Exception as e:
        logging.error(f"Set position test failed: {e}")
        return

    # Step 12: Test Bulk Read for Position
    logging.debug("Test Case: Bulk Read - Get current positions (in degrees)")
    try:
        motor_ids = controller.motor_groups['Wheg_Group']
        motor_positions = controller.bulk_read_group(motor_ids, ['present_position'])
        for motor_id, data in motor_positions.items():
            logging.info(f"Motor {motor_id} Position (Degrees): {data['position_degrees']:.2f}")
    except Exception as e:
        logging.error(f"Bulk read (position) test failed: {e}")
        return

    """
    Test to perform a bulk read of current velocities with torque off.
    """
    try:
        logging.debug("Test Case: Disable torque before reading velocities")

        # Step 1: Disable torque for the motor group
        motor_group = 'Wheg_Group'
        controller.torque_off_group(motor_group)
        logging.info(f"Torque disabled for {motor_group}.")
        
        # Step 2: Perform the bulk read for velocities while torque is off
        logging.debug("Test Case: Bulk Read - Get current velocities")
        motor_ids = controller.motor_groups[motor_group]
        motor_data = controller.bulk_read_group(motor_ids, ['present_velocity'])
        
        if motor_data is None:
            logging.error("Bulk read (velocity) failed: No data returned")
        else:
            # Log the velocities for each motor
            for motor_id, data in motor_data.items():
                logging.info(f"Motor {motor_id} Velocity: {data.get('present_velocity', 0)}")

        # Step 3: Re-enable torque if needed
        controller.torque_on_group(motor_group)
        logging.info(f"Torque re-enabled for {motor_group}.")
        
    except Exception as e:
        logging.error(f"Bulk read (velocity) test failed: {e}")

    try:
        # Step 1: Set drive mode for right-side motors to reverse direction
        logging.debug("Test Case: Set drive mode for right-side motors to reverse")
        controller.set_drive_mode_group('Right_Whegs', reverse_direction=True)
        
        # Step 2: Read the drive mode to confirm it was set correctly
        logging.debug("Test Case: Bulk Read - Get current drive modes for right-side motors")
        motor_data = controller.bulk_read_group('Right_Whegs', ['drive_mode'])
        
        if motor_data is None:
            logging.error("Bulk read (drive mode) failed: No data returned")
        else:
            for motor_id, data in motor_data.items():
                drive_mode = data.get('drive_mode', None)
                if drive_mode == 1:
                    logging.info(f"Motor {motor_id} is set to reverse direction.")
                else:
                    logging.error(f"Motor {motor_id} drive mode is not correctly set to reverse.")

        # Step 3: Change the operating mode (e.g., to velocity control)
        logging.debug("Test Case: Switch operating mode to velocity for right-side motors")
        controller.set_operating_mode_group('Right_Whegs', 'velocity')

        # Step 4: Read the drive mode again to check if it was reset
        logging.debug("Test Case: Bulk Read - Verify drive mode after switching control mode")
        motor_data = controller.bulk_read_group('Right_Side', ['drive_mode'])

        if motor_data is None:
            logging.error("Bulk read (drive mode) failed: No data returned")
        else:
            for motor_id, data in motor_data.items():
                drive_mode = data.get('drive_mode', None)
                if drive_mode == 1:
                    logging.info(f"Motor {motor_id} drive mode (reverse) persisted after switching control mode.")
                else:
                    logging.error(f"Motor {motor_id} drive mode was reset after switching control mode.")

        # Step 5: Reset the drive mode back to normal (if needed)
        logging.debug("Test Case: Reset drive mode for right-side motors to normal")
        controller.set_drive_mode_group('Right_Whegs', reverse_direction=False)

        logging.info("Test completed successfully.")

    except Exception as e:
        logging.error(f"Test for setting drive mode failed: {e}")

    return controller

def test_increment_motor_position(controller):
    """
    Test to increment motor positions by a specified number of degrees in extended position mode.
    """
    try:
        logging.debug("Test Case: Increment motor positions by 90 degrees")

        # Increment the motor positions by 90 degrees
        controller.increment_motor_position_by_degrees('Wheg_Group', 90)

        # Verify the positions were incremented correctly
        motor_ids = controller.motor_groups['Wheg_Group']
        motor_data = controller.bulk_read_group('Right_Whegs', ['present_position'])
        
        if motor_data is None:
            logging.error("Bulk read (positions) failed: No data returned")
        else:
            for motor_id, data in motor_data.items():
                position_degrees = controller.position_to_degrees(data.get('present_position', 0))
                logging.info(f"Motor {motor_id} Position after increment (Degrees): {position_degrees}")

    except Exception as e:
        logging.error(f"Increment motor position test failed: {e}")

if __name__ == "__main__":
    controller = test_dynamixel_controller()
    test_increment_motor_position(controller)
