import time
import pygame
from hardware import Arduino, Motor, Device

# ==========================================
# CONFIGURATION & MAPPINGS
# ==========================================
COM_PORT = '/dev/ttyACM0'  # Target port for Jetson Nano
DEADZONE = 0.12          # Filters out stick drift below 12% deflection
LOOP_HZ = 50             # Control loop update rate (50 Hz = 20ms)
LOOP_DELAY = 1.0 / LOOP_HZ

# PS5 DualSense Axis Mappings
AXIS_LEFT_STICK_X = 0    # Strafe Left / Right
AXIS_LEFT_STICK_Y = 1    # Forward / Backward
AXIS_RIGHT_STICK_X = 2   # Rotation (CW / CCW)


def apply_deadzone(value: float, threshold: float = DEADZONE) -> float:
    """Zeroes out minor joystick drift around center."""
    if abs(value) < threshold:
        return 0.0
    return value


def main():
    # 1. Connect to Arduino First
    print(f"🔌 Connecting to Arduino on {COM_PORT}...")
    Arduino.connect_arduino(COM_PORT)

    if not Arduino.connected:
        print(f"❌ Error: Failed to open serial connection on {COM_PORT}.")
        return

    # Teleop script has started -> Pin 27 goes SOLID ON
    Arduino.set_led(Device.LedStartup, 1)

    # 2. Initialize Controller Subsystem & Wait for PS5 Connection
    pygame.init()
    pygame.joystick.init()

    print("🔍 Searching for controller... Please plug in or pair your PS5 controller.")
    
    while pygame.joystick.get_count() == 0:
        time.sleep(0.5)
        pygame.joystick.quit()
        pygame.joystick.init()

    controller = pygame.joystick.Joystick(0)
    controller.init()
    print(f"🎮 Connected Controller: {controller.get_name()}")

    # Controller Connected -> Pin 28 goes SOLID ON
    Arduino.set_led(Device.LedBT, 1)

    # 3. Instantiate Motors
    front_left  = Motor(Device.FrontLeftDrive)
    front_right = Motor(Device.FrontRightDrive)
    back_left   = Motor(Device.BackLeftDrive)
    back_right  = Motor(Device.BackRightDrive)

    # Robot Ready to Drive Sequence:
    # Pin 27 turns OFF, Pin 26 turns SOLID ON
    time.sleep(0.2)
    Arduino.set_led(Device.LedStartup, 0)
    Arduino.set_led(Device.LedReady, 1)

    print("\n🚀 Robot Teleop Active & Ready to Drive!")
    print(" - Left Stick Up/Down    : Forward / Reverse")
    print(" - Left Stick Left/Right  : Strafe Left / Right")
    print(" - Right Stick Left/Right : Rotate")
    print(" - Press Ctrl+C in terminal to stop\n")

    try:
        while True:
            # Poll Pygame event queue
            pygame.event.pump()

            # --- Read Controller Inputs ---
            x = apply_deadzone(controller.get_axis(AXIS_LEFT_STICK_X))
            y = apply_deadzone(-controller.get_axis(AXIS_LEFT_STICK_Y))
            r = apply_deadzone(controller.get_axis(AXIS_RIGHT_STICK_X))

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
            front_left.run(fl_power)
            front_right.run(fr_power)
            back_left.run(bl_power)
            back_right.run(br_power)

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user. Shutting down...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        print("🛑 Stopping all motors...")
        try:
            front_left.stop()
            front_right.stop()
            back_left.stop()
            back_right.stop()
            Arduino.stop()
            time.sleep(0.1)
            Arduino.close()
        except Exception:
            pass
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()