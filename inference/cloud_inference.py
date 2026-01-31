"""
Cloud Inference Client
Sends frames to remote cloud inference API with timeout and fallback handling
"""

import os
import cv2
import numpy as np
import requests

# CLOUD ENDPOINT CONFIGURATION
# Set via environment variable: export CLOUD_INFERENCE_URL="http://your-vm-ip:8000"
# Default: localhost for local testing
CLOUD_ENDPOINT = os.getenv("CLOUD_INFERENCE_URL", "http://localhost:8000")
TIMEOUT_SECONDS = 5


def run_cloud_inference(frame: np.ndarray) -> dict:
    """
    Send frame to cloud inference API
    
    Args:
        frame: numpy array of shape (640, 640, 3) in RGB format
    
    Returns:
        dict: Detections from cloud API
    
    Raises:
        requests.Timeout: If request exceeds timeout
        requests.ConnectionError: If cannot connect to server
        requests.HTTPError: If server returns error status
    """
    # Convert RGB to BGR for JPEG encoding
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Encode frame as JPEG
    _, jpeg_buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    # Send to cloud API
    response = requests.post(
        f"{CLOUD_ENDPOINT}/infer",
        files={"file": ("frame.jpg", jpeg_buffer.tobytes(), "image/jpeg")},
        timeout=TIMEOUT_SECONDS
    )
    
    # Check for HTTP errors
    response.raise_for_status()
    
    # Parse JSON response
    detections = response.json()
    detections["source"] = "cloud"
    
    return detections


def test_cloud_connection() -> bool:
    """Test if cloud API is reachable"""
    try:
        response = requests.get(f"{CLOUD_ENDPOINT}/", timeout=2)
        return response.status_code == 200
    except:
        return False
