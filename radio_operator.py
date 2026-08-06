
import time

from subsystems.controller import Controller
from subsystems.radio_controller import RadioController, RadioHeaders, RadioType

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
                data = f'{RadioHeaders.generate(RadioHeaders.GAMEPAD)}{Controller.left_stick_x},{Controller.left_stick_y},{Controller.right_stick_x},{Controller.right_stick_y}'
                radio.send(data)
            else:
                radio.send(f'{RadioHeaders.generate(RadioHeaders.GAMEPAD)}0,0.2,0')
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
