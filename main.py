"""
This script implements the main logic for converting PS4 controller inputs into dynamixel motor commands.
Different gaits are implemented.
The script also logs motor positions and controller inputs to a log file.

Dependencies:
    DynamixelController class from dynamixel_control.py
    PS4Controller class from controller.py
    DYNAMIXELSDK
    init file uploaded to the Open RB-150 Board
"""
# External Imports
import os
import time
import logging
import yaml

# Internal Imports
from datetime import datetime
from controller import PS4Controller
from dynamixel_control import DynamixelController

# Load configuration from YAML file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Create Logs directory if it doesn't exist
log_directory = config['logging']['log_directory']
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Generate log file based on date and time
log_filename = f"{log_directory}/flik_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Set up logging to log motor positions and controller inputs
logging.basicConfig(
    filename=log_filename,
    level=getattr(logging, config['logging']['log_level_file']),  
    format='%(asctime)s %(levelname)s: %(message)s'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, config['logging']['log_level_console']))  # Set console output
console_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# Add the handler to the logger
logging.getLogger().addHandler(console_handler)

# Motor and pivot configurations from the YAML file
WHEGS = config['motor_ids']['whegs']
PIVOTS = config['motor_ids']['pivots']
MAX_RPM = config['wheg_parameters']['max_rpm']
MIN_RPM = config['wheg_parameters']['min_rpm']
SMOOTHNESS = config['wheg_parameters']['smoothness']
front_pivot_angle = config['pivot_parameters']['initial_front_angle']
rear_pivot_angle = config['pivot_parameters']['initial_rear_angle']

class RobotState:
    def __init__(self, config):
        """
        Initialize the robot state, including pivot angles and wheg RPMs.
        
        :param config: The configuration dictionary loaded from the YAML file.
        """
        self.config = config
        
        # Initialize pivot angles
        self.front_pivot_angle = config['pivot_parameters']['initial_front_angle']
        self.rear_pivot_angle = config['pivot_parameters']['initial_rear_angle']
        
        # Initialize wheg RPMs (assume they start at the minimum RPM)
        self.wheg_rpms = {wheg: config['wheg_parameters']['min_rpm'] for wheg in config['motor_ids']['whegs']}

    def adjust_front_pivot(self, step, min_angle, max_angle, direction):
        """Adjust the front pivot angle based on D-pad input."""
        if direction == 'up':
            self.front_pivot_angle = max(self.front_pivot_angle - step, min_angle)
        elif direction == 'down':
            self.front_pivot_angle = min(self.front_pivot_angle + step, max_angle)

    def adjust_rear_pivot(self, step, min_angle, max_angle, direction):
        """Adjust the rear pivot angle based on D-pad input."""
        if direction == 'left':
            self.rear_pivot_angle = max(self.rear_pivot_angle - step, min_angle)
        elif direction == 'right':
            self.rear_pivot_angle = min(self.rear_pivot_angle + step, max_angle)

    def adjust_wheg_rpm(self, wheg_id, trigger_value, max_rpm, min_rpm, smoothness):
        """Adjust the RPM of the specified wheg motor based on trigger input."""
        current_rpm = self.wheg_rpms[wheg_id]
        target_rpm = ((trigger_value + 1) / 2) * (max_rpm - min_rpm) + min_rpm
        
        # Smooth transition to target RPM
        if target_rpm > current_rpm:
            self.wheg_rpms[wheg_id] = min(current_rpm + smoothness, target_rpm)
        else:
            self.wheg_rpms[wheg_id] = max(current_rpm - smoothness, target_rpm)
    
    def log(self, motor_positions, l2_trigger, r2_trigger, button_states, dpad_input):
        """Log the current robot state, including pivots, whegs, and controller inputs."""
        logging.info(f"Front pivot angle: {self.front_pivot_angle}")
        logging.info(f"Rear pivot angle: {self.rear_pivot_angle}")
        logging.info(f"Wheg RPMs: {self.wheg_rpms}")
        logging.info(f"Motor Positions: {motor_positions}")
        logging.info(f"L2 Trigger: {l2_trigger}, R2 Trigger: {r2_trigger}")
        logging.info(f"Button States: {button_states}")
        logging.info(f"D-Pad Input: {dpad_input}")


def adjust_wheg_speed(trigger_value, current_rpm):
    """ Function to adjust the speed of the whegs based on how far the right trigger is pressed. Smooth transition to target RPM. """
    logging.debug(f"Adjusting wheg speed: trigger_value={trigger_value}, current_rpm={current_rpm}")
    target_rpm = ((trigger_value + 1) / 2) * (MAX_RPM - MIN_RPM) + MIN_RPM # Trigger value ranges from -1 to 1, map this to RPM range
    # Implement smooth transition to target RPM
    if target_rpm > current_rpm:
        current_rpm = min(current_rpm + SMOOTHNESS, target_rpm)
    else:
        current_rpm = max(current_rpm - SMOOTHNESS, target_rpm)
    logging.debug(f"Adjusted wheg speed: target_rpm={target_rpm}, current_rpm={current_rpm}")
    return current_rpm

# Function to log motor positions and controller inputs at the same time
def log_positions_and_inputs(motor_positions, l2_trigger, r2_trigger, button_states, dpad_input):
    logging.info(f"Motor Positions: {motor_positions}")
    logging.info(f"L2 Trigger: {l2_trigger}, R2 Trigger: {r2_trigger}")
    logging.info(f"Button States: {button_states}")
    logging.info(f"D-Pad Input: {dpad_input}")

def control_pivots_with_dpad(dynamixel, dpad_inputs, robot_state):
    """
    Control the front and rear pivots using the D-pad inputs from the controller.
    
    :param dynamixel: The DynamixelController instance.
    :param dpad_inputs: A dictionary with the state of each button, including the D-pad.
    :param config: The YAML configuration containing pivot parameters (pivot_step, min/max angles).
    :param robot_state: An instance of RobotState managing the pivot angles.
    """
    # Extract pivot parameters from config
    pivot_step = config['pivot_parameters']['pivot_step']
    pivot_min_angle = config['position_limits']['Hinges']['min_degrees']
    pivot_max_angle = config['position_limits']['Hinges']['max_degrees']

    # Adjust front and rear pivots based on D-pad input
    if dpad_inputs['dpad_down']:
        robot_state.adjust_front_pivot(pivot_step, pivot_min_angle, pivot_max_angle, 'down')
    elif dpad_inputs['dpad_up']:
        robot_state.adjust_front_pivot(pivot_step, pivot_min_angle, pivot_max_angle, 'up')

    if dpad_inputs['dpad_right']:
        robot_state.adjust_rear_pivot(pivot_step, pivot_min_angle, pivot_max_angle, 'right')
    elif dpad_inputs['dpad_left']:
        robot_state.adjust_rear_pivot(pivot_step, pivot_min_angle, pivot_max_angle, 'left')

    # Prepare positions for sync write
    pivot_positions = {
        config['motor_ids']['pivots']['FRONT_PIVOT']: robot_state.front_pivot_position,
        config['motor_ids']['pivots']['REAR_PIVOT']: robot_state.rear_pivot_position
    }
    
    # Sync write the goal positions for the pivots
    dynamixel.set_position_group('Pivot_Group', pivot_positions)

    # Logging
    logging.info(f"Front pivot angle set to {robot_state.front_pivot_angle} degrees (ticks: {robot_state.front_pivot_position})")
    logging.info(f"Rear pivot angle set to {robot_state.rear_pivot_angle} degrees (ticks: {robot_state.rear_pivot_position})")

# Define the initialization for each gait (for whegs only, pivots are disabled)
def gait_init_1(dynamixel):
    logging.info("Initializing Gait 1")
    dynamixel.set_position_group('Wheg_Group', 180)
    dynamixel.set_position_group('Pivot_Group', 180)

def gait_init_2(dynamixel):
    logging.info("Initializing Gait 2")
    dynamixel.set_position_group('Wheg_Group', 180)
    dynamixel.set_position_group('Pivot_Group', 180)

def gait_init_3(dynamixel):      
    logging.info("Initializing Gait 3")
    dynamixel.set_position_group('Wheg_Group', 180)
    dynamixel.set_position_group('Pivot_Group', 180)


def gait_init_4(dynamixel):
    logging.info("Initializing Gait 4")
    dynamixel.set_position_group('Wheg_Group', 180)
    dynamixel.set_position_group('Pivot_Group', 180)

    
# Define multiple gaits (for whegs only, pivots are disabled)
def gait_1(dynamixel, wheg_rpm, button_states, dpad_input, robot_state):
    logging.debug("Executing Gait 1")

    if wheg_rpm != 0:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_group_position('Wheg_Group', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input, robot_state)

def gait_2(dynamixel, wheg_rpm, button_states, dpad_input, robot_state):
    logging.debug("Executing Gait 2")
    
    if wheg_rpm != 0:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 360 # Increment by 180 degrees
        dynamixel.increment_motor_position_by_degrees('Wheg_Group', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input, robot_state)

def gait_3(dynamixel, wheg_rpm, button_states, dpad_input, robot_state):
    logging.debug("Executing Gait 3")

    if wheg_rpm != 0:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_motor_position_by_degrees('Wheg_Group', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input, robot_state)

def gait_4(dynamixel, wheg_rpm, button_states, dpad_input, robot_state):
    logging.debug("Executing Gait 4")
    
    if wheg_rpm != 0:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_motor_position_by_degrees('Wheg_Group', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input, robot_state)

# Emergency stop function
def emergency_stop(dynamixel):
    logging.warning("Emergency stop activated")
    dynamixel.set_group_velocity('All_Motors', 0)  # Stop all motors


def main():
    try:
        # Initialize PS4 controller, Dynamixel, and RobotState
        ps4_controller = PS4Controller()
        dynamixel = DynamixelController()
        robot_state = RobotState(config)

        logging.info("Initialized PS4 controller, Dynamixel, and Robot State")

        # Gait initialization and selection
        gait_list = [gait_1, gait_2, gait_3, gait_4]
        gait_init_list = [gait_init_1, gait_init_2, gait_init_3, gait_init_4]
        current_gait_index = 0
        total_gaits = len(gait_list)

        wheg_rpm = 0  # No motion at start
        current_gait = gait_list[current_gait_index]
        previous_gait = None
        emergency_stop_activated = False
        report_timer = time.time()

        # Set the right side whegs to reverse
        dynamixel.set_drive_mode_group('Right_Whegs', True)
        dynamixel.set_drive_mode_group('Left_Whegs', False)
        # Set position limits for the pivot motors
        # dynamixel.set_position_limits_group('Pivot_Group', config['position_limits']['Hinges']['min_degrees'], config['position_limits']['Hinges']['max_degrees'])

        # Main loop
        while True:
            button_states = ps4_controller.get_button_input()

            # Check for controller disconnection
            if button_states is None:
                logging.error("Controller is disconnected. Stopping robot.")
                emergency_stop(dynamixel)
                break

            # Emergency stop using Circle button
            if button_states['circle']:
                emergency_stop_activated = True
                emergency_stop(dynamixel)

            # Resume control after emergency stop with X button
            if button_states['x'] and emergency_stop_activated:
                emergency_stop_activated = False
                logging.info("Emergency Stop Deactivated. Resuming control...")

            motor_positions = dynamixel.bulk_read_group('All_Motors', ['present_position'])

            if not emergency_stop_activated:
                l2_trigger, r2_trigger = ps4_controller.get_trigger_input()
                dpad_input = ps4_controller.get_dpad_input()
                logging.debug(f"Trigger inputs: L2={l2_trigger}, R2={r2_trigger}")
                logging.debug(f"D-Pad input: {dpad_input}")

                # Adjust the speed of the whegs based on the right trigger
                wheg_rpm = adjust_wheg_speed(r2_trigger, wheg_rpm)

                # Gait selection with Triangle and Square buttons
                if button_states['triangle']:
                    current_gait_index = (current_gait_index + 1) % total_gaits
                    current_gait = gait_list[current_gait_index]
                elif button_states['square']:
                    current_gait_index = (current_gait_index - 1) % total_gaits
                    current_gait = gait_list[current_gait_index]

            # If the gait has changed, initialize the new gait
            if previous_gait != current_gait:
                logging.info(f"Switching to new gait: {current_gait_index}")
                gait_init_list[current_gait_index](dynamixel)

            previous_gait = current_gait
            current_gait(dynamixel, wheg_rpm, button_states, dpad_input, robot_state)

            # Report motor positions every 5 seconds
            current_time = time.time()
            if current_time - report_timer >= 5:
                robot_state.log(motor_positions, l2_trigger, r2_trigger, button_states, dpad_input)
                report_timer = current_time

            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("Terminating program...")

    finally:
        # Safely stop all motors
        dynamixel.set_velocity_group('All_Motors', 0)
        dynamixel.set_position_group('All_Motors', 180)
        ps4_controller.close()
        dynamixel.close()
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()
