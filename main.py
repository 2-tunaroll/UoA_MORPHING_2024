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
    
    def setup_pivots(self):
        # Set position limits for the pivot motors
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
        self.report_timer = time.time()
        self.gait_change_requested = True

        # Gait parameters
        self.odd_even = 0
        self.gait_parameters = {}
        self.gait_parameters['gait_2'] = {}
        self.gait_parameters['gait_2']['slow_ang'] = self.config['gaits']['gait_2']['slow_ang']
        self.gait_parameters['gait_2']['fast_ang'] = self.config['gaits']['gait_2']['fast_ang']

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
            self.front_pivot_angle = max(self.front_pivot_angle - self.pivot_step, self.pivot_max_angle)
        elif direction == 'down':
            self.front_pivot_angle = min(self.front_pivot_angle + self.pivot_step, self.pivot_min_angle)

    def adjust_rear_pivot(self, direction):
        """Adjust the rear pivot angle based on D-pad input."""
        if direction == 'up':
            self.rear_pivot_angle = max(self.rear_pivot_angle - self.pivot_step, self.pivot_max_angle)
        elif direction == 'down':
            self.rear_pivot_angle = min(self.rear_pivot_angle + self.pivot_step, self.pivot_min_angle)

    def adjust_wheg_rpm(self, trigger_value):
        """ Function to adjust the speed of the whegs based on how far the right trigger is pressed. Smooth transition to target RPM. """
        logging.debug(f"Adjusting wheg speed: trigger_value={trigger_value}, current_rpm={self.wheg_rpm}")
        target_rpm = ((trigger_value + 1) / 2) * (self.MAX_RPM - self.MIN_RPM) + self.MIN_RPM # Trigger value ranges from -1 to 1, map this to RPM range
        # Implement smooth transition to target RPM
        if target_rpm > self.wheg_rpm:
            self.wheg_rpm = min(self.wheg_rpm + self.SMOOTHNESS, target_rpm)
        elif trigger_value < -0.95: # Low trigger value, ensure velocity is 0
            self.wheg_rpm = 0
        else:
            self.wheg_rpm = max(self.wheg_rpm - self.SMOOTHNESS, target_rpm)
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

    def control_pivots_with_dpad(self, dpad_inputs):
        """
        Control the front and rear pivots using the D-pad inputs from the controller.
        
        :param dpad_inputs: A dictionary with the state of each button, including the D-pad.
        :param config: The YAML configuration containing pivot parameters (pivot_step, min/max angles).
        """
        # Adjust front and rear pivots based on D-pad input
        if dpad_inputs['dpad_down']:
            self.adjust_front_pivot('down')
        elif dpad_inputs['dpad_up']:
            self.adjust_front_pivot('up')
        elif dpad_inputs['dpad_right']:
            self.adjust_rear_pivot('up')
        elif dpad_inputs['dpad_left']:
            self.adjust_rear_pivot('down')

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
        
    # Define the initialization for each gait (for whegs only, pivots are disabled)
    async def gait_init_1(self):
        logging.info("Initialising Gait 1")
        self.wheg_rpm = 0
        self.dynamixel.set_position_group('Wheg_Group', 180)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 1
        logging.info(f"Initialised Gait 1, waiting for {wait_time} seconds")
        return wait_time

    async def gait_init_2(self):
        logging.info("Initialising Gait 2")
        self.wheg_rpm = 0
        positions = { # Setup dict with initial position for each wheg
            1: 160,
            2: 200,
            3: 160,
            4: 200,
            5: 160,
            6: 200,
        }
        self.dynamixel.set_position_group('Wheg_Group', positions)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 1
        logging.info(f"Initialised Gait 2, waiting for {wait_time} seconds")
        return wait_time

    async def gait_init_3(self):      
        logging.info("Initialsing Gait 3")
        self.wheg_rpm = 0
        self.set_position_group('Wheg_Group', 180)
        self.set_position_group('Pivot_Group', 180)
        wait_time = 1
        logging.info(f"Initialised Gait 3, waiting for {wait_time} seconds")
        return wait_time

    async def gait_init_4(self):
        logging.info("Initialising Gait 4")
        self.wheg_rpm = 0
        self.dynamixel.set_position_group('Wheg_Group', 180)
        self.dynamixel.set_position_group('Pivot_Group', 180)
        wait_time = 1
        logging.info(f"Initialised Gait 4, waiting for {wait_time} seconds")
        return wait_time
        
    async def gait_1(self):
        """Execute Gait 1 and return how long to wait before the next step."""
        logging.debug("Executing Gait 1")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 1:
        
            # Set the velocity limit for all whegs
            self.dynamixel.set_group_profile_velocity('Wheg_Group', self.wheg_rpm)
            increment = 180  # Example movement angle
            self.dynamixel.increment_group_position('Wheg_Group', increment)

            # Calculate wait time based on RPM (example formula: degrees moved / (6 * RPM))
            wait_time = 180 / (6 * self.wheg_rpm)
            logging.info(f"Gait 1 step executed, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time

    async def gait_2(self):
        """Execute Gait 2 and return how long to wait before the next step."""
        logging.debug("Executing Gait 2")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 1:
            # Example RPM-based alternating gait logic
            if self.odd_even % 2 == 0:
                rpm_1 = self.wheg_rpm
                rpm_2 = self.wheg_rpm * (self.gait_parameters['gait_2']['fast_ang'] / self.gait_parameters['gait_2']['slow_ang'])
                inc_1 = self.gait_parameters['gait_2']['slow_ang']
                inc_2 = self.gait_parameters['gait_2']['fast_ang']
            else:
                rpm_1 = self.wheg_rpm * (self.gait_parameters['gait_2']['fast_ang'] / self.gait_parameters['gait_2']['slow_ang'])
                rpm_2 = self.wheg_rpm
                inc_1 = self.gait_parameters['gait_2']['fast_ang']
                inc_2 = self.gait_parameters['gait_2']['slow_ang']

            # Set profile velocities and increments
            velocities = {1: rpm_1, 2: rpm_2, 3: rpm_1, 4: rpm_2, 5: rpm_1, 6: rpm_2}
            increments = {1: inc_1, 2: inc_2, 3: inc_1, 4: inc_2, 5: inc_1, 6: inc_2}
            self.dynamixel.set_group_profile_velocity('Wheg_Group', velocities)
            self.dynamixel.increment_group_position('Wheg_Group', increments)

            # Calculate wait time
            wait_time = inc_1 / (6 * self.wheg_rpm)
            self.odd_even += 1
            logging.info(f"Gait 2 step executed, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time

    async def gait_3(self):
        """Execute Gait 3 and return how long to wait before the next step."""
        logging.debug("Executing Gait 3")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 1:
            # Set the velocity limit for all whegs
            self.dynamixel.set_group_profile_velocity('Wheg_Group', self.wheg_rpm)
            increment = 180  # Example movement angle
            self.dynamixel.increment_group_position('Wheg_Group', increment)

            # Calculate wait time
            wait_time = 180 / (6 * self.wheg_rpm)
            logging.info(f"Gait 3 step executed, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time

    async def gait_4(self):
        """Execute Gait 4 and return how long to wait before the next step."""
        logging.debug("Executing Gait 4")
        self.wheg_rpm = self.adjust_wheg_rpm(self.r2_trigger)
        if self.wheg_rpm > 5:
            # Set the velocity limit for all whegs
            self.dynamixel.set_group_profile_velocity('Wheg_Group', self.wheg_rpm)
            increment = 180  # Example movement angle
            self.dynamixel.increment_group_position('Wheg_Group', increment)

            # Calculate wait time
            wait_time = 180 / (6 * self.wheg_rpm)
            logging.info(f"Gait 4 step executed, wait for {wait_time:.2f} seconds")
            return wait_time
        return 0  # No movement, no wait time

    async def async_emergency_stop(self):
        """Asynchronously stop all motors during an emergency."""
        logging.warning("Emergency stop activated! Stopping all motors asynchronously.")
        self.dynamixel.set_group_velocity('All_Motors', 0)  # Stop all motors immediately
        await asyncio.sleep(0.01)  # Let other tasks run (non-blocking)

    async def check_inputs(self):
        """Asynchronously check for controller inputs, including gait change."""
        while True:
            self.button_states = self.ps4_controller.get_button_input()
            self.dpad_input = self.ps4_controller.get_dpad_input()
            self.l2_trigger, self.r2_trigger = self.ps4_controller.get_trigger_input()

            # Check for emergency stop (Circle button)
            if 'circle' in self.button_states and self.button_states['circle']:
                self.emergency_stop_activated = True
                await self.async_emergency_stop()

            # Optionally, resume control after emergency stop (X button)
            if 'x' in self.button_states and self.button_states['x'] and self.emergency_stop_activated:
                self.emergency_stop_activated = False
                logging.info("Emergency Stop Deactivated. Resuming control...")

            # Monitor Triangle (increase gait) and Square (decrease gait) buttons for gait change
            if  self.button_states['triangle']:
                self.next_gait_index = (self.current_gait_index + 1) % len(self.gait_methods)
                self.gait_change_requested = True  # Request a gait change
                logging.info(f"Triangle pressed. Preparing to change to next gait: {self.next_gait_index}")

            if  self.button_states['square']:
                self.next_gait_index = (self.current_gait_index - 1) % len(self.gait_methods)
                self.gait_change_requested = True  # Request a gait change
                logging.info(f"Square pressed. Preparing to change to previous gait: {self.next_gait_index}")

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
                    wait_time = await init_gait_function()  # Initialize the new gait
                    await asyncio.sleep(wait_time)  # Wait for initialisation

                    # Update current gait index
                    self.current_gait_index = self.next_gait_index
                    self.gait_change_requested = False  # Reset the request flag
                    logging.info(f"New gait {self.current_gait_index} is now active.")

                if wait_time > 0:
                    logging.info(f"Waiting for {wait_time:.2f} seconds before next gait step")
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

                # Log the collected data
                logging.info(f"Motor Positions: {motor_positions}")
                logging.info(f"Motor Velocities: {motor_velocities}")
                logging.info(f"Motor Loads: {motor_loads}")

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
                self.report_states(5)   # Log states every 5 seconds (customizable interval)
            )
        
        except asyncio.CancelledError:
            logging.info("Tasks were cancelled, shutting down gracefully...")
            # Handle task cancellation properly, we still want to go to `finally`
            raise

        except KeyboardInterrupt:
            logging.info("Terminating program...")

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

