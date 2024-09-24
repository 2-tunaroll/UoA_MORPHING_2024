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

    # Step 13: Test Set Velocity
    logging.debug("Test Case: Set target velocities")
    try:
        velocities = {motor_id: 100 for motor_id in controller.motor_groups['Wheg_Group']}  # Set velocity to 100
        controller.set_velocity_group('Wheg_Group', velocities)
        logging.info(f"Velocities set to {velocities}")
    except Exception as e:
        logging.error(f"Set velocity test failed: {e}")
        return
    
    # Step 14: Return velocities to 0
    logging.debug("Test Case: Set target velocities")
    try:
        velocities = {motor_id: 0 for motor_id in controller.motor_groups['Wheg_Group']}  # Set velocity to 100
        controller.set_velocity_group('Wheg_Group', velocities)
        logging.info(f"Velocities set to {velocities}")
    except Exception as e:
        logging.error(f"Set velocity test failed: {e}")
        return


    # Step 14: Test Bulk Read for Velocity
    logging.debug("Test Case: Bulk Read - Get current velocities")
    try:
        motor_velocities = controller.bulk_read_group(motor_ids, ['present_velocity'])
        for motor_id, data in motor_velocities.items():
            logging.info(f"Motor {motor_id} Velocity: {data['present_velocity']}")
    except Exception as e:
        logging.error(f"Bulk read (velocity) test failed: {e}")
        return
    logging.info("All tests completed successfully.")

if __name__ == "__main__":
    test_dynamixel_controller()
