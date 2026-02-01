# Website Integration Guide

## Overview

The Raspberry Pi collects sorting data in a SQLite database. To display this data on your website, the Pi runs a **Data API Server** that the website can query.

## Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│                 │
│  ┌───────────┐  │      HTTP Requests
│  │ SQLite DB │◄─┼──────────────────┐
│  └─────▲─────┘  │                  │
│        │        │                  │
│  ┌─────┴─────┐  │                  │
│  │  Data API │◄─┼──────────────────┤
│  │  (Port    │  │                  │
│  │   8001)   │  │                  │
│  └───────────┘  │                  │
└─────────────────┘                  │
                                     │
                    ┌────────────────┴────────┐
                    │   Website Dashboard     │
                    │   (JavaScript/React)    │
                    │                         │
                    │  fetch('http://PI_IP:   │
                    │         8001/api/stats')│
                    └─────────────────────────┘
```

## Setup on Raspberry Pi

### 1. Start the Data API Server

```bash
cd ~/projects/sortacle/inference
source venv/bin/activate
python3 data_api.py
```

The API will be available at: `http://<PI_IP_ADDRESS>:8001`

### 2. Find Your Pi's IP Address

```bash
hostname -I
```

Example: `172.20.10.4`

### 3. Test the API

From any computer on the same network:
```bash
curl http://172.20.10.4:8001/api/stats
```

## API Endpoints

### 1. Overall Statistics
```http
GET /api/stats
```

**Response:**
```json
{
  "total_disposals": 127,
  "recyclable_count": 89,
  "trash_count": 38,
  "recycling_rate": 0.701,
  "today_count": 15,
  "top_items": {
    "aluminum can": 42,
    "plastic bottle": 35,
    "glass bottle": 12
  },
  "material_breakdown": {
    "metal_aluminum": 42,
    "plastic_bottle": 35,
    "glass_bottle": 12
  },
  "class_stats": [...]
}
```

### 2. Recent Events
```http
GET /api/recent?limit=50
```

**Response:**
```json
{
  "count": 50,
  "events": [
    {
      "id": 127,
      "timestamp": 1738368000.5,
      "datetime": "2026-01-31T14:30:00",
      "item_label": "aluminum can",
      "material_category": "metal_aluminum",
      "confidence": 0.92,
      "is_recyclable": true,
      "bin_id": "bin_001",
      "location": "Brown University"
    },
    ...
  ]
}
```

### 3. Recycling Rate (Simple)
```http
GET /api/recycling-rate
```

**Response:**
```json
{
  "rate": 0.701,
  "recyclable_count": 89,
  "trash_count": 38,
  "total_count": 127
}
```

### 4. Live Counter (For Polling)
```http
GET /api/live
```

**Response:**
```json
{
  "total": 127,
  "today": 15,
  "rate": 0.701,
  "recyclable": 89,
  "trash": 38
}
```

### 5. Class Breakdown
```http
GET /api/classes
```

**Response:**
```json
{
  "classes": [
    {
      "class": "aluminum can",
      "material": "metal_aluminum",
      "count": 42,
      "avg_confidence": "92.3%",
      "recyclable": 42,
      "trash": 0
    },
    ...
  ]
}
```

### 6. Today's Stats
```http
GET /api/today
```

**Response:**
```json
{
  "today_count": 15,
  "today_recyclable": 12
}
```

## Website Integration Examples

### Vanilla JavaScript

```javascript
// Fetch overall stats
async function fetchStats() {
    const response = await fetch('http://172.20.10.4:8001/api/stats');
    const data = await response.json();
    
    document.getElementById('total-count').textContent = data.total_disposals;
    document.getElementById('recycling-rate').textContent = 
        (data.recycling_rate * 100).toFixed(1) + '%';
}

// Fetch live counter (poll every 5 seconds)
async function updateLiveCounter() {
    const response = await fetch('http://172.20.10.4:8001/api/live');
    const data = await response.json();
    
    document.getElementById('live-total').textContent = data.total;
    document.getElementById('live-today').textContent = data.today;
}

// Update every 5 seconds
setInterval(updateLiveCounter, 5000);
```

### React Example

```jsx
import { useState, useEffect } from 'react';

function Dashboard() {
    const [stats, setStats] = useState(null);
    const PI_API = 'http://172.20.10.4:8001';
    
    useEffect(() => {
        // Fetch stats on mount
        fetch(`${PI_API}/api/stats`)
            .then(res => res.json())
            .then(data => setStats(data));
        
        // Poll live counter every 5 seconds
        const interval = setInterval(() => {
            fetch(`${PI_API}/api/live`)
                .then(res => res.json())
                .then(data => setStats(prev => ({...prev, ...data})));
        }, 5000);
        
        return () => clearInterval(interval);
    }, []);
    
    if (!stats) return <div>Loading...</div>;
    
    return (
        <div>
            <h1>Sortacle Dashboard</h1>
            <div className="stat-card">
                <h2>{stats.total}</h2>
                <p>Total Items Sorted</p>
            </div>
            <div className="stat-card">
                <h2>{(stats.rate * 100).toFixed(1)}%</h2>
                <p>Recycling Rate</p>
            </div>
            <div className="stat-card">
                <h2>{stats.today}</h2>
                <p>Sorted Today</p>
            </div>
        </div>
    );
}
```

### Chart.js Integration (Top Items Bar Chart)

```javascript
async function createTopItemsChart() {
    const response = await fetch('http://172.20.10.4:8001/api/stats');
    const data = await response.json();
    
    const labels = Object.keys(data.top_items);
    const values = Object.values(data.top_items);
    
    new Chart(document.getElementById('topItemsChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Count',
                data: values,
                backgroundColor: 'rgba(75, 192, 192, 0.6)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}
```

## CORS Configuration

The API has CORS enabled by default (`allow_origins: ["*"]`), so your website can make requests from any domain.

For production, update `data_api.py` to only allow your website's domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-website.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Running Both Services

The Pi needs to run TWO servers:

### Terminal 1: Main Detector (with UI and servo)
```bash
cd ~/projects/sortacle/inference
source venv/bin/activate
export CLOUD_INFERENCE_URL="http://VULTR_IP:8000"
python3 detector_ui_pro.py
```

### Terminal 2: Data API (for website)
```bash
cd ~/projects/sortacle/inference
source venv/bin/activate
python3 data_api.py
```

## Firewall / Network Access

Make sure port 8001 is accessible:

1. **On the same WiFi network**: Should work automatically
2. **Across networks**: May need to configure router port forwarding
3. **For demos**: Keep everything on the same network (Brown WiFi)

## Testing

Test from your website's computer:

```bash
# Check if API is reachable
curl http://172.20.10.4:8001/

# Get stats
curl http://172.20.10.4:8001/api/stats

# Get live counter
curl http://172.20.10.4:8001/api/live
```

## Alternative: Cloud Database Option

If you want the data available from anywhere (not just local network), you can:

1. **Set up PostgreSQL on Vultr**
2. **Modify Pi to send data to cloud DB instead of local SQLite**
3. **Website queries cloud DB directly**

Let me know if you want to implement this approach instead!

## Summary

✅ **Pi runs Data API on port 8001**
✅ **Website fetches JSON data via HTTP requests**
✅ **Real-time updates with polling (every 5s)**
✅ **CORS enabled for easy integration**
✅ **Multiple endpoints for different use cases**

The website team can now integrate the data using standard `fetch()` or `axios` calls!
