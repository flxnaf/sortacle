# Sortacle Detection Classes Reference

## YOLO-World Custom Classes

Your CV model detects these **20 specific waste classes**:

### Recyclable Metal (4 classes)
- `aluminum can` → Material: `metal_aluminum`
- `metal can` → Material: `metal`
- `soda can` → Material: `metal_aluminum`
- `beer can` → Material: `metal_aluminum`

### Recyclable Plastic (3 classes)
- `plastic bottle` → Material: `plastic_bottle`
- `water bottle` → Material: `plastic_bottle`
- `plastic container` → Material: `plastic`

### Recyclable Glass (2 classes)
- `glass bottle` → Material: `glass_bottle`
- `glass jar` → Material: `glass_jar`

### Recyclable Paper/Cardboard (4 classes)
- `cardboard box` → Material: `cardboard`
- `cardboard` → Material: `cardboard`
- `paper` → Material: `paper`
- `newspaper` → Material: `paper_newspaper`

### Cups (3 classes)
- `plastic cup` → Material: `plastic_cup`
- `paper cup` → Material: `paper_cup`
- `coffee cup` → Material: `cup_mixed`

### Non-Recyclable (4 classes)
- `plastic bag` → Material: `plastic_bag` ❌
- `styrofoam` → Material: `styrofoam` ❌
- `food waste` → Material: `food_waste` ❌
- `food scraps` → Material: `food_waste` ❌

## Material Categories

Your database automatically categorizes items into these material types:

| Category | Description | Examples |
|----------|-------------|----------|
| `metal_aluminum` | Aluminum items | Soda can, beer can |
| `metal` | Other metals | Metal can |
| `plastic_bottle` | Plastic bottles | Water bottle, plastic bottle |
| `plastic_bag` | Plastic bags | Grocery bags |
| `plastic_cup` | Plastic cups | Disposable cups |
| `plastic` | Other plastic | Containers |
| `glass_bottle` | Glass bottles | Wine bottles |
| `glass_jar` | Glass jars | Mason jars |
| `glass` | Other glass | |
| `cardboard` | Cardboard | Boxes |
| `paper` | Paper products | Paper |
| `paper_newspaper` | Newspapers | Newsprint |
| `paper_cup` | Paper cups | Coffee cups |
| `cup_mixed` | Unknown cup type | Coffee cup |
| `styrofoam` | Styrofoam | Foam containers |
| `food_waste` | Food waste | Food scraps |
| `other` | Unknown material | |

## Database Schema

### Table: `disposal_events`

```sql
CREATE TABLE disposal_events (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    datetime TEXT,
    item_label TEXT,           -- e.g., "plastic bottle"
    material_category TEXT,    -- e.g., "plastic_bottle"
    confidence REAL,
    is_recyclable BOOLEAN,
    bin_id TEXT,
    location TEXT,
    image_path TEXT,
    bbox_x1 REAL,
    bbox_y1 REAL,
    bbox_x2 REAL,
    bbox_y2 REAL
);
```

### View: `class_stats`

```sql
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

## Querying by Class

### Get all plastic bottles
```bash
sqlite3 sortacle_data.db "SELECT * FROM disposal_events WHERE item_label = 'plastic bottle';"
```

### Count by material category
```bash
sqlite3 sortacle_data.db "SELECT material_category, COUNT(*) FROM disposal_events GROUP BY material_category;"
```

### Get all aluminum items
```bash
sqlite3 sortacle_data.db "SELECT * FROM disposal_events WHERE material_category = 'metal_aluminum';"
```

### Class statistics
```bash
sqlite3 sortacle_data.db "SELECT * FROM class_stats;"
```

## Python API

```python
from data_logger import DataLogger

logger = DataLogger('sortacle_data.db')

# Get stats with class breakdown
stats = logger.get_stats()
print(stats['top_items'])           # Top detected classes
print(stats['material_breakdown'])  # Material distribution
print(stats['class_stats'])         # Detailed per-class stats

# Get class breakdown
breakdown = logger.get_class_breakdown()
for cls in breakdown['classes']:
    print(f"{cls['class']}: {cls['count']} ({cls['material']})")
```

## CLI Tools

```bash
# Show detailed class breakdown
python view_data.py --classes

# Show everything
python view_data.py --stats --recent 50

# Export with class info
python view_data.py --export data_with_classes.csv
```

## Example Output

```
🏷️  Top Detected Classes:
  • plastic bottle: 45
  • aluminum can: 32
  • cardboard box: 18
  • plastic bag: 12
  • glass bottle: 8

♻️  Material Breakdown:
  • plastic_bottle: 45
  • metal_aluminum: 32
  • cardboard: 18
  • plastic_bag: 12
  • glass_bottle: 8
```

## Adding New Classes

To add new detection classes, update:

1. **`model.py`** - Add to `WASTE_CATEGORIES` list
2. **`recyclability.py`** - Add to `RECYCLABILITY_TABLE`
3. **`data_logger.py`** - Update `_categorize_material()` if needed

Example:
```python
# model.py
WASTE_CATEGORIES = [
    # ... existing ...
    "tetra pak",  # New class
]

# recyclability.py
RECYCLABILITY_TABLE = {
    # ... existing ...
    "tetra pak": True,
}
```

The database will automatically start logging the new class with material categorization.
