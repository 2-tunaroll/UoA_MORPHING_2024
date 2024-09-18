from controller import PS4Controller
import time

def main():
    try:
        # Initialize PS4 controller
        ps4_controller = PS4Controller()

        while True:
            # Get joystick inputs (left and right sticks)
            x_axis_left, y_axis_left, x_axis_right, y_axis_right = ps4_controller.get_joystick_input()
            print(f"Left Stick - X: {x_axis_left:.2f}, Y: {y_axis_left:.2f}")
            print(f"Right Stick - X: {x_axis_right:.2f}, Y: {y_axis_right:.2f}")

            # Get button states
            button_states = ps4_controller.get_button_input()
            for button, state in button_states.items():
                print(f"Button {button}: {'Pressed' if state else 'Released'}")

            # Get trigger inputs (L2 and R2 as analog values)
            l2_trigger, r2_trigger = ps4_controller.get_trigger_input()
            print(f"L2 Trigger: {l2_trigger:.2f}, R2 Trigger: {r2_trigger:.2f}")

            # Get D-pad (Hat switch) state
            dpad_state = ps4_controller.get_dpad_input()
            print(f"D-Pad: {dpad_state}")

            print("-" * 40)  # Divider between input updates

            # Delay to reduce CPU usage and avoid flooding the terminal with too many updates
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nController test terminated.")

    finally:
        # Safely close the controller connection
        ps4_controller.close()

if __name__ == "__main__":
    main()
