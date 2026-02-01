#!/usr/bin/env python3
"""
Sortacle - Headless Detection Pipeline
Runs without GUI - perfect for SSH or production deployment
Controls servo motor based on detections
"""

import time
import argparse
import threading
import queue
import cv2
import numpy as np
from camera import Camera
from cloud_inference import run_cloud_inference, CLOUD_ENDPOINT
from recyclability import is_recyclable
from data_logger import DataLogger

# Try to import servo control (optional, fails gracefully if not on Pi)
try:
    import sys
    sys.path.append('./servo')
    from servo_move import get_kit, SERVO_CH
    SERVO_AVAILABLE = True
    print("✓ Servo control enabled")
except Exception as e:
    SERVO_AVAILABLE = False
    print(f"⚠ Servo control disabled: {e}")

class SortacleHeadless:
    def __init__(self, confidence_threshold=0.50, 
                 bin_id='bin_001', location='Brown University', 
                 enable_logging=True, db_path='sortacle_data.db',
                 enable_servo=True):
        self.confidence_threshold = confidence_threshold
        self.running = True
        self.camera = None
        self.frame_count = 0
        self.detection_count = 0
        
        # Data logging
        self.enable_logging = enable_logging
        self.bin_id = bin_id
        self.location = location
        self.logger = DataLogger(db_path) if enable_logging else None
        self.logged_count = 0
        
        # Servo control
        self.enable_servo = enable_servo and SERVO_AVAILABLE
        if self.enable_servo:
            self.servo_kit = get_kit(mock=False)
            # Initialize to recycle bin position (0 degrees)
            self.servo_kit.servo[SERVO_CH].angle = 180  # Inverted: 180 = 0°
            print("✓ Servo initialized at recycle position (0°)")
        else:
            self.servo_kit = None
            print("⚠ Servo control disabled")
    
    def move_servo(self, is_recyclable):
        """Move servo to appropriate bin"""
        if not self.enable_servo or self.servo_kit is None:
            print(f"  [SERVO] Would move to: {'RECYCLE' if is_recyclable else 'TRASH'} (disabled)")
            return
        
        try:
            if is_recyclable:
                angle = 0  # Recycle bin
                actual_angle = 180  # Inverted
            else:
                angle = 90  # Trash bin
                actual_angle = 90  # Inverted
            
            self.servo_kit.servo[SERVO_CH].angle = actual_angle
            print(f"  [SERVO] ✓ Moved to {angle}° ({'RECYCLE' if is_recyclable else 'TRASH'})")
            time.sleep(1)  # Wait for servo to move
            
            # Return to home position
            self.servo_kit.servo[SERVO_CH].angle = 180  # Back to 0°
            print(f"  [SERVO] ✓ Returned to home (0°)")
        except Exception as e:
            print(f"  [SERVO ERROR] {e}")
    
    def process_frame(self):
        """Capture and process a single frame"""
        frame = self.camera.capture_frame()
        if frame is None:
            print("[ERROR] Failed to capture frame")
            return
        
        self.frame_count += 1
        
        # Resize for inference
        ai_frame = cv2.resize(frame, (640, 640))
        
        try:
            print(f"\n[FRAME #{self.frame_count}] ================================")
            print(f"[INFERENCE] Sending to cloud ({CLOUD_ENDPOINT})...")
            
            start_time = time.time()
            detections = run_cloud_inference(ai_frame)
            inference_time = (time.time() - start_time) * 1000
            
            print(f"[INFERENCE] ✓ Complete in {inference_time:.1f}ms")
            
            # Filter by confidence
            raw_detections = detections.get("detections", [])
            filtered = [d for d in raw_detections if d["confidence"] >= self.confidence_threshold]
            
            print(f"[DETECTIONS] Found {len(filtered)} items (>= {self.confidence_threshold:.0%} confidence):")
            
            if len(filtered) == 0:
                print("  No items detected")
                return
            
            # Get highest confidence detection
            best_detection = max(filtered, key=lambda x: x['confidence'])
            label = best_detection['label']
            confidence = best_detection['confidence']
            recyclable = is_recyclable(label)
            
            print(f"\n  ▶ BEST: {label}")
            print(f"    Confidence: {confidence:.1%}")
            print(f"    Category: {'♻️  RECYCLABLE' if recyclable else '🗑️  TRASH'}")
            
            # Log to database
            if self.enable_logging and self.logger:
                try:
                    self.logger.log_disposal(
                        best_detection, 
                        bin_id=self.bin_id,
                        location=self.location
                    )
                    self.logged_count += 1
                    print(f"    Database: ✓ Logged (Total: {self.logged_count})")
                except Exception as e:
                    print(f"    Database: ✗ Error: {e}")
            
            # Move servo
            self.move_servo(recyclable)
            
            self.detection_count += 1
            
        except Exception as e:
            print(f"[INFERENCE ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        print("\n" + "="*70)
        print("Sortacle - Headless Detection Pipeline")
        print("="*70)
        print(f"Cloud endpoint: {CLOUD_ENDPOINT}")
        print(f"Confidence threshold: {self.confidence_threshold:.0%}")
        print(f"Bin ID: {self.bin_id}")
        print(f"Location: {self.location}")
        print(f"Logging: {'Enabled' if self.enable_logging else 'Disabled'}")
        print(f"Servo: {'Enabled' if self.enable_servo else 'Disabled'}")
        print("="*70)
        print("Press Ctrl+C to quit\n")
        
        self.camera = Camera()
        
        try:
            while self.running:
                self.process_frame()
                time.sleep(2)  # Wait 2 seconds between captures
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.camera.release()
            print(f"\n{'='*70}")
            print("Session Summary:")
            print(f"  Total frames: {self.frame_count}")
            print(f"  Detections: {self.detection_count}")
            print(f"  Logged to DB: {self.logged_count}")
            
            if self.enable_logging and self.logger:
                try:
                    stats = self.logger.get_stats()
                    print(f"\n📊 Database Stats:")
                    print(f"  Total disposals: {stats['total_disposals']}")
                    print(f"  Recycling rate: {stats['recycling_rate']:.1%}")
                    print(f"  Today's count: {stats['today_count']}")
                except Exception as e:
                    print(f"  Could not fetch stats: {e}")
            print("="*70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sortacle Headless Detection')
    parser.add_argument('--bin-id', type=str, default='bin_001', help='Unique bin identifier')
    parser.add_argument('--location', type=str, default='Brown University', help='Bin location')
    parser.add_argument('--no-logging', action='store_true', help='Disable data logging')
    parser.add_argument('--no-servo', action='store_true', help='Disable servo control')
    parser.add_argument('--db-path', type=str, default='sortacle_data.db', help='Database file path')
    parser.add_argument('--confidence', type=float, default=0.50, help='Confidence threshold (0-1)')
    
    args = parser.parse_args()
    
    detector = SortacleHeadless(
        confidence_threshold=args.confidence,
        bin_id=args.bin_id,
        location=args.location,
        enable_logging=not args.no_logging,
        enable_servo=not args.no_servo,
        db_path=args.db_path
    )
    detector.run()
