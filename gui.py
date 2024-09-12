import tkinter as tk
from tkinter import ttk
from tkinter import font

# Create the main window
root = tk.Tk()
root.title("Robot Gait Control")

# Set the size of the window and background color
root.geometry("600x850")
root.configure(bg="#141414")  # Set background to medium gray

# Global variable to control whether the GO button is held down
go_button_held_flag = False

# Function to send the speed value
def send_data():
    if go_button_held_flag:
        # Print or send the current speed value
        speed_value = speed_slider.get()
        turning_value = turning_slider.get()
        print(f"Sending Speed: {speed_value} RPM, Turning: {turning_value}")
        
        # Schedule the function to run again after 100ms (1/10th of a second)
        root.after(100, send_data)

# Function to handle when "GO" button is held down
def go_button_held(event):
    print("GO button is being held down")
    global go_button_held_flag
    go_button_held_flag = True
    send_data()  # Start sending the speed value every 100ms

# Function to handle when "GO" button is released
def go_button_released(event):
    global go_button_held_flag
    go_button_held_flag = False
    print("GO button released")

# Define button callback functions
def select_gait():
    selected_gait = gait_var.get()
    print(f"Gait {selected_gait} selected at {speed_slider.get()} RPM, Front Pivot: {front_pivot_slider.get()}°, Rear Pivot: {rear_pivot_slider.get()}°")

def reset():
    gait_var.set(1)  # Reset the selected gait to Gait 1
    speed_slider.set(0)  # Set RPM to 0
    front_pivot_slider.set(0)  # Reset front pivot to 0
    rear_pivot_slider.set(0)   # Reset rear pivot to 0
    turning_slider.set(50)
    update_speed_label(0)  # Update speed display
    update_rearpivot_label(0)  # Update pivot labels
    update_frontpivot_label(0)  # Update pivot labels
    update_turning_label(50)  # Update pivot labels
    print("Resetting and setting RPM and Pivots to 0")

def stop():
    print("STOP button pressed")
    gait_var.set(None)  # Deactivate any selected gait
    speed_slider.set(0)  # Set RPM to 0
    front_pivot_slider.set(0)  # Reset front pivot to 0
    rear_pivot_slider.set(0)   # Reset rear pivot to 0
    turning_slider.set(50)
    update_speed_label(0)  # Update speed display
    update_frontpivot_label(0)  # Update pivot labels
    update_rearpivot_label(0)
    update_turning_label(50)
    print("Stopping and setting RPM and Pivots and turning to 0")
    root.destroy()  # Close the window

def update_speed_label(value):
    current_speed.set(f"Current Speed: {int(float(value))} RPM")

def update_rearpivot_label(*args):
    # Update the pivot angle labels with the current values from the sliders
    rear_pivot_var.set(f"Rear Pivot: {int(rear_pivot_slider.get())}°")

def update_frontpivot_label(*args):
    # Update the pivot angle labels with the current values from the sliders
    front_pivot_var.set(f"Front Pivot: {int(front_pivot_slider.get())}°")

def update_turning_label(*args):
    # Update the pivot angle labels with the current values from the sliders
    turning_var.set(f"Turn: {int(turning_slider.get())}")


# Variable to hold the currently selected gait
gait_var = tk.IntVar()
gait_var.set(1)  # Set the default selection to Gait 1

# Create a fun font for the title
fun_font = font.Font(family="Bahnschrift SemiBold Condensed", size=28)

# Create a frame to hold the title and act as a "box"
title_frame = tk.Frame(root, highlightbackground="white", highlightthickness=2, padx=10, pady=10, bg="#000000")

# Add a title label inside the frame with purple text
title_label = tk.Label(title_frame, text="FLIK Control Panel", font=fun_font, fg="white", bg="#000000")
title_label.pack()

# Pack the title frame (box) at the top
title_frame.pack(pady=20)  # Add padding around the box

# Create a larger font for the Gait buttons
gait_button_font = font.Font(family="Helvetica", size=16, weight="bold")

# Create radio buttons for the gaits with a gray background and larger font
gait1_radio = tk.Radiobutton(root, text="Gait 1", variable=gait_var, value=1, command=select_gait, height=2, width=20, bg="#141414", font=gait_button_font, fg="#4c00b0")
gait2_radio = tk.Radiobutton(root, text="Gait 2", variable=gait_var, value=2, command=select_gait, height=2, width=20, bg="#141414", font=gait_button_font, fg="purple")
gait3_radio = tk.Radiobutton(root, text="Gait 3", variable=gait_var, value=3, command=select_gait, height=2, width=20, bg="#141414", font=gait_button_font, fg="#be2ed6")
gait4_radio = tk.Radiobutton(root, text="Gait 4", variable=gait_var, value=4, command=select_gait, height=2, width=20, bg="#141414", font=gait_button_font, fg="#b65fcf")

# Create a STOP button and place it at the top right corner
stop_button = tk.Button(root, text="STOP", command=stop, height=2, width=10, bg="red", fg="white")
stop_button.place(x=500, y=10)  # Position at top-right corner

# Create a GO button and bind the hold and release events
go_button = tk.Button(root, text="GO", height=2, width=10, bg="green", fg="white")

# Bind button press and release events to detect holding
go_button.bind("<ButtonPress-1>", go_button_held)    # Detect when GO button is pressed down
go_button.bind("<ButtonRelease-1>", go_button_released)  # Detect when GO button is released

# Position the GO button below the STOP button
go_button.place(x=500, y=70)

# Create a reset button
button_reset = tk.Button(root, text="Reset", command=reset, height=2, width=20)

# Create a label and a slider for speed control
current_speed = tk.StringVar()
speed_label = tk.Label(root, text="Speed (RPM)", bg="#141414", fg="white")
speed_slider = ttk.Scale(root, from_=0, to=100, orient='horizontal', length=300, command=update_speed_label)
speed_slider.set(0)  # Set initial speed to 0 RPM

# Create variables for the pivot labels
front_pivot_var = tk.StringVar()
rear_pivot_var = tk.StringVar()
turning_var = tk.StringVar()

# Set the initial value for pivot labels
front_pivot_var.set("Front Pivot: 0°")
rear_pivot_var.set("Rear Pivot: 0°")
turning_var.set("Turn: 50")

# Create two vertical sliders for front and rear pivots
pivot_frame = tk.Frame(root, bg="#141414")  # Frame to hold the two sliders side by side

# Define the sliders here
front_pivot_slider = ttk.Scale(pivot_frame, from_=-90, to=90, orient='vertical', length=200, command=update_frontpivot_label)
front_pivot_slider.set(0)  # Set initial pivot to 0°

rear_pivot_slider = ttk.Scale(pivot_frame, from_=-90, to=90, orient='vertical', length=200, command=update_rearpivot_label)
rear_pivot_slider.set(0)  # Set initial pivot to 0°

turning_slider = ttk.Scale(pivot_frame, from_=0, to=100, orient='horizontal', length=100, command=update_turning_label)
turning_slider.set(50)  # Set initial turning to 50

# Create labels for the sliders
front_pivot_label = tk.Label(pivot_frame, textvariable=front_pivot_var, bg="#141414", fg="white")
rear_pivot_label = tk.Label(pivot_frame, textvariable=rear_pivot_var, bg="#141414", fg="white")
turning_label = tk.Label(pivot_frame, textvariable=turning_var, bg="#141414", fg="white")

# Create labels to display the current speed, minimum, and maximum speed
bold_font = font.Font(weight="bold")  # Set bold font
current_speed_label = tk.Label(root, textvariable=current_speed, font=bold_font, bg="#141414", fg="white")
current_speed.set(f"Current Speed: {int(speed_slider.get())} RPM")

min_speed_label = tk.Label(root, text="Min: 0 RPM", bg="#141414")
max_speed_label = tk.Label(root, text="Max: 100 RPM", bg="#141414")

# Arrange the radio buttons and slider vertically
gait1_radio.pack()
gait2_radio.pack()
gait3_radio.pack()
gait4_radio.pack()
button_reset.pack()

# Pack the speed slider and its labels
speed_label.pack(pady=10)
speed_slider.pack(pady=10)
current_speed_label.pack(pady=20)

# Pack the front and rear pivot sliders side by side in the pivot_frame
front_pivot_label.grid(row=0, column=0, padx=20)
front_pivot_slider.grid(row=1, column=0, padx=20)
rear_pivot_label.grid(row=0, column=1, padx=20)
rear_pivot_slider.grid(row=1, column=1, padx=20)

turning_label.grid(row=0, column=2, padx=20)
turning_slider.grid(row=1, column=2, padx=20)

# Pack the pivot_frame into the main window
pivot_frame.pack(pady=20)

# Run the application
root.mainloop()


