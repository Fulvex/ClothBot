import time

from subsystems.camera import Camera
from subsystems.controller import Controller
from subsystems.drivetrain import Drivetrain
from subsystems.hardware import Arduino

LOOP_HZ = 50             # Control loop update rate (50 Hz = 20ms)
LOOP_DELAY = 1.0 / LOOP_HZ

class Robot:
    DIRECT_CONTROLLER = "DIRECT_CONTROLLER"
    WEB_CONTROLLER = "WEB_CONTROLLER"
    DEFAULT_CONTROLLER = WEB_CONTROLLER

    controller_mode = DEFAULT_CONTROLLER
    on = False

    @staticmethod
    def initiate():
        Robot.controller_mode = Robot.DEFAULT_CONTROLLER
        Arduino.connect_arduino()
        time.sleep(1)
        Drivetrain.initiate()
        time.sleep(0.5)
        Controller.connect()
        time.sleep(0.5)
        Camera.initiate()
        Robot.on = True
    @staticmethod
    def stop():
        Robot.on = False
        Arduino.stop()
        time.sleep(0.1)
        Arduino.close()
        time.sleep(.1)
        Camera.stop()
        time.sleep(0.1)
        if (Robot.controller_mode == Robot.DIRECT_CONTROLLER):
            Controller.disconnect()
    @staticmethod
    def run():
        if (not Robot.on):
            return
        x,y,r = Controller.left_stick_x, Controller.left_stick_y, Controller.right_stick_x
        if Robot.controller_mode == Robot.DIRECT_CONTROLLER:
            Controller.run()
            if (not Controller.connected):
                x,y,r = 0,0,0
        Drivetrain.run(x,y,r)

if __name__ == "__main__":
    try:
        Robot.initiate()
        time.sleep(1)
        while True:
            Robot.run()
            time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        print("🛑 Stopping all motors...")
        try:
            Robot.stop()
        finally:
            print("✅ Shutdown complete.")
