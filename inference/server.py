#!/usr/bin/env python3
"""
FastAPI Inference Server
Handles image uploads and runs computer vision inference
Can run locally or on cloud infrastructure
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import io
import numpy as np
from local_inference import run_local_inference

app = FastAPI(title="Sortacle Inference API")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "sortacle-inference"}


@app.post("/infer")
async def infer(file: UploadFile = File(...)):
    """
    Computer vision inference endpoint
    
    Accepts:
        - JPEG image upload
    
    Returns:
        - JSON with bounding boxes, labels, and confidence scores
    
    Process:
        1. Read uploaded image
        2. Resize to 640x640
        3. Run inference (currently mocked, will integrate YOLO/CV model)
        4. Return predictions
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPEG/PNG)"
            )
        
        # Read image from upload
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles PNG with alpha, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize to 640x640 (standard input size for YOLO)
        image = image.resize((640, 640), Image.Resampling.LANCZOS)
        
        # Convert PIL to numpy array for YOLO-World
        frame = np.array(image)
        
        # Run real YOLO-World inference
        predictions = run_local_inference(frame)
        
        return JSONResponse(content=predictions)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Run server on all interfaces so it works locally and on cloud VMs
    uvicorn.run(app, host="0.0.0.0", port=8000)
