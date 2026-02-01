# Inference Service

Computer vision inference service for Sortacle. This service runs identically on edge devices or cloud infrastructure.

## Edge → Cloud Architecture

This inference service is designed to run in multiple deployment scenarios:

1. **Edge Deployment**: Run directly on edge devices (Raspberry Pi, Jetson Nano, etc.)
2. **Cloud Deployment**: Deploy on cloud VMs (AWS EC2, GCP Compute Engine, Azure VM)
3. **Hybrid**: Process on edge when possible, fallback to cloud for heavy workloads

The API design allows transparent switching between deployment modes without client-side changes.

## Quick Start

### 1. Install Dependencies

```bash
cd inference
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python server.py
```

The server will start on `http://0.0.0.0:8000`

### Servo (hardware) 🔧

If you have an Adafruit PCA9685 servo driver connected via I²C (typical on Raspberry Pi), there's a separate requirements file for the servo helpers in `servo/servorequirements.txt`.

Quick steps:

```bash
cd servo
python -m venv ../venv
source ../venv/bin/activate
pip install -r servorequirements.txt
# Enable I2C on Raspberry Pi (raspi-config) and verify with:
i2cdetect -y 1  # look for device at 0x40
python calibrate.py   # exercise raw angles
python servo_move.py  # interactive control (enter 0-180 or q to quit)
```

Notes:

- `calibrate.py` writes raw angles (0–180) to the servo. Use this to find orientation.
- `servo_move.py` inverts the input angle before setting the servo (`actual_angle = 180 - angle`).
- Hardware deps were moved to `servo/servorequirements.txt` so the main `inference/requirements.txt` remains cloud-friendly.

### 3. Test the API

In another terminal:

```bash
# First, get a test image
curl -o test_image.jpg https://via.placeholder.com/640

# Run the test client
python test_client.py test_image.jpg
```

## API Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "service": "sortacle-inference"
}
```

### `POST /infer`
Computer vision inference endpoint

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Image file (JPEG/PNG)

**Response:**
```json
{
  "image_size": [640, 640, 3],
  "detections": [
    {
      "bbox": [100, 150, 300, 400],
      "label": "object_1",
      "confidence": 0.92
    }
  ],
  "model": "mock_detector_v1",
  "inference_time_ms": 45.2
}
```

## Project Structure

```
inference/
├── server.py          # FastAPI application
├── run_inference.py   # Core inference logic (currently mocked)
├── test_client.py     # Test client
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Model Integration

Currently, `run_inference.py` returns mock predictions. To integrate a real model (e.g., YOLO):

1. Add model dependency to `requirements.txt` (e.g., `ultralytics`, `torch`)
2. Update `run_inference()` function in `run_inference.py`
3. Load model weights
4. Replace mock predictions with actual inference

See comments in `run_inference.py` for integration guidance.

## Deployment

### Local Development
```bash
python server.py
```

### Production (Cloud VM)
```bash
# Using systemd, Docker, or PM2
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Cloud Considerations
- Ensure firewall allows port 8000
- Use HTTPS in production (add TLS termination)
- Consider auto-scaling based on inference load
- Monitor GPU utilization if using GPU acceleration

## Next Steps

- [ ] Integrate real computer vision model (YOLO, Faster R-CNN, etc.)
- [ ] Add GPU acceleration support
- [ ] Implement request queuing for high load
- [ ] Add model versioning
- [ ] Implement edge-to-cloud failover logic
