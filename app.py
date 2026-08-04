import time

from flask import Flask, render_template
from flask_socketio import SocketIO

from robot import *

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")


def get_telemetry():
    return {"Robot On" : Robot.on,
        "Arduino Connected": Arduino.connected,
        "Camera Connected": Camera.connected,
        "Controller Mode" : Robot.controller_mode,
        "Controller Connected (Direct)" : Controller.connected,
        "Robot State" : Robot.state
    }

def background_thread():
    start_time = time.perf_counter()
    while True:
        try:
            Robot.run()
            socketio.emit("telemetry_update", get_telemetry())
        finally:
            elapsed = time.perf_counter() - start_time
            if (elapsed < LOOP_DELAY):
                time.sleep(LOOP_DELAY - elapsed)
            start_time = time.perf_counter()

@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("Client connected to dashboard!")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected!")
    Controller.zero_joysticks()
    Robot.stop()
    Robot.controller_mode = ControllerState.DIRECT



@socketio.on("robot_command")
def handle_robot_command(data):
    print(f"Received command from laptop: {data}")
    command,val = None,None
    for key,value in data.items():
        if key == "command":
            command = value
        elif key == "val":
            val = value
    if (command == None):
        return
    if command == "STATE":
        if (isinstance(val,str)):
            Robot.state = val
    elif command == "DIRECT_CONTROL":
        Robot.controller_mode = ControllerState.DIRECT
        Robot.state = RobotState.TELEOP
    elif command == "WEB_CONTROL":
        Robot.controller_mode = ControllerState.WEB_BASED
        Robot.state = RobotState.TELEOP
    elif command == "DISCONNECT":
        Robot.stop()
    elif command == "CONNECT":
        Robot.initiate(socketio)
    elif command == "STOP":
        Controller.zero_joysticks()
        Arduino.stop()
    elif command == "GAMEPAD":
        if (not isinstance(val,str)):
            return
        if Robot.controller_mode == ControllerState.DIRECT:
            return
        x,_,val = val.partition(",")
        y,_,r = val.partition(",")
        x,y,r = float(x),float(y),float(r)
        Controller.left_stick_x,Controller.left_stick_y,Controller.right_stick_x = x,y,r

if __name__ == "__main__":
    try:
        app = Flask(__name__)
        socketio = SocketIO(app, async_mode="threading")
        time.sleep(1)
        Robot.initiate(socketio)
        socketio.start_background_task(background_thread)
        socketio.run(app, host="0.0.0.0", port=5000, debug=False,allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("User interupting")
    finally:
        Robot.stop()
