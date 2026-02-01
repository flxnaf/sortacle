#!/usr/bin/env python3
"""
Sortacle Web Viewer - Stream camera feed to browser
Much faster than X11 forwarding for remote viewing
"""

import time
import argparse
import threading
import queue
from flask import Flask, Response, render_template_string
import cv2
import numpy as np
from camera import Camera
from cloud_inference import run_cloud_inference
from recyclability import is_recyclable
from data_logger import DataLogger

# Servo control imports
try:
    from servo.servo_move import get_kit, SERVO_CH
    SERVO_AVAILABLE = True
except ImportError:
    SERVO_AVAILABLE = False

# HTML template for web viewer
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sortacle Live Stream</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            margin-bottom: 10px;
            color: #78e6a0;
        }
        .info {
            margin-bottom: 20px;
            color: #aaa;
        }
        img {
            max-width: 90%;
            border: 2px solid #78e6a0;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        .controls {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .recyclable { background: #78e6a0; color: #000; }
        .trash { background: #ff6b6b; color: #fff; }
        .center { background: #888; color: #fff; }
    </style>
</head>
<body>
    <h1>🌱 Sortacle Live Stream</h1>
    <div class="info">Real-time object detection and sorting</div>
    <img src="{{ url_for('video_feed') }}" />
    <div class="controls">
        <button class="recyclable" onclick="fetch('/servo/open')">📂 Open Bins</button>
        <button class="center" onclick="fetch('/servo/close')">⏹️ Close Bins</button>
    </div>
</body>
</html>
"""

app = Flask(__name__)

class SortacleWebViewer:
    def __init__(self, confidence_threshold=0.50, 
                 bin_id='bin_001', location='Brown University',
                 enable_logging=True, db_path='sortacle_data.db',
                 enable_servo=True, mock_servo=False):
        
        self.latest_detections = []
        self.detection_lock = threading.Lock()
        self.confidence_threshold = confidence_threshold
        self.running = True
        self.camera = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.frame_counter = 0  # For skipping frames to reduce server load
        
        # Data logging
        self.enable_logging = enable_logging
        self.bin_id = bin_id
        self.location = location
        self.logger = DataLogger(db_path) if enable_logging else None
        self.last_detection_time = 0  # Timestamp of last detection
        self.cooldown_seconds = 5  # Minimum time between detections
        
        # Servo control
        self.enable_servo = enable_servo and SERVO_AVAILABLE
        self.servo_kit = None
        if self.enable_servo:
            try:
                self.servo_kit = get_kit(mock=mock_servo)
                self.servo_kit.servo[SERVO_CH].angle = 0
                time.sleep(1.0)
                print("✅ Servo initialized at center position (0°)")
            except Exception as e:
                print(f"⚠️  Failed to initialize servo: {e}")
                self.enable_servo = False
        
        # Initialize camera
        self.camera = Camera()
        print(f"✓ Camera initialized")
        
        # Start inference thread
        self.inference_thread = threading.Thread(target=self._inference_worker, daemon=True)
        self.inference_thread.start()
    
    def _inference_worker(self):
        """Background thread for cloud inference"""
        print("[INFERENCE THREAD] Started")
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)
                
                # Run cloud inference (no confidence threshold - handled server-side)
                detections = run_cloud_inference(frame)
                
                # Filter by confidence threshold locally
                if 'detections' in detections:
                    filtered = [
                        det for det in detections['detections']
                        if det.get('confidence', 0) >= self.confidence_threshold
                    ]
                    detections['detections'] = filtered
                
                # Update latest detections
                with self.detection_lock:
                    self.latest_detections = detections.get('detections', [])
                
                # Log and trigger servo if needed
                if self.latest_detections:
                    current_time = time.time()
                    
                    # Check if cooldown period has passed
                    if current_time - self.last_detection_time < self.cooldown_seconds:
                        continue
                    
                    best_detection = max(self.latest_detections, key=lambda x: x['confidence'])
                    recyclable = is_recyclable(best_detection['label'])
                    
                    # Log detection
                    if self.enable_logging and self.logger:
                        detection_dict = {
                            'label': 'recyclable' if recyclable else 'non-recyclable',
                            'confidence': best_detection['confidence'],
                            'recyclable': recyclable
                        }
                        self.logger.log_disposal(
                            detection=detection_dict,
                            bin_id=self.bin_id,
                            location=self.location
                        )
                    
                    # Trigger servo
                    if self.enable_servo:
                        self.move_servo_for_item(recyclable, best_detection['label'])
                    
                    # Update last detection time
                    self.last_detection_time = current_time
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️  Inference error: {e}")
    
    def move_servo_for_item(self, recyclable: bool, label: str):
        """Move servo based on recyclability - directs to appropriate bin"""
        if not self.enable_servo or not self.servo_kit:
            return
        
        try:
            # Direct to appropriate bin with different angles
            if recyclable:
                target_angle = 160  # Recyclable bin
                bin_type = "♻️ RECYCLABLE"
            else:
                target_angle = 80   # Trash bin
                bin_type = "🗑️ TRASH"
            
            self.servo_kit.servo[SERVO_CH].angle = target_angle
            print(f"🔄 SERVO: Opening {bin_type} bin for '{label}' ({target_angle}°)")
            
            # Wait for item to clear
            time.sleep(3.0)
            
            # Close/reset to center
            self.servo_kit.servo[SERVO_CH].angle = 0
            print(f"↩️  SERVO: Closed")
            
        except Exception as e:
            print(f"⚠️  Servo error: {e}")
    
    def draw_detections(self, frame):
        """Draw bounding boxes on frame"""
        with self.detection_lock:
            detections = self.latest_detections.copy()
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            conf = det['confidence']
            recyclable = is_recyclable(det['label'])
            
            # Simplified label: just "Recyclable" or "Non-recyclable"
            label_text = "♻️ RECYCLABLE" if recyclable else "🗑️ NON-RECYCLABLE"
            color = (120, 230, 100) if recyclable else (80, 80, 255)  # BGR: green or bright red
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            # Draw label background
            display_text = f"{label_text} {conf:.0%}"
            (text_w, text_h), _ = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (x1, y1 - text_h - 15), (x1 + text_w + 15, y1), color, -1)
            cv2.putText(frame, display_text, (x1 + 7, y1 - 7), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        return frame
    
    def get_frame(self):
        """Get latest frame with detections drawn"""
        frame = self.camera.capture_frame()
        if frame is None:
            return None
        
        # Convert RGB to BGR for OpenCV drawing
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Only send every 5th frame to cloud to reduce server load
        self.frame_counter += 1
        if self.frame_counter % 5 == 0:
            try:
                self.frame_queue.put_nowait(frame.copy())
            except queue.Full:
                pass
        
        # Draw detections
        frame = self.draw_detections(frame)
        
        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()
    
    def servo_control(self, action):
        """Manual servo control via web interface"""
        if not self.enable_servo or not self.servo_kit:
            return False
        
        try:
            if action == 'open':
                self.servo_kit.servo[SERVO_CH].angle = 90
                print("📂 WEB: Opening bins (90°)")
            elif action == 'close':
                self.servo_kit.servo[SERVO_CH].angle = 0
                print("⏹️  WEB: Closing bins (0°)")
            return True
        except Exception as e:
            print(f"⚠️  Servo control error: {e}")
            return False

# Global viewer instance
viewer = None

@app.route('/')
def index():
    """Serve web viewer page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """MJPEG stream endpoint"""
    def generate():
        while True:
            frame = viewer.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/servo/<action>')
def servo_control(action):
    """Servo control endpoint"""
    if viewer.servo_control(action):
        return {'status': 'ok'}
    return {'status': 'error'}, 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sortacle Web Viewer')
    parser.add_argument('--bin-id', type=str, default='bin_001', help='Unique bin identifier')
    parser.add_argument('--location', type=str, default='Brown University', help='Bin location')
    parser.add_argument('--no-logging', action='store_true', help='Disable data logging')
    parser.add_argument('--db-path', type=str, default='sortacle_data.db', help='Database file path')
    parser.add_argument('--no-servo', action='store_true', help='Disable servo control')
    parser.add_argument('--mock-servo', action='store_true', help='Use mock servo')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    
    args = parser.parse_args()
    
    # Initialize viewer
    viewer = SortacleWebViewer(
        bin_id=args.bin_id,
        location=args.location,
        enable_logging=not args.no_logging,
        db_path=args.db_path,
        enable_servo=not args.no_servo,
        mock_servo=args.mock_servo
    )
    
    print("\n" + "="*70)
    print("🌐 Sortacle Web Viewer")
    print("="*70)
    print(f"Open in browser: http://172.20.10.4:{args.port}")
    print("Press Ctrl+C to quit")
    print("="*70 + "\n")
    
    # Run Flask server
    app.run(host='0.0.0.0', port=args.port, threaded=True)
