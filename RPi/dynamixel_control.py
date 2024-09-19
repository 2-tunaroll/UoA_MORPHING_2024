from dynamixel_sdk import *  # Import Dynamixel SDK library

class DynamixelController:
    def __init__(self, device_name, baudrate, protocol_version=2.0):
        self.port_handler = PortHandler(device_name)
        self.packet_handler = PacketHandler(protocol_version)

        if not self.port_handler.openPort():
            raise Exception("Failed to open the port")

        if not self.port_handler.setBaudRate(baudrate):
            raise Exception("Failed to change the baudrate")

        self.dxl_id1 = 1  # First motor ID
        self.dxl_id2 = 2  # Second motor ID
        self.ADDR_TORQUE_ENABLE = 64
        self.ADDR_GOAL_POSITION = 116
        self.ADDR_PRESENT_POSITION = 132
        self.TORQUE_ENABLE = 1
        self.TORQUE_DISABLE = 0

        # Enable torque on both motors
        self._enable_torque(self.dxl_id1)
        self._enable_torque(self.dxl_id2)

    def _enable_torque(self, dxl_id):
        self.packet_handler.write1ByteTxRx(self.port_handler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_ENABLE)

    def disable_torque(self):
        self.packet_handler.write1ByteTxRx(self.port_handler, self.dxl_id1, self.ADDR_TORQUE_ENABLE, self.TORQUE_DISABLE)
        self.packet_handler.write1ByteTxRx(self.port_handler, self.dxl_id2, self.ADDR_TORQUE_ENABLE, self.TORQUE_DISABLE)

    def set_goal_position(self, motor_id, position):
        self.packet_handler.write4ByteTxRx(self.port_handler, motor_id, self.ADDR_GOAL_POSITION, position)

    def get_present_position(self, motor_id):
        present_position, _, _ = self.packet_handler.read4ByteTxRx(self.port_handler, motor_id, self.ADDR_PRESENT_POSITION)
        return present_position

    def close(self):
        self.disable_torque()
        self.port_handler.closePort()
