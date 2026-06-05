"""
Dashboard Service for aggregating data across materialized views
Provides data for Quality and Operations dashboards
"""
from datetime import datetime, timedelta
from typing import Optional

from pymongo.asynchronous.database import AsyncDatabase

from app.utils.objectid import serialize_docs, serialize_doc


class DashboardService:
    """Service for dashboard data aggregation"""

    def __init__(self, db: AsyncDatabase):
        self.db = db
        # Separate collections for core vs analytics views
        self.quality_core = db["mv_quality_core"]
        self.quality_analytics = db["mv_quality_analytics"]
        self.production_core = db["mv_production_core"]
        self.production_analytics = db["mv_production_analytics"]
        self.telemetry_collection = db["machine_telemetry"]
        self.anomaly_collection = db["anomaly_detections"]
        self.machines_collection = db["machines"]

    async def get_quality_dashboard(
        self,
        date: Optional[str] = None,
        line_id: Optional[str] = None
    ) -> dict:
        """
        Get quality dashboard data from materialized views (fast!)

        Returns:
            - Overall quality score
            - Defect rates by line
            - Top alerts
            - Anomaly summary
            - Quality trend
        """
        # Build filter for core view
        match_filter = {}
        if date:
            match_filter["date"] = date
        if line_id:
            match_filter["lineId"] = line_id

        # Read from materialized view (pre-computed!)
        quality_docs = await self.quality_core.find(match_filter).to_list(length=100)

        if not quality_docs:
            return {
                "period": {
                    "type": "rolling",
                    "hours": 24,
                    "description": "Last 24 hours",
                    "dataRange": {"from": None, "to": None},
                    "notice": "No data available. Run view refresh to populate.",
                },
                "summary": {
                    "overallQualityScore": 0,
                    "avgDefectRate": 0,
                    "totalAlerts": 0,
                    "criticalAlerts": 0,
                    "anomalyCount": 0,
                },
                "byLine": [],
                "trend": [],
                "machineHealth": [],
                "lastUpdated": datetime.now().isoformat(),
            }

        # Calculate summary from pre-computed metrics
        total_readings = sum(d["metrics"]["totalReadings"] for d in quality_docs)
        total_alerts = sum(d["metrics"]["alertCount"] for d in quality_docs)
        critical_alerts = sum(d["metrics"]["criticalAlerts"] for d in quality_docs)
        anomaly_count = sum(d["metrics"]["anomalyCount"] for d in quality_docs)
        avg_quality = sum(
            d["metrics"]["qualityScore"] * d["metrics"]["totalReadings"]
            for d in quality_docs
        ) / max(total_readings, 1)
        avg_defect = sum(
            d["metrics"]["defectRate"] * d["metrics"]["totalReadings"]
            for d in quality_docs
        ) / max(total_readings, 1)

        # Group by line
        by_line = {}
        for doc in quality_docs:
            line = doc["lineId"]
            if line not in by_line:
                by_line[line] = {
                    "lineId": line,
                    "lineName": doc["lineName"],
                    "qualityScore": 0,
                    "defectRate": 0,
                    "alertCount": 0,
                    "readings": 0,
                }
            by_line[line]["readings"] += doc["metrics"]["totalReadings"]
            by_line[line]["alertCount"] += doc["metrics"]["alertCount"]
            by_line[line]["qualityScore"] += (
                doc["metrics"]["qualityScore"] * doc["metrics"]["totalReadings"]
            )
            by_line[line]["defectRate"] += (
                doc["metrics"]["defectRate"] * doc["metrics"]["totalReadings"]
            )

        for line in by_line.values():
            if line["readings"] > 0:
                line["qualityScore"] = round(line["qualityScore"] / line["readings"], 1)
                line["defectRate"] = round(line["defectRate"] / line["readings"], 2)

        # Get trend data from core view (group by date)
        trend_pipeline = [
            {"$group": {
                "_id": "$date",
                "avgQuality": {"$avg": "$metrics.qualityScore"},
                "totalAlerts": {"$sum": "$metrics.alertCount"},
                "anomalies": {"$sum": "$metrics.anomalyCount"},
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 7}
        ]
        trend_cursor = await self.quality_core.aggregate(trend_pipeline)
        trend_data = await trend_cursor.to_list(length=7)

        # Get machine health from analytics view
        analytics_docs = await self.quality_analytics.find({}).sort("healthScore", 1).limit(5).to_list(length=5)

        # Calculate actual date range from the data
        dates = sorted(set(d["date"] for d in quality_docs))
        
        return {
            "period": {
                "type": "rolling",
                "hours": 24,
                "description": "Last 24 hours",
                "dataRange": {
                    "from": dates[0] if dates else None,
                    "to": dates[-1] if dates else None,
                },
            },
            "summary": {
                "overallQualityScore": round(avg_quality, 1),
                "avgDefectRate": round(avg_defect, 2),
                "totalAlerts": total_alerts,
                "criticalAlerts": critical_alerts,
                "anomalyCount": anomaly_count,
            },
            "byLine": list(by_line.values()),
            "trend": [
                {
                    "date": t["_id"],
                    "qualityScore": round(t["avgQuality"], 1),
                    "alerts": t["totalAlerts"],
                    "anomalies": t["anomalies"],
                }
                for t in trend_data
            ],
            "machineHealth": serialize_docs(analytics_docs),
            "lastUpdated": datetime.now().isoformat(),
        }

    async def get_operations_dashboard(
        self,
        date: Optional[str] = None,
        line_id: Optional[str] = None
    ) -> dict:
        """
        Get operations dashboard data from materialized views (fast!)

        Returns:
            - Total units produced
            - Utilization rates
            - Cycle time analysis
            - Downtime summary
            - Production trend
        """
        # Build filter for core view
        match_filter = {}
        if date:
            match_filter["date"] = date
        if line_id:
            match_filter["lineId"] = line_id

        # Read from materialized view (pre-computed!)
        production_docs = await self.production_core.find(match_filter).to_list(length=100)

        if not production_docs:
            return {
                "period": {
                    "type": "rolling",
                    "hours": 24,
                    "description": "Last 24 hours",
                    "dataRange": {"from": None, "to": None},
                    "notice": "No data available. Run view refresh to populate.",
                },
                "summary": {
                    "totalUnits": 0,
                    "targetUnits": 0,
                    "completionRate": 0,
                    "utilizationRate": 0,
                    "avgCycleTime": 0,
                    "downtimeMinutes": 0,
                },
                "byLine": [],
                "trend": [],
                "downtime": [],
                "lastUpdated": datetime.now().isoformat(),
            }

        # Calculate summary from pre-computed metrics
        total_units = sum(d["production"]["unitsProduced"] for d in production_docs)
        target_units = sum(d["production"]["targetUnits"] for d in production_docs)
        total_running = sum(d["utilization"]["runningMinutes"] for d in production_docs)
        total_readings = sum(
            d["utilization"]["runningMinutes"] +
            d["utilization"]["idleMinutes"] +
            d["downtime"]["maintenanceMinutes"] +
            d["downtime"]["errorMinutes"]
            for d in production_docs
        )
        total_downtime = sum(
            d["downtime"]["maintenanceMinutes"] + d["downtime"]["errorMinutes"]
            for d in production_docs
        )
        avg_cycle = sum(
            d["cycleTime"]["avg"] * d["production"]["unitsProduced"]
            for d in production_docs if d["production"]["unitsProduced"] > 0
        ) / max(total_units, 1)

        utilization = (total_running / max(total_readings, 1)) * 100

        # Group by line
        by_line = {}
        for doc in production_docs:
            line = doc["lineId"]
            if line not in by_line:
                by_line[line] = {
                    "lineId": line,
                    "lineName": doc["lineName"],
                    "unitsProduced": 0,
                    "targetUnits": 0,
                    "utilizationRate": 0,
                    "totalMinutes": 0,
                    "runningMinutes": 0,
                }
            by_line[line]["unitsProduced"] += doc["production"]["unitsProduced"]
            by_line[line]["targetUnits"] += doc["production"]["targetUnits"]
            by_line[line]["runningMinutes"] += doc["utilization"]["runningMinutes"]
            by_line[line]["totalMinutes"] += (
                doc["utilization"]["runningMinutes"] +
                doc["utilization"]["idleMinutes"] +
                doc["downtime"]["maintenanceMinutes"] +
                doc["downtime"]["errorMinutes"]
            )

        for line in by_line.values():
            if line["totalMinutes"] > 0:
                line["utilizationRate"] = round(
                    (line["runningMinutes"] / line["totalMinutes"]) * 100, 1
                )
            del line["totalMinutes"]
            del line["runningMinutes"]

        # Get trend data from core view
        trend_pipeline = [
            {"$group": {
                "_id": "$date",
                "totalUnits": {"$sum": "$production.unitsProduced"},
                "avgUtilization": {"$avg": "$utilization.rate"},
                "avgCycleTime": {"$avg": "$cycleTime.avg"},
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 7}
        ]
        trend_cursor = await self.production_core.aggregate(trend_pipeline)
        trend_data = await trend_cursor.to_list(length=7)

        # Get downtime breakdown
        downtime_pipeline = [
            {"$group": {
                "_id": "$lineId",
                "lineName": {"$first": "$lineName"},
                "maintenance": {"$sum": "$downtime.maintenanceMinutes"},
                "error": {"$sum": "$downtime.errorMinutes"},
            }},
            {"$sort": {"_id": 1}}
        ]
        downtime_cursor = await self.production_core.aggregate(downtime_pipeline)
        downtime_data = await downtime_cursor.to_list(length=10)

        # Calculate actual date range from the data
        dates = sorted(set(d["date"] for d in production_docs))
        
        return {
            "period": {
                "type": "rolling",
                "hours": 24,
                "description": "Last 24 hours",
                "dataRange": {
                    "from": dates[0] if dates else None,
                    "to": dates[-1] if dates else None,
                },
            },
            "summary": {
                "totalUnits": total_units,
                "targetUnits": target_units,
                "completionRate": round((total_units / max(target_units, 1)) * 100, 1),
                "utilizationRate": round(utilization, 1),
                "avgCycleTime": round(avg_cycle, 1),
                "downtimeMinutes": total_downtime,
            },
            "byLine": list(by_line.values()),
            "trend": [
                {
                    "date": t["_id"],
                    "units": t["totalUnits"],
                    "utilization": round(t["avgUtilization"], 1) if t["avgUtilization"] else 0,
                    "cycleTime": round(t["avgCycleTime"], 1) if t["avgCycleTime"] else 0,
                }
                for t in trend_data
            ],
            "downtime": serialize_docs(downtime_data),
            "lastUpdated": datetime.now().isoformat(),
        }

    async def get_anomaly_summary(self) -> dict:
        """
        Get summary of detected anomalies from ML pipeline

        Returns:
            - Recent anomalies
            - Anomaly counts by type
            - Affected machines
        """
        # Get recent anomalies
        recent = await self.anomaly_collection.find(
            {"acknowledged": False}
        ).sort("detectedAt", -1).limit(20).to_list(length=20)

        # Count by type
        type_pipeline = [
            {"$group": {
                "_id": "$anomalyType",
                "count": {"$sum": 1},
                "avgConfidence": {"$avg": "$confidence"},
            }},
            {"$sort": {"count": -1}}
        ]
        type_cursor = await self.anomaly_collection.aggregate(type_pipeline)
        by_type = await type_cursor.to_list(length=10)

        # Count by machine
        machine_pipeline = [
            {"$match": {"acknowledged": False}},
            {"$group": {
                "_id": "$machineId",
                "lineId": {"$first": "$lineId"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        machine_cursor = await self.anomaly_collection.aggregate(machine_pipeline)
        by_machine = await machine_cursor.to_list(length=5)

        total_unack = await self.anomaly_collection.count_documents({"acknowledged": False})

        return {
            "unacknowledgedCount": total_unack,
            "recent": serialize_docs(recent),
            "byType": serialize_docs(by_type),
            "byMachine": serialize_docs(by_machine),
            "lastUpdated": datetime.now().isoformat(),
        }
