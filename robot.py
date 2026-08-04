import time

from subsystems.camera import Camera
from subsystems.controller import Controller
from subsystems.drivetrain import Drivetrain
from subsystems.hardware import Arduino

LOOP_HZ = 50             # Control loop update rate (50 Hz = 20ms)
LOOP_DELAY = 1.0 / LOOP_HZ
PING_DELAY = 1.0

class RobotState:
    IDLE = "IDLE"
    TELEOP = "TELEOP"
    AUTO = "AUTO"
class ControllerState:
    DIRECT = "DIRECT_CONTROLLER"
    WEB_BASED = "WEB_CONTROLLER"
    DEFAULT = WEB_BASED

class Robot:


    controller_mode = ControllerState.DEFAULT
    on = False

    state = RobotState.TELEOP

    ping_start_time = time.perf_counter()

    @staticmethod
    def initiate():
        Robot.controller_mode = ControllerState.DEFAULT
        Controller.connect()
        time.sleep(0.5)
        if Controller.connected:
            Robot.controller_mode = ControllerState.DIRECT
        Camera.initiate()
        time.sleep(0.5)
        Arduino.connect_arduino()
        time.sleep(1)
        Drivetrain.initiate()
        Robot.on = True
    @staticmethod
    def stop():
        print("Stopping Robot")
        Robot.on = False
        Arduino.stop()
        time.sleep(0.1)
        Arduino.close()
        time.sleep(.1)
        Camera.stop()
        time.sleep(0.1)
        if (Robot.controller_mode == ControllerState.DIRECT):
            Controller.disconnect()
    @staticmethod
    def run():
        if (not Robot.on):
            return
        Camera.read()
        elapsed = time.perf_counter() - Robot.ping_start_time
        if (elapsed > PING_DELAY):
            Arduino.ping()
            Robot.ping_start_time = time.perf_counter()

        if Robot.state == RobotState.IDLE:
            return

        x,y,r = Controller.left_stick_x, Controller.left_stick_y, Controller.right_stick_x
        if Robot.controller_mode == ControllerState.DIRECT:
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
