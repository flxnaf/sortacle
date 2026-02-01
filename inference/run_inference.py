"""
Inference Logic
Uses YOLO-World for open-vocabulary waste detection
"""

import numpy as np
from PIL import Image
from model import model, format_detections


def run_inference(image: Image.Image) -> dict:
    """
    Run YOLO-World inference on an image
    
    Args:
        image: PIL Image object (already resized to 640x640)
    
    Returns:
        dict with predictions containing:
            - detections: list of detected objects with bbox, label, confidence
            - model: model name
            - inference_time_ms: inference time in milliseconds
    """
    
    # Convert PIL Image to numpy array for YOLO
    img_array = np.array(image)
    
    # Run YOLO-World inference with custom waste categories
    # Using 25% confidence since open-vocabulary models can be less confident
    results = model(img_array, verbose=False, conf=0.25)
    
    # Convert to standardized format
    predictions = format_detections(results)
    
    # Add image size info
    predictions["image_size"] = img_array.shape
    
    return predictions


# Future integration example:
#
# import torch
# from ultralytics import YOLO
#
# # Load model once at startup
# model = YOLO('yolov8n.pt')
#
# def run_inference(image: Image.Image) -> dict:
#     results = model(image)
#     predictions = {
#         "detections": [
#             {
#                 "bbox": box.xyxy[0].tolist(),
#                 "label": model.names[int(box.cls)],
#                 "confidence": float(box.conf)
#             }
#             for result in results
#             for box in result.boxes
#         ]
#     }
#     return predictions
