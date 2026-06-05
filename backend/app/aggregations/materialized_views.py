"""
MongoDB Aggregation Pipelines for Materialized Views
Creates cross-department views from Time Series telemetry data

Manufacturing Group Manufacturing - OEMPartner Assembly Line MES
"""
from datetime import datetime, timedelta
from typing import Optional

from pymongo.asynchronous.database import AsyncDatabase

# =============================================================================
# QUALITY DEPARTMENT VIEW (mv_quality_metrics)
# Purpose: Defect rates, temperature/vibration anomalies, quality scores
# Refresh: Core metrics every 15 minutes, analytics every 30 minutes
# =============================================================================

QUALITY_METRICS_CORE_PIPELINE = [
    # Stage 1: Filter to recent data (last 24 hours for real-time view)
    {
        "$match": {
            "timestamp": {"$gte": datetime.now() - timedelta(hours=24)}
        }
    },
    # Stage 2: Group by line, shift, and hour for granular analysis
    {
        "$group": {
            "_id": {
                "lineId": "$metadata.lineId",
                "lineName": "$metadata.lineName",
                "shiftId": "$shiftId",
                "hour": {"$hour": "$timestamp"},
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
            },
            "totalReadings": {"$sum": 1},
            "alertCount": {"$sum": {"$size": {"$ifNull": ["$alerts", []]}}},
            "criticalAlerts": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$alerts", []]},
                            "as": "alert",
                            "cond": {"$eq": ["$$alert.severity", "critical"]}
                        }
                    }
                }
            },
            "warningAlerts": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$alerts", []]},
                            "as": "alert",
                            "cond": {"$eq": ["$$alert.severity", "warning"]}
                        }
                    }
                }
            },
            "avgTemperature": {"$avg": "$metrics.temperature"},
            "maxTemperature": {"$max": "$metrics.temperature"},
            "avgVibration": {"$avg": "$metrics.vibration"},
            "maxVibration": {"$max": "$metrics.vibration"},
            "errorStatusCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
            },
            "runningStatusCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "running"]}, 1, 0]}
            },
            "anomalyCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.injected", True]}, 1, 0]}
            },
        }
    },
    # Stage 3: Calculate quality score (0-100)
    {
        "$addFields": {
            "qualityScore": {
                "$round": [
                    {
                        "$multiply": [
                            100,
                            {
                                "$subtract": [
                                    1,
                                    {
                                        "$divide": [
                                            {"$add": [
                                                {"$multiply": ["$criticalAlerts", 3]},
                                                {"$multiply": ["$warningAlerts", 1]},
                                                "$errorStatusCount"
                                            ]},
                                            {"$max": ["$totalReadings", 1]}
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    1
                ]
            },
            "defectRate": {
                "$round": [
                    {
                        "$multiply": [
                            100,
                            {"$divide": ["$alertCount", {"$max": ["$totalReadings", 1]}]}
                        ]
                    },
                    2
                ]
            }
        }
    },
    # Stage 4: Ensure quality score is within bounds
    {
        "$addFields": {
            "qualityScore": {
                "$max": [0, {"$min": [100, "$qualityScore"]}]
            }
        }
    },
    # Stage 5: Reshape for output
    {
        "$project": {
            "_id": 0,
            "lineId": "$_id.lineId",
            "lineName": "$_id.lineName",
            "shiftId": "$_id.shiftId",
            "date": "$_id.date",
            "hour": "$_id.hour",
            "metrics": {
                "totalReadings": "$totalReadings",
                "alertCount": "$alertCount",
                "criticalAlerts": "$criticalAlerts",
                "warningAlerts": "$warningAlerts",
                "anomalyCount": "$anomalyCount",
                "qualityScore": "$qualityScore",
                "defectRate": "$defectRate",
            },
            "temperature": {
                "avg": {"$round": ["$avgTemperature", 2]},
                "max": {"$round": ["$maxTemperature", 2]},
            },
            "vibration": {
                "avg": {"$round": ["$avgVibration", 3]},
                "max": {"$round": ["$maxVibration", 3]},
            },
            "status": {
                "errorCount": "$errorStatusCount",
                "runningCount": "$runningStatusCount",
            },
            "refreshedAt": {"$literal": datetime.now()},
            "viewType": {"$literal": "core"},
            "periodCovered": {
                "type": {"$literal": "rolling"},
                "hours": {"$literal": 24},
                "description": {"$literal": "Last 24 hours"},
            },
        }
    },
    # Stage 6: Sort for consistent output
    {
        "$sort": {"date": -1, "hour": -1, "lineId": 1}
    }
]

# Analytics pipeline - deeper analysis, less frequent refresh
QUALITY_METRICS_ANALYTICS_PIPELINE = [
    # Stage 1: Look at last 7 days for trend analysis
    {
        "$match": {
            "timestamp": {"$gte": datetime.now() - timedelta(days=7)}
        }
    },
    # Stage 2: Group by machine for detailed analysis
    {
        "$group": {
            "_id": {
                "machineId": "$metadata.machineId",
                "lineId": "$metadata.lineId",
                "lineName": "$metadata.lineName",
            },
            "totalReadings": {"$sum": 1},
            "totalAlerts": {"$sum": {"$size": {"$ifNull": ["$alerts", []]}}},
            "criticalAlerts": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$alerts", []]},
                            "as": "alert",
                            "cond": {"$eq": ["$$alert.severity", "critical"]}
                        }
                    }
                }
            },
            "tempAlerts": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$alerts", []]},
                            "as": "alert",
                            "cond": {"$in": ["$$alert.code", ["TEMP_HIGH", "TEMP_CRITICAL"]]}
                        }
                    }
                }
            },
            "vibAlerts": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$alerts", []]},
                            "as": "alert",
                            "cond": {"$in": ["$$alert.code", ["VIB_HIGH", "VIB_CRITICAL"]]}
                        }
                    }
                }
            },
            "avgTemp": {"$avg": "$metrics.temperature"},
            "stdDevTemp": {"$stdDevPop": "$metrics.temperature"},
            "avgVib": {"$avg": "$metrics.vibration"},
            "stdDevVib": {"$stdDevPop": "$metrics.vibration"},
            "anomalyCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.injected", True]}, 1, 0]}
            },
            # Count anomalies by type instead of storing full list
            "tempSpikeCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.type", "temperature_spike"]}, 1, 0]}
            },
            "vibAnomalyCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.type", "vibration_anomaly"]}, 1, 0]}
            },
            "powerSurgeCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.type", "power_surge"]}, 1, 0]}
            },
            "cycleCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.type", "cycle_degradation"]}, 1, 0]}
            },
            "bearingCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.type", "bearing_failure"]}, 1, 0]}
            },
        }
    },
    # Stage 3: Calculate machine health score
    {
        "$addFields": {
            "healthScore": {
                "$round": [
                    {
                        "$max": [
                            0,
                            {
                                "$subtract": [
                                    100,
                                    {
                                        "$add": [
                                            {"$multiply": [{"$divide": ["$criticalAlerts", {"$max": ["$totalReadings", 1]}]}, 500]},
                                            {"$multiply": [{"$divide": ["$totalAlerts", {"$max": ["$totalReadings", 1]}]}, 100]}
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    1
                ]
            },
            "alertRate": {
                "$round": [
                    {"$multiply": [{"$divide": ["$totalAlerts", {"$max": ["$totalReadings", 1]}]}, 100]},
                    2
                ]
            }
        }
    },
    # Stage 4: Project final shape
    {
        "$project": {
            "_id": 0,
            "machineId": "$_id.machineId",
            "lineId": "$_id.lineId",
            "lineName": "$_id.lineName",
            "totalReadings": 1,
            "alerts": {
                "total": "$totalAlerts",
                "critical": "$criticalAlerts",
                "temperature": "$tempAlerts",
                "vibration": "$vibAlerts",
            },
            "temperature": {
                "avg": {"$round": ["$avgTemp", 2]},
                "stdDev": {"$round": [{"$ifNull": ["$stdDevTemp", 0]}, 2]},
            },
            "vibration": {
                "avg": {"$round": ["$avgVib", 3]},
                "stdDev": {"$round": [{"$ifNull": ["$stdDevVib", 0]}, 3]},
            },
            "anomalies": {
                "count": "$anomalyCount",
                "byType": {
                    "temperatureSpike": "$tempSpikeCount",
                    "vibrationAnomaly": "$vibAnomalyCount",
                    "powerSurge": "$powerSurgeCount",
                    "cycleDegradation": "$cycleCount",
                    "bearingFailure": "$bearingCount",
                },
            },
            "healthScore": 1,
            "alertRate": 1,
            "refreshedAt": {"$literal": datetime.now()},
            "viewType": {"$literal": "analytics"},
            "periodCovered": {
                "type": {"$literal": "rolling"},
                "days": {"$literal": 7},
                "description": {"$literal": "Last 7 days"},
            },
        }
    },
    # Stage 5: Sort by health score (worst first for attention)
    {
        "$sort": {"healthScore": 1, "alertRate": -1}
    }
]

# Combined pipeline for quality metrics
QUALITY_METRICS_PIPELINE = QUALITY_METRICS_CORE_PIPELINE


# =============================================================================
# OPERATIONS/PLANNING VIEW (mv_production_stats)
# Purpose: Units produced, utilization rates, cycle times, downtime analysis
# Refresh: Core metrics every 15 minutes, analytics every 30 minutes
# =============================================================================

PRODUCTION_STATS_CORE_PIPELINE = [
    # Stage 1: Filter to recent data
    {
        "$match": {
            "timestamp": {"$gte": datetime.now() - timedelta(hours=24)}
        }
    },
    # Stage 2: Group by line and shift
    {
        "$group": {
            "_id": {
                "lineId": "$metadata.lineId",
                "lineName": "$metadata.lineName",
                "shiftId": "$shiftId",
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
            },
            "totalReadings": {"$sum": 1},
            "unitsProduced": {"$sum": "$metrics.outputCount"},
            "avgCycleTime": {"$avg": "$metrics.cycleTime"},
            "minCycleTime": {"$min": "$metrics.cycleTime"},
            "maxCycleTime": {"$max": "$metrics.cycleTime"},
            "avgPowerConsumption": {"$avg": "$metrics.powerConsumption"},
            "totalPowerConsumption": {"$sum": "$metrics.powerConsumption"},
            "runningCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "running"]}, 1, 0]}
            },
            "idleCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "idle"]}, 1, 0]}
            },
            "maintenanceCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "maintenance"]}, 1, 0]}
            },
            "errorCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
            },
            "machineCount": {"$addToSet": "$metadata.machineId"},
        }
    },
    # Stage 3: Calculate utilization and efficiency
    {
        "$addFields": {
            "machineCount": {"$size": "$machineCount"},
            "utilizationRate": {
                "$round": [
                    {
                        "$multiply": [
                            100,
                            {"$divide": ["$runningCount", {"$max": ["$totalReadings", 1]}]}
                        ]
                    },
                    1
                ]
            },
            "downtimeRate": {
                "$round": [
                    {
                        "$multiply": [
                            100,
                            {
                                "$divide": [
                                    {"$add": ["$maintenanceCount", "$errorCount"]},
                                    {"$max": ["$totalReadings", 1]}
                                ]
                            }
                        ]
                    },
                    1
                ]
            },
            "idleRate": {
                "$round": [
                    {
                        "$multiply": [
                            100,
                            {"$divide": ["$idleCount", {"$max": ["$totalReadings", 1]}]}
                        ]
                    },
                    1
                ]
            },
        }
    },
    # Stage 4: Project final shape
    {
        "$project": {
            "_id": 0,
            "lineId": "$_id.lineId",
            "lineName": "$_id.lineName",
            "shiftId": "$_id.shiftId",
            "date": "$_id.date",
            "machineCount": 1,
            "production": {
                "unitsProduced": "$unitsProduced",
                "targetUnits": {"$multiply": ["$machineCount", 480]},  # Target: 1 unit/min/machine for 8hr shift
            },
            "cycleTime": {
                "avg": {"$round": ["$avgCycleTime", 1]},
                "min": {"$round": ["$minCycleTime", 1]},
                "max": {"$round": ["$maxCycleTime", 1]},
            },
            "power": {
                "avgConsumption": {"$round": ["$avgPowerConsumption", 2]},
                "totalConsumption": {"$round": ["$totalPowerConsumption", 2]},
            },
            "utilization": {
                "rate": "$utilizationRate",
                "runningMinutes": "$runningCount",
                "idleMinutes": "$idleCount",
                "idleRate": "$idleRate",
            },
            "downtime": {
                "rate": "$downtimeRate",
                "maintenanceMinutes": "$maintenanceCount",
                "errorMinutes": "$errorCount",
            },
            "refreshedAt": {"$literal": datetime.now()},
            "viewType": {"$literal": "core"},
            "periodCovered": {
                "type": {"$literal": "rolling"},
                "hours": {"$literal": 24},
                "description": {"$literal": "Last 24 hours"},
            },
        }
    },
    # Stage 5: Sort
    {
        "$sort": {"date": -1, "lineId": 1, "shiftId": 1}
    }
]

PRODUCTION_STATS_ANALYTICS_PIPELINE = [
    # Stage 1: 7-day lookback for trends
    {
        "$match": {
            "timestamp": {"$gte": datetime.now() - timedelta(days=7)}
        }
    },
    # Stage 2: Daily aggregation per line
    {
        "$group": {
            "_id": {
                "lineId": "$metadata.lineId",
                "lineName": "$metadata.lineName",
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
            },
            "totalReadings": {"$sum": 1},
            "unitsProduced": {"$sum": "$metrics.outputCount"},
            "avgCycleTime": {"$avg": "$metrics.cycleTime"},
            "totalPower": {"$sum": "$metrics.powerConsumption"},
            "runningCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "running"]}, 1, 0]}
            },
            "downtimeCount": {
                "$sum": {
                    "$cond": [
                        {"$in": ["$status", ["maintenance", "error"]]},
                        1,
                        0
                    ]
                }
            },
        }
    },
    # Stage 3: Group by line for weekly summary
    {
        "$group": {
            "_id": {
                "lineId": "$_id.lineId",
                "lineName": "$_id.lineName",
            },
            "dailyStats": {
                "$push": {
                    "date": "$_id.date",
                    "units": "$unitsProduced",
                    "avgCycleTime": "$avgCycleTime",
                    "utilization": {
                        "$multiply": [
                            100,
                            {"$divide": ["$runningCount", {"$max": ["$totalReadings", 1]}]}
                        ]
                    }
                }
            },
            "totalUnits": {"$sum": "$unitsProduced"},
            "avgCycleTime": {"$avg": "$avgCycleTime"},
            "avgUtilization": {
                "$avg": {
                    "$multiply": [
                        100,
                        {"$divide": ["$runningCount", {"$max": ["$totalReadings", 1]}]}
                    ]
                }
            },
            "totalDowntime": {"$sum": "$downtimeCount"},
            "totalPower": {"$sum": "$totalPower"},
        }
    },
    # Stage 4: Calculate efficiency metrics
    {
        "$addFields": {
            "efficiency": {
                "oee": {
                    "$round": [
                        {"$min": [100, "$avgUtilization"]},
                        1
                    ]
                },
                "powerPerUnit": {
                    "$round": [
                        {"$divide": ["$totalPower", {"$max": ["$totalUnits", 1]}]},
                        3
                    ]
                }
            }
        }
    },
    # Stage 5: Project final shape
    {
        "$project": {
            "_id": 0,
            "lineId": "$_id.lineId",
            "lineName": "$_id.lineName",
            "weeklyStats": {
                "totalUnits": "$totalUnits",
                "avgCycleTime": {"$round": ["$avgCycleTime", 1]},
                "avgUtilization": {"$round": ["$avgUtilization", 1]},
                "totalDowntimeMinutes": "$totalDowntime",
                "totalPowerKwh": {"$round": [{"$divide": ["$totalPower", 60]}, 2]},
            },
            "efficiency": 1,
            "dailyTrend": "$dailyStats",
            "refreshedAt": {"$literal": datetime.now()},
            "viewType": {"$literal": "analytics"},
            "periodCovered": {
                "type": {"$literal": "rolling"},
                "days": {"$literal": 7},
                "description": {"$literal": "Last 7 days"},
            },
        }
    },
    {
        "$sort": {"lineId": 1}
    }
]

PRODUCTION_STATS_PIPELINE = PRODUCTION_STATS_CORE_PIPELINE


# =============================================================================
# REFRESH FUNCTIONS
# =============================================================================

async def refresh_quality_metrics(
    db: AsyncDatabase,
    pipeline_type: str = "core"
) -> dict:
    """
    Refresh the mv_quality_metrics materialized view

    Args:
        db: MongoDB database
        pipeline_type: "core" (15-min refresh) or "analytics" (30-min refresh)

    Returns:
        dict with refresh status and document count
    """
    source_collection = db["machine_telemetry"]
    target_collection = db["mv_quality_metrics"]

    # Select pipeline
    if pipeline_type == "analytics":
        pipeline = QUALITY_METRICS_ANALYTICS_PIPELINE.copy()
    else:
        pipeline = QUALITY_METRICS_CORE_PIPELINE.copy()

    # Update timestamp in pipeline (recreate with current time)
    pipeline[0]["$match"]["timestamp"]["$gte"] = (
        datetime.now() - timedelta(hours=24 if pipeline_type == "core" else 168)
    )

    # Use separate collections for core vs analytics to avoid index conflicts
    target_name = f"mv_quality_{pipeline_type}"
    
    # Add $merge stage with proper unique keys per collection type
    if pipeline_type == "core":
        merge_on = ["lineId", "date", "hour", "shiftId"]
    else:
        merge_on = ["machineId"]
    
    pipeline.append({
        "$merge": {
            "into": target_name,
            "on": merge_on,
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }
    })

    # Execute aggregation
    cursor = await source_collection.aggregate(pipeline)
    await cursor.to_list(length=None)

    # Get document count
    count = await db[target_name].count_documents({})

    return {
        "collection": target_name,
        "type": pipeline_type,
        "documentsRefreshed": count,
        "refreshedAt": datetime.now().isoformat()
    }


async def refresh_production_stats(
    db: AsyncDatabase,
    pipeline_type: str = "core"
) -> dict:
    """
    Refresh the mv_production_stats materialized view

    Args:
        db: MongoDB database
        pipeline_type: "core" (15-min refresh) or "analytics" (30-min refresh)

    Returns:
        dict with refresh status and document count
    """
    source_collection = db["machine_telemetry"]
    target_collection = db["mv_production_stats"]

    # Select pipeline
    if pipeline_type == "analytics":
        pipeline = PRODUCTION_STATS_ANALYTICS_PIPELINE.copy()
    else:
        pipeline = PRODUCTION_STATS_CORE_PIPELINE.copy()

    # Update timestamp in pipeline
    pipeline[0]["$match"]["timestamp"]["$gte"] = (
        datetime.now() - timedelta(hours=24 if pipeline_type == "core" else 168)
    )

    # Use separate collections for core vs analytics
    target_name = f"mv_production_{pipeline_type}"
    
    # Add $merge stage with proper unique keys
    if pipeline_type == "core":
        merge_on = ["lineId", "date", "shiftId"]
    else:
        merge_on = ["lineId"]
    
    pipeline.append({
        "$merge": {
            "into": target_name,
            "on": merge_on,
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }
    })

    # Execute aggregation
    cursor = await source_collection.aggregate(pipeline)
    await cursor.to_list(length=None)

    # Get document count
    count = await db[target_name].count_documents({})

    return {
        "collection": target_name,
        "type": pipeline_type,
        "documentsRefreshed": count,
        "refreshedAt": datetime.now().isoformat()
    }


async def refresh_all_views(db: AsyncDatabase) -> dict:
    """
    Refresh all materialized views (both core and analytics)

    Returns:
        dict with all refresh results
    """
    results = {
        "quality_core": await refresh_quality_metrics(db, "core"),
        "quality_analytics": await refresh_quality_metrics(db, "analytics"),
        "production_core": await refresh_production_stats(db, "core"),
        "production_analytics": await refresh_production_stats(db, "analytics"),
        "completedAt": datetime.now().isoformat()
    }

    return results
