import time
from tokenize import String

from flask import Flask, render_template
from flask_socketio import SocketIO
from pygame import math

from robot import *

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

TELEMETRY_UPDATE_HZ = 4
TELEMETRY_UPDATE_TIME = 1 / TELEMETRY_UPDATE_HZ

def get_telemetry():
    return {"Robot On" : Robot.on,
        "Arduino Connected": Arduino.connected,
        "Camera Connected": Camera.connected,
        "Controller Mode" : Robot.controller_mode,
        "Controller Connected (Direct)" : Controller.connected,
        "Robot State" : Robot.state
    }
def get_tag_data():
    return {
        "Detector Enabled" : Camera.tag_enabled,
        "Visible": Camera.tag_visible,
        "Closest ID": Camera.closest_id,
        "Closest Distance": str(Camera.closest_distance)[:5],
        "Turn" : str(Camera.turn)[:5],
        "Drive" : str(Camera.drive)[:5]
    }
def background_thread():
    start_time = time.perf_counter()
    while True:
        elapsed = time.perf_counter() - start_time
        try:
            socketio.emit("telemetry_update", get_telemetry())
            socketio.emit("tag_update", get_tag_data())
        except:
            print("Error in background thread")
        finally:
            if (elapsed < TELEMETRY_UPDATE_TIME):
                time.sleep(TELEMETRY_UPDATE_TIME - elapsed)
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
    Robot.state = RobotState.IDLE



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
        if (val == RobotState.AUTO):
            Camera.tag_enabled = True
        else:
            Camera.tag_enabled = False
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
        time.sleep(1)
        Robot.initiate(socketio)
        time.sleep(0.5)
        socketio.start_background_task(background_thread)
        socketio.run(app, host="0.0.0.0", port=5001, debug=False,allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("User interupting")
    finally:
        Robot.stop()
