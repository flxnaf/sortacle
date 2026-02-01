#!/usr/bin/env python3
"""
View and query Sortacle disposal data
"""

import argparse
from data_logger import DataLogger
from datetime import datetime, timedelta


def print_stats(logger):
    """Print overall statistics"""
    stats = logger.get_stats()
    
    print("\n" + "="*70)
    print("📊 SORTACLE STATISTICS")
    print("="*70)
    print(f"Total Disposals:      {stats['total_disposals']}")
    print(f"Recyclable Items:     {stats['recyclable_count']} ({stats['recycling_rate']:.1%})")
    print(f"Trash Items:          {stats['trash_count']}")
    print(f"Today's Count:        {stats['today_count']}")
    
    print(f"\n🏷️  Top Detected Classes:")
    for item, count in list(stats['top_items'].items())[:10]:
        print(f"  • {item}: {count}")
    
    print(f"\n♻️  Material Breakdown:")
    for material, count in stats['material_breakdown'].items():
        print(f"  • {material}: {count}")
    
    print("\n📋 Detailed Class Stats:")
    print("-" * 70)
    print(f"{'Class':<25} {'Material':<20} {'Count':<8} {'Avg Conf':<10}")
    print("-" * 70)
    for cls_stat in stats['class_stats'][:15]:
        print(f"{cls_stat['item_label']:<25} {cls_stat['material_category']:<20} "
              f"{cls_stat['count']:<8} {cls_stat['avg_confidence']:.0%}")
    print("="*70)


def print_recent(logger, limit=20):
    """Print recent disposal events"""
    events = logger.get_recent_events(limit=limit)
    
    print(f"\n📋 Recent {len(events)} Disposals:")
    print("-" * 110)
    print(f"{'ID':<6} {'DateTime':<20} {'Item':<20} {'Material':<18} {'Conf':<6} {'Recyclable':<10} {'Bin'}")
    print("-" * 110)
    
    for event in events:
        dt = datetime.fromisoformat(event['datetime']).strftime('%Y-%m-%d %H:%M:%S')
        recyclable = "✓ Yes" if event['is_recyclable'] else "✗ No"
        conf = f"{event['confidence']:.0%}"
        material = event.get('material_category', 'unknown')
        
        print(f"{event['id']:<6} {dt:<20} {event['item_label']:<20} "
              f"{material:<18} {conf:<6} {recyclable:<10} {event['bin_id']}")
    
    print("-" * 110)


def export_data(logger, output_path):
    """Export data to CSV"""
    logger.export_to_csv(output_path)
    print(f"\n✓ Data exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='View Sortacle disposal data')
    parser.add_argument('--db', type=str, default='sortacle_data.db', 
                       help='Database file path')
    parser.add_argument('--stats', action='store_true', 
                       help='Show statistics')
    parser.add_argument('--recent', type=int, nargs='?', const=20, 
                       help='Show recent N events (default: 20)')
    parser.add_argument('--export', type=str, metavar='FILE', 
                       help='Export data to CSV file')
    parser.add_argument('--classes', action='store_true',
                       help='Show detailed class breakdown')
    parser.add_argument('--all', action='store_true', 
                       help='Show stats and recent events')
    
    args = parser.parse_args()
    
    # Create logger instance
    logger = DataLogger(db_path=args.db)
    
    # If no args, show everything
    if not any([args.stats, args.recent is not None, args.export, args.classes, args.all]):
        args.all = True
    
    # Execute commands
    if args.stats or args.all:
        print_stats(logger)
    
    if args.classes:
        breakdown = logger.get_class_breakdown()
        print("\n🏷️  DETECTED CLASSES BREAKDOWN")
        print("="*70)
        print(f"{'Class':<25} {'Material':<18} {'Count':<8} {'Avg Conf':<12} {'♻️':<6} {'🗑️'}")
        print("="*70)
        for cls in breakdown['classes']:
            print(f"{cls['class']:<25} {cls['material']:<18} {cls['count']:<8} "
                  f"{cls['avg_confidence']:<12} {cls['recyclable']:<6} {cls['trash']}")
        print("="*70)
    
    if args.recent is not None or args.all:
        limit = args.recent if args.recent is not None else 20
        print_recent(logger, limit)
    
    if args.export:
        export_data(logger, args.export)


if __name__ == '__main__':
    main()
