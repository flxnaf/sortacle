#!/usr/bin/env python3
"""
Data Logger for Sortacle - SQLite Backend
Logs disposal events to a SQLite database
"""

import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager


class DataLogger:
    """Logs disposal events to SQLite database"""
    
    def __init__(self, db_path='sortacle_data.db'):
        """
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create disposal_events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disposal_events (
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
        
        # Create class_stats view for easy querying
        cursor.execute('''
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
            ORDER BY count DESC
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ SQLite database initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for SQLite connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
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
        datetime_str = datetime.fromtimestamp(timestamp).isoformat()
        
        # Determine recyclability
        from recyclability import is_recyclable
        recyclable = is_recyclable(detection['label'])
        
        # Categorize material
        material_category = self._categorize_material(detection['label'])
        
        bbox = detection.get('bbox', [None, None, None, None])
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO disposal_events 
                (timestamp, datetime, item_label, material_category, confidence, is_recyclable, 
                 bin_id, location, image_path, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                datetime_str,
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
            event_id = cursor.lastrowid
            conn.commit()
        
        print(f"📊 LOGGED: {detection['label']} ({material_category}) "
              f"[{detection['confidence']:.0%}] - Recyclable: {recyclable} [ID: {event_id}]")
        
        return event_id
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent disposal events"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, datetime, item_label, material_category, confidence, 
                       is_recyclable, bin_id, location, image_path,
                       bbox_x1, bbox_y1, bbox_x2, bbox_y2
                FROM disposal_events
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'datetime': row[2],
                    'item_label': row[3],
                    'material_category': row[4],
                    'confidence': row[5],
                    'is_recyclable': bool(row[6]),
                    'bin_id': row[7],
                    'location': row[8],
                    'image_path': row[9],
                    'bbox': [row[10], row[11], row[12], row[13]] if row[10] is not None else None
                })
            
            return events
    
    def get_stats(self) -> Dict:
        """Get statistics about logged events"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total count
            cursor.execute('SELECT COUNT(*) FROM disposal_events')
            total = cursor.fetchone()[0]
            
            # Recyclable count
            cursor.execute('SELECT COUNT(*) FROM disposal_events WHERE is_recyclable = 1')
            recyclable = cursor.fetchone()[0]
            
            # Top items (specific classes)
            cursor.execute('''
                SELECT item_label, COUNT(*) as count 
                FROM disposal_events 
                GROUP BY item_label 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_items = dict(cursor.fetchall())
            
            # Material category breakdown
            cursor.execute('''
                SELECT material_category, COUNT(*) as count 
                FROM disposal_events 
                GROUP BY material_category 
                ORDER BY count DESC
            ''')
            material_breakdown = dict(cursor.fetchall())
            
            # Class statistics (from view)
            cursor.execute('SELECT * FROM class_stats LIMIT 20')
            class_stats = []
            for row in cursor.fetchall():
                class_stats.append({
                    'item_label': row[0],
                    'material_category': row[1],
                    'count': row[2],
                    'avg_confidence': row[3],
                    'recyclable_count': row[4],
                    'trash_count': row[5]
                })
            
            # Today's stats
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_timestamp = today_start.timestamp()
            
            cursor.execute('SELECT COUNT(*) FROM disposal_events WHERE timestamp >= ?', (today_timestamp,))
            today_count = cursor.fetchone()[0]
            
            return {
                'total_disposals': total,
                'recyclable_count': recyclable,
                'trash_count': total - recyclable,
                'recycling_rate': recyclable / total if total > 0 else 0,
                'top_items': top_items,
                'material_breakdown': material_breakdown,
                'class_stats': class_stats,
                'today_count': today_count
            }
    
    def get_class_breakdown(self) -> Dict:
        """Get detailed breakdown by detected class"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM class_stats')
            
            breakdown = []
            for row in cursor.fetchall():
                breakdown.append({
                    'class': row[0],
                    'material': row[1],
                    'count': row[2],
                    'avg_confidence': f"{row[3]:.1%}" if row[3] else "0%",
                    'recyclable': row[4],
                    'trash': row[5]
                })
            
            return {'classes': breakdown}
    
    def export_to_csv(self, output_path: str = 'disposal_data.csv'):
        """Export all data to CSV file"""
        import csv
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, datetime, item_label, material_category, 
                       confidence, is_recyclable, bin_id, location
                FROM disposal_events
                ORDER BY timestamp DESC
            ''')
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'timestamp', 'datetime', 'item_label', 'material_category',
                               'confidence', 'is_recyclable', 'bin_id', 'location'])
                writer.writerows(cursor.fetchall())
        
        print(f"✓ Data exported to {output_path}")


# Example usage
if __name__ == '__main__':
    # Test the logger
    logger = DataLogger(db_path='test_sortacle.db')
    
    # Simulate some disposal events
    test_detections = [
        {'label': 'plastic bottle', 'confidence': 0.95, 'bbox': [100, 150, 200, 400]},
        {'label': 'aluminum can', 'confidence': 0.88, 'bbox': [50, 100, 150, 300]},
        {'label': 'plastic bag', 'confidence': 0.76, 'bbox': [200, 250, 350, 450]},
        {'label': 'cardboard box', 'confidence': 0.82, 'bbox': [120, 180, 280, 420]},
    ]
    
    for det in test_detections:
        logger.log_disposal(det, bin_id='test_bin_001', location='Test Lab')
        time.sleep(0.5)
    
    # Get stats
    print("\n" + "="*50)
    stats = logger.get_stats()
    print("📊 Statistics:")
    print(f"  Total disposals: {stats['total_disposals']}")
    print(f"  Recycling rate: {stats['recycling_rate']:.1%}")
    print(f"  Today's count: {stats['today_count']}")
    print(f"  Top items: {stats['top_items']}")
    
    # Get recent events
    recent = logger.get_recent_events(limit=5)
    print(f"\n📋 Recent {len(recent)} events:")
    for event in recent:
        print(f"  - [{event['id']}] {event['item_label']} ({event['confidence']:.0%})")
    
    # Export to CSV
    print()
    logger.export_to_csv('test_export.csv')
