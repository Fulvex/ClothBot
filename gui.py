import base64
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import numpy as np
import pyrealsense2 as rs

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

# --- Configure Intel RealSense Pipeline ---
pipeline = rs.pipeline()
config = rs.config()

# Enable Color and Depth streams at 640x480, 30 FPS
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

pipeline.start(config)

# Align depth frame to color frame
align = rs.align(rs.stream.color)


def get_motor_telemetry():
    return {"speed": 45.2, "current": 1.2}


def generate_2d_map(depth_image, intrinsics):
    """Generates a simple 2D top-down map (occupancy grid style) from depth data."""
    # Create a blank black image for the map (400x400 pixels representing a top-down view)
    map_size = 400
    occupancy_map = np.zeros((map_size, map_size, 3), dtype=np.uint8)

    # Downsample depth image for performance on the Jetson Nano
    h, w = depth_image.shape
    step = 4  # Skip pixels to speed up processing

    for y in range(0, h, step):
        for x in range(0, w, step):
            distance = depth_image[y, x] * 0.001  # Convert millimeters to meters

            # Filter out invalid or out-of-range points (e.g., closer than 0.3m, further than 3.0m)
            if 0.3 < distance < 3.0:
                # Simple projection math to map 3D camera coordinates to a 2D top-down grid
                # Assuming camera points forward along the Z axis, X is left/right
                # Center of the map is the robot's position
                scaled_x = int(map_size / 2 + (x - w / 2) * distance * 50 / (w / 2))
                scaled_y = int(map_size - (distance * 100))  # Distance forward maps upward

                if 0 <= scaled_x < map_size and 0 <= scaled_y < map_size:
                    # Paint obstacle white/red on the map grid
                    cv2.circle(occupancy_map, (scaled_x, scaled_y), 1, (0, 0, 255), -1)

    # Draw a marker representing the robot at the bottom center of the map
    cv2.circle(occupancy_map, (int(map_size / 2), map_size - 20), 5, (0, 255, 0), -1)
    
    return occupancy_map


def background_thread():
    """Background task to continuously process RealSense frames and push updates."""
    while True:
        try:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
            depth_profile = depth_frame.get_profile().as_video_stream_profile()
            intrinsics = depth_profile.get_intrinsics()

            if color_frame and depth_frame:
                # 1. Process RGB Frame
                color_image = np.asanyarray(color_frame.get_data())
                _, buffer_color = cv2.imencode(".jpg", color_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
                color_b64 = base64.b64encode(buffer_color).decode("utf-8")

                # 2. Process 2D Map Frame
                depth_image = np.asanyarray(depth_frame.get_data())
                map_image = generate_2d_map(depth_image, intrinsics)
                _, buffer_map = cv2.imencode(".jpg", map_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
                map_b64 = base64.b64encode(buffer_map).decode("utf-8")

                # Emit both to the web browser
                socketio.emit("video_frame", {"image": color_b64, "map": map_b64})

            # Handle Motor Telemetry
            motor_data = get_motor_telemetry()
            socketio.emit("motor_update", motor_data)

            time.sleep(0.05)

        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(0.1)


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    print("Client connected to dashboard!")


@socketio.on("robot_command")
def handle_robot_command(data):
    print(f"Received command from laptop: {data}")


if __name__ == "__main__":
    try:
        socketio.start_background_task(background_thread)
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    finally:
        pipeline.stop()