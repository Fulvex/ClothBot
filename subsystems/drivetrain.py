from subsystems.hardware import *


class Drivetrain:
    front_left : Motor
    front_right : Motor
    back_left : Motor
    back_right : Motor
    @staticmethod
    def initiate():
        Drivetrain.front_left = Motor(Device.FrontLeftDrive)
        Drivetrain.front_right = Motor(Device.FrontRightDrive)
        Drivetrain.back_right = Motor(Device.BackRightDrive)
        Drivetrain.back_left = Motor(Device.BackLeftDrive)
    @staticmethod
    def run(x,y,r):
        if (not Arduino.connected):
            return
        # --- X-Drive Kinematics ---
        fl_power = -(y + x + r)
        fr_power = -(y - x - r)
        bl_power =   y - x + r
        br_power =   y + x - r

        # --- Power Normalization ---
        max_mag = max(abs(fl_power), abs(fr_power), abs(bl_power), abs(br_power), 1.0)
        fl_power /= max_mag
        fr_power /= max_mag
        bl_power /= max_mag
        br_power /= max_mag

        # --- Send Motor Commands ---
        Drivetrain.front_left.run(fl_power)
        Drivetrain.front_right.run(fr_power)
        Drivetrain.back_left.run(bl_power)
        Drivetrain.back_right.run(br_power)
    @staticmethod
    def stop():
        Drivetrain.front_left.stop()
        Drivetrain.front_right.stop()
        Drivetrain.back_right.stop()
        Drivetrain.back_left.stop()
