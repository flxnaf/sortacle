# Sortacle Database Setup (SQLite)

## Why SQLite?

- **No server setup needed** - just a single file
- **Built into Python** - no extra dependencies
- **Perfect for edge devices** - works on Raspberry Pi, Jetson, etc.
- **Easy to backup** - just copy the .db file
- **Easy to query** - standard SQL
- **Can scale later** - migrate to PostgreSQL/MySQL if needed

## Automatic Setup

The database is **automatically created** when you run the detector for the first time!

```bash
cd inference
python detector_ui_pro.py
```

This creates `sortacle_data.db` in the current directory.

## Database Schema

### Table: `disposal_events`

| Column         | Type    | Description                          |
|----------------|---------|--------------------------------------|
| id             | INTEGER | Auto-incrementing primary key        |
| timestamp      | REAL    | Unix timestamp                       |
| datetime       | TEXT    | ISO format datetime (human-readable) |
| item_label     | TEXT    | Item type (e.g., "plastic bottle")  |
| confidence     | REAL    | CV model confidence (0.0 - 1.0)     |
| is_recyclable  | BOOLEAN | True if recyclable, False if trash   |
| bin_id         | TEXT    | Unique bin identifier                |
| location       | TEXT    | Physical location of bin             |
| image_path     | TEXT    | Optional path to image snapshot      |
| bbox_x1        | REAL    | Bounding box coordinates             |
| bbox_y1        | REAL    |                                      |
| bbox_x2        | REAL    |                                      |
| bbox_y2        | REAL    |                                      |

### Indexes

- `idx_timestamp` - Fast queries by time
- `idx_datetime` - Fast queries by date
- `idx_item_label` - Fast queries by item type

## Usage Examples

### 1. Run detector with data logging (default)

```bash
python detector_ui_pro.py
```

### 2. Run with custom bin ID and location

```bash
python detector_ui_pro.py --bin-id "bin_sci_li_001" --location "SciLi Entrance"
```

### 3. Run without logging (testing only)

```bash
python detector_ui_pro.py --no-logging
```

### 4. Use custom database file

```bash
python detector_ui_pro.py --db-path "my_custom_data.db"
```

## Viewing Your Data

### Quick view with Python script

```bash
# Show stats and recent 20 events
python view_data.py

# Show stats only
python view_data.py --stats

# Show recent 50 events
python view_data.py --recent 50

# Export to CSV
python view_data.py --export disposal_data.csv
```

### Query with SQLite command line

```bash
# Open database
sqlite3 sortacle_data.db

# Show all disposals
SELECT * FROM disposal_events ORDER BY timestamp DESC LIMIT 10;

# Recycling rate
SELECT 
    COUNT(*) as total,
    SUM(is_recyclable) as recyclable,
    CAST(SUM(is_recyclable) AS FLOAT) / COUNT(*) as rate
FROM disposal_events;

# Top items
SELECT item_label, COUNT(*) as count 
FROM disposal_events 
GROUP BY item_label 
ORDER BY count DESC;

# Today's disposals
SELECT COUNT(*) 
FROM disposal_events 
WHERE date(datetime) = date('now');

# Exit
.quit
```

### Query with Python

```python
from data_logger import DataLogger

logger = DataLogger('sortacle_data.db')

# Get stats
stats = logger.get_stats()
print(f"Total: {stats['total_disposals']}")
print(f"Recycling rate: {stats['recycling_rate']:.1%}")

# Get recent events
recent = logger.get_recent_events(limit=50)
for event in recent:
    print(f"{event['datetime']}: {event['item_label']}")

# Export to CSV
logger.export_to_csv('export.csv')
```

## Data Flow

```
CV Detection → Filter by confidence → Log to SQLite
      ↓
Best detection (highest confidence)
      ↓
Trigger bin opening + Log event
      ↓
Database record created
```

## Accessing from Website/API

To show data on your website dashboard, you can:

### Option 1: Export to JSON

```python
import sqlite3
import json

conn = sqlite3.connect('sortacle_data.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM disposal_events ORDER BY timestamp DESC LIMIT 100')

events = [dict(zip([col[0] for col in cursor.description], row)) 
          for row in cursor.fetchall()]

with open('../website/data.json', 'w') as f:
    json.dump(events, f)
```

### Option 2: Simple API server (Flask)

```python
from flask import Flask, jsonify
from data_logger import DataLogger

app = Flask(__name__)
logger = DataLogger('sortacle_data.db')

@app.route('/api/stats')
def get_stats():
    return jsonify(logger.get_stats())

@app.route('/api/recent/<int:limit>')
def get_recent(limit=100):
    return jsonify(logger.get_recent_events(limit))

if __name__ == '__main__':
    app.run(port=5000)
```

Then fetch from your website:
```javascript
fetch('http://localhost:5000/api/stats')
    .then(r => r.json())
    .then(data => console.log(data));
```

## Backup & Export

### Backup database

```bash
# Simple copy
cp sortacle_data.db sortacle_data_backup_$(date +%Y%m%d).db

# Or export to CSV
python view_data.py --export backup.csv
```

### Transfer to cloud

```bash
# Upload to server
scp sortacle_data.db user@server:/path/to/backup/

# Or sync with rsync
rsync -avz sortacle_data.db user@server:/path/to/backup/
```

## Troubleshooting

**Database is locked:**
```bash
# Check if another process is using it
lsof sortacle_data.db

# Or just wait a moment and try again
```

**Database corrupted:**
```bash
# Dump and restore
sqlite3 sortacle_data.db ".dump" > backup.sql
rm sortacle_data.db
sqlite3 sortacle_data.db < backup.sql
```

**Need to reset:**
```bash
# Delete and it will be recreated
rm sortacle_data.db
python detector_ui_pro.py
```
