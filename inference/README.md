# Sortacle Inference

Machine learning inference service for Sortacle.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Run

```bash
python inference_server.py
```

## API

The inference service provides REST API endpoints for predictions.

### Health Check
```
GET /health
```

### Predict
```
POST /predict
Content-Type: application/json

{
    "data": [...your data...]
}
```
