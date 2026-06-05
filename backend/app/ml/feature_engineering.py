"""
Feature Engineering Pipeline for Anomaly Detection
Transforms MongoDB Time Series data into ML-ready features

Manufacturing Group Manufacturing - OEMPartner Assembly Line MES
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import os

from pymongo import AsyncMongoClient
from dotenv import load_dotenv

load_dotenv()

# Feature store schema for ML training
FEATURE_SCHEMA = {
    "machineId": str,
    "lineId": str,
    "timestamp": datetime,
    "windowStart": datetime,
    "windowEnd": datetime,
    # Raw features
    "temperature": float,
    "vibration": float,
    "powerConsumption": float,
    "cycleTime": float,
    # Statistical features (rolling window)
    "tempMean": float,
    "tempStd": float,
    "tempMin": float,
    "tempMax": float,
    "vibMean": float,
    "vibStd": float,
    "vibMin": float,
    "vibMax": float,
    "powerMean": float,
    "powerStd": float,
    "cycleMean": float,
    "cycleStd": float,
    # Derived features
    "tempZScore": float,  # How many std devs from mean
    "vibZScore": float,
    "powerZScore": float,
    "cycleZScore": float,
    "alertCount": int,
    "errorRate": float,
    # Labels (for supervised learning from injected anomalies)
    "isAnomaly": bool,
    "anomalyType": Optional[str],
}

# Aggregation pipeline to create feature store
FEATURE_STORE_PIPELINE = [
    # Stage 1: Filter to recent data for feature extraction
    {
        "$match": {
            "timestamp": {"$gte": datetime.now() - timedelta(days=7)}
        }
    },
    # Stage 2: Sort by machine and time for window calculations
    {
        "$sort": {"metadata.machineId": 1, "timestamp": 1}
    },
    # Stage 3: Group into 5-minute windows per machine
    {
        "$group": {
            "_id": {
                "machineId": "$metadata.machineId",
                "lineId": "$metadata.lineId",
                "window": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": "minute",
                        "binSize": 5
                    }
                }
            },
            "readings": {"$push": "$$ROOT"},
            "readingCount": {"$sum": 1},
            # Temperature stats
            "tempMean": {"$avg": "$metrics.temperature"},
            "tempStd": {"$stdDevPop": "$metrics.temperature"},
            "tempMin": {"$min": "$metrics.temperature"},
            "tempMax": {"$max": "$metrics.temperature"},
            # Vibration stats
            "vibMean": {"$avg": "$metrics.vibration"},
            "vibStd": {"$stdDevPop": "$metrics.vibration"},
            "vibMin": {"$min": "$metrics.vibration"},
            "vibMax": {"$max": "$metrics.vibration"},
            # Power stats
            "powerMean": {"$avg": "$metrics.powerConsumption"},
            "powerStd": {"$stdDevPop": "$metrics.powerConsumption"},
            # Cycle time stats
            "cycleMean": {"$avg": "$metrics.cycleTime"},
            "cycleStd": {"$stdDevPop": "$metrics.cycleTime"},
            # Alert counts
            "alertCount": {"$sum": {"$size": {"$ifNull": ["$alerts", []]}}},
            "errorCount": {
                "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
            },
            # Anomaly labels
            "anomalyCount": {
                "$sum": {"$cond": [{"$eq": ["$anomaly.injected", True]}, 1, 0]}
            },
            "anomalyTypes": {
                "$push": {
                    "$cond": [
                        {"$eq": ["$anomaly.injected", True]},
                        "$anomaly.type",
                        "$$REMOVE"
                    ]
                }
            },
            # Keep last reading for current values
            "lastReading": {"$last": "$$ROOT"},
        }
    },
    # Stage 4: Calculate derived features
    {
        "$addFields": {
            # Z-scores (standardized values)
            "tempZScore": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$tempStd", 0]}, 0]},
                    {
                        "$divide": [
                            {"$subtract": ["$lastReading.metrics.temperature", "$tempMean"]},
                            "$tempStd"
                        ]
                    },
                    0
                ]
            },
            "vibZScore": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$vibStd", 0]}, 0]},
                    {
                        "$divide": [
                            {"$subtract": ["$lastReading.metrics.vibration", "$vibMean"]},
                            "$vibStd"
                        ]
                    },
                    0
                ]
            },
            "powerZScore": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$powerStd", 0]}, 0]},
                    {
                        "$divide": [
                            {"$subtract": ["$lastReading.metrics.powerConsumption", "$powerMean"]},
                            "$powerStd"
                        ]
                    },
                    0
                ]
            },
            "cycleZScore": {
                "$cond": [
                    {"$gt": [{"$ifNull": ["$cycleStd", 0]}, 0]},
                    {
                        "$divide": [
                            {"$subtract": ["$lastReading.metrics.cycleTime", "$cycleMean"]},
                            "$cycleStd"
                        ]
                    },
                    0
                ]
            },
            "errorRate": {
                "$divide": ["$errorCount", {"$max": ["$readingCount", 1]}]
            },
            "isAnomaly": {"$gt": ["$anomalyCount", 0]},
            "primaryAnomalyType": {"$arrayElemAt": ["$anomalyTypes", 0]},
        }
    },
    # Stage 5: Project final feature store schema
    {
        "$project": {
            "_id": 0,
            "machineId": "$_id.machineId",
            "lineId": "$_id.lineId",
            "windowStart": "$_id.window",
            "windowEnd": {
                "$dateAdd": {
                    "startDate": "$_id.window",
                    "unit": "minute",
                    "amount": 5
                }
            },
            "timestamp": "$lastReading.timestamp",
            # Raw features (last reading in window)
            "temperature": "$lastReading.metrics.temperature",
            "vibration": "$lastReading.metrics.vibration",
            "powerConsumption": "$lastReading.metrics.powerConsumption",
            "cycleTime": "$lastReading.metrics.cycleTime",
            # Statistical features
            "tempMean": {"$round": ["$tempMean", 2]},
            "tempStd": {"$round": [{"$ifNull": ["$tempStd", 0]}, 2]},
            "tempMin": {"$round": ["$tempMin", 2]},
            "tempMax": {"$round": ["$tempMax", 2]},
            "vibMean": {"$round": ["$vibMean", 3]},
            "vibStd": {"$round": [{"$ifNull": ["$vibStd", 0]}, 3]},
            "vibMin": {"$round": ["$vibMin", 3]},
            "vibMax": {"$round": ["$vibMax", 3]},
            "powerMean": {"$round": ["$powerMean", 2]},
            "powerStd": {"$round": [{"$ifNull": ["$powerStd", 0]}, 2]},
            "cycleMean": {"$round": ["$cycleMean", 1]},
            "cycleStd": {"$round": [{"$ifNull": ["$cycleStd", 0]}, 1]},
            # Derived features
            "tempZScore": {"$round": ["$tempZScore", 3]},
            "vibZScore": {"$round": ["$vibZScore", 3]},
            "powerZScore": {"$round": ["$powerZScore", 3]},
            "cycleZScore": {"$round": ["$cycleZScore", 3]},
            "alertCount": 1,
            "errorRate": {"$round": ["$errorRate", 4]},
            "readingCount": 1,
            # Labels
            "isAnomaly": 1,
            "anomalyType": "$primaryAnomalyType",
            # Metadata
            "createdAt": {"$literal": datetime.now()},
        }
    },
    # Stage 6: Sort by time
    {
        "$sort": {"machineId": 1, "windowStart": 1}
    }
]


async def populate_feature_store(
    mongodb_uri: str = None,
    database_name: str = None,
    days: int = 7
) -> dict:
    """
    Populate feature store collection from time series data.

    This extracts features from raw telemetry for ML model training.

    Args:
        mongodb_uri: MongoDB connection string
        database_name: Database name
        days: Number of days of data to process

    Returns:
        dict with processing statistics
    """
    uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>")
    db_name = database_name or os.getenv("MONGODB_DATABASE", "OEMPartner_mes_demo")

    client = AsyncMongoClient(uri)
    db = client[db_name]

    try:
        # Update pipeline with correct time window
        pipeline = FEATURE_STORE_PIPELINE.copy()
        pipeline[0]["$match"]["timestamp"]["$gte"] = datetime.now() - timedelta(days=days)

        # Add merge stage to write to feature store
        pipeline.append({
            "$merge": {
                "into": "feature_store",
                "on": ["machineId", "windowStart"],
                "whenMatched": "replace",
                "whenNotMatched": "insert"
            }
        })

        # Execute aggregation
        source = db["machine_telemetry"]
        cursor = await source.aggregate(pipeline)
        await cursor.to_list(length=None)

        # Get stats
        feature_store = db["feature_store"]
        total_features = await feature_store.count_documents({})
        anomaly_features = await feature_store.count_documents({"isAnomaly": True})

        # Get anomaly type distribution
        type_pipeline = [
            {"$match": {"isAnomaly": True}},
            {"$group": {"_id": "$anomalyType", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        type_cursor = await feature_store.aggregate(type_pipeline)
        type_dist = await type_cursor.to_list(length=10)

        return {
            "status": "success",
            "totalFeatures": total_features,
            "anomalyFeatures": anomaly_features,
            "anomalyRate": round(anomaly_features / max(total_features, 1) * 100, 2),
            "anomalyTypeDistribution": {t["_id"]: t["count"] for t in type_dist},
            "processedAt": datetime.now().isoformat(),
        }

    finally:
        await client.close()


async def get_training_data(
    mongodb_uri: str = None,
    database_name: str = None,
    limit: int = 10000
) -> list:
    """
    Get training data from feature store for ML model.

    Returns list of feature dictionaries ready for model training.
    """
    uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>")
    db_name = database_name or os.getenv("MONGODB_DATABASE", "OEMPartner_mes_demo")

    client = AsyncMongoClient(uri)
    db = client[db_name]

    try:
        feature_store = db["feature_store"]

        # Get balanced sample (include more anomalies)
        normal_docs = await feature_store.find(
            {"isAnomaly": False}
        ).limit(int(limit * 0.7)).to_list(length=int(limit * 0.7))

        anomaly_docs = await feature_store.find(
            {"isAnomaly": True}
        ).limit(int(limit * 0.3)).to_list(length=int(limit * 0.3))

        return normal_docs + anomaly_docs

    finally:
        await client.close()


if __name__ == "__main__":
    # Run feature store population
    result = asyncio.run(populate_feature_store())
    print("Feature Store Population Complete:")
    print(f"  Total features: {result['totalFeatures']}")
    print(f"  Anomaly features: {result['anomalyFeatures']}")
    print(f"  Anomaly rate: {result['anomalyRate']}%")
    print(f"  Distribution: {result['anomalyTypeDistribution']}")
