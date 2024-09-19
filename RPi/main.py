import time
from controller import PS4Controller
from dynamixel_control import DynamixelController

# Motor IDs for the whegs and pivots
WHEGS = {
    'LR_WHEG': 1, 'LM_WHEG': 2, 'LF_WHEG': 3,
    'RR_WHEG': 4, 'RM_WHEG': 5, 'RF_WHEG': 6
}
FRONT_PIVOT = 7
REAR_PIVOT = 8

# Velocity and position control limits
MAX_RPM = 100  # Max RPM for wheg motors
MIN_RPM = 0    # Min RPM for wheg motors
SMOOTHNESS = 0.5  # Controls how smoothly the speed increases
START_POSITION = 180  # Start position of the pivots (180 degrees)
MAX_PIVOT_RANGE = 90  # Limit the pivot movement to a maximum of 90 degrees from the starting position

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

# Set pivots to specific positions while ensuring safety limits
def set_pivot_positions(dynamixel, front_offset, rear_offset):
    # The pivots will be set relative to the START_POSITION (180 degrees)
    front_angle = max(min(START_POSITION + front_offset, START_POSITION + MAX_PIVOT_RANGE), START_POSITION - MAX_PIVOT_RANGE)
    rear_angle = max(min(START_POSITION + rear_offset, START_POSITION + MAX_PIVOT_RANGE), START_POSITION - MAX_PIVOT_RANGE)
    
    # Set the pivot positions ensuring they stay within limits
    dynamixel.set_goal_position(FRONT_PIVOT, front_angle)
    dynamixel.set_goal_position(REAR_PIVOT, rear_angle)

# Define multiple gaits
def gait_1(dynamixel, wheg_rpm):
    print("Executing Gait 1")
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm)
    set_pivot_positions(dynamixel, 0, 0)  # Pivots stay in the starting position (180 degrees)

def gait_2(dynamixel, wheg_rpm):
    print("Executing Gait 2")
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm / 2)  # Slower whegs
    set_pivot_positions(dynamixel, -45, 45)  # Pivots move to 135 (front) and 225 (rear) degrees

def gait_3(dynamixel, wheg_rpm):
    print("Executing Gait 3")
    set_wheg_velocity(dynamixel, WHEGS.values(), wheg_rpm)
    set_pivot_positions(dynamixel, 45, -45)  # Pivots move to 225 (front) and 135 (rear) degrees

def gait_4(dynamixel, wheg_rpm):
    print("Executing Gait 4")
    set_wheg_velocity(dynamixel, WHEGS.values(), -wheg_rpm)  # Reverse direction for whegs
    set_pivot_positions(dynamixel, 0, 0)  # Pivots remain at the start position (180 degrees)

# Emergency stop function
def emergency_stop(dynamixel):
    print("Emergency Stop Activated! Stopping all motors.")
    set_wheg_velocity(dynamixel, WHEGS.values(), 0)  # Stop all wheg motors
    set_pivot_positions(dynamixel, 0, 0)  # Set pivots back to the neutral start position (180 degrees)

# Main function integrating the PS4 controller and Dynamixel SDK
def main():
    try:
        # Initialize PS4 controller and Dynamixel
        ps4_controller = PS4Controller()
        dynamixel = DynamixelController(device_name='/dev/ttyACM0', baudrate=57600)

        # Initial motor states
        wheg_rpm = 0  # Start with no motion
        current_gait = gait_1  # Start with Gait 1
        emergency_stop_activated = False  # Track emergency stop state

        # Turn on torque and set operating modes
        for wheg_id in WHEGS.values():
            dynamixel.set_operating_mode(wheg_id, 'velocity')
            dynamixel.torque_on(wheg_id)
        
        dynamixel.set_operating_mode(FRONT_PIVOT, 'position')
        dynamixel.set_operating_mode(REAR_PIVOT, 'position')
        dynamixel.torque_on(FRONT_PIVOT)
        dynamixel.torque_on(REAR_PIVOT)

        # Main loop
        while True:
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
                    print("Gait 1 selected")
                elif button_states['square']:
                    current_gait = gait_2
                    print("Gait 2 selected")
                elif button_states['x']:
                    current_gait = gait_3
                    print("Gait 3 selected")

                # Execute the currently selected gait
                current_gait(dynamixel, wheg_rpm)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nTerminating program...")

    finally:
        # Safely turn off motors and close the controller
        for wheg_id in WHEGS.values():
            dynamixel.torque_off(wheg_id)
        dynamixel.torque_off(FRONT_PIVOT)
        dynamixel.torque_off(REAR_PIVOT)

        ps4_controller.close()
        dynamixel.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
