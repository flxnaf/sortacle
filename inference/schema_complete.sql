-- ============================================================================
-- SORTACLE DATABASE - COMPLETE SCHEMA
-- Copy this file to your database person
-- ============================================================================

-- ============================================================================
-- MAIN TABLE: disposal_events
-- ============================================================================

CREATE TABLE IF NOT EXISTS disposal_events (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Timestamps
    timestamp REAL NOT NULL,              -- Unix timestamp (1706745600.123)
    datetime TEXT NOT NULL,               -- ISO 8601 format (2024-02-01T10:30:00)
    
    -- Detection information
    item_label TEXT NOT NULL,             -- One of 20 CV classes (see below)
    material_category TEXT,               -- Auto-categorized material type
    confidence REAL NOT NULL,             -- Model confidence: 0.0 to 1.0 (e.g., 0.95)
    is_recyclable BOOLEAN NOT NULL,       -- 1 = recyclable, 0 = trash
    
    -- Bin information
    bin_id TEXT DEFAULT 'bin_001',        -- Unique bin identifier
    location TEXT DEFAULT 'unknown',      -- Physical location
    
    -- Optional data
    image_path TEXT,                      -- Path to saved image (if capturing)
    
    -- Bounding box coordinates (640x640 frame)
    bbox_x1 REAL,                         -- Top-left X
    bbox_y1 REAL,                         -- Top-left Y
    bbox_x2 REAL,                         -- Bottom-right X
    bbox_y2 REAL                          -- Bottom-right Y
);

-- ============================================================================
-- INDEXES (for query performance)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_timestamp ON disposal_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_datetime ON disposal_events(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_item_label ON disposal_events(item_label);
CREATE INDEX IF NOT EXISTS idx_material_category ON disposal_events(material_category);

-- ============================================================================
-- VIEW: class_stats (pre-computed statistics)
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
-- ALL 20 CV DETECTION CLASSES
-- These are the EXACT classes that your model detects
-- ============================================================================

/*
RECYCLABLE (16 classes):
  1.  aluminum can       → metal_aluminum    ✅
  2.  metal can          → metal             ✅
  3.  soda can           → metal_aluminum    ✅
  4.  beer can           → metal_aluminum    ✅
  5.  plastic bottle     → plastic_bottle    ✅
  6.  water bottle       → plastic_bottle    ✅
  7.  plastic container  → plastic           ✅
  8.  glass bottle       → glass_bottle      ✅
  9.  glass jar          → glass_jar         ✅
  10. cardboard box      → cardboard         ✅
  11. cardboard          → cardboard         ✅
  12. paper              → paper             ✅
  13. newspaper          → paper_newspaper   ✅
  14. plastic cup        → plastic_cup       ✅
  15. paper cup          → paper_cup         ✅
  16. coffee cup         → cup_mixed         ✅

NON-RECYCLABLE (4 classes):
  17. plastic bag        → plastic_bag       ❌
  18. styrofoam          → styrofoam         ❌
  19. food waste         → food_waste        ❌
  20. food scraps        → food_waste        ❌
*/

-- ============================================================================
-- MATERIAL CATEGORIES (15 types)
-- ============================================================================

/*
metal_aluminum      - Aluminum cans (soda, beer)
metal               - Other metal cans
plastic_bottle      - PET/HDPE bottles
plastic_bag         - Plastic bags (not recyclable)
plastic_cup         - Disposable plastic cups
plastic             - Other plastic containers
glass_bottle        - Glass bottles
glass_jar           - Glass jars
glass               - Other glass items
cardboard           - Cardboard boxes/sheets
paper               - Plain paper
paper_newspaper     - Newspapers
paper_cup           - Paper cups
cup_mixed           - Coffee cups (mixed material)
styrofoam           - Styrofoam (not recyclable)
food_waste          - Food scraps (not recyclable)
other               - Unknown materials
*/

-- ============================================================================
-- EXAMPLE INSERT QUERY
-- ============================================================================

-- Example: Someone disposed a plastic bottle
INSERT INTO disposal_events 
(timestamp, datetime, item_label, material_category, confidence, 
 is_recyclable, bin_id, location, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
VALUES 
(1706745600.123, '2024-02-01T10:30:00', 'plastic bottle', 'plastic_bottle', 
 0.95, 1, 'bin_sci_li_001', 'SciLi Entrance', 100.5, 150.0, 300.0, 450.5);

-- ============================================================================
-- USEFUL QUERIES
-- ============================================================================

-- Get recent 20 disposals
-- SELECT * FROM disposal_events ORDER BY timestamp DESC LIMIT 20;

-- Get recycling rate
-- SELECT 
--     COUNT(*) as total,
--     SUM(is_recyclable) as recyclable,
--     CAST(SUM(is_recyclable) AS FLOAT) / COUNT(*) as recycling_rate
-- FROM disposal_events;

-- Top 10 detected items
-- SELECT item_label, COUNT(*) as count 
-- FROM disposal_events 
-- GROUP BY item_label 
-- ORDER BY count DESC LIMIT 10;

-- Material breakdown
-- SELECT material_category, COUNT(*) as count 
-- FROM disposal_events 
-- GROUP BY material_category 
-- ORDER BY count DESC;

-- Today's disposals
-- SELECT COUNT(*) FROM disposal_events WHERE date(datetime) = date('now');

-- Class statistics (uses view)
-- SELECT * FROM class_stats;

-- High confidence detections only (>= 90%)
-- SELECT * FROM disposal_events WHERE confidence >= 0.90;

-- All aluminum items
-- SELECT * FROM disposal_events WHERE material_category = 'metal_aluminum';

-- All plastic bottles at specific location
-- SELECT * FROM disposal_events 
-- WHERE item_label = 'plastic bottle' AND location = 'SciLi Entrance';

-- Disposals per hour
-- SELECT 
--     strftime('%Y-%m-%d %H:00', datetime) as hour,
--     COUNT(*) as count
-- FROM disposal_events 
-- GROUP BY hour 
-- ORDER BY hour DESC;

-- Average confidence per class
-- SELECT item_label, AVG(confidence) as avg_conf
-- FROM disposal_events 
-- GROUP BY item_label 
-- ORDER BY avg_conf DESC;

-- ============================================================================
-- TEST DATA (for validation)
-- ============================================================================

-- Insert 3 test rows to verify setup
-- INSERT INTO disposal_events 
-- (timestamp, datetime, item_label, material_category, confidence, 
--  is_recyclable, bin_id, location, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
-- VALUES 
-- (1706745600, '2024-02-01T10:30:00', 'plastic bottle', 'plastic_bottle', 0.95, 1, 'bin_001', 'Test Location', 100, 150, 300, 450),
-- (1706745605, '2024-02-01T10:30:05', 'aluminum can', 'metal_aluminum', 0.92, 1, 'bin_001', 'Test Location', 120, 180, 280, 420),
-- (1706745610, '2024-02-01T10:30:10', 'plastic bag', 'plastic_bag', 0.88, 0, 'bin_001', 'Test Location', 150, 200, 350, 480);

-- Verify: Should show 3 rows
-- SELECT COUNT(*) FROM disposal_events;

-- ============================================================================
-- NOTES FOR DATABASE PERSON
-- ============================================================================

/*
CRITICAL REQUIREMENTS:
1. All 20 classes MUST be supported (see list above)
2. item_label is the exact string from CV model (case-sensitive in storage)
3. material_category follows the categorization logic (see DATABASE_HANDOFF.md)
4. is_recyclable: 1 = recyclable, 0 = trash (SQLite stores boolean as integer)
5. confidence is 0.0 to 1.0 (NOT percentage: 0.95, not 95)
6. timestamp is Unix timestamp in seconds with decimals
7. datetime is ISO 8601 format: YYYY-MM-DDTHH:MM:SS
8. bbox coordinates are relative to 640x640 frame
9. Primary key (id) auto-increments - never set manually

DATA FLOW:
1. CV detects item → extracts highest confidence detection
2. Lookup is_recyclable from class table
3. Categorize material_category using logic
4. Insert row into disposal_events
5. Trigger bin to open

FILES PROVIDED:
- schema.sql (this file) - Complete database schema
- DATABASE_HANDOFF.md - Implementation guide with all 20 classes
- SCHEMA_REFERENCE.md - Documentation
- data_logger.py - Python reference implementation
*/
