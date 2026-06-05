#!/usr/bin/env python3
"""
OEMPartner Motorcycle Assembly Line - Time Series Data Generator
Generates 30 days of realistic machine telemetry data for MES demo

Manufacturing Group Malaysia - MongoDB Time Series Demo
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
import random

import numpy as np
from pymongo import AsyncMongoClient
from pymongo.errors import CollectionInvalid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "OEMPartner_mes_demo")

# Assembly Line Configuration - Realistic OEMPartner Motorcycle Production
ASSEMBLY_LINES = {
    "LINE-1": {
        "name": "Frame Welding",
        "machines": [
            {"id": "WLD-001", "name": "Robotic Welder A", "type": "welding_robot"},
            {"id": "WLD-002", "name": "Robotic Welder B", "type": "welding_robot"},
            {"id": "WLD-003", "name": "Robotic Welder C", "type": "welding_robot"},
        ],
        "base_cycle_time": 45,  # seconds
        "base_temperature": 85,  # Celsius - welding runs hot
        "base_vibration": 1.2,  # mm/s
        "base_power": 25.0,  # kW
    },
    "LINE-2": {
        "name": "Engine Assembly",
        "machines": [
            {"id": "ENG-001", "name": "Crankshaft Station", "type": "assembly_station"},
            {"id": "ENG-002", "name": "Piston Assembly", "type": "assembly_station"},
            {"id": "ENG-003", "name": "Cylinder Head", "type": "assembly_station"},
            {"id": "ENG-004", "name": "Transmission Install", "type": "assembly_station"},
        ],
        "base_cycle_time": 60,
        "base_temperature": 35,
        "base_vibration": 0.5,
        "base_power": 8.0,
    },
    "LINE-3": {
        "name": "Paint Shop",
        "machines": [
            {"id": "PNT-001", "name": "Paint Booth A", "type": "paint_booth"},
            {"id": "PNT-002", "name": "Paint Booth B", "type": "paint_booth"},
        ],
        "base_cycle_time": 120,
        "base_temperature": 55,  # Curing temperature
        "base_vibration": 0.2,
        "base_power": 15.0,
    },
    "LINE-4": {
        "name": "Final Assembly",
        "machines": [
            {"id": "FIN-001", "name": "Electrical Harness", "type": "assembly_station"},
            {"id": "FIN-002", "name": "Fuel System", "type": "assembly_station"},
            {"id": "FIN-003", "name": "Wheel Assembly", "type": "assembly_station"},
            {"id": "FIN-004", "name": "Body Panels", "type": "assembly_station"},
            {"id": "FIN-005", "name": "Quality Check", "type": "inspection_station"},
        ],
        "base_cycle_time": 90,
        "base_temperature": 28,
        "base_vibration": 0.3,
        "base_power": 5.0,
    },
}

# Shift Configuration (Malaysian factory schedule)
SHIFTS = {
    "SHIFT-A": {"start": 6, "end": 14, "name": "Morning Shift"},   # 6am - 2pm
    "SHIFT-B": {"start": 14, "end": 22, "name": "Evening Shift"},  # 2pm - 10pm
    "SHIFT-C": {"start": 22, "end": 6, "name": "Night Shift"},     # 10pm - 6am
}

# Operators pool
OPERATORS = [f"OP-{str(i).zfill(3)}" for i in range(1, 51)]

# Alert types for anomaly detection
ALERT_TYPES = [
    {"code": "TEMP_HIGH", "severity": "warning", "description": "Temperature above threshold"},
    {"code": "TEMP_CRITICAL", "severity": "critical", "description": "Temperature critically high"},
    {"code": "VIB_HIGH", "severity": "warning", "description": "Excessive vibration detected"},
    {"code": "VIB_CRITICAL", "severity": "critical", "description": "Critical vibration - bearing failure risk"},
    {"code": "POWER_SPIKE", "severity": "warning", "description": "Unusual power consumption"},
    {"code": "CYCLE_SLOW", "severity": "info", "description": "Cycle time above normal"},
    {"code": "QUALITY_FAIL", "severity": "error", "description": "Quality check failed"},
]


def get_shift_id(hour: int) -> str:
    """Determine shift ID based on hour"""
    if 6 <= hour < 14:
        return "SHIFT-A"
    elif 14 <= hour < 22:
        return "SHIFT-B"
    else:
        return "SHIFT-C"


def get_shift_productivity_factor(shift_id: str, hour: int) -> float:
    """
    Get productivity factor based on shift and time of day
    Simulates realistic production patterns
    """
    base_factors = {
        "SHIFT-A": 1.0,   # Day shift - full productivity
        "SHIFT-B": 0.95,  # Evening shift - slightly lower
        "SHIFT-C": 0.85,  # Night shift - reduced
    }

    # Add hourly variation within shift
    if shift_id == "SHIFT-A":
        # Ramp up in first hour, peak mid-shift
        if hour == 6:
            return 0.7
        elif hour == 7:
            return 0.9
        elif 10 <= hour <= 12:
            return 1.05  # Peak performance
    elif shift_id == "SHIFT-B":
        # Post-lunch slowdown, recovery
        if hour == 14:
            return 0.8
        elif hour == 15:
            return 0.9
    elif shift_id == "SHIFT-C":
        # Night shift fatigue patterns
        if 2 <= hour <= 4:
            return 0.75  # Early morning low

    return base_factors.get(shift_id, 0.9)


def is_maintenance_window(timestamp: datetime, machine_id: str) -> bool:
    """
    Determine if machine is in scheduled maintenance
    Each machine has different maintenance schedules
    """
    day_of_week = timestamp.weekday()
    hour = timestamp.hour

    # Sunday maintenance windows (reduced production day)
    if day_of_week == 6:
        # Different machines have different maintenance slots
        machine_num = int(machine_id.split("-")[1])
        maintenance_hour = 8 + (machine_num % 8)  # Stagger maintenance
        if hour == maintenance_hour:
            return random.random() < 0.7  # 70% chance of maintenance during slot

    # Weekly maintenance on Wednesday nights for welding robots
    if day_of_week == 2 and machine_id.startswith("WLD") and 22 <= hour <= 23:
        return random.random() < 0.5

    return False


def generate_machine_metrics(
    line_config: dict,
    machine: dict,
    timestamp: datetime,
    productivity_factor: float,
    is_maintenance: bool,
    inject_anomaly: bool = False,
    anomaly_type: Optional[str] = None
) -> dict:
    """
    Generate realistic machine metrics with noise and patterns
    """
    if is_maintenance:
        return {
            "temperature": line_config["base_temperature"] * 0.3,  # Cool during maintenance
            "vibration": 0.0,
            "powerConsumption": 0.5,  # Standby power
            "cycleTime": 0,
            "outputCount": 0,
        }

    # Base values with productivity adjustment
    base_temp = line_config["base_temperature"]
    base_vib = line_config["base_vibration"]
    base_power = line_config["base_power"]
    base_cycle = line_config["base_cycle_time"]

    # Add realistic noise using numpy
    temp_noise = np.random.normal(0, base_temp * 0.05)
    vib_noise = np.random.normal(0, base_vib * 0.1)
    power_noise = np.random.normal(0, base_power * 0.08)
    cycle_noise = np.random.normal(0, base_cycle * 0.05)

    # Time-based patterns (machines heat up over shift)
    hour_in_shift = timestamp.hour % 8
    heat_buildup = 1 + (hour_in_shift * 0.02)  # 2% increase per hour

    metrics = {
        "temperature": round(max(20, (base_temp * heat_buildup + temp_noise) * productivity_factor), 2),
        "vibration": round(max(0.1, base_vib + vib_noise), 3),
        "powerConsumption": round(max(0.5, (base_power + power_noise) * productivity_factor), 2),
        "cycleTime": round(max(10, base_cycle / productivity_factor + cycle_noise), 1),
        "outputCount": 1 if random.random() < productivity_factor else 0,
    }

    # Inject anomalies for ML training
    if inject_anomaly:
        if anomaly_type == "temperature_spike":
            metrics["temperature"] = round(base_temp * np.random.uniform(1.4, 1.8), 2)
        elif anomaly_type == "vibration_anomaly":
            metrics["vibration"] = round(base_vib * np.random.uniform(2.5, 4.0), 3)
        elif anomaly_type == "power_surge":
            metrics["powerConsumption"] = round(base_power * np.random.uniform(1.5, 2.2), 2)
        elif anomaly_type == "cycle_degradation":
            metrics["cycleTime"] = round(base_cycle * np.random.uniform(1.3, 1.8), 1)
        elif anomaly_type == "bearing_failure":
            # Gradual degradation pattern
            metrics["vibration"] = round(base_vib * np.random.uniform(3.0, 5.0), 3)
            metrics["temperature"] = round(base_temp * np.random.uniform(1.2, 1.4), 2)

    return metrics


def generate_alerts(metrics: dict, line_config: dict, inject_anomaly: bool) -> list:
    """
    Generate alerts based on metric thresholds
    """
    alerts = []
    base_temp = line_config["base_temperature"]
    base_vib = line_config["base_vibration"]
    base_power = line_config["base_power"]

    # Temperature alerts
    if metrics["temperature"] > base_temp * 1.3:
        alerts.append({
            "code": "TEMP_CRITICAL" if metrics["temperature"] > base_temp * 1.5 else "TEMP_HIGH",
            "severity": "critical" if metrics["temperature"] > base_temp * 1.5 else "warning",
            "value": metrics["temperature"],
            "threshold": round(base_temp * 1.3, 2),
        })

    # Vibration alerts
    if metrics["vibration"] > base_vib * 2.0:
        alerts.append({
            "code": "VIB_CRITICAL" if metrics["vibration"] > base_vib * 3.0 else "VIB_HIGH",
            "severity": "critical" if metrics["vibration"] > base_vib * 3.0 else "warning",
            "value": metrics["vibration"],
            "threshold": round(base_vib * 2.0, 3),
        })

    # Power alerts
    if metrics["powerConsumption"] > base_power * 1.4:
        alerts.append({
            "code": "POWER_SPIKE",
            "severity": "warning",
            "value": metrics["powerConsumption"],
            "threshold": round(base_power * 1.4, 2),
        })

    return alerts


def determine_status(is_maintenance: bool, alerts: list, metrics: dict) -> str:
    """Determine machine status based on current state"""
    if is_maintenance:
        return "maintenance"

    if any(a["severity"] == "critical" for a in alerts):
        return "error"

    if metrics["outputCount"] == 0:
        return "idle"

    return "running"


async def create_time_series_collection(db) -> None:
    """Create MongoDB Time Series collection with proper configuration"""
    try:
        await db.create_collection(
            "machine_telemetry",
            timeseries={
                "timeField": "timestamp",
                "metaField": "metadata",
                "granularity": "minutes"
            },
            expireAfterSeconds=90 * 24 * 60 * 60  # 90 days retention
        )
        print("Created time series collection: machine_telemetry")
    except CollectionInvalid:
        print("Time series collection already exists")

    # Create indexes for query performance
    collection = db["machine_telemetry"]
    await collection.create_index([("metadata.machineId", 1), ("timestamp", -1)])
    await collection.create_index([("metadata.lineId", 1), ("timestamp", -1)])
    await collection.create_index([("status", 1), ("timestamp", -1)])
    print("Created indexes on machine_telemetry")


async def create_machines_collection(db) -> None:
    """Create machines reference collection with assembly line structure"""
    machines_collection = db["machines"]

    # Clear existing
    await machines_collection.delete_many({})

    machines = []
    for line_id, line_config in ASSEMBLY_LINES.items():
        for machine in line_config["machines"]:
            machines.append({
                "machineId": machine["id"],
                "machineName": machine["name"],
                "machineType": machine["type"],
                "lineId": line_id,
                "lineName": line_config["name"],
                "specifications": {
                    "baseCycleTime": line_config["base_cycle_time"],
                    "baseTemperature": line_config["base_temperature"],
                    "baseVibration": line_config["base_vibration"],
                    "basePower": line_config["base_power"],
                },
                "thresholds": {
                    "tempWarning": round(line_config["base_temperature"] * 1.3, 2),
                    "tempCritical": round(line_config["base_temperature"] * 1.5, 2),
                    "vibWarning": round(line_config["base_vibration"] * 2.0, 3),
                    "vibCritical": round(line_config["base_vibration"] * 3.0, 3),
                    "powerWarning": round(line_config["base_power"] * 1.4, 2),
                },
                "installedDate": datetime(2022, 3, 15),
                "lastMaintenance": datetime(2024, 11, 1),
                "status": "active",
            })

    await machines_collection.insert_many(machines)
    print(f"Inserted {len(machines)} machines into reference collection")


async def generate_telemetry_data(
    db,
    days: int = 30,
    anomaly_rate: float = 0.02  # 2% of readings have anomalies for ML training
) -> None:
    """
    Generate realistic time series telemetry data

    Args:
        db: MongoDB database
        days: Number of days of historical data to generate
        anomaly_rate: Percentage of readings to inject anomalies for ML training
    """
    collection = db["machine_telemetry"]

    # Clear existing telemetry data
    await collection.delete_many({})

    # Start from 'days' ago
    end_time = datetime.now().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(days=days)

    print(f"Generating telemetry data from {start_time} to {end_time}")
    print(f"Anomaly injection rate: {anomaly_rate * 100}%")

    # Anomaly types for injection
    anomaly_types = ["temperature_spike", "vibration_anomaly", "power_surge",
                     "cycle_degradation", "bearing_failure"]

    total_docs = 0
    batch = []
    batch_size = 5000

    current_time = start_time
    while current_time <= end_time:
        hour = current_time.hour
        day_of_week = current_time.weekday()

        # Skip some readings on weekends (reduced production)
        if day_of_week in [5, 6] and random.random() < 0.3:
            current_time += timedelta(minutes=1)
            continue

        shift_id = get_shift_id(hour)
        productivity_factor = get_shift_productivity_factor(shift_id, hour)

        # Weekend reduction
        if day_of_week == 5:  # Saturday
            productivity_factor *= 0.7
        elif day_of_week == 6:  # Sunday
            productivity_factor *= 0.4

        for line_id, line_config in ASSEMBLY_LINES.items():
            for machine in line_config["machines"]:
                # Check maintenance
                is_maintenance = is_maintenance_window(current_time, machine["id"])

                # Determine if we inject an anomaly
                inject_anomaly = random.random() < anomaly_rate
                anomaly_type = random.choice(anomaly_types) if inject_anomaly else None

                # Generate metrics
                metrics = generate_machine_metrics(
                    line_config, machine, current_time,
                    productivity_factor, is_maintenance,
                    inject_anomaly, anomaly_type
                )

                # Generate alerts
                alerts = generate_alerts(metrics, line_config, inject_anomaly)

                # Determine status
                status = determine_status(is_maintenance, alerts, metrics)

                # Select operator (same operator per machine per shift typically)
                operator_seed = hash(f"{machine['id']}-{shift_id}-{current_time.date()}")
                operator_id = OPERATORS[operator_seed % len(OPERATORS)]

                # Create document with metadata for time series
                doc = {
                    "timestamp": current_time,
                    "metadata": {
                        "machineId": machine["id"],
                        "lineId": line_id,
                        "lineName": line_config["name"],
                        "machineType": machine["type"],
                    },
                    "metrics": metrics,
                    "status": status,
                    "alerts": alerts,
                    "operatorId": operator_id,
                    "shiftId": shift_id,
                    "anomaly": {
                        "injected": inject_anomaly,
                        "type": anomaly_type,
                    } if inject_anomaly else None,
                }

                batch.append(doc)

                if len(batch) >= batch_size:
                    await collection.insert_many(batch)
                    total_docs += len(batch)
                    print(f"Inserted {total_docs} documents... ({current_time.date()})")
                    batch = []

        current_time += timedelta(minutes=1)

    # Insert remaining documents
    if batch:
        await collection.insert_many(batch)
        total_docs += len(batch)

    print(f"\nTotal documents inserted: {total_docs:,}")

    # Count anomalies
    anomaly_count = await collection.count_documents({"anomaly.injected": True})
    print(f"Anomalies injected: {anomaly_count:,} ({anomaly_count/total_docs*100:.2f}%)")


async def main():
    """Main entry point for data generation"""
    print("=" * 60)
    print("Manufacturing Group Manufacturing - OEMPartner Assembly Line")
    print("Time Series Data Generator")
    print("=" * 60)

    # Connect to MongoDB
    client = AsyncMongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]

    try:
        # Verify connection
        await client.admin.command("ping")
        print(f"Connected to MongoDB: {MONGODB_DATABASE}")

        # Create collections
        await create_time_series_collection(db)
        await create_machines_collection(db)

        # Generate telemetry data
        days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
        await generate_telemetry_data(db, days=days, anomaly_rate=0.02)

        print("\nData generation complete!")
        print("Collections created:")
        print("  - machine_telemetry (Time Series)")
        print("  - machines (Reference)")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
