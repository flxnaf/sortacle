"""
YOLO-World Model Loader
Uses YOLO-World for open-vocabulary detection of recyclables
YOLO-World can detect custom categories like "aluminum can", "plastic bottle" etc.
"""

from ultralytics import YOLO
import time

# Define the EXACT categories we want to detect for waste sorting
# YOLO-World uses CLIP embeddings - be descriptive but not too specific!
# Simplified for better accuracy - fewer similar categories
WASTE_CATEGORIES = [
    # Recyclable items - simplified
    "can",                  # Metal cans (soda, beer, etc.)
    "bottle",              # Plastic/glass bottles
    "cardboard box",
    "cardboard",
    "paper",
    "cup",
    # Non-recyclable items
    "plastic bag",
    "chip bag",
    "food package",
    "wrapper",
    "styrofoam",
    "foam container",
    "straw",
    "fork",
    "spoon",
    "plastic utensil",
    "napkin",
    "tissue",
]

print("Loading YOLO-World model for open-vocabulary waste detection...")
start_time = time.time()

# YOLO-World for open-vocabulary detection
model = YOLO("yolov8s-worldv2.pt")  # small version (already downloaded)

# Set our custom waste categories - THIS is the key difference
# YOLO-World will now specifically look for these items
model.set_classes(WASTE_CATEGORIES)

load_time = time.time() - start_time
print(f"✓ YOLO-World loaded in {load_time:.2f}s")
print(f"✓ Custom categories: {len(WASTE_CATEGORIES)} waste types")
print("  Detecting: cans, bottles, cardboard, cups, plastic bags, etc.")


def compute_iou(box1, box2):
    """Compute Intersection over Union between two boxes [x1,y1,x2,y2]"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter = max(0, x2-x1) * max(0, y2-y1)
    area1 = (box1[2]-box1[0]) * (box1[3]-box1[1])
    area2 = (box2[2]-box2[0]) * (box2[3]-box2[1])
    union = area1 + area2 - inter
    
    return inter / union if union > 0 else 0

def filter_overlapping(detections, iou_threshold=0.5):
    """Keep only highest confidence detection when boxes overlap"""
    if not detections:
        return detections
    
    # Sort by confidence (highest first)
    sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    kept = []
    
    for det in sorted_dets:
        # Check if this box overlaps with any kept box
        dominated = False
        for kept_det in kept:
            if compute_iou(det['bbox'], kept_det['bbox']) > iou_threshold:
                dominated = True
                break
        if not dominated:
            kept.append(det)
    
    return kept

def format_detections(results) -> dict:
    """
    Convert YOLO-World results to unified output format
    Filters overlapping detections to keep only the highest confidence one
    """
    detections = []
    
    for result in results:
        if hasattr(result, 'boxes') and result.boxes is not None:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                cls_idx = int(boxes.cls[i])
                label = result.names[cls_idx] if hasattr(result, 'names') else f"class_{cls_idx}"
                
                detection = {
                    "bbox": boxes.xyxy[i].cpu().numpy().tolist(),
                    "label": label,
                    "confidence": float(boxes.conf[i])
                }
                detections.append(detection)
    
    # Filter overlapping detections - keep highest confidence
    detections = filter_overlapping(detections, iou_threshold=0.5)
    
    return {
        "detections": detections,
        "model": "yolov8s-worldv2",
        "inference_time_ms": getattr(results[0], 'speed', {}).get('inference', 0) if results else 0
    }
