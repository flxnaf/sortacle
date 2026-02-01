#!/usr/bin/env python3
"""
Cloud Data Logger for Sortacle - PostgreSQL Backend
Logs disposal events to a PostgreSQL database (cloud)
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
import os

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
    POSTGRES_AVAILABLE = False


class CloudDataLogger:
    """Logs disposal events to PostgreSQL database"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Args:
            db_url: PostgreSQL connection URL 
                   Format: postgresql://user:password@host:port/database
                   Or set environment variable: DATABASE_URL
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")
        
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError(
                "Database URL not provided. Set DATABASE_URL environment variable or pass db_url parameter.\n"
                "Example: postgresql://sortacle_user:password@vultr_ip:5432/sortacle_db"
            )
        
        self._test_connection()
        self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def _test_connection(self):
        """Test database connection"""
        try:
            conn = self._get_connection()
            conn.close()
            print(f"✅ Connected to PostgreSQL database")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")
    
    def _init_database(self):
        """Initialize PostgreSQL database with schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create disposal_events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS disposal_events (
                    id SERIAL PRIMARY KEY,
                    timestamp DOUBLE PRECISION NOT NULL,
                    datetime TIMESTAMP NOT NULL,
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
                    bbox_y2 REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON disposal_events(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_datetime 
                ON disposal_events(datetime DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_item_label 
                ON disposal_events(item_label)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_material_category 
                ON disposal_events(material_category)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_bin_id 
                ON disposal_events(bin_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_location 
                ON disposal_events(location)
            ''')
            
            # Create view for class statistics
            cursor.execute('''
                CREATE OR REPLACE VIEW class_stats AS
                SELECT 
                    item_label,
                    material_category,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN is_recyclable THEN 1 ELSE 0 END) as recyclable_count,
                    SUM(CASE WHEN NOT is_recyclable THEN 1 ELSE 0 END) as trash_count
                FROM disposal_events
                GROUP BY item_label, material_category
                ORDER BY count DESC
            ''')
            
            conn.commit()
            print(f"✅ PostgreSQL database schema initialized")
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def _categorize_material(self, label: str) -> str:
        """Categorize item into material type"""
        label_lower = label.lower()
        
        # Metal
        if any(word in label_lower for word in ['aluminum', 'metal', 'can', 'soda', 'beer']):
            if 'aluminum' in label_lower or 'soda' in label_lower or 'beer' in label_lower:
                return 'metal_aluminum'
            return 'metal'
        
        # Plastic
        if any(word in label_lower for word in ['plastic', 'bottle', 'water bottle', 'container']):
            if 'bottle' in label_lower:
                return 'plastic_bottle'
            if 'bag' in label_lower:
                return 'plastic_bag'
            if 'cup' in label_lower:
                return 'plastic_cup'
            return 'plastic'
        
        # Glass
        if 'glass' in label_lower:
            if 'bottle' in label_lower:
                return 'glass_bottle'
            if 'jar' in label_lower:
                return 'glass_jar'
            return 'glass'
        
        # Paper/Cardboard
        if any(word in label_lower for word in ['cardboard', 'paper', 'newspaper']):
            if 'cardboard' in label_lower:
                return 'cardboard'
            if 'newspaper' in label_lower:
                return 'paper_newspaper'
            if 'cup' in label_lower:
                return 'paper_cup'
            return 'paper'
        
        # Cup (if not already categorized)
        if 'cup' in label_lower or 'coffee' in label_lower:
            return 'cup_mixed'
        
        # Other
        if 'styrofoam' in label_lower:
            return 'styrofoam'
        if 'food' in label_lower:
            return 'food_waste'
        
        return 'other'
    
    def log_disposal(self, detection: Dict, bin_id: str = 'bin_001', 
                     location: str = 'unknown', image_path: Optional[str] = None):
        """
        Log a disposal event
        
        Args:
            detection: Detection dict with 'label', 'confidence', 'bbox'
            bin_id: Unique identifier for the bin
            location: Location of the bin (e.g., "Engineering Quad", "SciLi")
            image_path: Optional path to saved image snapshot
        
        Returns:
            Event ID (database row id)
        """
        timestamp = time.time()
        datetime_obj = datetime.fromtimestamp(timestamp)
        
        # Determine recyclability
        from recyclability import is_recyclable
        recyclable = is_recyclable(detection['label'])
        
        # Categorize material
        material_category = self._categorize_material(detection['label'])
        
        bbox = detection.get('bbox', [None, None, None, None])
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO disposal_events 
                (timestamp, datetime, item_label, material_category, confidence, is_recyclable, 
                 bin_id, location, image_path, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                timestamp,
                datetime_obj,
                detection['label'],
                material_category,
                detection['confidence'],
                recyclable,
                bin_id,
                location,
                image_path,
                bbox[0] if len(bbox) > 0 else None,
                bbox[1] if len(bbox) > 1 else None,
                bbox[2] if len(bbox) > 2 else None,
                bbox[3] if len(bbox) > 3 else None
            ))
            
            event_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"📊 LOGGED TO CLOUD: {detection['label']} ({material_category}) "
                  f"[{detection['confidence']:.0%}] - Recyclable: {recyclable} [ID: {event_id}]")
            
            return event_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to log to cloud database: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent disposal events"""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT id, timestamp, datetime, item_label, material_category, confidence, 
                       is_recyclable, bin_id, location, image_path,
                       bbox_x1, bbox_y1, bbox_x2, bbox_y2
                FROM disposal_events
                ORDER BY timestamp DESC
                LIMIT %s
            ''', (limit,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'datetime': row['datetime'].isoformat() if row['datetime'] else None,
                    'item_label': row['item_label'],
                    'material_category': row['material_category'],
                    'confidence': row['confidence'],
                    'is_recyclable': bool(row['is_recyclable']),
                    'bin_id': row['bin_id'],
                    'location': row['location'],
                    'image_path': row['image_path'],
                    'bbox': [row['bbox_x1'], row['bbox_y1'], row['bbox_x2'], row['bbox_y3']] 
                            if row['bbox_x1'] is not None else None
                })
            
            return events
            
        finally:
            cursor.close()
            conn.close()
    
    def get_stats(self) -> Dict:
        """Get statistics about logged events"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Total count
            cursor.execute('SELECT COUNT(*) FROM disposal_events')
            total = cursor.fetchone()[0]
            
            # Recyclable count
            cursor.execute('SELECT COUNT(*) FROM disposal_events WHERE is_recyclable = TRUE')
            recyclable = cursor.fetchone()[0]
            
            # Top items
            cursor.execute('''
                SELECT item_label, COUNT(*) as count 
                FROM disposal_events 
                GROUP BY item_label 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_items = dict(cursor.fetchall())
            
            # Material breakdown
            cursor.execute('''
                SELECT material_category, COUNT(*) as count 
                FROM disposal_events 
                GROUP BY material_category 
                ORDER BY count DESC
            ''')
            material_breakdown = dict(cursor.fetchall())
            
            # Today's stats
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            cursor.execute(
                'SELECT COUNT(*) FROM disposal_events WHERE datetime >= %s',
                (today_start,)
            )
            today_count = cursor.fetchone()[0]
            
            return {
                'total_disposals': total,
                'recyclable_count': recyclable,
                'trash_count': total - recyclable,
                'recycling_rate': recyclable / total if total > 0 else 0,
                'top_items': top_items,
                'material_breakdown': material_breakdown,
                'today_count': today_count
            }
            
        finally:
            cursor.close()
            conn.close()


# Example usage
if __name__ == '__main__':
    import sys
    
    # Check if DATABASE_URL is set
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Set it like this:")
        print("export DATABASE_URL='postgresql://sortacle_user:password@vultr_ip:5432/sortacle_db'")
        sys.exit(1)
    
    # Test the logger
    logger = CloudDataLogger(db_url=db_url)
    
    # Simulate a disposal event
    test_detection = {
        'label': 'aluminum can',
        'confidence': 0.92,
        'bbox': [100, 150, 200, 400]
    }
    
    event_id = logger.log_disposal(
        test_detection,
        bin_id='test_bin_001',
        location='Test Location'
    )
    
    print(f"\n✅ Test event logged with ID: {event_id}")
    
    # Get stats
    stats = logger.get_stats()
    print(f"\n📊 Statistics:")
    print(f"  Total disposals: {stats['total_disposals']}")
    print(f"  Recycling rate: {stats['recycling_rate']:.1%}")
