from controller import PS4Controller
from dynamixel_control import DynamixelController
import time

def main():
    try:
        # Initialize PS4 controller and Dynamixel controller
        ps4_controller = PS4Controller()
        dynamixel = DynamixelController(device_name='/dev/ttyACM0', baudrate=57600)

        emergency_stop = False  # Track emergency stop state

        while True:
            # Get joystick inputs
            x_axis_left, y_axis_left, x_axis_right, y_axis_right = ps4_controller.get_joystick_input()

            # Get button inputs
            button_states = ps4_controller.get_button_input()

            # Convert joystick y-axis input into Dynamixel goal positions
            goal_position1 = convert_joystick_to_position(y_axis_left)
            goal_position2 = convert_joystick_to_position(y_axis_left)

            # Send goal position to the Dynamixel motors only if emergency stop is NOT activated
            if not emergency_stop:
                dynamixel.set_goal_position(dynamixel.dxl_id1, goal_position1)
                dynamixel.set_goal_position(dynamixel.dxl_id2, goal_position2)

            # Print present positions for debugging
            present_position1 = dynamixel.get_present_position(dynamixel.dxl_id1)
            present_position2 = dynamixel.get_present_position(dynamixel.dxl_id2)
            print(f"Motor1 - GoalPos: {goal_position1}, PresentPos: {present_position1}")
            print(f"Motor2 - GoalPos: {goal_position2}, PresentPos: {present_position2}")

            # Emergency stop using Circle button
            if button_states['circle']:  # Circle button
                print("Emergency Stop Activated! Disabling motors.")
                emergency_stop = True
                dynamixel.set_goal_position(dynamixel.dxl_id1, 0)
                dynamixel.set_goal_position(dynamixel.dxl_id2, 0)
                dynamixel.disable_torque()

            # Reactivate motors after emergency stop if Circle button is released
            if not button_states['circle'] and emergency_stop:
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

