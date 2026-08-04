import time

import pygame
from pygame.joystick import JoystickType


class Controller:
    # PS5 DualSense Axis Mappings
    AXIS_LEFT_STICK_X = 0    # Strafe Left / Right
    AXIS_LEFT_STICK_Y = 1    # Forward / Backward
    AXIS_RIGHT_STICK_X = 3   # Rotation (CW / CCW)

    DEADZONE = 0.12          # Filters out stick drift below 12% deflection

    controller : JoystickType
    connected = False

    left_stick_x,left_stick_y,right_stick_x = 0.0,0.0,0.0 #I switched my code editor to zed and it for some reason loves consistent data types so these are floats...
    @staticmethod
    def apply_deadzone(value: float, threshold: float = DEADZONE) -> float:
        """Zeroes out minor joystick drift around center."""
        if abs(value) < threshold:
            return 0.0
        return value
    @staticmethod
    def disconnect():
        Controller.connected = False
        pygame.joystick.quit()
        pygame.joystick.init()
    @staticmethod
    def connect():
        try:
            pygame.init()
            pygame.joystick.init()
            Controller.connected = True
        except:
            print("No gamepad found")

        if (not Controller.connected):
            return
        time.sleep(0.2)

        try:
            Controller.controller = pygame.joystick.Joystick(0)
            Controller.controller.init()
            print(f"🎮 Connected Controller: {Controller.controller.get_name()}")
        except:
            Controller.connected = False
            print("gamepad disconnected")
    @staticmethod
    def run():
        pygame.event.pump()
        if not Controller.connected:
            return
        controller = Controller.controller
        Controller.left_stick_x = Controller.apply_deadzone(controller.get_axis(Controller.AXIS_LEFT_STICK_X))
        Controller.left_stick_y = -Controller.apply_deadzone(controller.get_axis(Controller.AXIS_LEFT_STICK_Y))
        Controller.right_stick_x = Controller.apply_deadzone(controller.get_axis(Controller.AXIS_RIGHT_STICK_X))
    @staticmethod
    def zero_joysticks():
        Controller.left_stick_x = 0.0
        Controller.left_stick_y = 0.0
        Controller.right_stick_x = 0.0
