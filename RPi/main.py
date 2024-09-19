import time
import logging
from controller import PS4Controller
from dynamixel_control import DynamixelController

# Motor IDs for the whegs (wheeled legs)
WHEGS = {
    'LR_WHEG': 1, 'LM_WHEG': 2, 'LF_WHEG': 3,
    'RR_WHEG': 4, 'RM_WHEG': 5, 'RF_WHEG': 6
}

# Velocity control limits for whegs
MAX_RPM = 50  # Max RPM for wheg motors
MIN_RPM = 0    # Min RPM for wheg motors
SMOOTHNESS = 0.5  # Controls how smoothly the speed increases

# Set up logging to log motor positions and controller inputs
logging.basicConfig(filename='robot_log.txt', level=logging.INFO, format='%(asctime)s %(message)s')

# Adjust the velocity based on the right trigger input
def adjust_wheg_speed(trigger_value, current_rpm):
    # Map trigger value (-1 to 1) to RPM range (MIN_RPM to MAX_RPM)
    target_rpm = ((trigger_value + 1) / 2) * (MAX_RPM - MIN_RPM) + MIN_RPM
    
    # Smooth the transition to the target RPM
    if target_rpm > current_rpm:
        current_rpm = min(current_rpm + SMOOTHNESS, target_rpm)
    else:
        current_rpm = max(current_rpm - SMOOTHNESS, target_rpm)
    
    return current_rpm

# Function to control whegs velocity
def set_wheg_velocity(dynamixel, wheg_ids, rpm):
    for wheg_id in wheg_ids:
        dynamixel.set_goal_velocity(wheg_id, rpm)

# Function to get and report the positions of all whegs
def report_motor_positions(dynamixel):
    motor_positions = []
    for wheg_name, wheg_id in WHEGS.items():
        position = dynamixel.get_present_position(wheg_id)
        motor_positions.append(f"{wheg_name}: {position} degrees")
    return motor_positions

# Function to log controller inputs
def log_controller_inputs(l2_trigger, r2_trigger, button_states):
    logging.info(f"L2 Trigger: {l2_trigger}, R2 Trigger: {r2_trigger}")
    logging.info(f"Button States: {button_states}")

# Define multiple gaits (for whegs only, pivots are disabled)
def gait_1(dynamixel, wheg_rpm):
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm)

def gait_2(dynamixel, wheg_rpm):
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm / 2)  # Slower whegs

def gait_3(dynamixel, wheg_rpm):
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm)

def gait_4(dynamixel, wheg_rpm):
    set_wheg_velocity(dynamixel, WHEGS.values(), -wheg_rpm)  # Reverse direction for whegs

# Emergency stop function (whegs only)
def emergency_stop(dynamixel):
    set_wheg_velocity(dynamixel, WHEGS.values(), 0)  # Stop all wheg motors

# Main function integrating the PS4 controller and Dynamixel SDK
def main():
    try:
        # Initialize PS4 controller and Dynamixel
        ps4_controller = PS4Controller()
        dynamixel = DynamixelController(device_name='/dev/ttyACM0', baudrate=57600)

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

        # Main loop
        while True:
            start_time = time.time()  # Track time for position reporting
            
            # Get button states for emergency stop and gait selection
            button_states = ps4_controller.get_button_input()

            # Emergency Stop using Circle button
            if button_states['circle']:
                emergency_stop_activated = True
                emergency_stop(dynamixel)

            # Deactivate emergency stop if X button is pressed
            if button_states['x'] and emergency_stop_activated:
                emergency_stop_activated = False
                print("Emergency Stop Deactivated. Resuming control...")

            if not emergency_stop_activated:
                # Get trigger input (R2) for speed adjustment
                l2_trigger, r2_trigger = ps4_controller.get_trigger_input()

                # Adjust the speed of the whegs based on the right trigger
                wheg_rpm = adjust_wheg_speed(r2_trigger, wheg_rpm)

                # Gait selection using buttons (Triangle, Square, X)
                if button_states['triangle']:
                    current_gait = gait_1
                elif button_states['square']:
                    current_gait = gait_2
                elif button_states['x']:
                    current_gait = gait_3

                # Print gait change only when it occurs
                if current_gait != previous_gait:
                    print(f"Gait changed to {current_gait.__name__}")
                    previous_gait = current_gait

                # Execute the currently selected gait (whegs only)
                current_gait(dynamixel, wheg_rpm)

                # Log controller inputs
                log_controller_inputs(l2_trigger, r2_trigger, button_states)

            # Report motor positions every second
            current_time = time.time()
            if current_time - report_timer >= 1:  # Report every 1 second
                motor_positions = report_motor_positions(dynamixel)
                # Log motor positions
                logging.info("Motor Positions:\n" + "\n".join(motor_positions))
                report_timer = current_time  # Reset the timer

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nTerminating program...")

    finally:
        # Safely turn off wheg motors and close the controller
        for wheg_id in WHEGS.values():
            dynamixel.torque_off(wheg_id)

        ps4_controller.close()
        dynamixel.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
