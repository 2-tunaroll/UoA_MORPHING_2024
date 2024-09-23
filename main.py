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
PIVOT_STEP = config['pivot_parameters']['pivot_step']
PIVOT_MAX_ANGLE = config['pivot_parameters']['max_angle']
PIVOT_MIN_ANGLE = config['pivot_parameters']['min_angle']
front_pivot_angle = config['pivot_parameters']['initial_front_angle']
rear_pivot_angle = config['pivot_parameters']['initial_rear_angle']

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

def set_wheg_velocity(dynamixel, wheg_ids, rpm):
    # Check the mode of the whegs
    for wheg_id in wheg_ids:
        mode = dynamixel.check_operating_mode(wheg_id)
        if mode != 'velocity':
            dynamixel.set_operating_mode(wheg_id, 'velocity')
            logging.info(f"Operating mode set to 'velocity' for wheg_id={wheg_id}")
    logging.debug(f"Setting wheg velocity: wheg_ids={list(wheg_ids)}, rpm={rpm}")
    for wheg_id in wheg_ids:
        dynamixel.set_goal_velocity(wheg_id, rpm)
        logging.debug(f"Set wheg velocity: wheg_id={wheg_id}, rpm={rpm}")

# Function to set wheg position
def set_wheg_position(dynamixel, wheg_ids, position):
    # Check the mode of the whegs
    for wheg_id in wheg_ids:
        mode = dynamixel.check_operating_mode(wheg_id)
        if mode != 'position':
            dynamixel.set_operating_mode(wheg_id, 'position')
            logging.info(f"Operating mode set to 'position' for wheg_id={wheg_id}")
    logging.debug(f"Setting wheg position: wheg_ids={list(wheg_ids)}, position={position}")
    for wheg_id in wheg_ids:
        dynamixel.set_group_profile_velocity('Wheg_Group', 10)  # Set velocity limit to move pivots
        dynamixel.set_goal_position(wheg_id, position)
        logging.debug(f"Set wheg position: wheg_id={wheg_id}, position={position}")

# Function to control pivot position
def set_pivot_position(dynamixel, pivot_id, position):
    logging.debug(f"Setting pivot position: pivot_id={pivot_id}, position={position}")
    dynamixel.set_goal_position(pivot_id, position)
    logging.debug(f"Set pivot position: pivot_id={pivot_id}, position={position}")

# Function to get and store positions of all whegs and pivots
def get_motor_positions(dynamixel):
    logging.debug("Getting motor positions")
    motor_positions = {}
    for wheg_name, wheg_id in WHEGS.items():
        position = dynamixel.get_present_position(wheg_id)
        motor_positions[wheg_name] = position
    for pivot_name, pivot_id in PIVOTS.items():
        position = dynamixel.get_present_position(pivot_id)
        motor_positions[pivot_name] = position
    logging.debug(f"Motor positions: {motor_positions}")
    return motor_positions

# Function to log motor positions and controller inputs at the same time
def log_positions_and_inputs(motor_positions, l2_trigger, r2_trigger, button_states, dpad_input):
    logging.info(f"Motor Positions: {motor_positions}")
    logging.info(f"L2 Trigger: {l2_trigger}, R2 Trigger: {r2_trigger}")
    logging.info(f"Button States: {button_states}")
    logging.info(f"D-Pad Input: {dpad_input}")

# Function to control pivot movement using the D-pad
def control_pivots_with_dpad(dynamixel, button_states):
    global front_pivot_angle, rear_pivot_angle

    # Front pivot control (D-pad up/down)
    if button_states['dpad_down']:
        front_pivot_angle = min(front_pivot_angle + PIVOT_STEP, PIVOT_MAX_ANGLE)
    elif button_states['dpad_up']:
        front_pivot_angle = max(front_pivot_angle - PIVOT_STEP, PIVOT_MIN_ANGLE)
    
    # Rear pivot control (D-pad left/right)
    if button_states['dpad_right']:
        rear_pivot_angle = min(rear_pivot_angle + PIVOT_STEP, PIVOT_MAX_ANGLE)
    elif button_states['dpad_left']:
        rear_pivot_angle = max(rear_pivot_angle - PIVOT_STEP, PIVOT_MIN_ANGLE)

    # Set the new goal positions for the pivots
    dynamixel.set_goal_position(PIVOTS['FRONT_PIVOT'], front_pivot_angle)
    dynamixel.set_goal_position(PIVOTS['REAR_PIVOT'], rear_pivot_angle)

    logging.info(f"Front pivot angle set to {front_pivot_angle}")
    logging.info(f"Rear pivot angle set to {rear_pivot_angle}")

# Define the initialization for each gait (for whegs only, pivots are disabled)
def gait_init_1(dynamixel):
    logging.info("Initializing Gait 1")
    dynamixel.set_group_profile_velocity('Wheg_Group', 10)  # Set velocity limit to move pivots
    dynamixel.set_group_profile_acceleration('Wheg_Group', 1)
    time.sleep(3) # Wait for the motors to reach the velocity limit
    set_wheg_position(dynamixel, WHEGS.values(), 180)
    set_pivot_position(dynamixel, PIVOTS['FRONT_PIVOT'], 180)
    set_pivot_position(dynamixel, PIVOTS['REAR_PIVOT'], 180)
    time.sleep(3) # Wait for the motors to reach the position

def gait_init_2(dynamixel):
    logging.info("Initializing Gait 2")
    dynamixel.set_group_profile_velocity('Wheg_Group', 10)  # Set velocity limit to move pivots
    dynamixel.set_group_profile_acceleration('Wheg_Group', 10)
    time.sleep(3) # Wait for the motors to reach the velocity limit
    set_wheg_position(dynamixel, WHEGS.values(), 180)
    set_pivot_position(dynamixel, PIVOTS['FRONT_PIVOT'], 180)
    set_pivot_position(dynamixel, PIVOTS['REAR_PIVOT'], 180)
    time.sleep(3) # Wait for the motors to reach the position

def gait_init_3(dynamixel):      
    logging.info("Initializing Gait 3")
    dynamixel.set_group_profile_velocity('Wheg_Group', 10)  # Set velocity limit to move pivots
    dynamixel.set_group_profile_acceleration('Wheg_Group', 100)
    time.sleep(3) # Wait for the motors to reach the velocity limit
    set_wheg_position(dynamixel, WHEGS.values(), 180)
    set_pivot_position(dynamixel, PIVOTS['FRONT_PIVOT'], 180)
    set_pivot_position(dynamixel, PIVOTS['REAR_PIVOT'], 180)
    time.sleep(3) # Wait for the motors to reach the position

def gait_init_4(dynamixel):
    logging.info("Initializing Gait 4")
    dynamixel.set_group_profile_velocity('Wheg_Group', 10)  # Set velocity limit to move pivots
    dynamixel.set_group_profile_acceleration('Wheg_Group', 1000)
    time.sleep(3) # Wait for the motors to reach the velocity limit
    set_wheg_position(dynamixel, WHEGS.values(), 180)
    set_pivot_position(dynamixel, PIVOTS['FRONT_PIVOT'], 180)
    set_pivot_position(dynamixel, PIVOTS['REAR_PIVOT'], 180)
    time.sleep(3) # Wait for the motors to reach the position
    
# Define multiple gaits (for whegs only, pivots are disabled)
def gait_1(dynamixel, wheg_rpm, button_states, dpad_input=None):
    logging.debug("Executing Gait 1")

    if wheg_rpm > 1:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_group_position('Two_Right_One_Left', increment)
        dynamixel.increment_group_position('Two_Left_One_Right', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input)

def gait_2(dynamixel, wheg_rpm, button_states, dpad_input=None):
    logging.debug("Executing Gait 2")
    
    if wheg_rpm > 1:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_group_position('Two_Right_One_Left', increment)
        dynamixel.increment_group_position('Two_Left_One_Right', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input)

def gait_3(dynamixel, wheg_rpm, button_states, dpad_input=None):
    logging.debug("Executing Gait 3")

    if wheg_rpm > 1:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_group_position('Two_Right_One_Left', increment)
        dynamixel.increment_group_position('Two_Left_One_Right', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input)

def gait_4(dynamixel, wheg_rpm, button_states, dpad_input=None):
    logging.debug("Executing Gait 4")
    
    if wheg_rpm > 1:
        # Set the velocity limit for all whegs based on controller input
        dynamixel.set_group_profile_velocity('Wheg_Group', wheg_rpm)  # Set velocity based on input

        # Increase the position of the whegs in groups
        increment = 180 # Increment by 180 degrees
        dynamixel.increment_group_position('Two_Right_One_Left', increment)
        dynamixel.increment_group_position('Two_Left_One_Right', increment)

    # Control pivots using the D-pad
    control_pivots_with_dpad(dynamixel, dpad_input)

# Emergency stop function (whegs only)
def emergency_stop(dynamixel):
    logging.warning("Emergency stop activated")
    set_wheg_velocity(dynamixel, WHEGS.values(), 0)  # Stop all wheg motors

# Main function integrating the PS4 controller and Dynamixel SDK
def main():
    try:
        # Initialize PS4 controller and Dynamixel
        ps4_controller = PS4Controller()
        dynamixel = DynamixelController(device_name='/dev/ttyACM0', baudrate=57600)
        logging.info("Initialized PS4 controller and Dynamixel")

        # List of gaits available for selection
        gait_list = [gait_1, gait_2, gait_3, gait_4]
        gait_init_list = [gait_init_1, gait_init_2, gait_init_3, gait_init_4]
        current_gait_index = 0
        total_gaits = len(gait_list)

        wheg_rpm = 0  # Start with no motion
        current_gait = gait_1  # Start with Gait 1
        previous_gait = None  # Keep track of the previous gait to detect changes
        emergency_stop_activated = False  # Track emergency stop state
        report_timer = 0  # Timer to report motor positions every second

        # Turn on torque and set operating modes for whegs only
        for wheg_id in WHEGS.values():
            #Check that the whegs on the right side have correct direction
            if wheg_id in [WHEGS['RM_WHEG'], WHEGS['RF_WHEG'], WHEGS['RR_WHEG']]:
                offset = dynamixel.get_homing_offset(wheg_id)  # Get homing offset for whegs
                logging.info(f"Homing offset for wheg_id={wheg_id} is {offset}")
                if offset != 0:
                    dynamixel.set_homing_offset(wheg_id, 0)
                    logging.info(f"Set homing offset to 4096 for wheg_id={wheg_id}")
            dynamixel.set_operating_mode(wheg_id, 'velocity')
            dynamixel.torque_on(wheg_id)
            logging.info(f"Torque on for wheg_id={wheg_id}")

        # Turn on torque for pivots (although they are disabled in gaits)
        for pivot_id in PIVOTS.values():
            dynamixel.get_homing_offset(pivot_id)  # Get homing offset for pivots
            dynamixel.set_operating_mode(pivot_id, 'position')
            dynamixel.torque_on(pivot_id)

        # Set initial velocity limits for pivots to 2 RPM
        dynamixel.set_group_velocity_limit('Pivot_Group', 5)
        dynamixel.set_group_profile_velocity('Pivot_Group', 5)
        # Set initial velocity limit for whegs to 10 RPM
        dynamixel.set_group_velocity_limit('Wheg_Group', 10)
        dynamixel.set_group_profile_velocity('Wheg_Group', 10)
        dynamixel.set_group_profile_acceleration('Wheg_Group', 1)

        # Main loop
        while True:
            start_time = time.time()  # Track time for position reporting
            # Get button states for emergency stop and gait selection
            button_states = ps4_controller.get_button_input()
            logging.debug(f"Button states: {button_states}")

            # Check if controller is disconnected
            if button_states is None:
                logging.error("Controller is disconnected. Stopping robot.")
                emergency_stop()
                break

            # Emergency Stop using Circle button
            if button_states['circle']:
                emergency_stop_activated = True
                emergency_stop(dynamixel)

            # Deactivate emergency stop if X button is pressed
            if button_states['x'] and emergency_stop_activated:
                emergency_stop_activated = False
                logging.info("Emergency Stop Deactivated. Resuming control...")
            
            motor_positions = get_motor_positions(dynamixel)

            if not emergency_stop_activated:
                # Get trigger input (R2) for speed adjustment
                l2_trigger, r2_trigger = ps4_controller.get_trigger_input()
                logging.debug(f"Trigger inputs: L2={l2_trigger}, R2={r2_trigger}")
                dpad_input = ps4_controller.get_dpad_input()
                logging.debug(f"D-Pad input: {dpad_input}")

                # Adjust the speed of the whegs based on the right trigger
                wheg_rpm = adjust_wheg_speed(r2_trigger, wheg_rpm)

                # Triangle button: Move to the next gait
                if button_states['triangle']:
                    current_gait_index = (current_gait_index + 1) % total_gaits
                    current_gait = gait_list[current_gait_index]
                
                # Square button: Move to the previous gait
                elif button_states['square']:
                    current_gait_index = (current_gait_index - 1) % total_gaits
                    current_gait = gait_list[current_gait_index]

            if previous_gait != current_gait:    # Execute the new gait
                logging.info("Switching to new gait: " + str(current_gait_index))
                gait_init_list[current_gait_index](dynamixel)

            previous_gait = current_gait
            current_gait(dynamixel, wheg_rpm, button_states, dpad_input)

            # Report motor positions and log controller inputs every 5 seconds
            current_time = time.time()
            if current_time - report_timer >= 5:  # Report every 5 seconds
                log_positions_and_inputs(motor_positions, l2_trigger, r2_trigger, button_states, dpad_input)
                report_timer = current_time  # Reset the timer

            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("Terminating program...")

    finally:
        # Safely set wheg and pivot motors' velocity to 0 and close the controller
        for wheg_id in WHEGS.values():
            set_wheg_velocity(dynamixel, [wheg_id], 0)
            logging.info(f"Set velocity to 0 for wheg_id={wheg_id}")

        ps4_controller.close()
        dynamixel.close()
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()
