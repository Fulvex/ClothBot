import serial
import serial.tools.list_ports
import time

class Device:
    Stop = -1
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
    def connect_arduino(port='COM12'):
        """Connects to the specified serial port (e.g. 'COM12' or '/dev/ttyACM0')."""
        Arduino.connected = False
        
        # Build candidate ports list, starting with the requested port
        ports_to_try = [port]
        
        # Auto-detect other active system ports as fallback
        system_ports = [p.device for p in serial.tools.list_ports.comports()]
        ports_to_try.extend(system_ports)
        ports_to_try.extend(['/dev/ttyACM0', 'COM12'])

        # Remove duplicate entries while maintaining priority order
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
            except Exception:
                continue

        print("❌ Could not connect to Arduino on any port.")

    @staticmethod
    def send_command(command, read=False, override=False):
        if not Arduino.connected and not override:
            print("Arduino not connected")
            return
        
        encoded_command = (command + "\n").encode('utf-8')
        Arduino.serial.write(encoded_command)
        
        if read:
            raw_data = Arduino.serial.readline()
            return raw_data.decode('utf-8').strip()

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


class Stepper:
    pass