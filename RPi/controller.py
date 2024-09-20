import pygame
import logging

class PS4Controller:
    def __init__(self):
        logging.info("Initializing PS4Controller")
        
        # Initialize pygame
        pygame.init()
        logging.debug("Pygame initialized")

        # Initialize the joystick (assuming it's the first one connected)
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        logging.debug("Joystick initialized")

        # Get the number of buttons on the controller
        self.num_buttons = self.joystick.get_numbuttons()
        logging.debug(f"Number of buttons on the controller: {self.num_buttons}")

        # Corrected button indices
        self.buttons = {
            'square': 3,  # Square button
            'x': 0,       # X button
            'circle': 1,  # Circle button (corrected)
            'triangle': 2, # Triangle button (corrected)
            'l1': 4,      # L1 button
            'r1': 5,      # R1 button
            'l2': 6,      # L2 trigger (binary)
            'r2': 7,      # R2 trigger (binary)
            'share': 8,   # Share button
            'options': 9, # Options button
            'l3': 10,     # Left joystick button
            'r3': 11,     # Right joystick button
            'ps': 12,     # PS button
            'touchpad': 13 # Touchpad button
        }

        # D-Pad (Hat switch) index
        self.dpad_index = 0

    def get_joystick_input(self):
        logging.info("Getting joystick input")
        pygame.event.pump()
        x_axis_left = self.joystick.get_axis(0)  # Left joystick X-axis
        y_axis_left = self.joystick.get_axis(1)  # Left joystick Y-axis
        x_axis_right = self.joystick.get_axis(3)  # Right joystick X-axis (corrected)
        y_axis_right = self.joystick.get_axis(4)  # Right joystick Y-axis (corrected)
        logging.debug(f"Joystick positions - Left: ({x_axis_left}, {y_axis_left}), Right: ({x_axis_right}, {y_axis_right})")
        return x_axis_left, y_axis_left, x_axis_right, y_axis_right

    def get_button_input(self):
        logging.info("Getting button input")
        pygame.event.pump()
        button_states = {}
        for button, index in self.buttons.items():
            if index < self.num_buttons:
                button_states[button] = self.joystick.get_button(index)
                logging.debug(f"Button {button} (index {index}) state: {button_states[button]}")
            else:
                button_states[button] = None  # Button doesn't exist on this controller
                logging.warning(f"Button {button} (index {index}) does not exist on this controller")
        return button_states

    def get_trigger_input(self):
        logging.info("Getting trigger input")
        pygame.event.pump()
        l2_trigger = self.joystick.get_axis(2)  # L2 trigger (corrected)
        r2_trigger = self.joystick.get_axis(5)  # R2 trigger (corrected)
        logging.debug(f"Trigger values - L2: {l2_trigger}, R2: {r2_trigger}")
        return l2_trigger, r2_trigger

    def get_dpad_input(self):
        logging.info("Getting D-pad input")
        pygame.event.pump()
        dpad_state = self.joystick.get_hat(self.dpad_index)
        logging.debug(f"D-pad state: {dpad_state}")
        return dpad_state

    def close(self):
        logging.info("Closing PS4Controller and quitting pygame")
        pygame.quit()
