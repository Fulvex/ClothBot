import re
import threading
import time

import cv2
import serial


from subsystems.controller import Controller


class RadioHeaders:
    GAMEPAD = 'GAMEPAD'
    CAMERA = 'CAMERA'
    MESSAGE = 'MESSAGE'
    SEPERATOR = ':'
    @staticmethod
    def generate(type,encode = False):
        if not encode:
            return f"{type}{RadioHeaders.SEPERATOR}"
        else:
            return f"{type}{RadioHeaders.SEPERATOR}".encode('utf-8')

class RadioType:
    DRONE = 'DRONE'
    OPERATOR = 'OPERATOR'

class RadioController:
    PORT = '/dev/radio'
    BAUD_RATE = 57600
    connected = False
    thread: threading.Thread
    name = RadioType.DRONE

    FREQUENCY : float = 30
    DELAY : float = 1 / FREQUENCY

    start_time = time.perf_counter()

    x = 0.0
    y = 0.0
    r = 0.0

    def __init__(self,name):
        self.name = name
        print(f"Connecting to radio... {name}")
        self.connected = False
        try:
            self.serial = serial.Serial(RadioController.PORT, RadioController.BAUD_RATE)
            self.connected = True
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            self.serial = None
        time.sleep(0.5)
        if self.connected:
            print(f"Radio {name} connected")
            self.start_time = time.perf_counter()
            self.thread = threading.Thread(target=self._read_loop)
            self.thread.start()

    def send(self, data, encoded = False,print_out = True):
        if (not self.connected):
            return
        try:
            if (not encoded):
                data = (data + "\n").encode('utf-8')
            self.serial.write(data)
            if print_out:
                print(f"Sent: {data}")
        except Exception as e:
            print(f"Failed to send data: {e}")


    def _read_loop(self):
        while self.connected:
            if (not self.connected):
                return
            lines = ''
            try:
                lines = self.serial.read_all().decode('utf-8', errors='ignore').strip()
            except:
                print(f"{self.name}: read failed")
                continue
            lines = re.split(r'(\n)',lines)
            header = None
            values = None
            for line in (lines):
                if len(line) < 8:
                    continue
                try:
                    header,values = line.split(RadioHeaders.SEPERATOR)
                except:
                    continue
                if (header is None or values is None):
                    continue
                if (header == RadioHeaders.GAMEPAD and self.name == RadioType.DRONE):
                    values = values.split(',')
                    if len(values) != 3:
                        continue
                    if (not all([v.replace('.', '', 1).isdigit() for v in values])):
                        continue
                    self.x = float(values[0])
                    self.y = float(values[1])
                    self.r = float(values[2])
                    continue
                elif (header == RadioHeaders.CAMERA and self.name == RadioType.OPERATOR):
                    if (len(values) < 100):
                        continue
                    cv2.imshow("Camera", values)
                else:
                    continue
                print(f"Received {header}: {values}")
            elapsed_time = time.perf_counter() - self.start_time
            if elapsed_time < RadioController.DELAY:
                time.sleep(RadioController.DELAY - elapsed_time)
            self.start_time = time.perf_counter()


    def close(self):
        print(f"Closing {self.name} radio...")
        if self.connected:
            self.connected = False
            self.thread.join()
            self.serial.close()
            print("Radio disconnected")
