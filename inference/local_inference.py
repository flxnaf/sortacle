"""
Local Inference Fallback
Runs YOLO-World inference locally when cloud API is unreachable
Uses custom waste categories: aluminum can, plastic bottle, cardboard box, etc.
"""

import numpy as np
from model import model, format_detections


def run_local_inference(frame: np.ndarray) -> dict:
    """
    Run inference using YOLO-World with custom waste categories
    
    Args:
        frame: numpy array of shape (640, 640, 3) in RGB format
    
    Returns:
        dict: Detections in standardized format
    """
    print(f"  [LOCAL] Running YOLO-World on frame {frame.shape}")
    
    # Run inference - YOLO-World will only detect our custom waste categories
    # Using 25% confidence since open-vocabulary models can be less confident
    results = model(frame, verbose=True, conf=0.25)
    
    # Convert to standardized format
    detections = format_detections(results)
    
    print(f"  [LOCAL] Found {len(detections['detections'])} waste items")
    for det in detections['detections']:
        print(f"    ✓ {det['label']}: {det['confidence']*100:.1f}%")
    
    # Mark source as local fallback
    detections["source"] = "local"
    
    return detections
