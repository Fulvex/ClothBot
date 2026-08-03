import base64
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

from robot import *

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")


def get_telemetry():
    return {"Robot On" : Robot.on, "Arduino Connected": Arduino.connected, "Camera Connected": Camera.connected, "Controller Mode" : Robot.controller_mode, "Controller Connected (Direct)" : Controller.connected}

def background_thread():
    """Background task to continuously process RealSense frames and push updates."""
    start_time = time.perf_counter()
    while True:
        try:
            Robot.run()
            color_b64 = Camera.color_b64
            # Emit both to the web browser
            #socketio.emit("video_frame", {"image": color_b64})
            # Handle Motor Telemetry
            socketio.emit("telemetry_update", get_telemetry())

            time.sleep(0.05)

        except Exception as e:
            print(f"Stream error: {e}")
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
    if command == "DIRECT_CONTROL":
        Robot.controller_mode = Robot.DIRECT_CONTROLLER
    elif command == "WEB_CONTROL":
        Robot.controller_mode = Robot.WEB_CONTROLLER
    elif command == "DISCONNECT":
        Robot.stop()
    elif command == "CONNECT":
        Robot.initiate()



if __name__ == "__main__":
    try:
        Robot.initiate()
        socketio.start_background_task(background_thread)
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    finally:
        Robot.stop()