import time
from hardware import *
from drivetrain import Drivetrain
time.sleep(1)
Arduino.connect_arduino()
time.sleep(1)
Drivetrain.initiate()

time.sleep(1)
Drivetrain.run(0,1,0)
time.sleep(1)
Drivetrain.stop()

time.sleep(1)
Drivetrain.run(1,0,0)
time.sleep(1)
Drivetrain.stop()

time.sleep(1)
Drivetrain.run(0,0,1)
time.sleep(1)
Drivetrain.stop()

Arduino.stop()
time.sleep(0.5)
Arduino.close()


