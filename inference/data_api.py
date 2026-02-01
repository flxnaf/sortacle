#!/usr/bin/env python3
"""
Data API Server for Sortacle
Serves disposal data from SQLite database via REST API
Website can fetch statistics and recent events
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from data_logger import DataLogger
from typing import Optional
import uvicorn

app = FastAPI(title="Sortacle Data API", version="1.0.0")

# Enable CORS so website can access API from different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your website domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data logger
logger = DataLogger(db_path='sortacle_data.db')


@app.get("/")
def root():
    """API health check"""
    return {
        "service": "Sortacle Data API",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/api/stats")
def get_stats():
    """
    Get overall statistics
    
    Returns:
        - total_disposals: Total items sorted
        - recyclable_count: Number of recyclable items
        - trash_count: Number of trash items
        - recycling_rate: Percentage recycled (0-1)
        - top_items: Dict of most common items
        - material_breakdown: Dict of material categories
        - today_count: Items sorted today
    """
    try:
        stats = logger.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recent")
def get_recent_events(limit: int = 50):
    """
    Get recent disposal events
    
    Args:
        limit: Number of recent events to return (default 50, max 500)
    
    Returns:
        List of disposal events with timestamps, items, confidence, etc.
    """
    try:
        if limit > 500:
            limit = 500
        events = logger.get_recent_events(limit=limit)
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/classes")
def get_class_breakdown():
    """
    Get detailed breakdown by detected class
    
    Returns:
        List of classes with counts, avg confidence, recyclable vs trash
    """
    try:
        breakdown = logger.get_class_breakdown()
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recycling-rate")
def get_recycling_rate():
    """
    Get simple recycling rate (for dashboard gauge)
    
    Returns:
        - rate: Recycling rate (0-1)
        - recyclable_count: Number of recyclable items
        - total_count: Total items sorted
    """
    try:
        stats = logger.get_stats()
        return {
            "rate": stats['recycling_rate'],
            "recyclable_count": stats['recyclable_count'],
            "trash_count": stats['trash_count'],
            "total_count": stats['total_disposals']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/today")
def get_today_stats():
    """
    Get today's statistics only
    
    Returns:
        Count of items sorted today
    """
    try:
        stats = logger.get_stats()
        return {
            "today_count": stats['today_count'],
            "today_recyclable": stats.get('today_recyclable', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live")
def get_live_count():
    """
    Get live counter for real-time display
    Lightweight endpoint for frequent polling
    
    Returns:
        - total: Total items sorted (all time)
        - today: Items sorted today
        - rate: Current recycling rate
    """
    try:
        stats = logger.get_stats()
        return {
            "total": stats['total_disposals'],
            "today": stats['today_count'],
            "rate": stats['recycling_rate'],
            "recyclable": stats['recyclable_count'],
            "trash": stats['trash_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting Sortacle Data API Server")
    print("📊 Serving data from: sortacle_data.db")
    print("🌐 API will be available at: http://0.0.0.0:8001")
    print("\nEndpoints:")
    print("  GET /api/stats          - Overall statistics")
    print("  GET /api/recent?limit=N - Recent N events")
    print("  GET /api/classes        - Class breakdown")
    print("  GET /api/recycling-rate - Recycling rate")
    print("  GET /api/live           - Live counter (for polling)")
    print("  GET /api/today          - Today's stats")
    print("\n")
    
    # Run on port 8001 (different from inference server on 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)
