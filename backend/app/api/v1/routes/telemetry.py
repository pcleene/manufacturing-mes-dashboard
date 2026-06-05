"""
Telemetry API Routes
Raw telemetry data access for engineers
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.database import (
    get_telemetry_collection,
    get_machines_collection,
)
from app.utils.objectid import serialize_docs, serialize_doc

router = APIRouter()


@router.get("")
async def get_telemetry(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for query (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for query (ISO format)"
    ),
    machine_id: Optional[str] = Query(
        None,
        description="Filter by machine ID (e.g., WLD-001)"
    ),
    line_id: Optional[str] = Query(
        None,
        description="Filter by line ID (e.g., LINE-1)"
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status (running, idle, maintenance, error)"
    ),
    has_alerts: Optional[bool] = Query(
        None,
        description="Filter for readings with alerts"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
):
    """
    Query raw telemetry data from time series collection.

    Supports filtering by date range, machine, line, and status.
    Returns paginated results sorted by timestamp descending.
    """
    collection = get_telemetry_collection()

    # Build query filter
    query = {}

    # Date range filter
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    else:
        # Default to last 24 hours
        query["timestamp"] = {"$gte": datetime.now() - timedelta(hours=24)}

    # Machine filter
    if machine_id:
        query["metadata.machineId"] = machine_id

    # Line filter
    if line_id:
        query["metadata.lineId"] = line_id

    # Status filter
    if status:
        query["status"] = status

    # Alerts filter
    if has_alerts is True:
        query["alerts.0"] = {"$exists": True}
    elif has_alerts is False:
        query["alerts"] = {"$size": 0}

    # Execute query
    cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    documents = await cursor.to_list(length=limit)

    # Get total count for pagination
    total_count = await collection.count_documents(query)

    return {
        "data": serialize_docs(documents),
        "pagination": {
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "hasMore": (skip + len(documents)) < total_count,
        },
        "query": {
            "startDate": start_date.isoformat() if start_date else None,
            "endDate": end_date.isoformat() if end_date else None,
            "machineId": machine_id,
            "lineId": line_id,
            "status": status,
        }
    }


@router.get("/latest")
async def get_latest_telemetry(
    machine_id: Optional[str] = Query(
        None,
        description="Filter by machine ID"
    ),
    line_id: Optional[str] = Query(
        None,
        description="Filter by line ID"
    ),
):
    """
    Get the latest telemetry reading for each machine.

    Useful for real-time dashboard updates.
    """
    collection = get_telemetry_collection()

    # Build aggregation pipeline for latest reading per machine
    pipeline = [
        {"$sort": {"timestamp": -1}},
    ]

    # Add filters if provided
    if machine_id:
        pipeline.insert(0, {"$match": {"metadata.machineId": machine_id}})
    elif line_id:
        pipeline.insert(0, {"$match": {"metadata.lineId": line_id}})

    # Group by machine to get latest
    pipeline.extend([
        {
            "$group": {
                "_id": "$metadata.machineId",
                "latestDoc": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$latestDoc"}},
        {"$sort": {"metadata.lineId": 1, "metadata.machineId": 1}},
    ])

    cursor = await collection.aggregate(pipeline)
    documents = await cursor.to_list(length=100)

    return {
        "data": serialize_docs(documents),
        "count": len(documents),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/machines")
async def get_machines(
    line_id: Optional[str] = Query(None, description="Filter by line ID"),
):
    """
    Get machine reference data.

    Returns machine specifications and alert thresholds.
    """
    collection = get_machines_collection()

    query = {}
    if line_id:
        query["lineId"] = line_id

    documents = await collection.find(query).sort("lineId", 1).to_list(length=100)

    return {
        "data": serialize_docs(documents),
        "count": len(documents),
    }


@router.get("/machines/{machine_id}")
async def get_machine(machine_id: str):
    """
    Get details for a specific machine.
    """
    collection = get_machines_collection()

    document = await collection.find_one({"machineId": machine_id})

    if not document:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    return serialize_doc(document)


@router.get("/stats")
async def get_telemetry_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    line_id: Optional[str] = Query(None, description="Filter by line ID"),
):
    """
    Get aggregated statistics for telemetry data.

    Returns min, max, avg for key metrics over the specified time window.
    """
    collection = get_telemetry_collection()

    # Build match filter
    match_filter = {
        "timestamp": {"$gte": datetime.now() - timedelta(hours=hours)}
    }
    if machine_id:
        match_filter["metadata.machineId"] = machine_id
    if line_id:
        match_filter["metadata.lineId"] = line_id

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "avgTemperature": {"$avg": "$metrics.temperature"},
                "minTemperature": {"$min": "$metrics.temperature"},
                "maxTemperature": {"$max": "$metrics.temperature"},
                "avgVibration": {"$avg": "$metrics.vibration"},
                "minVibration": {"$min": "$metrics.vibration"},
                "maxVibration": {"$max": "$metrics.vibration"},
                "avgPower": {"$avg": "$metrics.powerConsumption"},
                "totalPower": {"$sum": "$metrics.powerConsumption"},
                "avgCycleTime": {"$avg": "$metrics.cycleTime"},
                "totalOutput": {"$sum": "$metrics.outputCount"},
                "alertCount": {"$sum": {"$size": {"$ifNull": ["$alerts", []]}}},
                "errorCount": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
            }
        }
    ]

    cursor = await collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return {
            "message": "No data found for specified filters",
            "hours": hours,
            "machineId": machine_id,
            "lineId": line_id,
        }

    stats = result[0]
    del stats["_id"]

    # Round values
    for key in ["avgTemperature", "minTemperature", "maxTemperature",
                "avgVibration", "minVibration", "maxVibration",
                "avgPower", "totalPower", "avgCycleTime"]:
        if stats.get(key) is not None:
            stats[key] = round(stats[key], 2)

    return {
        "stats": stats,
        "period": {
            "hours": hours,
            "start": (datetime.now() - timedelta(hours=hours)).isoformat(),
            "end": datetime.now().isoformat(),
        },
        "filters": {
            "machineId": machine_id,
            "lineId": line_id,
        }
    }


@router.get("/anomalies")
async def get_anomalies(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    line_id: Optional[str] = Query(None, description="Filter by line ID"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type"),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Get telemetry readings flagged as anomalies.

    These are readings with injected anomalies for ML training,
    or detected by the anomaly detection pipeline.
    """
    collection = get_telemetry_collection()

    query = {
        "timestamp": {"$gte": datetime.now() - timedelta(hours=hours)},
        "anomaly.injected": True,
    }

    if line_id:
        query["metadata.lineId"] = line_id
    if anomaly_type:
        query["anomaly.type"] = anomaly_type

    documents = await collection.find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)

    # Group by anomaly type for summary
    type_pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$anomaly.type",
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}}
    ]
    type_cursor = await collection.aggregate(type_pipeline)
    type_summary = await type_cursor.to_list(length=10)

    return {
        "data": serialize_docs(documents),
        "count": len(documents),
        "byType": serialize_docs(type_summary),
        "period": {
            "hours": hours,
            "start": (datetime.now() - timedelta(hours=hours)).isoformat(),
        }
    }
