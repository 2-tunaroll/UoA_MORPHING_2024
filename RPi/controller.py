import pygame

class PS4Controller:
    def __init__(self):
        # Initialize pygame
        pygame.init()

        # Initialize the joystick (assuming it's the first one connected)
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        # Define button indices for easy reference
        self.buttons = {
            'square': 3,  # Square button
            'x': 0,       # X button
            'circle': 2,  # Circle button
            'triangle': 1, # Triangle button
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
        """
        Returns the X and Y axis positions of both joysticks.
        Left joystick: x_axis_left, y_axis_left
        Right joystick: x_axis_right, y_axis_right
        """
        pygame.event.pump()
        x_axis_left = self.joystick.get_axis(0)  # Left joystick X-axis
        y_axis_left = self.joystick.get_axis(1)  # Left joystick Y-axis
        x_axis_right = self.joystick.get_axis(2)  # Right joystick X-axis
        y_axis_right = self.joystick.get_axis(5)  # Right joystick Y-axis
        return x_axis_left, y_axis_left, x_axis_right, y_axis_right

    def get_button_input(self):
        """
        Returns a dictionary with the state (pressed or not) of each button.
        """
        pygame.event.pump()
        button_states = {button: self.joystick.get_button(index) for button, index in self.buttons.items()}
        return button_states

    def get_trigger_input(self):
        """
        Returns the values of the L2 and R2 triggers (analog values between -1 and 1).
        """
        pygame.event.pump()
        l2_trigger = self.joystick.get_axis(3)  # L2 trigger (analog)
        r2_trigger = self.joystick.get_axis(4)  # R2 trigger (analog)
        return l2_trigger, r2_trigger

    def get_dpad_input(self):
        """
        Returns the current state of the D-pad (Hat switch) as a tuple (x, y).
        Example:
        (0, 1) for up, (1, 0) for right, (-1, 0) for left, (0, -1) for down
        """
        pygame.event.pump()
        dpad_state = self.joystick.get_hat(self.dpad_index)
        return dpad_state

    def close(self):
        """
        Cleans up and quits pygame.
        """
        pygame.quit()
