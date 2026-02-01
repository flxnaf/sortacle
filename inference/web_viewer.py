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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sortacle Live | AI Controller</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --primary: #10b981;
            --primary-hover: #059669;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            background: var(--bg); 
            color: var(--text);
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 { 
            margin: 0; 
            font-size: 2.2rem;
            background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }
        .header p { color: var(--text-muted); margin-top: 8px; font-size: 0.95rem; }
        
        .container {
            background: var(--card);
            padding: 24px;
            border-radius: 24px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.05);
            max-width: 800px;
            width: 100%;
        }
        .video-wrapper {
            position: relative;
            border-radius: 16px;
            overflow: hidden;
            background: #000;
            line-height: 0;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .video-feed { 
            width: 100%;
            height: auto;
        }
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 24px;
        }
        button {
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            border-radius: 12px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .btn-open {
            background: var(--primary);
            color: white;
        }
        .btn-open:hover { 
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }
        .btn-close {
            background: #475569;
            color: white;
        }
        .btn-close:hover { 
            background: #334155;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .status-badge {
            position: absolute;
            top: 16px;
            left: 16px;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(8px);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
            z-index: 10;
        }
        .dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.5; }
            100% { transform: scale(0.95); opacity: 1; }
        }
        footer {
            margin-top: auto;
            padding: 30px 20px;
            color: var(--text-muted);
            font-size: 14px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 Sortacle Live</h1>
        <p>Real-time AI Vision & Robotics Controller</p>
    </div>

    <div class="container">
        <div class="video-wrapper">
            <div class="status-badge">
                <div class="dot"></div>
                LIVE FEED
            </div>
            <img class="video-feed" src="{{ url_for('video_feed') }}" alt="Live Feed">
        </div>
        
        <div class="controls">
            <button class="btn-open" onclick="fetch('/servo/open')">
                <span>📂</span> Open Bins
            </button>
            <button class="btn-close" onclick="fetch('/servo/close')">
                <span>⏹️</span> Close Bins
            </button>
        </div>
    </div>

    <footer>
        &copy; 2026 Sortacle AI. All systems operational.
    </footer>
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
        self.cooldown_seconds = 8  # Wait 8 seconds between new items (servo takes 3s to move)
        
        # Servo control
        self.enable_servo = enable_servo and SERVO_AVAILABLE
        self.servo_kit = None
        if self.enable_servo:
            try:
                self.servo_kit = get_kit(mock=mock_servo)
                self.servo_kit.servo[SERVO_CH].angle = 90  # Center/closed at 90°
                time.sleep(1.0)
                print("✅ Servo initialized at center position (90°)")
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
                
                # Process detection and trigger servo/logging
                if self.latest_detections:
                    current_time = time.time()
                    
                    # Check if cooldown period has passed
                    if current_time - self.last_detection_time < self.cooldown_seconds:
                        continue
                    
                    best_detection = max(self.latest_detections, key=lambda x: x['confidence'])
                    recyclable = is_recyclable(best_detection['label'])
                    
                    # Only log and move servo if servo is enabled
                    # This ensures we only count items that were actually sorted
                    if self.enable_servo:
                        # Move servo first
                        self.move_servo_for_item(recyclable, best_detection['label'])
                        
                        # Log detection AFTER successful servo movement
                        if self.enable_logging and self.logger:
                            self.logger.log_disposal(
                                detection=best_detection,
                                bin_id=self.bin_id,
                                location=self.location
                            )
                    
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
            # Direct to appropriate bin - start from 90° (center)
            if recyclable:
                target_angle = 180  # Recyclable bin (rotate right from center)
                bin_type = "♻️ RECYCLABLE"
            else:
                target_angle = 0    # Trash bin (rotate left from center)
                bin_type = "🗑️ TRASH"
            
            self.servo_kit.servo[SERVO_CH].angle = target_angle
            print(f"🔄 SERVO: Opening {bin_type} bin for '{label}' ({target_angle}°)")
            
            # Wait for item to clear
            time.sleep(3.0)
            
            # Return to center (90°)
            self.servo_kit.servo[SERVO_CH].angle = 90
            print(f"↩️  SERVO: Closed (90°)")
            
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
        
        # Only send every 3rd frame to cloud to reduce server load (was every 5th)
        self.frame_counter += 1
        if self.frame_counter % 3 == 0:
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
                # Alternate between recyclable (180) and trash (0) positions
                current = self.servo_kit.servo[SERVO_CH].angle
                if current == 90 or current == 0:
                    self.servo_kit.servo[SERVO_CH].angle = 180
                    print("📂 WEB: Opening recyclable bin (180°)")
                else:
                    self.servo_kit.servo[SERVO_CH].angle = 0
                    print("📂 WEB: Opening trash bin (0°)")
            elif action == 'close':
                self.servo_kit.servo[SERVO_CH].angle = 90
                print("⏹️  WEB: Closing bins (90°)")
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

@app.route('/stats')
def get_stats():
    """Get disposal statistics from database"""
    try:
        if not viewer.logger:
            return {'error': 'Database not available'}, 500
        
        # Query database for counts
        import sqlite3
        conn = sqlite3.connect(viewer.logger.db_path)
        cursor = conn.cursor()
        
        # Count recyclable vs non-recyclable
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_recyclable = 1 THEN 1 ELSE 0 END) as recyclable_count,
                SUM(CASE WHEN is_recyclable = 0 THEN 1 ELSE 0 END) as non_recyclable_count
            FROM disposal_events
        """)
        result = cursor.fetchone()
        conn.close()
        
        recyclable = result[0] if result[0] else 0
        non_recyclable = result[1] if result[1] else 0
        
        response = {
            'recyclable': recyclable,
            'non_recyclable': non_recyclable,
            'total': recyclable + non_recyclable
        }
        
        # Add CORS headers
        from flask import jsonify
        resp = jsonify(response)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception as e:
        print(f"⚠️  Stats error: {e}")
        return {'error': str(e)}, 500

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
