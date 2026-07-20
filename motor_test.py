import time
from hardware import *
time.sleep(1)
Arduino.connect_arduino()
time.sleep(1)
front_left = Motor(Device.FrontLeftDrive)
front_right = Motor(Device.FrontRightDrive)
back_left = Motor(Device.BackLeftDrive)
back_right = Motor(Device.BackRightDrive)

time.sleep(1)
front_left.run(0.5)
time.sleep(0.5)
front_left.stop()

time.sleep(1)
front_right.run(0.5)
time.sleep(0.5)
front_right.stop()

time.sleep(1)
back_right.run(0.5)
time.sleep(0.5)
back_right.stop()

time.sleep(1)
back_left.run(0.5)
time.sleep(0.5)
back_left.stop()

Arduino.stop()
time.sleep(0.5)
Arduino.close()


