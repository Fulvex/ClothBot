import threading
import time

from flask_socketio import SocketIO
from pygame.threads import Thread
from subsystems.radio_controller import RadioController

from subsystems.camera import Camera, ConnectionType
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
    DEFAULT = DIRECT

class Robot:
    controller_mode = ControllerState.DEFAULT
    on = False

    state = RobotState.TELEOP

    ping_start_time = time.perf_counter()
    start_time = time.perf_counter()

    thread : Thread

    radio : RadioController | None

    @staticmethod
    def initiate(socket : SocketIO | None):
        Robot.controller_mode = ControllerState.DEFAULT
        Controller.connect()
        time.sleep(0.5)
        if Controller.connected:
            Robot.controller_mode = ControllerState.DIRECT
        Robot.radio = RadioController('DRONE')
        time.sleep(0.5)
        Camera.initiate(socket,Robot.radio)
        time.sleep(0.5)
        Arduino.connect_arduino()
        time.sleep(1)
        Drivetrain.initiate()
        time.sleep(0.5)
        Robot.on = True
        Robot.thread = threading.Thread(target=Robot.run)
        Robot.thread.start()
        Robot.start_time = time.perf_counter()

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
        if (Robot.thread is not None):
            Robot.thread.join()
    @staticmethod
    def run():
        while Robot.on:
            elapsed = time.perf_counter() - Robot.start_time
            if (elapsed < LOOP_DELAY):
                time.sleep(LOOP_DELAY - elapsed)
                Robot.start_time = time.perf_counter()
            elapsed = time.perf_counter() - Robot.ping_start_time
            if (elapsed > PING_DELAY):
                Arduino.ping()
                Robot.ping_start_time = time.perf_counter()

            if Robot.state == RobotState.IDLE:
                continue
            x,y,r = Controller.left_stick_x, Controller.left_stick_y, Controller.right_stick_x
            if Robot.controller_mode == ControllerState.DIRECT:
                Controller.run()
                if (not Controller.connected):
                    if (isinstance(Robot.radio,RadioController)):
                        x,y,r = Robot.radio.x, Robot.radio.y, Robot.radio.r
                    else:
                        x,y,r = 0,0,0
                else:
                    if Controller.controller.get_button(Controller.RIGHT_BUMPER) and not Controller.prev_rb:
                        if (Robot.state == RobotState.TELEOP):
                            Robot.state = RobotState.AUTO
                            Camera.tag_enabled = True
                        else:
                            Robot.state = RobotState.TELEOP
                            Camera.tag_enabled = False
                    Controller.prev_rb = Controller.controller.get_button(Controller.RIGHT_BUMPER)

            if (Robot.state == RobotState.AUTO):
                Camera.tag_enabled = True
                r = Camera.turn
                y = Camera.drive
            Drivetrain.run(x,y,r)
