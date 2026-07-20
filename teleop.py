import time
import pygame
from hardware import Arduino, Motor, Device

# ==========================================
# CONFIGURATION & MAPPINGS
# ==========================================
COM_PORT = 'COM12'       # Target COM port for your laptop
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
    # 1. Initialize Controller Subsystem
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("❌ Error: No PS5 controller detected!")
        print("Please connect your controller via USB-C or Bluetooth and try again.")
        return

    controller = pygame.joystick.Joystick(0)
    controller.init()
    print(f"🎮 Connected Controller: {controller.get_name()}")

    # 2. Connect to Arduino
    print(f"🔌 Connecting to Arduino on {COM_PORT}...")
    Arduino.connect_arduino(COM_PORT)

    if not Arduino.connected:
        print(f"❌ Error: Failed to open serial connection on {COM_PORT}.")
        print("Check if the Serial Monitor in the Arduino IDE is open and close it.")
        return

    # 3. Instantiate Motors
    front_left  = Motor(Device.FrontLeftDrive)
    front_right = Motor(Device.FrontRightDrive)
    back_left   = Motor(Device.BackLeftDrive)
    back_right  = Motor(Device.BackRightDrive)

    print("\n🚀 Laptop Teleop Active!")
    print(" - Left Stick Up/Down    : Forward / Reverse")
    print(" - Left Stick Left/Right  : Strafe Left / Right")
    print(" - Right Stick Left/Right : Rotate")
    print(" - Press Ctrl+C in terminal to stop\n")

    try:
        while True:
            # Poll Pygame event queue
            pygame.event.pump()

            # --- Read Controller Inputs ---
            # Pygame Y-axis is inverted by default (Up = -1.0), so we negate it.
            x = apply_deadzone(controller.get_axis(AXIS_LEFT_STICK_X))
            y = apply_deadzone(-controller.get_axis(AXIS_LEFT_STICK_Y))
            r = apply_deadzone(controller.get_axis(AXIS_RIGHT_STICK_X))

            # --- X-Drive Kinematics (Front Motors Inverted) ---
            fl_power = -(y + x + r)  # Negated for front hardware mounting
            fr_power = -(y - x - r)  # Negated for front hardware mounting
            bl_power =   y - x + r
            br_power =   y + x - r

            # --- Power Normalization ---
            # Keeps power proportional if total magnitude exceeds 1.0 (100%)
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
        # Safety Shutdown Sequence
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