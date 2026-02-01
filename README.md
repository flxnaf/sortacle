# Sortacle

AI-powered waste sorting system with edge-to-cloud architecture for automated recyclable detection and bin routing.

![Sortacle Pipeline](sortacle-pipeline-diagram.png)

## 🎯 How It Works

Sortacle uses computer vision to automatically sort waste into recyclable and trash bins:

1. **📷 Camera Capture** - Raspberry Pi camera captures items placed in the sorting area
2. **☁️ Cloud Inference** - Frame is sent to Vultr server running YOLO-World object detection
3. **🤖 AI Detection** - YOLO-World identifies the item (e.g., "aluminum can", "plastic bottle")
4. **♻️ Recyclability Check** - System determines if item is recyclable based on material type
5. **🔄 Servo Control** - Rotating platform moves to appropriate bin:
   - **Recyclable** → 0° (green bin)
   - **Trash** → 180° (red bin)
6. **📊 Data Logging** - All detections logged to SQLite database for analytics

## Project Structure

```
sortacle/
├── website/          # Sustainability dashboard & visualization UI
├── inference/        # Computer vision inference service (edge/cloud)
│   ├── server.py           # FastAPI cloud inference server
│   ├── detector_ui_pro.py  # Raspberry Pi UI + servo control
│   ├── camera.py           # Camera interface (picamera2/OpenCV)
│   ├── cloud_inference.py  # Cloud API client
│   ├── model.py            # YOLO-World model loader
│   ├── recyclability.py    # Material classification
│   ├── data_logger.py      # SQLite database logger
│   └── servo/
│       └── servo_move.py   # Servo motor control
└── sortacle-pipeline-diagram.png
```

## Quick Start

### 1. Cloud Inference Server (Vultr)

```bash
cd inference
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

### 2. Raspberry Pi Edge Device

```bash
cd inference
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# Set cloud inference endpoint
export CLOUD_INFERENCE_URL="http://YOUR_VULTR_IP:8000"

# Run with servo control
python3 detector_ui_pro.py

# Or test without servo hardware
python3 detector_ui_pro.py --mock-servo
```

### 3. View Data Dashboard

```bash
cd website
python3 -m http.server 8080
```
Visit `http://localhost:8080` to view the sustainability dashboard.

**Or view database directly:**
```bash
cd inference
python3 view_data.py
```

## ✨ Features

- **Real-time Object Detection** - YOLO-World identifies 30+ waste categories
- **Cloud Inference** - Offloads heavy computation to Vultr server
- **Automated Sorting** - Servo motor routes items to correct bin
- **Live UI Display** - X11-forwarded GUI shows detections in real-time
- **Data Analytics** - SQLite database tracks all disposals with timestamps
- **Recyclability Engine** - Material-based classification (aluminum, plastic, glass, paper)
- **Graceful Fallbacks** - Works with/without servo hardware

## 🎬 Demo Tips

1. **Items that work well:**
   - Aluminum/soda cans (high accuracy)
   - Plastic bottles (clear labels)
   - Glass bottles
   - Cardboard boxes
   - Paper cups

2. **Camera positioning:**
   - Place item 6-12 inches from camera
   - Ensure good lighting
   - Adjust focus by twisting camera lens

3. **Servo timing:**
   - System waits 1.5s for item to drop
   - Auto-returns to center (90°) after sorting
   - Use `--mock-servo` to test without hardware

4. **Data logging:**
   - Items logged once every 5 seconds (avoids duplicates)
   - View stats with `python3 view_data.py`
   - Check recycling rate on dashboard

## Architecture

### Hardware Components
- **Raspberry Pi 4** - Edge device for camera, UI, servo control
- **Pi Camera Module** - Real-time video capture
- **Servo Motor (180°)** - Rotating platform for bin routing
- **Vultr Cloud Server** - Remote inference with YOLO-World model

### Software Stack
- **YOLO-World** - Open-vocabulary object detection
- **FastAPI** - Cloud inference API
- **OpenCV + picamera2** - Camera interface
- **SQLite** - Local data storage
- **X11** - Remote GUI display

The inference service is designed to run identically on:
- Edge devices (Raspberry Pi, Jetson Nano)
- Cloud infrastructure (AWS, GCP, Azure, Vultr)
- Hybrid deployments

## License

MIT
