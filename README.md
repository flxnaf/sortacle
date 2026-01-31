# Sortacle

Computer vision inference system with edge-to-cloud architecture.

## Project Structure

```
sortacle/
├── website/          # Sustainability dashboard & visualization UI
└── inference/        # Computer vision inference service (edge/cloud)
```

## Quick Start

### Website Dashboard

```bash
cd website
python3 -m http.server 8080
```
Visit `http://localhost:8080` to view the dashboard.

### Inference Service

```bash
cd inference
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

See `inference/README.md` for detailed documentation.

### Website

A beautifully stylized sustainability dashboard with interactive heatmaps and sponsor metrics. See `website/README.md` for preview instructions.

## Architecture

The inference service is designed to run identically on:
- Edge devices (Raspberry Pi, Jetson Nano)
- Cloud infrastructure (AWS, GCP, Azure)
- Hybrid deployments

## License

MIT
