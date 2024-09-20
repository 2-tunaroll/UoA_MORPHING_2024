import os
import time
import logging
from datetime import datetime
from controller import PS4Controller
from dynamixel_control import DynamixelController

# Create Logs directory if it doesn't exist
if not os.path.exists('Logs'):
    os.makedirs('Logs')

# Generate log file based on date and time
log_filename = f"Logs/robot_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Set up logging to log motor positions and controller inputs
logging.basicConfig(
    filename=log_filename, 
    level=logging.DEBUG,  # Changed to DEBUG to capture more detailed logs
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Motor IDs for wheeled legs, front on the robot is defined by arrow on body
WHEGS = {
    'LR_WHEG': 1, 'LM_WHEG': 2, 'LF_WHEG': 3,
    'RR_WHEG': 4, 'RM_WHEG': 5, 'RF_WHEG': 6
}
# Motor IDs for pivots, front pivot is defined by the arrow on the body
PIVOTS = {
    'FRONT_PIVOT': 7, 'REAR_PIVOT': 8
}

# Velocity control limits for whegs and pivots
MAX_RPM = 200  # Max RPM for wheg motors
MIN_RPM = 0    # Min RPM for wheg motors
SMOOTHNESS = 10  # Controls how smoothly the speed increases
PIVOT_STEP = 1  # Step size in degrees for each D-pad press

# Track the current pivot positions
front_pivot_angle = 180  # Start position for front pivot
rear_pivot_angle = 180   # Start position for rear pivot

# Track the current wheg positions
wheg_positions = {
    'LR_WHEG': 0, 'LM_WHEG': 0, 'LF_WHEG': 0,
    'RR_WHEG': 0, 'RM_WHEG': 0, 'RF_WHEG': 0
}

# Adjust the velocity based on the right trigger input
def adjust_wheg_speed(trigger_value, current_rpm):
    logging.debug(f"Adjusting wheg speed: trigger_value={trigger_value}, current_rpm={current_rpm}")
    # Map trigger value (-1 to 1) to RPM range (MIN_RPM to MAX_RPM)
    target_rpm = ((trigger_value + 1) / 2) * (MAX_RPM - MIN_RPM) + MIN_RPM
    
    # Smooth the transition to the target RPM
    if target_rpm > current_rpm:
        current_rpm = min(current_rpm + SMOOTHNESS, target_rpm)
    else:
        current_rpm = max(current_rpm - SMOOTHNESS, target_rpm)
    
    logging.debug(f"Adjusted wheg speed: target_rpm={target_rpm}, current_rpm={current_rpm}")
    return current_rpm

# Function to control whegs velocity
def set_wheg_velocity(dynamixel, wheg_ids, rpm):
    logging.debug(f"Setting wheg velocity: wheg_ids={list(wheg_ids)}, rpm={rpm}")
    for wheg_id in wheg_ids:
        dynamixel.set_goal_velocity(wheg_id, rpm)
        logging.debug(f"Set wheg velocity: wheg_id={wheg_id}, rpm={rpm}")

# Function to set wheg position
def set_wheg_position(dynamixel, wheg_ids, position):
    logging.debug(f"Setting wheg position: wheg_ids={list(wheg_ids)}, position={position}")
    for wheg_id in wheg_ids:
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
def log_positions_and_inputs(motor_positions, l2_trigger, r2_trigger, button_states):
    logging.info(f"Motor Positions: {motor_positions}")
    logging.info(f"L2 Trigger: {l2_trigger}, R2 Trigger: {r2_trigger}")
    logging.info(f"Button States: {button_states}")

# Function to control pivot movement using the D-pad
def control_pivots_with_dpad(dynamixel, button_states):
    global front_pivot_angle, rear_pivot_angle

    # Front pivot control (D-pad up/down)
    if button_states['dpad_up']:
        front_pivot_angle = min(front_pivot_angle + PIVOT_STEP, PIVOT_MAX_ANGLE)
    elif button_states['dpad_down']:
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

# Define multiple gaits (for whegs only, pivots are disabled)
def gait_1(dynamixel, wheg_rpm):
    logging.info("Executing Gait 1")
    set_wheg_position(dynamixel, WHEGS.values(), 180)

def gait_2(dynamixel, wheg_rpm):
    logging.info("Executing Gait 2")
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm / 2)  # Slower whegs

def gait_3(dynamixel, wheg_rpm):
    logging.info("Executing Gait 3")
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm)

def gait_4(dynamixel, wheg_rpm):
    logging.info("Executing Gait 4")
    set_wheg_velocity(dynamixel, WHEGS.values(), -wheg_rpm)  # Reverse direction for whegs

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

        # Initial motor states
        wheg_rpm = 0  # Start with no motion
        current_gait = gait_1  # Start with Gait 1
        previous_gait = None  # Keep track of the previous gait to detect changes
        emergency_stop_activated = False  # Track emergency stop state
        report_timer = 0  # Timer to report motor positions every second

        # Turn on torque and set operating modes for whegs only
        for wheg_id in WHEGS.values():
            dynamixel.set_operating_mode(wheg_id, 'velocity')
            dynamixel.torque_on(wheg_id)
            logging.info(f"Torque on for wheg_id={wheg_id}")

        # # Turn on torque for pivots (although they are disabled in gaits)
        # for pivot_id in PIVOTS.values():
        #     dynamixel.set_operating_mode(pivot_id, 'position')
        #     dynamixel.torque_on(pivot_id)

        # Main loop
        while True:
            start_time = time.time()  # Track time for position reporting
            
            # Get button states for emergency stop and gait selection
            button_states = ps4_controller.get_button_input()
            logging.debug(f"Button states: {button_states}")

            # Emergency Stop using Circle button
            if button_states['circle']:
                emergency_stop_activated = True
                emergency_stop(dynamixel)

            # Deactivate emergency stop if X button is pressed
            if button_states['x'] and emergency_stop_activated:
                emergency_stop_activated = False
                logging.info("Emergency Stop Deactivated. Resuming control...")

            if not emergency_stop_activated:
                # Get trigger input (R2) for speed adjustment
                l2_trigger, r2_trigger = ps4_controller.get_trigger_input()
                logging.debug(f"Trigger inputs: L2={l2_trigger}, R2={r2_trigger}")

                # Adjust the speed of the whegs based on the right trigger
                wheg_rpm = adjust_wheg_speed(r2_trigger, wheg_rpm)

                # Gait selection using buttons (Triangle, Square, X)
                if button_states['triangle']:
                    current_gait = gait_1
                    logging.info("Triangle button pressed: Gait 1 Selected")
                elif button_states['square']:
                    current_gait = gait_2
                    logging.info("Square button pressed: Gait 2 Selected")
                elif button_states['x']:
                    current_gait = gait_3
                    logging.info("X button pressed: Gait 3 Selected")
                elif button_states['circle']:
                    current_gait = gait_4
                    logging.info("Circle button pressed: Gait 4 Selected")

                # Execute the current gait
                if current_gait != previous_gait:
                    logging.info(f"Changing to new gait: {current_gait.__name__}")
                    previous_gait = current_gait
                # Execute the current gate
                current_gait(dynamixel, wheg_rpm)
                # Control pivots using the D-pad
                control_pivots_with_dpad(dynamixel, button_states)

            # Report motor positions and log controller inputs every second
            current_time = time.time()
            if current_time - report_timer >= 5:  # Report every 5 seconds
                motor_positions = get_motor_positions(dynamixel)
                log_positions_and_inputs(motor_positions, l2_trigger, r2_trigger, button_states)
                report_timer = current_time  # Reset the timer

            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("Terminating program...")

    finally:
        # Safely turn off wheg and pivot motors and close the controller
        for wheg_id in WHEGS.values():
            dynamixel.torque_off(wheg_id)
            logging.info(f"Torque off for wheg_id={wheg_id}")
        # for pivot_id in PIVOTS.values():
        #     dynamixel.torque_off(pivot_id)

        ps4_controller.close()
        dynamixel.close()
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()
