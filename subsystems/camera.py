import base64

import cv2
import numpy as np
import pyrealsense2.pyrealsense2 as rs


class Camera:
    connected = False
    pipeline : rs.pipeline
    align : rs.align

    color_b64 : str = ""
    @staticmethod
    def initiate():
        # --- Configure Intel RealSense Pipeline ---
        print("Connecting Camera")
        try:
            Camera.pipeline = rs.pipeline()
            config = rs.config()

            # Enable Color and Depth streams at 640x480, 30 FPS
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

            Camera.pipeline.start(config)

            # Align depth frame to color frame
            Camera.align = rs.align(rs.stream.color)
            Camera.connected = True
            print("Camera connected! (if I was gemini I would put an emoji here)")
        except:
            print("Camera not connected")
    @staticmethod
    def read():
        if (not Camera.connected or Camera.pipeline == None or Camera.align == None):
            return
        try:
            frames = Camera.pipeline.wait_for_frames()
            aligned_frames = Camera.align.process(frames)

            color_frame = aligned_frames.get_color_frame()
            #depth_frame = aligned_frames.get_depth_frame()
            #depth_profile = depth_frame.get_profile().as_video_stream_profile()
            #intrinsics = depth_profile.get_intrinsics()

            if color_frame:
                # 1. Process RGB Frame
                color_image = np.asanyarray(color_frame.get_data())
                _, buffer_color = cv2.imencode(".jpg", color_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
                color_b64 = base64.b64encode(buffer_color).decode("utf-8")
                Camera.color_b64 = color_b64
        except:
            print("Camera Read Failed")
    @staticmethod
    def stop():
        if (not Camera.connected):
            return
        Camera.pipeline.stop()
