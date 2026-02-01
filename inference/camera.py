"""
Camera Capture Module
Automatically detects and uses either picamera2 (Pi Camera Module) or OpenCV (USB webcam)
"""

import cv2
import numpy as np

# Try to import picamera2 for Raspberry Pi Camera Module
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False


class Camera:
    """
    Camera interface for frame capture
    
    Automatically uses:
    - picamera2 for Raspberry Pi Camera Module
    - OpenCV VideoCapture for USB webcams
    """
    
    def __init__(self, source=0, use_picamera=None):
        """
        Initialize camera
        
        Args:
            source: Camera source (0 for default, or device path)
            use_picamera: Force picamera2 (True) or OpenCV (False), None = auto-detect
        """
        self.source = source
        self.use_picamera = use_picamera
        
        # Auto-detect: Try picamera2 first if available
        if use_picamera is None:
            use_picamera = PICAMERA2_AVAILABLE
        
        if use_picamera and PICAMERA2_AVAILABLE:
            try:
                # Initialize Pi Camera Module with picamera2
                self.picam = Picamera2()
                config = self.picam.create_preview_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                )
                self.picam.configure(config)
                self.picam.start()
                
                self.width = 640
                self.height = 480
                self.cap = None
                print(f"✓ Pi Camera Module initialized at {self.width}x{self.height} (picamera2)")
                return
            except Exception as e:
                print(f"⚠ picamera2 failed ({e}), falling back to OpenCV...")
        
        # Fall back to OpenCV VideoCapture
        self.picam = None
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera at source {source}")
            
        # Get native resolution
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Camera initialized at {self.width}x{self.height} (OpenCV, source: {source})")
    
    def capture_frame(self) -> np.ndarray:
        """
        Capture a single frame from the camera
        
        Returns:
            numpy.ndarray: Frame in RGB format, or None if capture fails
        """
        if self.picam:
            # Use picamera2
            try:
                frame = self.picam.capture_array()
                return frame  # Already in RGB format
            except Exception as e:
                print(f"[ERROR] picamera2 capture failed: {e}")
                return None
        else:
            # Use OpenCV
            ret, frame = self.cap.read()
            
            if not ret:
                return None
            
            # Convert BGR (OpenCV default) to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            return frame
    
    def release(self):
        """Release camera resources"""
        if hasattr(self, 'picam') and self.picam:
            self.picam.stop()
            print("✓ Pi Camera released")
        elif hasattr(self, 'cap') and self.cap:
            self.cap.release()
            print("✓ Camera released")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
