import threading
import time

import serial

from subsystems.controller import Controller


class RadioHeaders:
    GAMEPAD = 'G:'
    CAMERA = 'C:'
    MESSAGE = 'M:'
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

    def send(self, data, encrypted = False):
        if (not self.connected):
            return
        try:
            if (not encrypted):
                data = (data + "\n").encode('utf-8')
            self.serial.write(data)
            print(f"Sent: {data}")
        except Exception as e:
            print(f"Failed to send data: {e}")

    def read(self,decoded = False):
        if (not self.connected):
            return
        try:
            raw_data = self.serial.readline()
            if (not decoded):
                raw_data = raw_data.decode('utf-8').strip()
            print(f'Received: {raw_data}')
            return raw_data
        except Exception as e:
            print(f"Failed to read data: {e}")
            return None

    def _read_loop(self):
        while self.connected:
            data = self.serial.read()
            if (len(data) > 7):
                try:
                    header = data.split(':')[0]
                    if (header == RadioHeaders.GAMEPAD):
                        print(f"Received gamepad data: {data}")
                    elif (header == RadioHeaders.CAMERA):
                        print(f"Received camera data: {data}")
                    elif (header == RadioHeaders.MESSAGE):
                        print(f"Received message data: {data}")
                except:
                    header = None
            if (data is not None):
                print(f"Received: {data}")
            elapsed_time = time.perf_counter() - self.start_time
            if elapsed_time < RadioController.DELAY:
                time.sleep(RadioController.DELAY - elapsed_time)
            self.start_time = time.perf_counter()


    def close(self):
        print("Closing radio...")
        if self.connected:
            self.connected = False
            self.thread.join()
            self.serial.close()
            print("Radio disconnected")


SEND_FREQUENCY : float = 15
SEND_DELAY : float = 1 / SEND_FREQUENCY

start_time = time.perf_counter()

#python3 -m subsystems.radio_controller
if __name__ == "__main__":
    radio = RadioController(RadioType.OPERATOR)
    Controller.connect()
    time.sleep(1)
    try:
        while True:
            Controller.run()
            if Controller.connected:
                data = f'{RadioHeaders.GAMEPAD}{Controller.left_stick_x},{Controller.left_stick_y},{Controller.right_stick_x},{Controller.right_stick_y}'
                radio.send(data)
            else:
                radio.send(f'{RadioHeaders.GAMEPAD}0,0,0,0')
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time < SEND_DELAY:
                time.sleep(SEND_DELAY - elapsed_time)
            start_time = time.perf_counter()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if Controller.connected:
            Controller.disconnect()
        radio.close()
