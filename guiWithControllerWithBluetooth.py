import tkinter as tk
from tkinter import ttk
from tkinter import font

import serial
import time
from XInputPython.XInput import *
import threading

nothingList=[50, 0, 0, False, False, False, False, False, False, False, False]
lastmessage=[50, 0, 0, False, False, False, False, False, False, False, False]
a_button_held_flag=False

# Replace with your device's serial port (e.g., COM3, /dev/rfcomm0)
serial_port = 'COM11'
baud_rate = 115200  # Set this to the baud rate of your device

# Initialize serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=60)

# Example of a function to run in the background
def background_task():
    global lastmessage
    global a_button_held_flag

    while True:
        x=0
        # Reset all values to None
        #control_message["Turn amount"]= None
        #control_message["Throttle"]= None
        #control_message["Brake"]= None
        #print("Hello!")
        state=get_state(0)
        Ltrigger_values=get_trigger_values(state)[0]
        Rtrigger_values=get_trigger_values(state)[1]
        Lthumb_stick_values=get_thumb_values(state)[0]
        Rthumb_stick_values=get_thumb_values(state)[1]
        
        #print(Lthumb_stick_values, Rthumb_stick_values, Ltrigger_values, Rtrigger_values)

        buttonsPressed=contains_true(str(get_button_values(state)))
        LtriggersPressed=is_zero(Ltrigger_values)
        RtriggersPressed=is_zero(Rtrigger_values)
        #print(Lthumb_stick_values)
        if Lthumb_stick_values != (0,0):
            LthumbSticksPressed=True
        else:
            LthumbSticksPressed=False

        if Rthumb_stick_values != (0,0):
            RthumbSticksPressed=True
        else:
            RthumbSticksPressed=False

        #print(Rthumb_stick_values, RthumbSticksPressed)

        #print(buttonsPressed, triggersPressed, thumbSticksPressed)

        if (buttonsPressed == LtriggersPressed == RtriggersPressed == LthumbSticksPressed == LthumbSticksPressed == False):
                control_message["Brake"]=0
                control_message["Throttle"]=0
                control_message["Turn amount"]=50
                control_message["A"]=False
                control_message["B"]=False
                control_message["Y"]=False
                control_message["X"]=False
                control_message["Left bumper"]=False
                control_message["Right bumper"]=False
                control_message["Left dpad"]=False
                control_message["Right dpad"]=False

                # TRANSMIT ONE MESSAGE
    
        else:
            # Figure out what is being pressed
            # and transmit the information to the Pi
            events = get_events()
            x=0
            for event in events:
                #print(LtriggersPressed)
                if event.type == EVENT_CONNECTED:
                    pass            
                elif event.type == EVENT_DISCONNECTED:
                    print("Controller Disconnected!")   

                elif event.type == EVENT_BUTTON_PRESSED:
                    #print(event.button)
                    if event.button == "LEFT_THUMB":
                        pass
                    elif event.button == "RIGHT_THUMB":
                        pass
                    elif event.button == "LEFT_SHOULDER":
                        control_message["Left bumper"]=True
                    elif event.button == "RIGHT_SHOULDER":
                        control_message["Right bumper"]=True
                    elif event.button == "BACK":
                        pass
                    elif event.button == "START":
                        pass

                    elif event.button == "DPAD_LEFT":
                        control_message["Left dpad"]=True
                        pass
                    elif event.button == "DPAD_RIGHT":
                        control_message["Right dpad"]=True
                        pass
                    elif event.button == "DPAD_UP":
                        pass
                    elif event.button == "DPAD_DOWN":
                        pass

                    elif event.button == "A":
                        control_message["A"]=True
                        a_button_held_flag=True
                        send_data()
                    elif event.button == "B":
                        control_message["B"]=True
                    elif event.button == "Y":
                        control_message["Y"]=True
                    elif event.button == "X":
                        control_message["X"]=True


                elif event.type == EVENT_BUTTON_RELEASED:
                    if event.button == "LEFT_THUMB":
                        pass
                    elif event.button == "RIGHT_THUMB":
                        pass

                    elif event.button == "LEFT_SHOULDER":
                        control_message["Left bumper"]=False
                    elif event.button == "RIGHT_SHOULDER":
                        pass
                    elif event.button == "BACK":
                        pass
                    elif event.button == "START":
                        pass

                    elif event.button == "DPAD_LEFT":
                        pass
                    elif event.button == "DPAD_RIGHT":
                        pass
                    elif event.button == "DPAD_UP":
                        pass
                    elif event.button == "DPAD_DOWN":
                        pass

                    elif event.button == "A":
                        control_message["A"] = 0
                        a_button_held_flag=False
                        print("a button is off")
                        speed_slider.set(0)  # Set RPM to 0
                        update_speed_label(0)  # Update speed display
                        x=1
                    elif event.button == ["B"]:
                        control_message["B"] = None
                    elif event.button == "Y":
                        control_message["Y"] = None
                    elif event.button == "X":
                        control_message["X"] = None

            if (LtriggersPressed == True)|(RtriggersPressed == True)|(LthumbSticksPressed == True)|(RthumbSticksPressed == True):
                control_message["Brake"]=int(100*Ltrigger_values)
                if (x!=1):
                    control_message["Throttle"]=int(100*Rtrigger_values)
                else:
                    control_message["Throttle"]=0
                control_message["Turn amount"]=int((50*Lthumb_stick_values[0]+50))


            tempDict=get_button_values(get_state(0))

            control_message["A"]=(tempDict["A"])
            control_message["B"]=(tempDict["B"])
            control_message["Y"]=(tempDict["Y"])
            control_message["X"]=(tempDict["X"])
            control_message["Left bumper"]=(tempDict["LEFT_SHOULDER"])
            control_message["Right bumper"]=(tempDict["RIGHT_SHOULDER"])
            control_message["Left dpad"]=(tempDict["DPAD_LEFT"])
            control_message["Right dpad"]=(tempDict["DPAD_RIGHT"])

        message=list(control_message.values())
        #if (message!=nothingList)|(lastmessage!=nothingList):
            #print(message)
        lastmessage=message
        #time.sleep(0.05)

set_deadzone(DEADZONE_TRIGGER,10)

# Create the main window
root = tk.Tk()
root.title("Robot Gait Control")

# Set the size of the window and background color
root.geometry("600x850")
root.configure(bg="#141414")  # Set background to medium gray

# Global variable to control whether the GO button is held down
go_button_held_flag = False



state=get_state(0)
contains_true = lambda s: 'True' in s
is_zero = lambda t: t != 0

set_deadzone(DEADZONE_TRIGGER,10)

control_message = {
        "Turn amount": None,
        "Throttle": None,
        "Brake": None,
        "A": None,
        "B": None,
        "Y": None,
        "X": None,
        "Left dpad": None,
        "Right dpad": None,
        "Right bumper": None,
        "Left bumper": None
}

# Function to send the speed value
def send_data():
    #print("hi")
    if (go_button_held_flag | a_button_held_flag):
        # Print or send the current speed value
        speed_value = speed_slider.get()
        turning_value = turning_slider.get()
        #print(f"Sending Speed: {speed_value} RPM, Turning: {turning_value}")
        #print(f"Turning is actually: {lastmessage[0]}")

        # -------------------------------------

        # SEND DATA VIA BLUETOOTH HERE

        # -------------------------------------

        controllerState = "update," + str(lastmessage[0]) + "," + str(lastmessage[1]) + "\n"
        ser.write(controllerState.encode())

        # -------------------------------------
        speed_slider.set(lastmessage[1])  
        turning_slider.set(lastmessage[0])
        update_speed_label(lastmessage[1])  # Update speed display
        update_turning_label(lastmessage[0])  # Update labels

        # Schedule the function to run again after 100ms (1/10th of a second)
        root.after(50, send_data)

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
    speed_slider.set(0)  # Set RPM to 0
    update_speed_label(0)  # Update speed display

# Bind the spacebar to simulate pressing the GO button
root.bind("<KeyPress-space>", go_button_held)
root.bind("<KeyRelease-space>", go_button_released)

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

# Function to close the application and stop background task
def on_closing():
    print("Stopping the application.")
    root.quit()

# Bind closing event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the background task in a separate thread
thread = threading.Thread(target=background_task)
thread.daemon = True  # Daemonize thread to exit when main program exits
thread.start()

# Run the Tkinter main event loop
root.mainloop()

# After the application window is closed
print("Tkinter window closed. Continuing other tasks...")
# Run any additional code here after the window closes

#-----------------------------------------------------------

# Close the serial connection when exiting
ser.close()
print("Serial connection closed.")




