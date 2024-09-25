import logging
from dynamixel_control import DynamixelController
import time

# Initialize logging for console output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def test_dynamixel_controller():
    """
    Test the DynamixelController with basic motor group operations.
    """
    try:
        # Initialize the controller
        logging.debug("Test Case: Initialize DynamixelController")
        controller = DynamixelController(config_path='config.yaml')
        logging.info("DynamixelController initialized successfully.")

        # Open port and set baudrate
        logging.debug("Test Case: Open port and set baudrate")
        controller.open_port()
        logging.info(f"Port {controller.device_name} opened with baudrate {controller.baudrate}.")

        # Test torque off and on for the 'Wheg_Group'
        logging.debug("Test Case: Torque OFF for Wheg_Group")
        controller.torque_off_group('Wheg_Group')
        logging.info("Torque disabled for Wheg_Group.")
        time.sleep(1)

        logging.debug("Test Case: Torque ON for Wheg_Group")
        controller.torque_on_group('Wheg_Group')
        logging.info("Torque enabled for Wheg_Group.")
        time.sleep(1)

        # Sync write to set initial positions
        logging.debug("Test Case: Sync Write - Set initial motor positions")
        initial_positions = {motor_id: 2048 for motor_id in controller.motor_groups['Wheg_Group']}
        controller.sync_write_group('Wheg_Group', 'position_goal', initial_positions)
        logging.info("Sync write (position_goal) executed successfully.")
        time.sleep(2)

        # Bulk read motor positions in degrees
        logging.debug("Test Case: Bulk Read - Read motor positions (in degrees)")
        motor_positions = controller.bulk_read_group('Wheg_Group', ['present_position'])
        for motor_id, data in motor_positions.items():
            logging.info(f"Motor {motor_id} Position (Degrees): {data['position_degrees']:.2f}")

        # Set operating mode to velocity control
        logging.debug("Test Case: Set operating mode to velocity control")
        controller.set_operating_mode_group('Wheg_Group', 'velocity')
        logging.info("Operating mode set to 'velocity' successfully.")

        # Set velocity limits
        logging.debug("Test Case: Set velocity limit for Wheg_Group")
        controller.set_group_velocity_limit('Wheg_Group')
        logging.info("Velocity limit set successfully.")

        # Set profile velocity
        logging.debug("Test Case: Set profile velocity for Wheg_Group")
        controller.set_group_profile_velocity('Wheg_Group')
        logging.info("Profile velocity set successfully.")

        # Set positions to 180 degrees
        logging.debug("Test Case: Set target positions")
        positions = {motor_id: 180.0 for motor_id in controller.motor_groups['Wheg_Group']}
        controller.set_position_group('Wheg_Group', positions)
        logging.info(f"Positions set to {positions}")
        time.sleep(2)

        # Bulk read current positions
        logging.debug("Test Case: Bulk Read - Get current positions (in degrees)")
        motor_positions = controller.bulk_read_group('Wheg_Group', ['present_position'])
        for motor_id, data in motor_positions.items():
            logging.info(f"Motor {motor_id} Position (Degrees): {data['position_degrees']:.2f}")

        # Bulk read velocities with torque off
        logging.debug("Test Case: Torque OFF and Bulk Read - Get current velocities")
        controller.torque_off_group('Wheg_Group')
        motor_data = controller.bulk_read_group('Wheg_Group', ['present_velocity'])
        for motor_id, data in motor_data.items():
            logging.info(f"Motor {motor_id} Velocity: {data.get('present_velocity', 0)}")
        controller.torque_on_group('Wheg_Group')
        logging.info("Torque re-enabled for Wheg_Group.")

        # Set and test drive mode
        logging.debug("Test Case: Set drive mode for Right_Whegs")
        controller.set_drive_mode_group('Right_Whegs', reverse_direction=True)
        motor_data = controller.bulk_read_group('Right_Whegs', ['drive_mode'])
        for motor_id, data in motor_data.items():
            drive_mode = data.get('drive_mode', None)
            if drive_mode == 1:
                logging.info(f"Motor {motor_id} is set to reverse direction.")
            else:
                logging.error(f"Motor {motor_id} drive mode is not correctly set to reverse.")
        controller.set_drive_mode_group('Right_Whegs', reverse_direction=False)

        logging.info("All tests completed successfully.")
        return controller

    except Exception as e:
        logging.error(f"Test failed: {e}")
        return None

def test_increment_motor_position(controller):
    """
    Test to increment motor positions by 90 degrees in extended position mode.
    """
    try:
        logging.debug("Test Case: Increment motor positions by 90 degrees")
        controller.increment_motor_position_by_degrees('Wheg_Group', 90)
        motor_data = controller.bulk_read_group('Wheg_Group', ['present_position'])
        for motor_id, data in motor_data.items():
            position_degrees = controller.position_to_degrees(data.get('present_position', 0))
            logging.info(f"Motor {motor_id} Position after increment (Degrees): {position_degrees}")

    except Exception as e:
        logging.error(f"Increment motor position test failed: {e}")

if __name__ == "__main__":
    # Run the test cases
    controller = test_dynamixel_controller()
    if controller:
        test_increment_motor_position(controller)
