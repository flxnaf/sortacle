#!/usr/bin/env python3
"""
Servo calibration helper.

Usage:
  python calibrate.py [--mock]

If --mock is passed (or real hardware can't be initialized), a fake ServoKit will be used
so you can run and test the script without I2C hardware.
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

    print("=== SERVO CALIBRATION ===")
    print("This will help you find the right angles")
    print("\nType angles 0-180 to test positions")
    print("Type 'q' to quit\n")

    while True:
        cmd = input("Test angle: ")

        if cmd == 'q':
            break

        try:
            angle = int(cmd)
            if 0 <= angle <= 180:
                kit.servo[SERVO_CH].angle = angle
                print(f"Servo at {angle}° (raw)")
            else:
                print("Use 0-180")
        except:
            print("Invalid")

if __name__ == "__main__":
    main()