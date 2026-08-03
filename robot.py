import time
from hardware import Arduino
from drivetrain import Drivetrain
from controller import Controller
from camera import Camera

LOOP_HZ = 50             # Control loop update rate (50 Hz = 20ms)
LOOP_DELAY = 1.0 / LOOP_HZ

class Robot:
    DIRECT_CONTROLLER = "CONTROLLER"
    WEB_CONTROLLER = "WEB_CONTROLLER"

    controller_mode = DIRECT_CONTROLLER
    on = False
    def initiate():
        Robot.controller_mode = Robot.DIRECT_CONTROLLER
        Arduino.connect_arduino()
        time.sleep(1)
        Drivetrain.initiate()
        time.sleep(0.5)
        Controller.connect()
        time.sleep(0.5)
        Camera.initiate()
        Robot.on = True
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
    def run():
        if (not Robot.on):
            return
        x,y,r = 0,0,0
        if Robot.controller_mode == Robot.WEB_CONTROLLER:
            return
        if not Controller.connected:
            return
        Controller.run()
        controller = Controller.controller
        x = Controller.apply_deadzone(controller.get_axis(Controller.AXIS_LEFT_STICK_X))
        y = -Controller.apply_deadzone(controller.get_axis(Controller.AXIS_LEFT_STICK_Y))
        r = Controller.apply_deadzone(controller.get_axis(Controller.AXIS_RIGHT_STICK_X))
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
        except Exception:
            pass
        print("✅ Shutdown complete.")






    