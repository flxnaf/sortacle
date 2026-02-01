-- ============================================================================
-- SORTACLE DATABASE SCHEMA (SQLite)
-- Complete SQL setup for waste sorting data collection
-- ============================================================================

-- Main Table: disposal_events
-- Stores every item detected and disposed
CREATE TABLE IF NOT EXISTS disposal_events (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Timestamps
    timestamp REAL NOT NULL,              -- Unix timestamp (1706745600.123)
    datetime TEXT NOT NULL,               -- ISO format (2024-02-01T10:30:00)
    
    -- Detection info
    item_label TEXT NOT NULL,             -- CV class: "plastic bottle", "aluminum can"
    material_category TEXT,               -- Material type: "plastic_bottle", "metal_aluminum"
    confidence REAL NOT NULL,             -- 0.0 to 1.0 (e.g., 0.95 = 95%)
    is_recyclable BOOLEAN NOT NULL,       -- 1 = recyclable, 0 = trash
    
    -- Bin info
    bin_id TEXT DEFAULT 'bin_001',        -- Unique bin identifier
    location TEXT DEFAULT 'unknown',      -- Physical location: "SciLi", "Ratty"
    
    -- Optional data
    image_path TEXT,                      -- Path to saved image (if any)
    
    -- Bounding box coordinates (640x640 frame)
    bbox_x1 REAL,                         -- Top-left X
    bbox_y1 REAL,                         -- Top-left Y
    bbox_x2 REAL,                         -- Bottom-right X
    bbox_y2 REAL                          -- Bottom-right Y
);

-- ============================================================================
-- INDEXES for faster queries
-- ============================================================================

-- Index on timestamp (most common query)
CREATE INDEX IF NOT EXISTS idx_timestamp 
ON disposal_events(timestamp DESC);

-- Index on datetime for date-based queries
CREATE INDEX IF NOT EXISTS idx_datetime 
ON disposal_events(datetime DESC);

-- Index on item_label for class-based queries
CREATE INDEX IF NOT EXISTS idx_item_label 
ON disposal_events(item_label);

-- Index on material_category for material breakdown
CREATE INDEX IF NOT EXISTS idx_material_category 
ON disposal_events(material_category);

-- ============================================================================
-- VIEW: class_stats
-- Pre-computed statistics per detected class
-- ============================================================================

CREATE VIEW IF NOT EXISTS class_stats AS
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

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Get recent disposals
-- SELECT * FROM disposal_events ORDER BY timestamp DESC LIMIT 20;

-- Get recycling rate
-- SELECT 
--     COUNT(*) as total,
--     SUM(is_recyclable) as recyclable,
--     CAST(SUM(is_recyclable) AS FLOAT) / COUNT(*) as rate
-- FROM disposal_events;

-- Top detected items
-- SELECT item_label, COUNT(*) as count 
-- FROM disposal_events 
-- GROUP BY item_label 
-- ORDER BY count DESC 
-- LIMIT 10;

-- Material breakdown
-- SELECT material_category, COUNT(*) as count 
-- FROM disposal_events 
-- GROUP BY material_category 
-- ORDER BY count DESC;

-- Today's disposals
-- SELECT COUNT(*) FROM disposal_events 
-- WHERE date(datetime) = date('now');

-- Class statistics
-- SELECT * FROM class_stats;

-- High confidence detections only
-- SELECT * FROM disposal_events 
-- WHERE confidence >= 0.80 
-- ORDER BY timestamp DESC;

-- All aluminum items
-- SELECT * FROM disposal_events 
-- WHERE material_category = 'metal_aluminum';

-- Disposals at specific location
-- SELECT * FROM disposal_events 
-- WHERE location = 'SciLi' 
-- ORDER BY timestamp DESC;

-- ============================================================================
-- EXAMPLE DATA ROWS
-- ============================================================================

-- Example insert (normally done by data_logger.py):
-- INSERT INTO disposal_events 
-- (timestamp, datetime, item_label, material_category, confidence, 
--  is_recyclable, bin_id, location, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
-- VALUES 
-- (1706745600.123, '2024-02-01T10:30:00', 'plastic bottle', 'plastic_bottle', 
--  0.95, 1, 'bin_sci_li_001', 'SciLi Entrance', 100, 150, 300, 450);

-- ============================================================================
-- COLUMN DETAILS
-- ============================================================================

/*
id:                 Auto-incrementing unique identifier
timestamp:          Unix timestamp (seconds since epoch)
datetime:           Human-readable ISO 8601 format
item_label:         Detected class from YOLO-World model (20 classes)
material_category:  Auto-categorized material type (15 categories)
confidence:         Model confidence score (0.0 - 1.0)
is_recyclable:      Boolean: 1=recyclable, 0=trash
bin_id:             Unique identifier for physical bin
location:           Physical location of bin
image_path:         Optional path to snapshot image
bbox_x1, y1, x2, y2: Bounding box coordinates in 640x640 frame
*/

-- ============================================================================
-- DATA TYPES EXPLANATION
-- ============================================================================

/*
INTEGER:  Whole numbers (1, 2, 3, 100)
REAL:     Floating point numbers (0.95, 123.456, 1706745600.123)
TEXT:     String data ("plastic bottle", "2024-02-01T10:30:00")
BOOLEAN:  SQLite stores as INTEGER (0=false, 1=true)
*/
