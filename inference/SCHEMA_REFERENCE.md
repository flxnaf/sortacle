# Sortacle Database Schema

## Quick Reference: What Gets Stored

Every time your CV detects an item that triggers the bin, this data is logged:

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| **id** | INTEGER | `1` | Auto-incrementing ID |
| **timestamp** | REAL | `1706745600.123` | Unix timestamp |
| **datetime** | TEXT | `2024-02-01T10:30:00` | Human-readable time |
| **item_label** | TEXT | `"plastic bottle"` | CV detected class (1 of 20) |
| **material_category** | TEXT | `"plastic_bottle"` | Material type (1 of 15) |
| **confidence** | REAL | `0.95` | Model confidence (0.0-1.0) |
| **is_recyclable** | BOOLEAN | `1` | 1=recyclable, 0=trash |
| **bin_id** | TEXT | `"bin_sci_li_001"` | Your bin's ID |
| **location** | TEXT | `"SciLi Entrance"` | Where the bin is |
| **image_path** | TEXT | `"/path/to/img.jpg"` | Optional snapshot |
| **bbox_x1** | REAL | `100.5` | Bounding box coords |
| **bbox_y1** | REAL | `150.0` | |
| **bbox_x2** | REAL | `300.0` | |
| **bbox_y2** | REAL | `450.5` | |

## 20 Detected Classes (item_label)

```
Recyclable:
  ♻️ aluminum can, metal can, soda can, beer can
  ♻️ plastic bottle, water bottle, plastic container
  ♻️ glass bottle, glass jar
  ♻️ cardboard box, cardboard, paper, newspaper
  ♻️ plastic cup, paper cup, coffee cup

Non-Recyclable:
  🗑️ plastic bag, styrofoam, food waste, food scraps
```

## 15 Material Categories (material_category)

```
metal_aluminum      → Soda cans, beer cans
metal               → Other metal cans
plastic_bottle      → Water bottles, plastic bottles
plastic_bag         → Grocery bags
plastic_cup         → Disposable cups
plastic             → Other plastic containers
glass_bottle        → Glass bottles
glass_jar           → Glass jars
glass               → Other glass
cardboard           → Cardboard boxes
paper               → Plain paper
paper_newspaper     → Newspapers
paper_cup           → Paper cups
cup_mixed           → Coffee cups (unknown material)
styrofoam           → Foam containers
food_waste          → Food scraps
other               → Unknown materials
```

## Example Data Row

```json
{
  "id": 42,
  "timestamp": 1706745600.123,
  "datetime": "2024-02-01T10:30:00",
  "item_label": "plastic bottle",
  "material_category": "plastic_bottle",
  "confidence": 0.95,
  "is_recyclable": true,
  "bin_id": "bin_sci_li_001",
  "location": "SciLi Entrance",
  "image_path": null,
  "bbox": [100.5, 150.0, 300.0, 450.5]
}
```

## Creating the Database

**Automatic (Recommended):**
```bash
python detector_ui_pro.py
# Database is auto-created on first run
```

**Manual (if needed):**
```bash
sqlite3 sortacle_data.db < schema.sql
```

## Querying Your Data

### Python
```python
from data_logger import DataLogger
logger = DataLogger('sortacle_data.db')

stats = logger.get_stats()
print(stats['top_items'])  # {"plastic bottle": 45, "aluminum can": 32}
```

### Command Line
```bash
# View schema
sqlite3 sortacle_data.db ".schema"

# Count disposals
sqlite3 sortacle_data.db "SELECT COUNT(*) FROM disposal_events;"

# Top items
sqlite3 sortacle_data.db "SELECT item_label, COUNT(*) FROM disposal_events GROUP BY item_label ORDER BY COUNT(*) DESC;"
```

### View Tool
```bash
python view_data.py --stats
```

## What Questions Can You Answer?

With this schema, you can answer:

- ✅ How many items were disposed per day/week/month?
- ✅ What's the recycling rate?
- ✅ What are the top detected items?
- ✅ What materials are most common?
- ✅ Which classes have highest/lowest confidence?
- ✅ How many plastic bottles vs aluminum cans?
- ✅ Which bin is most used?
- ✅ What time of day has most disposals?
- ✅ Are users disposing items correctly?

## Database File

- **Location**: `sortacle_data.db` (in inference folder)
- **Size**: ~1KB per 100 entries
- **Backup**: Just copy the .db file
- **Transfer**: `scp sortacle_data.db user@server:/path/`

## No Setup Required!

The database is **automatically created** when you run:
```bash
python detector_ui_pro.py
```

That's it! The schema is applied automatically by `data_logger.py`.
