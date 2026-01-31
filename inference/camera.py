"""
Camera Capture Module
Isolated camera interface that can be swapped between OpenCV and Raspberry Pi camera

RASPBERRY PI SWAP POINT:
When deploying to Raspberry Pi, replace the OpenCV VideoCapture implementation
with picamera2. The interface remains the same (capture_frame() returns numpy array).
"""

import cv2
import numpy as np


class Camera:
    """
    Camera interface for frame capture
    
    Currently uses OpenCV VideoCapture for local webcam.
    Can be swapped for Raspberry Pi camera without changing downstream code.
    """
    
    def __init__(self, source=0):
        """
        Initialize camera
        
        Args:
            source: Camera source (0 for default webcam, or device path)
        
        RASPBERRY PI NOTE:
        Replace cv2.VideoCapture with picamera2.Picamera2 for RPi deployment
        """
        self.source = source
        
        # OpenCV VideoCapture - works with USB webcams and built-in cameras
        # TODO: Replace with picamera2 for Raspberry Pi camera module
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera at source {source}")
            
        # Get native resolution
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Camera initialized at {self.width}x{self.height} (source: {source})")
    
    def capture_frame(self) -> np.ndarray:
        """
        Capture a single frame from the camera
        
        Returns:
            numpy.ndarray: Native frame in RGB, or None if capture fails
        """
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        # Convert BGR (OpenCV default) to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return frame
    
    def release(self):
        """Release camera resources"""
        if hasattr(self, 'cap'):
            self.cap.release()
        print("✓ Camera released")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
