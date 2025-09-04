import serial
import time
import pygame
import CoOrdinateBase as Arm  # your arm code

# Arduino serial setup
PORT = "/dev/ttyACM0"
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # wait for Arduino reset

# Arm position variables
x = 10
y = 0
z = 10


def set_motors(left_speed, right_speed):
    command = f"{left_speed},{right_speed}\n"
    ser.write(command.encode("utf-8"))
    print(f"Sent: {command.strip()}")


def scale_axis(val):
    """Convert joystick axis (-1.0 to 1.0) to motor speed (-100 to 100)."""
    return int(val * 100)


def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("⚠️ No controller detected.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"✅ Connected to controller: {joystick.get_name()}")

    mode = "drive"  # start in drive mode
    print(f"▶ Starting in {mode.upper()} mode")

    try:
        while True:
            pygame.event.pump()

            # Use globals for arm control
            global x, y, z

            # Mode toggle with "grenade button"
            if joystick.get_button(7):
                mode = "arm" if mode == "drive" else "drive"
                print(f"🔀 Switched to {mode.upper()} mode")
                time.sleep(0.3)  # debounce

            if mode == "drive":
                # Joystick axes for driving
                left_y = joystick.get_axis(1)
                right_y = joystick.get_axis(3)

                left_speed = -scale_axis(left_y)
                right_speed = -scale_axis(right_y)

                if abs(left_speed) < 10:
                    left_speed = 0
                if abs(right_speed) < 10:
                    right_speed = 0

                set_motors(-left_speed, -right_speed)

            elif mode == "arm":
                # Stop motors while in arm mode
                set_motors(0, 0)

                # Read joystick axes
                left_x = joystick.get_axis(0)   # left stick horizontal
                left_y = joystick.get_axis(1)   # left stick vertical
                right_y = joystick.get_axis(3)  # right stick vertical

                # Deadzone (ignore small noise)
                deadzone = 0.2
                step_size = 0.5  # how much to move per tick

                # Move X with left stick horizontal
                if abs(left_x) > deadzone:
                    x += left_x * step_size

                # Move Z with left stick vertical (inverted so up = increase z)
                if abs(left_y) > deadzone:
                    z -= left_y * step_size

                # Move Y with right stick vertical
                if abs(right_y) > deadzone:
                    y -= right_y * step_size

                # Send move command if anything changed
                Arm.move_arm_to(x, y, z)
                print(f"Arm target → X:{x:.2f}, Y:{y:.2f}, Z:{z:.2f}")


            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        set_motors(0, 0)


if __name__ == "__main__":
    main()
