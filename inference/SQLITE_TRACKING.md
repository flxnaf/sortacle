# SQLite Database Tracking

## What Gets Logged

**Every time the servo motor rotates**, the system logs to SQLite `disposal_events` table:

### Database Entry (per item sorted)

| Field | Example | Description |
|-------|---------|-------------|
| `id` | 42 | Unique ID for this disposal |
| `timestamp` | 1738368000.5 | Unix timestamp |
| `datetime` | 2026-01-31T14:30:00 | Human-readable time |
| `item_label` | "aluminum can" | What YOLO detected |
| `material_category` | "metal_aluminum" | Material classification |
| `confidence` | 0.92 | Detection confidence (0-1) |
| `is_recyclable` | True | Whether it went to recycle bin |
| `bin_id` | "bin_001" | Which physical bin |
| `location` | "Brown University" | Bin location |
| `bbox_x1, y1, x2, y2` | [100, 150, 300, 400] | Bounding box coordinates |

## Automatic Counters

The database automatically tracks:

✅ **Total items sorted** (all-time counter)
✅ **Recyclable items count** (green bin counter)
✅ **Trash items count** (red bin counter)
✅ **Per-item type counters** (e.g., "aluminum can": 15, "plastic bottle": 23)
✅ **Per-material counters** (e.g., "metal_aluminum": 15, "plastic_bottle": 23)
✅ **Recycling rate** (% of items that were recyclable)
✅ **Today's count** (items sorted since midnight)

## View Your Data

### Quick Stats
```bash
python3 view_data.py
```

Output:
```
======================================================================
📊 SORTACLE STATISTICS
======================================================================
Total Disposals:      127
Recyclable Items:     89 (70.1%)
Trash Items:          38
Today's Count:        15

🏷️  Top Detected Classes:
  • aluminum can: 42
  • plastic bottle: 35
  • glass bottle: 12
  • plastic bag: 18
  • cardboard box: 10
  • paper cup: 10

♻️  Material Breakdown:
  • metal_aluminum: 42
  • plastic_bottle: 35
  • plastic_bag: 18
  • glass_bottle: 12
  • cardboard: 10
  • paper_cup: 10
```

### Recent Activity
```bash
python3 view_data.py --recent 10
```

### Export to CSV
```bash
python3 view_data.py --export data.csv
```

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  ITEM DETECTED                                      │
│  ↓                                                  │
│  "aluminum can" (92% confidence)                    │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  CHECK RECYCLABILITY                                │
│  ↓                                                  │
│  is_recyclable("aluminum can") → True               │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  LOG TO DATABASE ✓                                  │
│  ↓                                                  │
│  disposal_events table: new row added               │
│  - item_label: "aluminum can"                       │
│  - is_recyclable: True                              │
│  - timestamp: now                                   │
│  - material_category: "metal_aluminum"              │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  MOVE SERVO MOTOR                                   │
│  ↓                                                  │
│  rotate_to(0°) → RECYCLABLE BIN ♻️                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  COUNTERS UPDATED AUTOMATICALLY                     │
│  ↓                                                  │
│  Total: 127 → 128                                   │
│  Recyclable: 89 → 90                                │
│  "aluminum can": 42 → 43                            │
└─────────────────────────────────────────────────────┘
```

## Material Categories

The system automatically categorizes detected items:

| Material Category | Examples |
|------------------|----------|
| `metal_aluminum` | aluminum can, soda can, beer can |
| `plastic_bottle` | water bottle, plastic bottle |
| `plastic_bag` | plastic bag |
| `plastic_cup` | plastic cup |
| `glass_bottle` | glass bottle |
| `glass_jar` | glass jar |
| `cardboard` | cardboard box, cardboard |
| `paper` | paper, newspaper |
| `paper_cup` | paper cup, coffee cup |
| `styrofoam` | styrofoam |
| `food_waste` | food waste, food scraps |
| `other` | anything else |

## Database Schema

```sql
CREATE TABLE disposal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    datetime TEXT NOT NULL,
    item_label TEXT NOT NULL,
    material_category TEXT,
    confidence REAL NOT NULL,
    is_recyclable BOOLEAN NOT NULL,
    bin_id TEXT DEFAULT 'bin_001',
    location TEXT DEFAULT 'unknown',
    image_path TEXT,
    bbox_x1 REAL,
    bbox_y1 REAL,
    bbox_x2 REAL,
    bbox_y2 REAL
);

-- Indexes for fast queries
CREATE INDEX idx_timestamp ON disposal_events(timestamp DESC);
CREATE INDEX idx_item_label ON disposal_events(item_label);
CREATE INDEX idx_material_category ON disposal_events(material_category);
```

## Summary

✅ **Counter updates automatically** - every servo movement = 1 database entry
✅ **Tracks what was detected** - item name, material type, recyclable status
✅ **Provides analytics** - recycling rate, top items, material breakdown
✅ **Timestamped** - know exactly when each item was sorted
✅ **Exportable** - can export to CSV for further analysis

**The servo rotation and database logging happen together** - you can't have one without the other!
