import pygame

# Initialize pygame
pygame.init()

# Initialize joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

while True:
    pygame.event.pump()  # Capture events
    x_axis = joystick.get_axis(0)  # Left joystick X-axis
    y_axis = joystick.get_axis(1)  # Left joystick Y-axis
    button_square = joystick.get_button(0)  # Square button

    # Print the values for debugging
    print(f"X: {x_axis}, Y: {y_axis}, Square: {button_square}")
