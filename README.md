# Sortacle

Computer vision inference system with edge-to-cloud architecture.

## Project Structure

```
sortacle/
├── website/          # Future: data visualization, dashboards, sponsor UI
└── inference/        # Computer vision inference service (edge/cloud)
```

## Quick Start

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

Reserved for future data visualization components. See `website/README.md`.

## Architecture

The inference service is designed to run identically on:
- Edge devices (Raspberry Pi, Jetson Nano)
- Cloud infrastructure (AWS, GCP, Azure)
- Hybrid deployments

## License

MIT
