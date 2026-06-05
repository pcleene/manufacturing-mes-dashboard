"""
Dashboard API Routes
Quality and Operations dashboard endpoints
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.database import MongoDB
from app.services.dashboard_service import DashboardService
from app.aggregations import refresh_all_views, refresh_quality_metrics, refresh_production_stats

router = APIRouter()


def get_dashboard_service() -> DashboardService:
    """Get dashboard service instance"""
    return DashboardService(MongoDB.get_database())


@router.get("/quality")
async def get_quality_dashboard(
    date: Optional[str] = Query(
        None,
        description="Filter by date (YYYY-MM-DD format)"
    ),
    line_id: Optional[str] = Query(
        None,
        description="Filter by line ID"
    ),
):
    """
    Get Quality Department dashboard data.

    Returns:
    - Overall quality score
    - Defect rates by production line
    - Alert summaries
    - Anomaly counts
    - Quality trend over time
    - Machine health scores
    """
    service = get_dashboard_service()
    return await service.get_quality_dashboard(date=date, line_id=line_id)


@router.get("/operations")
async def get_operations_dashboard(
    date: Optional[str] = Query(
        None,
        description="Filter by date (YYYY-MM-DD format)"
    ),
    line_id: Optional[str] = Query(
        None,
        description="Filter by line ID"
    ),
):
    """
    Get Operations/Planning Department dashboard data.

    Returns:
    - Total units produced vs target
    - Utilization rates by line
    - Cycle time analysis
    - Downtime breakdown (maintenance vs errors)
    - Production trend over time
    """
    service = get_dashboard_service()
    return await service.get_operations_dashboard(date=date, line_id=line_id)


@router.get("/anomalies")
async def get_anomaly_dashboard():
    """
    Get Anomaly Detection dashboard data.

    Returns:
    - Recent unacknowledged anomalies
    - Anomaly counts by type
    - Most affected machines
    """
    service = get_dashboard_service()
    return await service.get_anomaly_summary()


@router.get("/summary")
async def get_dashboard_summary():
    """
    Get combined summary for main dashboard (lightweight query).

    Returns key metrics from materialized views with minimal aggregation.
    """
    db = MongoDB.get_database()
    
    # Quick aggregation on small materialized view collections
    # Quality summary from mv_quality_core (96 docs max)
    quality_pipeline = [
        {"$group": {
            "_id": None,
            "totalReadings": {"$sum": "$metrics.totalReadings"},
            "totalAlerts": {"$sum": "$metrics.alertCount"},
            "criticalAlerts": {"$sum": "$metrics.criticalAlerts"},
            "weightedQuality": {"$sum": {"$multiply": ["$metrics.qualityScore", "$metrics.totalReadings"]}},
            "weightedDefect": {"$sum": {"$multiply": ["$metrics.defectRate", "$metrics.totalReadings"]}},
        }}
    ]
    quality_cursor = await db["mv_quality_core"].aggregate(quality_pipeline)
    quality_result = await quality_cursor.to_list(length=1)
    
    # Production summary from mv_production_core (20 docs max)
    prod_pipeline = [
        {"$group": {
            "_id": None,
            "totalUnits": {"$sum": "$production.unitsProduced"},
            "targetUnits": {"$sum": "$production.targetUnits"},
            "totalRunning": {"$sum": "$utilization.runningMinutes"},
            "totalReadings": {"$sum": {"$add": [
                "$utilization.runningMinutes",
                "$utilization.idleMinutes",
                "$downtime.maintenanceMinutes",
                "$downtime.errorMinutes"
            ]}},
            "weightedCycle": {"$sum": {"$multiply": ["$cycleTime.avg", "$production.unitsProduced"]}},
        }}
    ]
    prod_cursor = await db["mv_production_core"].aggregate(prod_pipeline)
    prod_result = await prod_cursor.to_list(length=1)
    
    # Anomaly count (quick count query)
    anomaly_count = await db["anomaly_detections"].count_documents({"acknowledged": False})
    
    # Extract values with defaults
    q = quality_result[0] if quality_result else {}
    p = prod_result[0] if prod_result else {}
    
    total_readings = q.get("totalReadings", 1) or 1
    total_units = p.get("totalUnits", 1) or 1
    total_prod_readings = p.get("totalReadings", 1) or 1
    
    return {
        "period": {
            "type": "rolling",
            "hours": 24,
            "description": "Last 24 hours (from materialized views)",
        },
        "quality": {
            "score": round(q.get("weightedQuality", 0) / total_readings, 1),
            "defectRate": round(q.get("weightedDefect", 0) / total_readings, 2),
            "criticalAlerts": q.get("criticalAlerts", 0),
        },
        "operations": {
            "unitsProduced": p.get("totalUnits", 0),
            "targetUnits": p.get("targetUnits", 0),
            "utilizationRate": round((p.get("totalRunning", 0) / total_prod_readings) * 100, 1),
            "avgCycleTime": round(p.get("weightedCycle", 0) / total_units, 1),
        },
        "anomalies": {
            "unacknowledged": anomaly_count,
        },
        "lastUpdated": datetime.now().isoformat(),
    }


@router.post("/views/refresh")
async def refresh_materialized_views(
    view: Optional[str] = Query(
        None,
        description="Specific view to refresh: 'quality' or 'production'. Leave empty for all."
    ),
    pipeline_type: str = Query(
        "core",
        description="Pipeline type: 'core' (15-min) or 'analytics' (30-min)"
    ),
):
    """
    Manually refresh materialized views.

    Use this to update dashboard data on-demand.
    In production, these would be scheduled:
    - Core pipelines: Every 15 minutes
    - Analytics pipelines: Every 30 minutes
    """
    db = MongoDB.get_database()

    if view == "quality":
        result = await refresh_quality_metrics(db, pipeline_type)
        return {"refreshed": [result]}
    elif view == "production":
        result = await refresh_production_stats(db, pipeline_type)
        return {"refreshed": [result]}
    else:
        result = await refresh_all_views(db)
        return {"refreshed": result}


@router.get("/lines")
async def get_assembly_lines():
    """
    Get list of assembly lines with summary stats.
    """
    db = MongoDB.get_database()
    machines_collection = db["machines"]

    pipeline = [
        {
            "$group": {
                "_id": "$lineId",
                "lineName": {"$first": "$lineName"},
                "machineCount": {"$sum": 1},
                "machineTypes": {"$addToSet": "$machineType"},
            }
        },
        {"$sort": {"_id": 1}}
    ]

    cursor = await machines_collection.aggregate(pipeline)
    lines = await cursor.to_list(length=10)

    return {
        "lines": [
            {
                "lineId": line["_id"],
                "lineName": line["lineName"],
                "machineCount": line["machineCount"],
                "machineTypes": line["machineTypes"],
            }
            for line in lines
        ]
    }
