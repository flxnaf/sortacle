#!/usr/bin/env python3
"""
Sortacle - Recyclable Detection Pipeline (PRO Edition)
Modern, elegant UI for demos with glassmorphism and rounded corners.
Supports variable camera resolutions and native aspect ratios.
"""

import time
import argparse
import threading
import queue
import requests
import cv2
import numpy as np
from camera import Camera
from cloud_inference import run_cloud_inference, CLOUD_ENDPOINT, test_cloud_connection
from recyclability import is_recyclable
from data_logger import DataLogger

# Servo control imports
try:
    from servo.servo_move import get_kit, SERVO_CH
    SERVO_AVAILABLE = True
except ImportError:
    print("⚠️  Servo module not available - servo control disabled")
    SERVO_AVAILABLE = False

# Color Palette (Modern/Elegant)
ACCENT_GREEN = (120, 230, 100)  # Recyclable
ACCENT_RED = (100, 100, 255)    # Trash (BGR)
ACCENT_BLUE = (255, 180, 80)    # UI Focus
TEXT_WHITE = (245, 245, 245)

def draw_rounded_rect(img, pt1, pt2, color, thickness, r, d):
    """Draw a rounded rectangle"""
    x1, y1 = pt1
    x2, y2 = pt2
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
    cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)

def draw_filled_rounded_rect(img, pt1, pt2, color, r):
    """Draw a filled rounded rectangle"""
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    x1, y1, x2, y2 = pt1[0], pt1[1], pt2[0], pt2[1]
    cv2.circle(mask, (x1 + r, y1 + r), r, 255, -1)
    cv2.circle(mask, (x2 - r, y1 + r), r, 255, -1)
    cv2.circle(mask, (x1 + r, y2 - r), r, 255, -1)
    cv2.circle(mask, (x2 - r, y2 - r), r, 255, -1)
    cv2.rectangle(mask, (x1 + r, y1), (x2 - r, y2), 255, -1)
    cv2.rectangle(mask, (x1, y1 + r), (x2, y2 - r), 255, -1)
    img[mask > 0] = color

class SortacleUIPro:
    def __init__(self, confidence_threshold=0.50, display_fps=30.0, 
                 bin_id='bin_001', location='Brown University', 
                 enable_logging=True, db_path='sortacle_data.db',
                 enable_servo=True, mock_servo=False):
        self.latest_detections = []
        self.detection_lock = threading.Lock()
        self.inference_source = "none"
        self.inference_time_ms = 0
        self.confidence_threshold = confidence_threshold
        self.display_fps = display_fps
        self.paused = False
        self.force_local = False
        self.show_settings = True
        self.running = True
        self.camera = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.frame_count = 0
        self.detection_count = 0
        
        # Data logging
        self.enable_logging = enable_logging
        self.bin_id = bin_id
        self.location = location
        self.logger = DataLogger(db_path) if enable_logging else None
        self.logged_count = 0
        self.last_logged_items = set()  # Track recently logged to avoid duplicates
        
        # Servo control
        self.enable_servo = enable_servo and SERVO_AVAILABLE
        self.servo_kit = None
        if self.enable_servo:
            try:
                self.servo_kit = get_kit(mock=mock_servo)
                # Force reset to center position (90°) on startup
                print("🔄 Resetting servo to center position...")
                self.servo_kit.servo[SERVO_CH].angle = 90
                time.sleep(1.0)  # Longer delay to ensure servo physically moves
                self.servo_kit.servo[SERVO_CH].angle = 90  # Set again for reliability
                time.sleep(0.5)
                print("✅ Servo initialized at center position (90°)")
            except Exception as e:
                print(f"⚠️  Failed to initialize servo: {e}")
                self.enable_servo = False

    def move_servo_for_item(self, recyclable: bool, current_label: str):
        """
        Smart servo control: opens bin, waits for item to drop and leave view, then closes.
        
        Args:
            recyclable: True for recyclable bin, False for trash bin
            current_label: Label of detected item (e.g., "glass bottle")
        """
        if not self.enable_servo or not self.servo_kit:
            return
        
        try:
            # 0. Reset to center position first (in case servo is already rotated)
            self.servo_kit.servo[SERVO_CH].angle = 90
            print(f"🔄 SERVO: Resetting to center (90°)")
            time.sleep(0.5)  # Brief pause to ensure reset completes
            
            # 1. Open the appropriate bin
            target_angle = 0 if recyclable else 180
            actual_angle = 180 - target_angle  # Inverted as per servo_move.py
            
            self.servo_kit.servo[SERVO_CH].angle = actual_angle
            bin_type = "♻️ RECYCLABLE" if recyclable else "🗑️ TRASH"
            print(f"🔄 SERVO: Opening {bin_type} bin (angle {target_angle}°)")
            
            # 2. Wait for item to start rolling down (allow time for gravity)
            time.sleep(2.0)
            
            # 3. Check if item has left the view (with timeout and flexibility)
            print(f"⏳ SERVO: Waiting for '{current_label}' to clear...")
            max_wait_time = 5.0  # Maximum 5 seconds wait
            check_interval = 0.3  # Check every 300ms
            waited = 0
            item_gone = False
            consecutive_clear_checks = 0
            required_clear_checks = 2  # Need 2 consecutive checks without item (flexibility)
            
            while waited < max_wait_time:
                time.sleep(check_interval)
                waited += check_interval
                
                # Check current detections
                with self.detection_lock:
                    current_detections = self.latest_detections.copy()
                
                # See if the same item type is still detected
                item_still_visible = any(
                    det['label'].lower() == current_label.lower() 
                    for det in current_detections
                )
                
                if not item_still_visible:
                    consecutive_clear_checks += 1
                    if consecutive_clear_checks >= required_clear_checks:
                        item_gone = True
                        print(f"✅ SERVO: '{current_label}' cleared from view")
                        break
                else:
                    consecutive_clear_checks = 0  # Reset if item reappears
            
            if not item_gone:
                print(f"⚠️  SERVO: Timeout waiting for item to clear (waited {waited:.1f}s)")
            
            # 4. Close the bin (return to center)
            self.servo_kit.servo[SERVO_CH].angle = 90
            print(f"↩️  SERVO: Closed - ready for next item (90°)")
            
        except Exception as e:
            print(f"⚠️  Servo movement error: {e}")
            # Emergency: return to center position
            try:
                self.servo_kit.servo[SERVO_CH].angle = 90
            except:
                pass

    def draw_glass_panel(self, frame, x1, y1, x2, y2, opacity=0.85):
        """Draw a semi-transparent 'glass' panel"""
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1: return
        sub_img = frame[y1:y2, x1:x2].copy()
        black_rect = np.zeros_like(sub_img)
        draw_filled_rounded_rect(black_rect, (0, 0), (x2-x1, y2-y1), (30, 30, 30), 15)
        res = cv2.addWeighted(sub_img, 1 - opacity, black_rect, opacity, 0)
        frame[y1:y2, x1:x2] = res
        draw_rounded_rect(frame, (x1, y1), (x2, y2), (80, 80, 80), 1, 15, 0)

    def draw_ui(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Header
        header_w = min(400, w // 2)
        self.draw_glass_panel(display_frame, 20, 20, 20 + header_w, 75, 0.7)
        cv2.putText(display_frame, "SORTACLE", (40, 55), cv2.FONT_HERSHEY_TRIPLEX, 0.9, TEXT_WHITE, 1, cv2.LINE_AA)
        cv2.putText(display_frame, "Vision AI", (240 if header_w > 300 else 200, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.45, ACCENT_BLUE, 1, cv2.LINE_AA)
        
        # Stats
        stats_w = min(450, w // 2)
        stats_x = w - stats_w - 20
        self.draw_glass_panel(display_frame, stats_x, 20, w - 20, 75, 0.6)
        inf_color = ACCENT_GREEN if self.inference_source == "cloud" else ACCENT_BLUE
        cv2.putText(display_frame, f"SOURCE: {self.inference_source.upper()}", (stats_x + 20, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.4, inf_color, 1, cv2.LINE_AA)
        cv2.putText(display_frame, f"INF: {self.inference_time_ms:.0f}ms", (stats_x + 190, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.4, TEXT_WHITE, 1, cv2.LINE_AA)
        cv2.putText(display_frame, f"FPS: {self.display_fps:.0f}", (stats_x + 330, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.4, TEXT_WHITE, 1, cv2.LINE_AA)

        # Settings Panel
        if self.show_settings:
            p_w = 220  # Narrower panel
            p_x = w - p_w - 15
            self.draw_glass_panel(display_frame, p_x, 90, w - 15, h - 15, 0.9)
            
            y = 120
            cv2.putText(display_frame, "CONFIDENCE", (p_x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1, cv2.LINE_AA)
            y += 20
            cv2.line(display_frame, (p_x + 15, y), (p_x + 195, y), (80, 80, 80), 2)
            s_pos = int(p_x + 15 + 180 * self.confidence_threshold)
            cv2.circle(display_frame, (s_pos, y), 6, ACCENT_BLUE, -1)
            cv2.putText(display_frame, f"{self.confidence_threshold:.0%}", (p_x + 170, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, TEXT_WHITE, 1)
            
            y += 40
            btn_h = 30
            p_color = (60, 150, 60) if self.paused else (60, 60, 150)
            draw_filled_rounded_rect(display_frame, (p_x + 15, y), (p_x + 195, y + btn_h), p_color, 6)
            label = "RESUME" if self.paused else "PAUSE"
            cv2.putText(display_frame, label, (p_x + 75, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, TEXT_WHITE, 1, cv2.LINE_AA)
            
            y += 45
            l_color = (150, 100, 30) if self.force_local else (60, 60, 60)
            draw_filled_rounded_rect(display_frame, (p_x + 15, y), (p_x + 195, y + btn_h), l_color, 6)
            cv2.putText(display_frame, "LOCAL AI", (p_x + 65, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, TEXT_WHITE, 1, cv2.LINE_AA)
            
            y = h - 75
            cv2.putText(display_frame, f"Frames: {self.frame_count}", (p_x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)
            cv2.putText(display_frame, f"Detections: {self.detection_count}", (p_x + 15, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)
            if self.enable_logging:
                cv2.putText(display_frame, f"Logged: {self.logged_count}", (p_x + 15, y + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.35, ACCENT_GREEN, 1)
        else:
            cv2.putText(display_frame, "Press 'S' for Settings", (w - 180, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1, cv2.LINE_AA)

        # Detections
        with self.detection_lock:
            detections = self.latest_detections.copy()
        
        if len(detections) > 0:
            print(f"[UI] Drawing {len(detections)} detections on frame")
            
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            x1 = int(x1 * w / 640)
            x2 = int(x2 * w / 640)
            y1 = int(y1 * h / 640)
            y2 = int(y2 * h / 640)
            
            print(f"[UI] Drawing box: ({x1},{y1}) to ({x2},{y2}) for '{d['label']}'")
            
            rec = is_recyclable(d["label"])
            color = ACCENT_GREEN if rec else ACCENT_RED
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
            
            lbl = f"{'RECYCLE' if rec else 'TRASH'} | {d['label'].upper()}"
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            tag_y1 = max(0, y1 - 25)
            draw_filled_rounded_rect(display_frame, (x1, tag_y1), (x1 + tw + 20, tag_y1 + 25), color, 5)
            cv2.putText(display_frame, lbl, (x1 + 10, tag_y1 + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)

        return display_frame

    def mouse_callback(self, event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN: return
        try:
            _, _, w, h = cv2.getWindowImageRect("Sortacle - Vision AI Pro")
        except: return
        
        p_w, p_x = 280, w - 280 - 20
        if self.show_settings:
            if p_x + 20 <= x <= p_x + 240 and 150 <= y <= 170:
                self.confidence_threshold = max(0.1, min(0.99, (x - (p_x + 20)) / 220))
            elif p_x + 20 <= x <= p_x + 240 and 210 <= y <= 245:
                self.paused = not self.paused
            elif p_x + 20 <= x <= p_x + 240 and 265 <= y <= 300:
                self.force_local = not self.force_local
            elif x < p_x:
                self.show_settings = False

    def inference_thread(self):
        print("\n[INFERENCE THREAD] Started")
        inference_count = 0
        while self.running:
            if self.paused:
                time.sleep(0.1); continue
            try:
                frame = None
                while not self.frame_queue.empty(): frame = self.frame_queue.get_nowait()
                if frame is None:
                    time.sleep(0.1); continue
                
                inference_count += 1
                print(f"\n[INFERENCE #{inference_count}] ========================================")
                print(f"[INFERENCE] Frame shape: {frame.shape}")
                
                ai_frame = cv2.resize(frame, (640, 640))
                print(f"[INFERENCE] Resized to: {ai_frame.shape}")
                print(f"[INFERENCE] Confidence threshold: {self.confidence_threshold:.1%}")
                
                try:
                    print(f"[INFERENCE] Attempting CLOUD inference...")
                    detections = run_cloud_inference(ai_frame)
                    source = "cloud"
                    print(f"[INFERENCE] Cloud inference succeeded")
                except Exception as e:
                    print(f"[INFERENCE] Cloud inference failed: {e}")
                    print(f"[INFERENCE] Skipping this frame (no local fallback)")
                    time.sleep(1)
                    continue
                
                raw_detections = detections.get("detections", [])
                print(f"[INFERENCE] Raw detections: {len(raw_detections)}")
                
                for i, d in enumerate(raw_detections):
                    print(f"  [{i+1}] {d['label']}: {d['confidence']:.1%} @ {d['bbox']}")
                
                filtered = [d for d in raw_detections if d["confidence"] >= self.confidence_threshold]
                print(f"[INFERENCE] After filtering (>= {self.confidence_threshold:.1%}): {len(filtered)}")
                
                for i, d in enumerate(filtered):
                    print(f"  ✓ [{i+1}] {d['label']}: {d['confidence']:.1%}")
                
                # Log high-confidence detections to database
                if self.enable_logging and self.logger and len(filtered) > 0:
                    # Log the highest confidence detection (the one that would trigger bin opening)
                    best_detection = max(filtered, key=lambda x: x['confidence'])
                    
                    # Avoid logging duplicate items within 5 seconds
                    item_key = f"{best_detection['label']}_{int(time.time() / 5)}"
                    if item_key not in self.last_logged_items:
                        try:
                            recyclable = is_recyclable(best_detection['label'])
                            
                            self.logger.log_disposal(
                                best_detection, 
                                bin_id=self.bin_id,
                                location=self.location
                            )
                            self.logged_count += 1
                            self.last_logged_items.add(item_key)
                            
                            # Keep only recent items in memory (last 10)
                            if len(self.last_logged_items) > 10:
                                self.last_logged_items.pop()
                            
                            recycle_icon = "♻️" if recyclable else "🗑️"
                            print(f"📊 LOGGED: {best_detection['label']} ({best_detection.get('category', 'other')}) [{best_detection['confidence']:.0%}] - Recyclable: {recyclable} [ID: {self.logged_count}]")
                            print(f"[DATA] Logged to database (Total logged: {self.logged_count})")
                            
                            # Move servo to appropriate bin with smart waiting
                            self.move_servo_for_item(recyclable, best_detection['label'])
                            
                        except Exception as e:
                            print(f"[DATA ERROR] Failed to log: {e}")
                
                with self.detection_lock:
                    self.latest_detections = filtered
                    self.inference_source = source
                    self.inference_time_ms = detections.get("inference_time_ms", 0)
                
                self.detection_count += len(filtered)
                print(f"[INFERENCE] Inference time: {self.inference_time_ms:.1f}ms")
                print(f"[INFERENCE] Total detections so far: {self.detection_count}")
                
                time.sleep(0.4)
            except Exception as e:
                print(f"[INFERENCE ERROR] {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

    def run(self):
        print("\n" + "="*70)
        print("Sortacle - Vision AI Pro")
        print("="*70)
        print("Press 'Q' or click red X to quit")
        print("Press 'S' to toggle settings | SPACE to pause")
        print("="*70 + "\n")
        
        self.camera = Camera()
        inf_thread = threading.Thread(target=self.inference_thread, daemon=True)
        inf_thread.start()
        
        win_name = "Sortacle - Vision AI Pro"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(win_name, 960, 640)  # Better size for X11 forwarding
        cv2.setMouseCallback(win_name, self.mouse_callback)
        
        try:
            while self.running:
                start = time.time()
                frame = self.camera.capture_frame()
                if frame is None: continue
                
                self.frame_count += 1
                if not self.paused and not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                
                display = self.draw_ui(frame)
                cv2.imshow(win_name, display)
                
                key = cv2.waitKey(1) & 0xFF
                
                # Check if window was closed (red X button)
                try:
                    if cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1:
                        print("\nWindow closed by user")
                        break
                except:
                    break
                
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord(' '): self.paused = not self.paused
                elif key == ord('s'): self.show_settings = not self.show_settings
                
                elapsed = time.time() - start
                time.sleep(max(0, (1.0/self.display_fps) - elapsed))
        finally:
            self.running = False
            self.camera.release()
            cv2.destroyAllWindows()
            print(f"\nSession Summary:")
            print(f"  Total frames: {self.frame_count}")
            print(f"  Detections: {self.detection_count}")
            print(f"  Logged to DB: {self.logged_count}")
            
            # Print final stats if logging enabled
            if self.enable_logging and self.logger:
                try:
                    stats = self.logger.get_stats()
                    print(f"\n📊 Database Stats:")
                    print(f"  Total disposals: {stats['total_disposals']}")
                    print(f"  Recycling rate: {stats['recycling_rate']:.1%}")
                    print(f"  Today's count: {stats['today_count']}")
                except Exception as e:
                    print(f"  Could not fetch stats: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Sortacle Vision AI Pro')
    parser.add_argument('--bin-id', type=str, default='bin_001', help='Unique bin identifier')
    parser.add_argument('--location', type=str, default='Brown University', help='Bin location')
    parser.add_argument('--no-logging', action='store_true', help='Disable data logging')
    parser.add_argument('--db-path', type=str, default='sortacle_data.db', help='Database file path')
    parser.add_argument('--no-servo', action='store_true', help='Disable servo control')
    parser.add_argument('--mock-servo', action='store_true', help='Use mock servo (testing without hardware)')
    
    args = parser.parse_args()
    
    ui = SortacleUIPro(
        bin_id=args.bin_id,
        location=args.location,
        enable_logging=not args.no_logging,
        db_path=args.db_path,
        enable_servo=not args.no_servo,
        mock_servo=args.mock_servo
    )
    ui.run()
