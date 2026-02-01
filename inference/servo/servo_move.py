#!/usr/bin/env python3
"""
Interactive servo mover.

Usage:
  python servo_move.py [--mock]
"""
import time
import argparse

SERVO_CH = 0

class MockServo:
    def __init__(self):
        self.angle = None

class MockKit:
    def __init__(self, channels=16):
        self.servo = [MockServo() for _ in range(channels)]

def get_kit(mock=False):
    if mock:
        return MockKit(16)
    try:
        from adafruit_servokit import ServoKit
        return ServoKit(channels=16)
    except Exception as e:
        print(f"Warning: could not initialize real ServoKit ({e}). Falling back to mock mode.")
        return MockKit(16)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Force mock mode (no hardware)")
    args = parser.parse_args()

    kit = get_kit(mock=args.mock)

    # Automatically move to 0 on startup (or simulate)
    kit.servo[SERVO_CH].angle = 180  # This is your "0"
    time.sleep(1)  # Give it a second to get there

    print("Servo ready at 0°. Type angle (0-180) or 'q' to quit")

    while True:
        cmd = input("\nCommand: ")

        if cmd == 'q':
            break

        try:
            angle = int(cmd)
            if 0 <= angle <= 180:
                # INVERTED: flip the angle
                actual_angle = 180 - angle
                kit.servo[SERVO_CH].angle = actual_angle
                print(f"Moved to {angle}°")
            else:
                print("Use 0-180")
        except:
            print("Invalid")

if __name__ == "__main__":
    main()