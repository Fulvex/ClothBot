import time

import serial
import serial.tools.list_ports


class Device:
    Stop = -1
    Ping = 0
    FrontLeftDrive = 1
    FrontRightDrive = 2
    BackRightDrive = 3
    BackLeftDrive = 4
    Shoulder = 5
    Elbow = 6
    ClawDiffyRight = 7
    ClawDiffyLeft = 8
    Gripper = 9


class Arduino:
    TIMEOUT = 0.1
    serial = None
    connected = False

    @staticmethod
    def connect_arduino(port='/dev/ttyACM0'):
        """Connects to the specified serial port (e.g. '/dev/ttyACM0' or 'COM12')."""
        Arduino.connected = False

        ports_to_try = [port]
        system_ports = [p.device for p in serial.tools.list_ports.comports()]
        ports_to_try.extend(system_ports)
        ports_to_try.extend(['/dev/ttyACM0', 'COM12'])

        seen = set()
        deduped_ports = [p for p in ports_to_try if not (p in seen or seen.add(p))]

        for p in deduped_ports:
            try:
                print(f"Connecting to Arduino on {p}...")
                Arduino.serial = serial.Serial(p, 115200, timeout=Arduino.TIMEOUT)
                time.sleep(1.5)  # Wait for Arduino auto-reset on serial connection
                Arduino.connected = True
                print(f"✅ Successfully connected to Arduino on {p}")
                return
            finally:
                if (Arduino.connected):
                    Arduino.ping()
                else:
                    print("❌ Could not connect to Arduino on any port.")
    @staticmethod
    def ping():
        print("Pinging...")
        Arduino.send_command(f'{Device.Ping},0')
    @staticmethod
    def send_command(command, read=False, override=False):
        if not Arduino.connected and not override:
            return
        if not isinstance(Arduino.serial,serial.Serial):
            return
        encoded_command = (command + "\n").encode('utf-8')
        Arduino.serial.write(encoded_command)

        if read:
            raw_data = Arduino.serial.readline()
            return raw_data.decode('utf-8').strip()

    @staticmethod
    def set_led(device_id, state):
        """State: 0 = Off, 1 = On, 2 = Blink (for startup LED)"""
        Arduino.send_command(f"{device_id},{state}")

    @staticmethod
    def close():
        if Arduino.serial and Arduino.serial.is_open:
            Arduino.serial.close()
        Arduino.connected = False

    @staticmethod
    def stop():
        Arduino.send_command(f"{Device.Stop},0")


class Motor:
    MAX_POWER = 255

    def __init__(self, id):
        self.id = id

    def run(self, power):
        """Power is -1.0 to 1.0, scaled to -255 to 255."""
        power = max(-1.0, min(1.0, power))  # Clamp within bounds
        power_val = round(power * Motor.MAX_POWER)
        cmd = f'{self.id},{power_val}'
        Arduino.send_command(cmd)

    def stop(self):
        cmd = f'{self.id},0'
        Arduino.send_command(cmd)
