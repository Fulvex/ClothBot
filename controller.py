import pygame
import time
class Controller:
    # PS5 DualSense Axis Mappings
    AXIS_LEFT_STICK_X = 0    # Strafe Left / Right
    AXIS_LEFT_STICK_Y = 1    # Forward / Backward
    AXIS_RIGHT_STICK_X = 3   # Rotation (CW / CCW)

    DEADZONE = 0.12          # Filters out stick drift below 12% deflection

    controller = None
    connected = False
    def apply_deadzone(value: float, threshold: float = DEADZONE) -> float:
        """Zeroes out minor joystick drift around center."""
        if abs(value) < threshold:
            return 0.0
        return value
    def disconnect():
        Controller.connected = False
        pygame.joystick.quit()
        pygame.joystick.init()
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
    def run():
        pygame.event.pump()
