# Reads inputs of Xbox controller and sends them to the ESP32 via bluetooth

import serial
import time

import time
from XInputPython.XInput import *

state=get_state(0)
time.sleep(0.05)
contains_true = lambda s: 'True' in s
is_zero = lambda t: t != 0
lastmessage=[50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

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

# Replace with your device's serial port (e.g., COM3, /dev/rfcomm0)
serial_port = 'COM11'
baud_rate = 115200  # Set this to the baud rate of your device

# Initialize serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=60)

try:
    while True:

        # Reset all values to None
        #control_message["Turn amount"]= None
        #control_message["Throttle"]= None
        #control_message["Brake"]= None

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
            LthumbSticksPressed=1
        else:
            LthumbSticksPressed=0

        if Rthumb_stick_values != (0,0):
            RthumbSticksPressed=1
        else:
            RthumbSticksPressed=0

        #print(Rthumb_stick_values, RthumbSticksPressed)

        #print(buttonsPressed, triggersPressed, thumbSticksPressed)

        if (buttonsPressed == LtriggersPressed == RtriggersPressed == LthumbSticksPressed == LthumbSticksPressed == 0):
                control_message["Brake"]=0
                control_message["Throttle"]=0
                control_message["Turn amount"]=50
                control_message["A"]=0
                control_message["B"]=0
                control_message["Y"]=0
                control_message["X"]=0
                control_message["Left bumper"]=0
                control_message["Right bumper"]=0
                control_message["Left dpad"]=0
                control_message["Right dpad"]=0

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
                        control_message["Left bumper"]=1
                    elif event.button == "RIGHT_SHOULDER":
                        control_message["Right bumper"]=1
                    elif event.button == "BACK":
                        pass
                    elif event.button == "START":
                        pass

                    elif event.button == "DPAD_LEFT":
                        control_message["Left dpad"]=1
                        pass
                    elif event.button == "DPAD_RIGHT":
                        control_message["Right dpad"]=1
                        pass
                    elif event.button == "DPAD_UP":
                        pass
                    elif event.button == "DPAD_DOWN":
                        pass

                    elif event.button == "A":
                        control_message["A"]=1
                    elif event.button == "B":
                        control_message["B"]=1
                    elif event.button == "Y":
                        control_message["Y"]=1
                    elif event.button == "X":
                        control_message["X"]=1


                elif event.type == EVENT_BUTTON_RELEASED:
                    if event.button == "LEFT_THUMB":
                        pass
                    elif event.button == "RIGHT_THUMB":
                        pass

                    elif event.button == "LEFT_SHOULDER":
                        control_message["Left bumper"]=0
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
                    elif event.button == ["B"]:
                        control_message["B"] = 0
                    elif event.button == "Y":
                        control_message["Y"] = 0
                    elif event.button == "X":
                        control_message["X"] = 0

            if (LtriggersPressed == 1)|(RtriggersPressed == 1)|(LthumbSticksPressed == 1)|(RthumbSticksPressed == 1):
                control_message["Brake"]=int(100*Ltrigger_values)
                control_message["Throttle"]=int(100*Rtrigger_values)
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
        nothingList=[50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if (message!=nothingList)|(lastmessage!=nothingList):
            # send the message
            #print(message)
            dataList = message
            dataList2 = dataList[:3] + [1 if item else 0 for item in dataList[3:]]
            data = ','.join(map(str, dataList2)) + '\n'
            #print(data)
            
            # Write the data to the serial port
            ser.write(data.encode())
            print(f"Sent: {data}")
        lastmessage=message

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopping serial communication...")

finally:
    # Close the serial connection when exiting
    ser.close()
    print("Serial connection closed.")


                        