"""
This script implements the main logic for converting PS4 controller inputs into dynamixel motor commands.
Different gaits are implemented.
The script also logs motor positions and controller inputs to a log file.

Dependencies:
    DynamixelController class from dynamixel_control.py
    PS4Controller class from controller.py
    DYNAMIXELSDK
    init file uploaded to the Open RB-150 Board
"""
# External Imports
import os
import time
import logging
import yaml
import asyncio

# Internal Imports
from datetime import datetime
from controller import PS4Controller
from dynamixel_control import DynamixelController

class FLIKRobot:
    def __init__(self):
        # Load configuration from YAML file
        with open('config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

        # Setup logging
        self.setup_logging()

        # Create variables from the configuration
        self.setup_variables()

        # Initisalise components
        try:
            self.ps4_controller = PS4Controller()
            self.dynamixel = DynamixelController()
            logging.info("Initialised PS4 controller, Dynamixel, and Robot State")
        except Exception as e:
            logging.error(f"Error initialising components: {e}")
        
        # Setup the whegs and pivots
        self.setup_whegs()
        self.setup_pivots()

    def setup_logging(self):
        # Create Logs directory if it doesn't exist
        log_directory = self.config['logging']['log_directory']
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        # Generate log file based on date and time
        log_filename = f"{log_directory}/flik_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

        # Set up logging to log motor positions and controller inputs
        logging.basicConfig(
            filename=log_filename,
            level=getattr(logging, self.config['logging']['log_level_file']),  
            format='%(asctime)s %(levelname)s: %(message)s'
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config['logging']['log_level_console']))  # Set console output
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)

        # Add the handler to the logger
        logging.getLogger().addHandler(console_handler)

    def setup_whegs(self):
        # Set the right side whegs to reverse
        self.dynamixel.set_drive_mode_group('Right_Whegs', True)
        self.dynamixel.set_drive_mode_group('Left_Whegs', False)
        logging.info("Set the right side whegs to reverse direction")
    
    def reverse_direction(self):
        # Read the current drive mode for all whegs
        direction = self.dynamixel.bulk_read_group('Wheg_Group', ['drive_mode'])
        
        # Log the structure of the direction data to debug
        logging.info(f"Direction data: {direction}")

        # Ensure the correct extraction of drive mode values
        try:
            # Reverse the direction for each motor (0 -> 1, 1 -> 0)
            reversed_direction = {
                motor_id: 0 if drive_data['drive_mode'] == 1 else 1
                for motor_id, drive_data in direction.items()
            }

            # Set the reversed drive mode for each motor
            self.dynamixel.set_drive_mode_group('Wheg_Group', reversed_direction)
            logging.warning("Reversed the direction of all whegs")

        except Exception as e:
            logging.error(f"Failed to reverse direction: {e}")
        
        self.direction_change_requested = False
        self.gait_change_requested = True

    def setup_pivots(self):
        # Set position limits for the pivot motors
        self.dynamixel.set_drive_mode_group('Pivot_Group', False)
        self.dynamixel.set_position_limits_group('Pivot_Group', self.config['position_limits']['Hinges']['min_degrees'], self.config['position_limits']['Hinges']['max_degrees'])
        logging.info("Set position limits for the pivot motors")

    def setup_variables(self):
        # Motor and pivot configurations from the YAML file
        self.WHEGS = self.config['motor_ids']['whegs']
        self.PIVOTS = self.config['motor_ids']['pivots']
        self.MAX_RPM = self.config['wheg_parameters']['max_rpm']
        self.MIN_RPM = self.config['wheg_parameters']['min_rpm']
        self.SMOOTHNESS = self.config['wheg_parameters']['smoothness']
        self.front_pivot_angle = self.config['pivot_parameters']['initial_front_angle']
        self.rear_pivot_angle = self.config['pivot_parameters']['initial_rear_angle']
        self.pivot_max_angle = self.config['position_limits']['Hinges']['max_degrees']
        self.pivot_min_angle = self.config['position_limits']['Hinges']['min_degrees']
        self.pivot_step = self.config['pivot_parameters']['pivot_step']
        self.wheg_rpm = self.config['wheg_parameters']['min_rpm']
        self.current_gait_index = 0
        self.next_gait_index = 0
        self.total_gaits = len(self.config['gaits'])
        self.emergency_stop_activated = False
        self.reboot_requested = False
        self.report_timer = time.time()
        self.gait_change_requested = True
        self.direction_change_requested = False
        self.allow_pivot_control = True
        # Gait parameters
        self.odd_even = 0
        self.gait_parameters = {}
        self.gait2_params = self.config['gaits'].get('gait_2', {})
        self.gait3_params = self.config['gaits'].get('gait_3', {})

        self.gait_init_methods = {
            0: self.gait_init_1,
            1: self.gait_init_2,
            2: self.gait_init_3,
            3: self.gait_init_4
        }

        self.gait_methods = {
            0: self.gait_1,
            1: self.gait_2,
            2: self.gait_3,
            3: self.gait_4
        }
        
    def adjust_front_pivot(self, direction):
        """Adjust the front pivot angle based on D-pad input."""
        if direction == 'up':
            self.front_pivot_angle = max(self.front_pivot_angle - self.pivot_step, self.pivot_min_angle)
        elif direction == 'down':
            self.front_pivot_angle = min(self.front_pivot_angle + self.pivot_step, self.pivot_max_angle)

    def adjust_rear_pivot(self, direction):
        """Adjust the rear pivot angle based on D-pad input."""
        if direction == 'up':
            self.rear_pivot_angle = max(self.rear_pivot_angle - self.pivot_step, self.pivot_min_angle)
        elif direction == 'down':
            self.rear_pivot_angle = min(self.rear_pivot_angle + self.pivot_step, self.pivot_max_angle)

    def adjust_wheg_rpm(self, trigger_value):
        """ Function to adjust the speed of the whegs based on how far the right trigger is pressed. Smooth transition to target RPM. """
        logging.debug(f"Adjusting wheg speed: trigger_value={trigger_value}, current_rpm={self.wheg_rpm}")
        target_rpm = ((trigger_value + 1) / 2) * (self.MAX_RPM - self.MIN_RPM) + self.MIN_RPM # Trigger value ranges from -1 to 1, map this to RPM range
        # Implement smooth transition to target RPM
        if target_rpm > self.wheg_rpm:
            self.wheg_rpm = min(self.wheg_rpm + self.SMOOTHNESS, target_rpm)
            self.wheg_rpm = max(self.wheg_rpm, self.MIN_RPM)
            self.wehg_rpm = min(self.wheg_rpm, self.MAX_RPM)
        else:
            self.wheg_rpm = max(self.wheg_rpm - self.SMOOTHNESS, target_rpm)
        if trigger_value == -1.0: # Low trigger value, ensure velocity is 0
            self.wheg_rpm = 0
        logging.debug(f"Adjusted wheg speed: target_rpm={target_rpm}, current_rpm={self.wheg_rpm}")
        return self.wheg_rpm
    
    def log(self, motor_positions, l2_trigger, r2_trigger, button_states, dpad_input):
        """Log the current robot state, including pivots, whegs, and controller inputs."""
        logging.info(f"Front pivot angle: {self.front_pivot_angle}")
        logging.info(f"Rear pivot angle: {self.rear_pivot_angle}")
        logging.info(f"Wheg RPMs: {self.wheg_rpms}")
        logging.info(f"Motor Positions: {motor_positions}")
        logging.info(f"L2 Trigger: {l2_trigger}, R2 Trigger: {r2_trigger}")
        logging.info(f"Button States: {button_states}")
        logging.info(f"D-Pad Input: {dpad_input}")

    async def control_pivots_with_dpad(self):
        """
        Control the front and rear pivots using the D-pad inputs from the controller.
        
        :param dpad_inputs: A dictionary with the state of each button, including the D-pad.
        :param config: The YAML configuration containing pivot parameters (pivot_step, min/max angles).
        """
        while self.allow_pivot_control:
            try:
                change = False
                # Adjust front and rear pivots based on D-pad input
                if self.dpad_inputs['dpad_down']:
                    self.adjust_front_pivot('down')
                    change = True
                elif self.dpad_inputs['dpad_up']:
                    self.adjust_front_pivot('up')
                    change = True
                elif self.dpad_inputs['dpad_right']:
                    self.adjust_rear_pivot('up')
                    change = True
                elif self.dpad_inputs['dpad_left']:
                    self.adjust_rear_pivot('down')
                    change = True

                if change:
                    # Prepare positions for sync write
                    pivot_positions = {
                        self.config['motor_ids']['pivots']['FRONT_PIVOT']: self.front_pivot_angle,
                        self.config['motor_ids']['pivots']['REAR_PIVOT']: self.rear_pivot_angle
                    }
                    
                    # Sync write the goal positions for the pivots
                    self.dynamixel.set_position_group('Pivot_Group', pivot_positions)

                    # Logging
                    logging.info(f"Front pivot angle set to {self.front_pivot_angle} degrees (ticks: {self.front_pivot_angle})")
                    logging.info(f"Rear pivot angle set to {self.rear_pivot_angle} degrees (ticks: {self.rear_pivot_angle})")
                    
            except Exception as e:
                logging.error(f"Error controlling pivots: {e}")
            
            await asyncio.sleep(0.25) #Control responsiveness
        
    # Define the initialization for each gait (for whegs only, pivots are disabled)
    async def gait_init_1(self):
        logging.info("Initialising Gait 1")
        self.gait_change_requested = False  # Reset the request flag
        if self.reboot_requested:
            logging.info("Reboot requested, resetting torque all motors")
            self.reboot_requested = False
            await asyncio.sleep(0.5) # Wait one second
            self.front_pivot_angle = self.config['pivot_parameters']['initial_front_angle'] # Reset the pivot angles
            self.rear_pivot_angle = self.config['pivot_parameters']['initial_rear_angle']
            self.dynamixel.torque_on_group('All_Motors')
        self.wheg_rpm = 0
        self.dynamixel.set_position_group('Wheg_Group', 180)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 3
        logging.info(f"Initialised Gait 1, waiting for {wait_time} seconds")
        await asyncio.sleep(wait_time)
        self.dynamixel.set_operating_mode_group('Wheg_Group', 'multi_turn')
        return

    async def gait_init_2(self):
        logging.info("Initialising Gait 2")
        self.gait_change_requested = False  # Reset the request flag
        # Update the min and max RPM for this gait:
        self.MIN_RPM = self.gait2_params['min_rpm']
        self.MAX_RPM = self.gait2_params['max_rpm']
        self.SMOOTHNESS = self.gait2_params['smoothness']
        self.LOW_POS = self.gait2_params['low_pos']
        self.HIGH_POS = self.gait2_params['high_pos']
        self.TOLERANCE = self.gait2_params['tolerance']
        self.odd_even = 0
        self.wheg_rpm = 0
        self.positions = { 1: self.LOW_POS, 2: self.HIGH_POS, 3: self.LOW_POS, 4: self.HIGH_POS, 5: self.LOW_POS, 6: self.HIGH_POS }
        self.dynamixel.set_position_group('Wheg_Group', self.positions)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 3
        logging.info(f"Initialised Gait 2, waiting for {wait_time} seconds")
        await asyncio.sleep(wait_time)
        self.dynamixel.set_operating_mode_group('Wheg_Group', 'multi_turn')
        return

    async def gait_init_3(self):      
        logging.info("Initialsing Gait 3")
        self.gait_change_requested = False  # Reset the request flag
        # Update the min, max and smoothness for this gait
        self.MIN_RPM = self.gait3_params['min_rpm']
        self.MAX_RPM = self.gait3_params['max_rpm']
        self.SMOOTHNESS = self.gait3_params['smoothness']
        self.wheg_rpm = 0
        self.odd_even = 0
        self.positions = { 1: self.gait3_params['high_pos'], 2: self.gait3_params['low_pos'], 3: self.gait3_params['low_pos'], 4: self.gait3_params['high_pos'], 5: self.gait3_params['low_pos'], 6: self.gait3_params['low_pos']}
        self.dynamixel.set_position_group('Wheg_Group', self.positions)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 3
        logging.info(f"Initialised Gait 3, waiting for {wait_time} seconds")
        await asyncio.sleep(wait_time)
        self.dynamixel.set_operating_mode_group('Wheg_Group', 'multi_turn')
        return

    async def gait_init_4(self):
        logging.info("Initialising Gait 4")
        self.gait_change_requested = False  # Reset the request flag
        self.wheg_rpm = 0
        self.dynamixel.set_position_group('Wheg_Group', 180)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 3
        logging.info(f"Initialised Gait 4, waiting for {wait_time} seconds")
        await asyncio.sleep(wait_time)
        self.dynamixel.set_operating_mode_group('Wheg_Group', 'multi_turn')
        return
        
    async def gait_1(self):
        """Execute Gait 1 and return how long to wait before the next step."""
        logging.debug("Executing Gait 1")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 1 and self.gait_change_requested == False:
        
            # Set the velocity limit for all whegs
            self.dynamixel.set_group_profile_velocity('Wheg_Group', self.wheg_rpm)
            increment = 360  # Example movement angle
            self.dynamixel.increment_group_position('Wheg_Group', increment)

            # Calculate wait time based on RPM (example formula: degrees moved / (6 * RPM))
            wait_time = increment / (6 * self.wheg_rpm)
            logging.info(f"Gait 1 step executed at {self.wheg_rpm:.2f}RPM, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time

    async def gait_2(self):
        """Execute Gait 2 and return how long to wait before the next step."""
        logging.debug("Executing Gait 2")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 1 and self.gait_change_requested == False:
            # Example RPM-based alternating gait logic
            if self.odd_even % 2 == 0:
                rpm_1 = self.wheg_rpm
                rpm_2 = self.wheg_rpm * (self.gait2_params['fast_ang'] / self.gait2_params['slow_ang'])
                inc_1 = self.gait2_params['slow_ang']
                inc_2 = self.gait2_params['fast_ang']
            else:
                rpm_1 = self.wheg_rpm * (self.gait2_params['fast_ang'] / self.gait2_params['slow_ang'])
                rpm_2 = self.wheg_rpm
                inc_1 = self.gait2_params['fast_ang']
                inc_2 = self.gait2_params['slow_ang']

            # Get the current motor positions
            current_positions = self.dynamixel.bulk_read_group('Wheg_Group', ['present_position'])

            # Convert the positions from dict to degrees by extracting the 'present_position' key from the dict
            current_positions = {
                motor_id: (pos_data['present_position'] * (360 / 4096))%359
                for motor_id, pos_data in current_positions.items()
            }

            # On even steps
            if self.odd_even % 2 == 0:
                # Check if not all motors are within the tolerance
                if not all(
                    abs(current_positions[motor_id] - self.positions[motor_id]) < self.TOLERANCE 
                    for motor_id in current_positions.keys()
                ):
                    logging.warning(f"Motors are not in the correct positions for Gait 2. Positions: {current_positions}")
                    logging.warning("Waiting for 1 second before checking for movement")
                    await asyncio.sleep(0.1)

                    # Get the current motor positions again after waiting
                    new_positions = self.dynamixel.bulk_read_group('Wheg_Group', ['present_position'])

                    # Convert the positions from dict to degrees
                    new_positions = {
                        motor_id: (pos_data['present_position'] * (360 / 4096))%359
                        for motor_id, pos_data in new_positions.items()
                    }

                    # Check if the motors are still moving
                    if all(abs(new_positions[motor_id] - current_positions[motor_id]) < 1 for motor_id in new_positions.keys()):
                        wait_time = 3 # Wait for 3 seconds to allow for resetting the gait
                        logging.critical("Motors are not moving, reseting positions, and waiting for 3 seconds.")
                        self.dynamixel.set_position_group('Wheg_Group', self.positions)                      
                        await asyncio.sleep(0.5)  # Wait for 0.5 second to allow for resetting the gait
                        self.dynamixel.set_operating_mode_group('Wheg_Group', 'multi_turn')
                    else:
                        logging.info("Motors are moving. Continuing with the gait.")
                        return 0.5  # No wait time, motors are moving correctly

            # Set profile velocities and increments
            velocities = {1: rpm_1, 2: rpm_2, 3: rpm_1, 4: rpm_2, 5: rpm_1, 6: rpm_2}
            increments = {1: inc_1, 2: inc_2, 3: inc_1, 4: inc_2, 5: inc_1, 6: inc_2}
            self.dynamixel.set_group_profile_velocity('Wheg_Group', velocities)
            self.dynamixel.increment_group_position('Wheg_Group', increments)

            # Calculate wait time
            wait_time = (inc_1 / (6 * rpm_1))+self.gait2_params['delay']
            self.odd_even += 1
            logging.info(f"Gait 2 step executed at {self.wheg_rpm:.2f}RPM, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time

    async def gait_3(self):
        """Execute Gait 3 and return how long to wait before the next step."""
        logging.debug("Executing Gait 3")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        
        if self.wheg_rpm > 1 and self.gait_change_requested == False:

            # Example alternating gait logic for three sets of whegs
            if self.odd_even % 3 == 0:
                rpm_1 = self.wheg_rpm
                rpm_2 = self.wheg_rpm
                rpm_3 = self.wheg_rpm
                inc_1 = self.gait3_params['fast_ang']
                inc_2 = self.gait3_params['slow_ang']
                inc_3 = 0
            elif self.odd_even % 3 == 1:
                rpm_1 = self.wheg_rpm
                rpm_2 = self.wheg_rpm
                rpm_3 = self.wheg_rpm
                inc_1 = 0
                inc_2 = self.gait3_params['fast_ang']
                inc_3 = self.gait3_params['slow_ang']
            else:
                rpm_1 = self.wheg_rpm
                rpm_2 = self.wheg_rpm
                rpm_3 = self.wheg_rpm
                inc_1 = self.gait3_params['slow_ang']
                inc_2 = 0
                inc_3 = self.gait3_params['fast_ang']
            
            # Get the current motor positions
            current_positions = self.dynamixel.bulk_read_group('Wheg_Group', ['present_position'])

            # Convert the positions from dict to degrees by extracting the 'present_position' key from the dict
            current_positions = {
                motor_id: (pos_data['present_position'] * (360 / 4096)) % 359
                for motor_id, pos_data in current_positions.items()
            }

            # Check if all motors are within the tolerance on even steps
            if self.odd_even % 3 == 0:
                if not all(
                    abs(current_positions[motor_id] - self.positions[motor_id]) < self.gait3_params['tolerance'] 
                    for motor_id in current_positions.keys()
                ):
                    logging.warning(f"Motors are not in the correct positions for Gait 3. Positions: {current_positions}")
                    logging.warning("Waiting for 1 second before checking for movement")
                    await asyncio.sleep(0.1)

                    # Get the current motor positions again after waiting
                    new_positions = self.dynamixel.bulk_read_group('Wheg_Group', ['present_position'])

                    # Convert the positions from dict to degrees
                    new_positions = {
                        motor_id: (pos_data['present_position'] * (360 / 4096)) % 359
                        for motor_id, pos_data in new_positions.items()
                    }

                    # Check if the motors are still moving
                    if all(abs(new_positions[motor_id] - current_positions[motor_id]) < 1 for motor_id in new_positions.keys()):
                        wait_time = 3  # Wait for 3 seconds to allow for resetting the gait
                        logging.critical("Motors are not moving, resetting positions, and waiting for 3 seconds.")
                        self.dynamixel.set_position_group('Wheg_Group', self.positions)                      
                        await asyncio.sleep(0.5)  # Wait for 0.5 second to allow for resetting the gait
                        self.dynamixel.set_operating_mode_group('Wheg_Group', 'multi_turn')
                    else:
                        logging.info("Motors are moving. Continuing with the gait.")
                        return 0.5  # No wait time, motors are moving correctly

            # Set profile velocities for all whegs
            velocities = {1: rpm_1, 2: rpm_2, 3: rpm_3, 4: rpm_1, 5: rpm_2, 6: rpm_3}
            increments = {1: inc_1, 2: inc_2, 3: inc_3, 4: inc_1, 5: inc_2, 6: inc_3}

            self.dynamixel.set_group_profile_velocity('Wheg_Group', velocities)
            self.dynamixel.increment_group_position('Wheg_Group', increments)

            # Calculate wait time based on the largest movement (300 degrees)
            wait_time = (self.gait3_params['fast_ang'] / (6 * self.wheg_rpm)) + self.gait3_params['delay']
            self.odd_even += 1
            logging.info(f"Gait 3 step executed at {self.wheg_rpm:.2f} RPM, wait for {wait_time:.2f} seconds")
            return wait_time

        return 0  # No movement, no wait time

    async def gait_4(self):
        """Execute Gait 4 and return how long to wait before the next step."""
        logging.debug("Executing Gait 4")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 1 and self.gait_change_requested == False:
        
            # Set the velocity limit for all whegs
            self.dynamixel.set_group_profile_velocity('Wheg_Group', self.wheg_rpm)
            increment = 360  # Example movement angle
            self.dynamixel.increment_group_position('Wheg_Group', increment)

            # Calculate wait time based on RPM (example formula: degrees moved / (6 * RPM))
            wait_time = increment / (6 * self.wheg_rpm)
            logging.info(f"Gait 4 step executed at {self.wheg_rpm:.2f}RPM, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time
    
    async def async_emergency_stop(self):
        """Asynchronously stop all motors during an emergency."""
        logging.warning("Emergency stop activated! Stopping all motors asynchronously.")
        self.dynamixel.set_velocity_group('All_Motors', 0)  # Stop all motors immediately
        await asyncio.sleep(0.01)  # Let other tasks run (non-blocking)

    async def check_inputs(self):
        """Asynchronously check for controller inputs, including gait change."""
        while True:
            self.button_states = self.ps4_controller.get_button_input()
            self.dpad_inputs = self.ps4_controller.get_dpad_input()
            self.l2_trigger, self.r2_trigger = self.ps4_controller.get_trigger_input()

            # Check for emergency stop (Circle button)
            if 'circle' in self.button_states and self.button_states['circle']:
                self.emergency_stop_activated = True
                await self.async_emergency_stop()

            # Optionally, resume control after emergency stop (X button)
            if 'x' in self.button_states and self.button_states['x'] and self.emergency_stop_activated:
                self.emergency_stop_activated = False
                logging.info("Emergency Stop Deactivated. Resuming control...")
                self.gait_change_requested = True
                self.next_gait_index = 0

            # Monitor Triangle (increase gait) and Square (decrease gait) buttons for gait change
            if  self.button_states['triangle']:
                self.next_gait_index = (self.current_gait_index + 1) % len(self.gait_methods)
                self.gait_change_requested = True  # Request a gait change
                logging.info(f"Triangle pressed. Preparing to change to next gait: {self.next_gait_index+1}")

            if  self.button_states['square']:
                self.next_gait_index = (self.current_gait_index - 1) % len(self.gait_methods)
                self.gait_change_requested = True  # Request a gait change
                logging.info(f"Square pressed. Preparing to change to previous gait: {self.next_gait_index+1}")
            
            if  self.button_states['share']:
                self.direction_change_requested = True # Request a direction change
                logging.info(f"Share pressed. Reversing the direction of the whegs")

            # Check for controller disconnection
            if self.button_states is None:
                logging.error("Controller is disconnected. Stopping robot.")
                self.emergency_stop()
                break

            await asyncio.sleep(0.01)  # Non-blocking wait to continue checking inputs

    async def execute_gait(self):
        """Execute the current gait asynchronously, adding a 2-second wait for initialization."""
        while True:
            if not self.emergency_stop_activated:

                # Get the current gait function and execute it
                gait_function = self.gait_methods[self.current_gait_index]
                wait_time = await gait_function()

                # Check if a gait change has been requested
                if self.gait_change_requested:
                    # Initialise the new gait (with a 2-second wait)
                    init_gait_function = self.gait_init_methods[self.next_gait_index]
                    await init_gait_function()  # Initialise the new gait
                    # Update current gait index
                    self.current_gait_index = self.next_gait_index
                    logging.info(f"New gait {self.current_gait_index + 1} is now active.")
                
                if self.direction_change_requested:
                    self.reverse_direction()
                    logging.info("Direction of whegs reversed.")

                if wait_time > 0:
                    logging.debug(f"Waiting for {wait_time:.2f} seconds before next gait step")
                    await asyncio.sleep(wait_time)  # Non-blocking wait for the calculated time
            else:
                logging.info("Emergency stop activated, gait execution paused.")

            await asyncio.sleep(0.01)  # Small sleep to allow other tasks to run

    async def report_states(self, log_interval=5):
        """
        Asynchronously collect and log critical information from the robot using bulk read.
        
        :param log_interval: Time (in seconds) between each report logging.
        """
        while True:
            try:
                # Perform a bulk read to gather critical motor information (e.g., positions, velocities)
                motor_positions = self.dynamixel.bulk_read_group('All_Motors', ['present_position'])
                motor_velocities = self.dynamixel.bulk_read_group('All_Motors', ['present_velocity'])
                
                # Optionally, you can include other states like motor loads
                motor_loads = self.dynamixel.bulk_read_group('All_Motors', ['present_load'])
                hardware_errors = self.dynamixel.bulk_read_group('All_Motors', ['hardware_error_status'])

                # Logging system with load conversion
                logging.info(f"{'Motor':<10}{'Position (degrees)':<25}{'Velocity (RPM)':<20}{'Load (%)':<10}")

                for motor_id in motor_positions.keys():
                    position_ticks = motor_positions[motor_id].get('present_position', 'N/A')
                    velocity = motor_velocities[motor_id].get('present_velocity', 'N/A')
                    load = motor_loads[motor_id].get('present_load', 'N/A') if motor_loads else 'N/A'

                    # Convert position from ticks to degrees
                    if isinstance(position_ticks, (int, float)):
                        position_degrees = ((position_ticks * 360) / 4096) % 359
                    else:
                        position_degrees = 'N/A'

                    # Convert velocity from ticks/sec to RPM
                    if isinstance(velocity, (int, float)):
                        velocity_rpm = (velocity * 0.229)
                    else:
                        velocity_rpm = 'N/A'

                    # Convert load to signed 16-bit
                    if isinstance(load, (int, float)):
                        if load > 32767:
                            load_signed = load - 65536
                        else:
                            load_signed = load
                    else:
                        load_signed = 'N/A'

                    # Log the motor information
                    logging.info(f"{motor_id:<10}{position_degrees:<25.2f}{velocity_rpm:<20.2f}{load_signed:<10}")

                # Check for hardware errors and log them
                error_detected = False
                reboot_id = None

                # Ensure hardware_errors contains valid data
                if hardware_errors:
                    for motor_id, error_status_dict in hardware_errors.items():
                        error_status = error_status_dict.get('hardware_error_status', 0)
                        if error_status != 0:  # Non-zero error status indicates a hardware error
                            error_detected = True
                            logging.error(f"Hardware error detected on motor {motor_id}: Error code {error_status}")
                            reboot_id = motor_id
                            
                            # Decode the hardware error based on the error status bits
                            if error_status & 0b00000001:  # Bit 0 - Input Voltage Error
                                logging.error(f"Motor {motor_id}: Input Voltage Error detected.")
                            if error_status & 0b00000100:  # Bit 2 - Overheating Error
                                logging.error(f"Motor {motor_id}: Overheating Error detected.")
                            if error_status & 0b00001000:  # Bit 3 - Motor Encoder Error
                                logging.error(f"Motor {motor_id}: Motor Encoder Error detected.")
                            if error_status & 0b00010000:  # Bit 4 - Electrical Shock Error
                                logging.error(f"Motor {motor_id}: Electrical Shock Error detected.")
                            if error_status & 0b00100000:  # Bit 5 - Overload Error
                                logging.error(f"Motor {motor_id}: Overload Error detected.")

                # If any hardware errors are detected, reset motors and change gait
                if error_detected and reboot_id is not None:
                    logging.warning(f"Hardware error detected on motor {reboot_id}. Rebooting motor and resetting gait...")
                    reboot_success = self.dynamixel.reboot_motor(reboot_id)  # Reboot the motor
                    if reboot_success: # If reboot is successful, request a gait change
                        logging.info(f"Motor {reboot_id} rebooted successfully.")
                        self.reboot_requested = True
                        self.gait_change_requested = True
                        self.next_gait_index = 0 # Set the next gait index to 0
                    else: # Emergency stop if reboot fails
                        logging.warning(f"Warning - Motor {reboot_id} reboot failed. Executing emergency stop.")
                        await self.async_emergency_stop()

                # Wait for the specified log_interval before the next report
                await asyncio.sleep(log_interval)

            except Exception as e:
                logging.error(f"Error while reporting robot states: {e}")
                # In case of an error, wait briefly before retrying
                await asyncio.sleep(1)

    async def main_loop(self):
        """Main loop to run the asynchronous tasks, with safe shutdown on KeyboardInterrupt."""
        try:
            await asyncio.gather(
                self.check_inputs(),    # Run input checking
                self.execute_gait(),    # Run gait execution
                self.control_pivots_with_dpad(),
                self.report_states(5)   # Log states every 5 seconds (customizable interval)
            )
        
        except asyncio.CancelledError:
            # Handle task cancellation gracefully and log that tasks were cancelled
            logging.info("Tasks were cancelled due to shutdown, proceeding to cleanup...")
            # Suppress further propagation of CancelledError
            pass

        except KeyboardInterrupt:
            # This block might not be necessary if KeyboardInterrupt triggers a CancelledError
            logging.info("Program interrupted. Proceeding to shutdown.")

        finally:
            # Safely stop all motors and close connections
            logging.info("Initiating safe shutdown...")
            self.dynamixel.set_velocity_group('All_Motors', {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0})  # Stop all motors
            self.dynamixel.set_position_group('All_Motors', 180)  # Reset motor positions
            self.ps4_controller.close()  # Close the PS4 controller connection
            self.dynamixel.close()  # Close the Dynamixel controller connection
            logging.info("Shutdown complete.")

if __name__ == "__main__":
    robot = FLIKRobot()
    asyncio.run(robot.main_loop())

