# DATABASE HANDOFF DOCUMENT
# Complete guide for implementing Sortacle database

## ⚡ Quick Start

The database is **already implemented** in Python. Your person can either:

**Option A: Use the existing Python implementation** (recommended)
- Database auto-creates on first run
- No manual SQL needed
- Just run: `python detector_ui_pro.py`

**Option B: Implement from scratch in another language**
- Use the SQL schema below
- Reference the 20 classes table
- Follow the data flow diagram

---

## 📊 DATABASE SCHEMA

### Table: `disposal_events`

```sql
CREATE TABLE disposal_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           REAL NOT NULL,              -- Unix timestamp: 1706745600.123
    datetime            TEXT NOT NULL,              -- ISO 8601: "2024-02-01T10:30:00"
    item_label          TEXT NOT NULL,              -- One of 20 CV classes (see below)
    material_category   TEXT,                       -- Auto-categorized (see mapping)
    confidence          REAL NOT NULL,              -- 0.0 to 1.0 (e.g., 0.95 = 95%)
    is_recyclable       BOOLEAN NOT NULL,           -- 1 = recyclable, 0 = trash
    bin_id              TEXT DEFAULT 'bin_001',     -- Unique bin identifier
    location            TEXT DEFAULT 'unknown',      -- Physical location
    image_path          TEXT,                       -- Optional: path to image
    bbox_x1             REAL,                       -- Bounding box top-left X
    bbox_y1             REAL,                       -- Bounding box top-left Y
    bbox_x2             REAL,                       -- Bounding box bottom-right X
    bbox_y2             REAL                        -- Bounding box bottom-right Y
);

-- Indexes for performance
CREATE INDEX idx_timestamp ON disposal_events(timestamp DESC);
CREATE INDEX idx_datetime ON disposal_events(datetime DESC);
CREATE INDEX idx_item_label ON disposal_events(item_label);
CREATE INDEX idx_material_category ON disposal_events(material_category);

-- Pre-computed statistics view
CREATE VIEW class_stats AS
SELECT 
    item_label,
    material_category,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence,
    SUM(is_recyclable) as recyclable_count,
    COUNT(*) - SUM(is_recyclable) as trash_count
FROM disposal_events
GROUP BY item_label, material_category
ORDER BY count DESC;
```

---

## 🏷️ ALL 20 CV DETECTION CLASSES

These are the **exact classes** from YOLO-World model (`model.py`):

| # | Class Name | Material Category | Recyclable | Notes |
|---|------------|-------------------|------------|-------|
| 1 | `aluminum can` | `metal_aluminum` | ✅ YES | Soda/beer cans |
| 2 | `metal can` | `metal` | ✅ YES | Other metal cans |
| 3 | `soda can` | `metal_aluminum` | ✅ YES | Aluminum soda cans |
| 4 | `beer can` | `metal_aluminum` | ✅ YES | Aluminum beer cans |
| 5 | `plastic bottle` | `plastic_bottle` | ✅ YES | PET/HDPE bottles |
| 6 | `water bottle` | `plastic_bottle` | ✅ YES | Water bottles |
| 7 | `plastic container` | `plastic` | ✅ YES | Food containers |
| 8 | `glass bottle` | `glass_bottle` | ✅ YES | Glass bottles |
| 9 | `glass jar` | `glass_jar` | ✅ YES | Glass jars |
| 10 | `cardboard box` | `cardboard` | ✅ YES | Cardboard boxes |
| 11 | `cardboard` | `cardboard` | ✅ YES | Cardboard sheets |
| 12 | `paper` | `paper` | ✅ YES | Plain paper |
| 13 | `newspaper` | `paper_newspaper` | ✅ YES | Newsprint |
| 14 | `plastic cup` | `plastic_cup` | ✅ YES | Disposable plastic cups |
| 15 | `paper cup` | `paper_cup` | ✅ YES | Paper coffee cups |
| 16 | `coffee cup` | `cup_mixed` | ✅ YES | Mixed material cups |
| 17 | `plastic bag` | `plastic_bag` | ❌ NO | Not recyclable |
| 18 | `styrofoam` | `styrofoam` | ❌ NO | Not recyclable |
| 19 | `food waste` | `food_waste` | ❌ NO | Organic waste |
| 20 | `food scraps` | `food_waste` | ❌ NO | Organic waste |

**Total: 20 classes** (16 recyclable, 4 non-recyclable)

---

## 🗂️ MATERIAL CATEGORIZATION LOGIC

Map `item_label` → `material_category`:

```python
def categorize_material(label):
    label_lower = label.lower()
    
    # Metal
    if 'aluminum' in label_lower or 'soda' in label_lower or 'beer' in label_lower:
        return 'metal_aluminum'
    if 'metal' in label_lower or 'can' in label_lower:
        return 'metal'
    
    # Plastic
    if 'bottle' in label_lower and 'plastic' in label_lower:
        return 'plastic_bottle'
    if 'water bottle' in label_lower:
        return 'plastic_bottle'
    if 'plastic bag' in label_lower:
        return 'plastic_bag'
    if 'plastic cup' in label_lower:
        return 'plastic_cup'
    if 'plastic' in label_lower:
        return 'plastic'
    
    # Glass
    if 'glass bottle' in label_lower:
        return 'glass_bottle'
    if 'glass jar' in label_lower:
        return 'glass_jar'
    if 'glass' in label_lower:
        return 'glass'
    
    # Paper/Cardboard
    if 'cardboard' in label_lower:
        return 'cardboard'
    if 'newspaper' in label_lower:
        return 'paper_newspaper'
    if 'paper cup' in label_lower:
        return 'paper_cup'
    if 'paper' in label_lower:
        return 'paper'
    
    # Cups
    if 'coffee' in label_lower or 'cup' in label_lower:
        return 'cup_mixed'
    
    # Other
    if 'styrofoam' in label_lower:
        return 'styrofoam'
    if 'food' in label_lower:
        return 'food_waste'
    
    return 'other'
```

---

## 📥 DATA FLOW

```
1. CV Model detects item
   ↓
2. Get highest confidence detection
   ↓
3. Extract data:
   - item_label (e.g., "plastic bottle")
   - confidence (e.g., 0.95)
   - bbox coordinates
   ↓
4. Determine:
   - is_recyclable (lookup in table above)
   - material_category (use categorization logic)
   ↓
5. Insert into database:
   INSERT INTO disposal_events (
     timestamp, datetime, item_label, material_category,
     confidence, is_recyclable, bin_id, location,
     bbox_x1, bbox_y1, bbox_x2, bbox_y2
   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   ↓
6. Trigger bin to open (GPIO/servo command)
```

---

## 📝 EXAMPLE IMPLEMENTATION

### Python (Already Done)
```python
from data_logger import DataLogger

logger = DataLogger('sortacle_data.db')

# When CV detects item:
detection = {
    'label': 'plastic bottle',
    'confidence': 0.95,
    'bbox': [100, 150, 300, 450]
}

logger.log_disposal(
    detection,
    bin_id='bin_sci_li_001',
    location='SciLi Entrance'
)
```

### JavaScript/Node.js (If rebuilding)
```javascript
const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('sortacle_data.db');

function logDisposal(detection, binId, location) {
    const timestamp = Date.now() / 1000;
    const datetime = new Date().toISOString();
    const material = categorizeMaterial(detection.label);
    const recyclable = isRecyclable(detection.label);
    
    db.run(`
        INSERT INTO disposal_events 
        (timestamp, datetime, item_label, material_category, 
         confidence, is_recyclable, bin_id, location,
         bbox_x1, bbox_y1, bbox_x2, bbox_y2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
        timestamp, datetime, detection.label, material,
        detection.confidence, recyclable ? 1 : 0,
        binId, location,
        detection.bbox[0], detection.bbox[1],
        detection.bbox[2], detection.bbox[3]
    ]);
}
```

---

## 🔍 COMMON QUERIES

### Get recycling rate
```sql
SELECT 
    COUNT(*) as total,
    SUM(is_recyclable) as recyclable,
    CAST(SUM(is_recyclable) AS FLOAT) / COUNT(*) as rate
FROM disposal_events;
```

### Top 10 detected items
```sql
SELECT item_label, COUNT(*) as count 
FROM disposal_events 
GROUP BY item_label 
ORDER BY count DESC 
LIMIT 10;
```

### Material breakdown
```sql
SELECT material_category, COUNT(*) as count 
FROM disposal_events 
GROUP BY material_category 
ORDER BY count DESC;
```

### Today's disposals
```sql
SELECT COUNT(*) 
FROM disposal_events 
WHERE date(datetime) = date('now');
```

### All plastic bottles
```sql
SELECT * FROM disposal_events 
WHERE item_label = 'plastic bottle'
ORDER BY timestamp DESC;
```

---

## ✅ VALIDATION CHECKLIST

Before going live, verify:

- [ ] Database file created: `sortacle_data.db`
- [ ] Table `disposal_events` exists with 13 columns
- [ ] All 4 indexes created
- [ ] View `class_stats` created
- [ ] Can insert test data
- [ ] Can query recent events
- [ ] All 20 classes are handled
- [ ] Material categorization works
- [ ] Recyclability lookup works
- [ ] Timestamps are correct (Unix + ISO)

---

## 🚨 IMPORTANT NOTES

1. **All 20 classes must be supported** - See table above
2. **Case-insensitive matching** - "Plastic Bottle" = "plastic bottle"
3. **Confidence is 0.0-1.0** - Not percentage (0.95, not 95)
4. **Boolean as integer** - SQLite: 1=true, 0=false
5. **Timestamps**: Unix timestamp (1706745600.123) AND ISO string
6. **Bbox coordinates**: Relative to 640x640 frame
7. **Auto-increment ID** - Don't manually set
8. **Default values**: bin_id='bin_001', location='unknown'

---

## 📦 FILES TO HAND OFF

Give your person these files:

1. ✅ **`schema.sql`** - Complete SQL schema
2. ✅ **`SCHEMA_REFERENCE.md`** - Documentation
3. ✅ **`CLASSES_REFERENCE.md`** - All 20 classes details
4. ✅ **`DATABASE_HANDOFF.md`** - This file
5. ✅ **`data_logger.py`** - Reference implementation (Python)

Optional (if using Python):
6. **`detector_ui_pro.py`** - Full working system
7. **`view_data.py`** - Query tool

---

## 🧪 TEST DATA

Insert this to test:

```sql
INSERT INTO disposal_events 
(timestamp, datetime, item_label, material_category, confidence, 
 is_recyclable, bin_id, location, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
VALUES 
(1706745600, '2024-02-01T10:30:00', 'plastic bottle', 'plastic_bottle', 0.95, 1, 'bin_001', 'Brown University', 100, 150, 300, 450),
(1706745605, '2024-02-01T10:30:05', 'aluminum can', 'metal_aluminum', 0.92, 1, 'bin_001', 'Brown University', 120, 180, 280, 420),
(1706745610, '2024-02-01T10:30:10', 'plastic bag', 'plastic_bag', 0.88, 0, 'bin_001', 'Brown University', 150, 200, 350, 480);
```

Then verify:
```sql
SELECT COUNT(*) FROM disposal_events;  -- Should return 3
SELECT * FROM class_stats;              -- Should show 3 classes
```

---

## ❓ QUESTIONS FOR YOUR PERSON

Have them confirm:

1. What language/framework are they using? (Python? JavaScript? C++?)
2. Do they want to use the existing Python code or rebuild?
3. What database system? (SQLite as-is? MySQL? PostgreSQL?)
4. How will they integrate with CV detection pipeline?
5. Where will database be deployed? (Edge device? Cloud?)

---

## 📞 CONTACT

If they have questions about:
- **CV classes**: Check `model.py` WASTE_CATEGORIES list
- **Recyclability**: Check `recyclability.py` RECYCLABILITY_TABLE
- **Schema**: Use `schema.sql`
- **Implementation**: Reference `data_logger.py`

Everything is documented in the files listed above.
