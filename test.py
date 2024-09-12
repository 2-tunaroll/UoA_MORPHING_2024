import time
from XInputPython.XInput import *

state=get_state(0)
time.sleep(0.05)
contains_true = lambda s: 'True' in s
is_zero = lambda t: t != 0
lastmessage=[50, 0, 0, False, False, False, False, False, False, False, False]

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
                elif event.button == ["B"]:
                    control_message["B"] = None
                elif event.button == "Y":
                    control_message["Y"] = None
                elif event.button == "X":
                    control_message["X"] = None

        if (LtriggersPressed == True)|(RtriggersPressed == True)|(LthumbSticksPressed == True)|(RthumbSticksPressed == True):
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
    nothingList=[50, 0, 0, False, False, False, False, False, False, False, False]
    if (message!=nothingList)|(lastmessage!=nothingList):
        print(message)
    lastmessage=message
    time.sleep(0.05)

                        
