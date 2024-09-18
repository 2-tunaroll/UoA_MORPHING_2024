from controller import PS4Controller
from dynamixel_control import DynamixelController
import time

# Convert joystick input (-1 to 1) to Dynamixel position (0 to 4095)
def convert_joystick_to_position(joystick_value):
    return int((joystick_value + 1) / 2 * 4095)

def main():
    try:
        # Initialize PS4 controller and Dynamixel controller
        ps4_controller = PS4Controller()
        dynamixel = DynamixelController(device_name='/dev/ttyACM0', baudrate=57600)

        emergency_stop = False  # Track emergency stop state

        while True:
            # Get joystick inputs
            x_axis, y_axis = ps4_controller.get_joystick_input()

            # Convert joystick y-axis input into Dynamixel goal positions
            goal_position1 = convert_joystick_to_position(y_axis)
            goal_position2 = convert_joystick_to_position(y_axis)

            # Send goal position to the Dynamixel motors only if emergency stop is NOT activated
            if not emergency_stop:
                dynamixel.set_goal_position(dynamixel.dxl_id1, goal_position1)
                dynamixel.set_goal_position(dynamixel.dxl_id2, goal_position2)

            # Print present positions for debugging
            present_position1 = dynamixel.get_present_position(dynamixel.dxl_id1)
            present_position2 = dynamixel.get_present_position(dynamixel.dxl_id2)
            print(f"Motor1 - GoalPos: {goal_position1}, PresentPos: {present_position1}")
            print(f"Motor2 - GoalPos: {goal_position2}, PresentPos: {present_position2}")

            # Check if the X button is pressed
            if ps4_controller.get_button_input():  # X button
                print("X button pressed, resetting motors to zero position")
                dynamixel.set_goal_position(dynamixel.dxl_id1, 0)
                dynamixel.set_goal_position(dynamixel.dxl_id2, 0)

            # Check if the Circle button is pressed (Emergency Stop)
            if ps4_controller.joystick.get_button(2):  # Circle button
                print("Emergency Stop Activated! Disabling motors.")
                emergency_stop = True
                dynamixel.set_goal_position(dynamixel.dxl_id1, 0)
                dynamixel.set_goal_position(dynamixel.dxl_id2, 0)
                dynamixel.disable_torque()

            # Reset emergency stop if no button is pressed
            if not ps4_controller.joystick.get_button(2) and emergency_stop:
                print("Emergency Stop Deactivated! Re-enabling motors.")
                dynamixel._enable_torque(dynamixel.dxl_id1)
                dynamixel._enable_torque(dynamixel.dxl_id2)
                emergency_stop = False

            time.sleep(0.1)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        print("\nTerminating program...")

    finally:
        # Safely close the controller and Dynamixel connections
        ps4_controller.close()
        dynamixel.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
