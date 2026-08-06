import base64
import threading
import time

import cv2
import numpy as np
import pyrealsense2.pyrealsense2 as rs
from flask_socketio import SocketIO
from pupil_apriltags import Detector
from subsystems.radio_controller import RadioController, RadioHeaders


def meters_to_inches(meters):
    return meters * 39.3700787402

class ConnectionType:
    WIFI = "WIFI"
    RADIO = "RADIO"


class Camera:
    connected = False
    pipeline : rs.pipeline
    align : rs.align

    color_b64 : str = ""

    start_time = time.perf_counter()

    FRAME_RATE_HZ = 30
    FRAME_DELAY = 1.0 / FRAME_RATE_HZ

    thread : threading.Thread

    TURN_P = 0.8
    DRIVE_P = 0.12

    MAX_TURN = 1
    MAX_DRIVE = 0.5

    MIN_TURN = 0.05
    MIN_DRIVE = 0.05

    MIN_DISTANCE = 8 #inches

    turn = 0
    drive = 0

    WIDTH = 640
    HEIGHT = 480

    tag_enabled : bool = False

    closest_id : int = -1
    closest_distance : float = 10000
    tag_visible : bool = False

    connection_type = ConnectionType.WIFI

    VISIBILITY_LOSS_DECAY = 0.75

    @staticmethod
    def initiate(socket : SocketIO | None, radio : RadioController | None):
        Camera.connected = False
        # --- Configure Intel RealSense Pipeline ---
        print("Connecting Camera")
        try:
            Camera.pipeline = rs.pipeline()
            config = rs.config()

            # Enable Color and Depth streams at 640x480, 30 FPS
            config.enable_stream(rs.stream.color, Camera.WIDTH, Camera.HEIGHT, rs.format.bgr8, Camera.FRAME_RATE_HZ)
            #config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

            Camera.pipeline.start(config)

            # Align depth frame to color frame
            Camera.align = rs.align(rs.stream.color)
            Camera.connected = True
            print("Camera connected! (if I was gemini I would put an emoji here)")
        except:
            print("Failed to connect camera")
        finally:
            time.sleep(0.5)
            if (Camera.connected):
                print("Threading started")
                Camera.thread = threading.Thread(target=Camera.socket_thread,args=(socket,radio))
                Camera.thread.start()
                Camera.start_time = time.perf_counter()
            else:
                print("Camera not connected")
    @staticmethod
    def socket_thread(socket : SocketIO | None, radio : RadioController | None):
        at_detector = Detector(families="tag36h11")
        while (Camera.connected and Camera.pipeline is not None and Camera.align is not None):
            elapsed = time.perf_counter() - Camera.start_time
            if (elapsed < Camera.FRAME_DELAY):
                time.sleep(Camera.FRAME_DELAY - elapsed)
            Camera.start_time = time.perf_counter()
            try:
                frames = Camera.pipeline.wait_for_frames()
                aligned_frames = Camera.align.process(frames)

                color_frame = aligned_frames.get_color_frame()
                #depth_frame = aligned_frames.get_depth_frame()
                #depth_profile = depth_frame.get_profile().as_video_stream_profile()
                #intrinsics = depth_profile.get_intrinsics()
                Camera.turn = Camera.turn * Camera.VISIBILITY_LOSS_DECAY
                Camera.drive = Camera.drive * Camera.VISIBILITY_LOSS_DECAY

                if (abs(Camera.turn) < Camera.MIN_TURN):
                    Camera.turn = 0
                if (abs(Camera.drive) < Camera.MIN_DRIVE):
                    Camera.drive = 0

                Camera.tag_visible = False
                Camera.closest_distance = 10000
                Camera.closest_id = -1

                if color_frame:
                    color_image = np.asanyarray(color_frame.get_data())
                    if (Camera.tag_enabled):
                        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
                        camera_params = [325.0, 325.0, 320.0, 240.0]
                        tag_size = .1651 #meters
                        tags = at_detector.detect(gray,estimate_tag_pose=True, camera_params=camera_params, tag_size=tag_size)  # pyright: ignore[reportArgumentType]

                        for tag in tags:  # pyright: ignore[reportGeneralTypeIssues]
                            Camera.tag_visible = True
                            pts = [(int(corner[0]), int(corner[1])) for corner in tag.corners]

                            # Draw the 4 lines of the hitbox (Green)
                            for i in range(4):
                                cv2.line(color_image, pts[i], pts[(i + 1) % 4], (0, 255, 0), 3)

                            # Draw center point (Red)
                            center = (int(tag.center[0]), int(tag.center[1]))
                            cv2.circle(color_image, center, 4, (0, 0, 255), -1)

                            # Put the Tag ID label above the box (Blue text)
                            cv2.putText(color_image, f"ID: {tag.tag_id}", (pts[0][0], pts[0][1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                            translation = tag.pose_t
                            if (translation is None):
                                continue
                            perpendicular_distance = translation[2][0]  # Z distance in meters
                            if (perpendicular_distance < 0 or perpendicular_distance is None):
                                continue
                            perpendicular_distance = meters_to_inches(perpendicular_distance)
                            if (perpendicular_distance < Camera.closest_distance):
                                Camera.closest_id = tag.tag_id
                                Camera.closest_distance = perpendicular_distance
                            else:
                                continue



                            Camera.turn = Camera.TURN_P * ((center[0] - Camera.WIDTH // 2) / Camera.WIDTH)
                            perpendicular_distance = max(perpendicular_distance, Camera.MIN_DISTANCE)
                            Camera.drive = Camera.DRIVE_P * perpendicular_distance / Camera.MIN_DISTANCE

                            Camera.turn = max(-Camera.MAX_TURN, min(Camera.turn, Camera.MAX_TURN))
                            Camera.drive = max(-Camera.MAX_DRIVE, min(Camera.drive, Camera.MAX_DRIVE))

                            if (tag.tag_id == 30):
                                Camera.drive = -1 / Camera.drive

                            if abs(Camera.turn) < Camera.MIN_TURN:
                                Camera.turn = 0
                            if abs(Camera.drive) < Camera.MIN_DRIVE:
                                Camera.drive = 0

                    # 4. Encode the annotated frame to JPEG and base64
                    _, buffer_color = cv2.imencode(".jpg", color_image, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    color_b64 = base64.b64encode(buffer_color).decode("utf-8")
                    Camera.color_b64 = color_b64

                    if (socket is not None):
                        socket.emit("video_frame", {"image": Camera.color_b64})
                    if (radio is not None):
                        _, buffer_color = cv2.imencode(".jpg", color_image, [cv2.IMWRITE_JPEG_QUALITY, 50])
                        radio.send(RadioHeaders.generate(RadioHeaders.CAMERA,encode = True) + buffer_color,encoded = True,print_out=False)
            except:
                print("Camera Read Failed")

        Camera.connected = False
    @staticmethod
    def stop():
        if (not Camera.connected):
            return
        Camera.thread.join()
        Camera.pipeline.stop()
