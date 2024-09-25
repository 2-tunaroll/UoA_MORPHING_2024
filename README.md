# BIO-INSPIRED MORPHING ROBOT FOR EXTRATERRESTRIAL TERRAIN

This repository contains the code required to run the FLIK rebot.

1. [Installation](#installation)
2. [Usage](#usage)
3. [Features](#features)
5. [License](#license)
6. [Contact](#contact)

## Installlation

DynamixelController Python Module README

This script utilizes the dynamixel_sdk to control Dynamixel motors connected to a Raspberry Pi via an Open RB15 motor controller board. The DynamixelController class provides an interface to control motor groups using sync write and bulk read commands.
Requirements

    dynamixel_sdk
    yaml
    logging

Initialization
DynamixelController(config_path='config.yaml', device_name=None, baudrate=None, protocol_version=2.0)

Initializes the controller using the provided configuration file and optional device parameters.

    config_path: Path to the configuration YAML file.
    device_name: Device name (e.g., /dev/ttyUSB0). If not provided, it will use the config file.
    baudrate: Baud rate for communication. If not provided, it will use the config file.
    protocol_version: Protocol version for the Dynamixel motors (default is 2.0).

Functions
open_port()

Opens the communication port for the motors and sets the baud rate based on the configuration.
create_motor_group(group_name, motor_ids)

Creates a group of motors for easier control. This is useful when controlling multiple motors simultaneously.

    group_name: A string representing the name of the motor group.
    motor_ids: A list of motor IDs.

setup_motor_groups()

Loads motor groups from the YAML config and sets them up in the controller. Motors can be grouped logically for bulk operations.
load_control_table()

Loads the control table from the configuration file. The control table defines addresses and lengths for various motor control parameters like position_goal, velocity_goal, etc.
set_status_return_level(group_name, level=1)

Sets the status return level for a group of motors. The status return level defines how much feedback the motors return.

    group_name: Name of the motor group.
    level: Status return level (0: no return, 1: return only for read commands, 2: return for all commands).

sync_write_group(group_name, parameter_name, param_dict)

Sync write a parameter to multiple motors in a group.

    group_name: Name of the motor group.
    parameter_name: Parameter to write (e.g., position_goal, velocity_goal).
    param_dict: Dictionary mapping motor IDs to the values to be written.

bulk_read_group(group_name, parameters)

Performs a bulk read operation for a group of motors.

    group_name: Name of the motor group.
    parameters: List of control parameters to read (e.g., present_position, present_velocity).
    Returns: Dictionary where keys are motor IDs and values are the read data for each parameter.

set_operating_mode_group(group_name, mode)

Sets the operating mode for a group of motors. Available modes are 'position', 'velocity', and 'multi_turn'.

    group_name: Name of the motor group.
    mode: Operating mode to set (e.g., 'position', 'velocity', 'multi_turn').

set_group_velocity_limit(group_name)

Sets the velocity limit for a motor group. The velocity limit is loaded from the config file.

    group_name: Name of the motor group.

set_group_profile_velocity(group_name, profile_velocity=None)

Sets the profile velocity for a motor group. It can either use the profile velocity from the config or an optional override value.

    group_name: Name of the motor group.
    profile_velocity: Optional override value for the profile velocity.

torque_off_group(group_name)

Disables torque for all motors in a group.

    group_name: Name of the motor group.

torque_on_group(group_name)

Enables torque for all motors in a group.

    group_name: Name of the motor group.

set_position_group(group_name, positions_dict)

Sets target positions (in degrees) for all motors in a group.

    group_name: Name of the motor group.
    positions_dict: Dictionary where keys are motor IDs and values are the target positions in degrees.

set_velocity_group(group_name, velocities_dict)

Sets target velocities for all motors in a group.

    group_name: Name of the motor group.
    velocities_dict: Dictionary where keys are motor IDs and values are the target velocities.

set_drive_mode_group(group_name, reverse_direction=False)

Sets the drive mode for all motors in a group. Allows for normal or reverse mode.

    group_name: Name of the motor group.
    reverse_direction: If True, sets motors to reverse mode; otherwise, normal mode.

increment_motor_position_by_degrees(group_name, new_positions_dict)

Increments the motor positions for a group by a specified number of degrees.

    group_name: Name of the motor group.
    new_positions_dict: Dictionary where keys are motor IDs and values are the new target positions in degrees.

set_position_limits_group(group_name, min_degrees=None, max_degrees=None)

Sets the position limits (min and max) for a group of motors.

    group_name: Name of the motor group.
    min_degrees: Minimum allowable position in degrees (optional).
    max_degrees: Maximum allowable position in degrees (optional).

set_motor_baud_rate(group_name, baud_rate_value)

Sets the baud rate for a group of motors.

    group_name: Name of the motor group.
    baud_rate_value: Baud rate value to set (e.g., 3 for 1 Mbps).