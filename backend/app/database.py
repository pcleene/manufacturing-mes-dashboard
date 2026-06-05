"""
MongoDB Async Database Connection using PyMongo Async
NOTE: Using pymongo.AsyncMongoClient (NOT Motor - deprecated May 2025)
"""
from contextlib import asynccontextmanager
from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection

from app.config import settings


class MongoDB:
    """
    MongoDB connection manager using PyMongo Async
    Provides async context manager for database operations
    """

    client: Optional[AsyncMongoClient] = None
    database: Optional[AsyncDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """Initialize MongoDB connection"""
        cls.client = AsyncMongoClient(settings.mongodb_uri)
        cls.database = cls.client[settings.mongodb_database]
        # Verify connection
        await cls.client.admin.command("ping")
        print(f"Connected to MongoDB: {settings.mongodb_database}")

    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection"""
        if cls.client:
            await cls.client.close()
            print("Disconnected from MongoDB")

    @classmethod
    def get_database(cls) -> AsyncDatabase:
        """Get database instance"""
        if cls.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.database

    @classmethod
    def get_collection(cls, name: str) -> AsyncCollection:
        """Get collection by name"""
        return cls.get_database()[name]


# Collection accessors for convenience
def get_telemetry_collection() -> AsyncCollection:
    """Get machine_telemetry time series collection"""
    return MongoDB.get_collection("machine_telemetry")


def get_machines_collection() -> AsyncCollection:
    """Get machines reference collection"""
    return MongoDB.get_collection("machines")


def get_quality_metrics_collection() -> AsyncCollection:
    """Get mv_quality_metrics materialized view"""
    return MongoDB.get_collection("mv_quality_metrics")


def get_production_stats_collection() -> AsyncCollection:
    """Get mv_production_stats materialized view"""
    return MongoDB.get_collection("mv_production_stats")


def get_anomaly_collection() -> AsyncCollection:
    """Get anomaly_detections collection for ML results"""
    return MongoDB.get_collection("anomaly_detections")


def get_feature_store_collection() -> AsyncCollection:
    """Get feature_store collection for ML training data"""
    return MongoDB.get_collection("feature_store")


@asynccontextmanager
async def get_db_session():
    """
    Async context manager for database operations
    Ensures proper connection handling
    """
    try:
        yield MongoDB.get_database()
    except Exception as e:
        print(f"Database error: {e}")
        raise
