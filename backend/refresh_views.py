#!/usr/bin/env python3
"""
Materialized View Refresh Script
Refreshes all dashboard materialized views from time series data

Manufacturing Group Manufacturing - OEMPartner Assembly Line MES

Usage:
    python refresh_views.py                  # Refresh all views
    python refresh_views.py --view quality   # Refresh quality view only
    python refresh_views.py --view production # Refresh production view only
    python refresh_views.py --type analytics  # Refresh analytics pipelines only
    python refresh_views.py --schedule        # Run as scheduled job

In production, schedule this script:
    - Core pipelines: Every 15 minutes
    - Analytics pipelines: Every 30 minutes
"""
import asyncio
import argparse
import os
from datetime import datetime

from pymongo import AsyncMongoClient
from dotenv import load_dotenv

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.aggregations import (
    refresh_quality_metrics,
    refresh_production_stats,
    refresh_all_views,
)

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "OEMPartner_mes_demo")


async def refresh_views(
    view: str = "all",
    pipeline_type: str = "all"
) -> dict:
    """
    Refresh materialized views.

    Args:
        view: "quality", "production", or "all"
        pipeline_type: "core", "analytics", or "all"

    Returns:
        dict with refresh results
    """
    print("=" * 60)
    print("Manufacturing Group Manufacturing - View Refresh")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    client = AsyncMongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]

    results = {}

    try:
        # Verify connection
        await client.admin.command("ping")
        print(f"Connected to MongoDB: {MONGODB_DATABASE}")

        if view == "all" and pipeline_type == "all":
            print("\nRefreshing all views (core + analytics)...")
            results = await refresh_all_views(db)

        else:
            types_to_run = ["core", "analytics"] if pipeline_type == "all" else [pipeline_type]
            views_to_run = ["quality", "production"] if view == "all" else [view]

            for v in views_to_run:
                for t in types_to_run:
                    print(f"\nRefreshing {v} ({t})...")
                    if v == "quality":
                        result = await refresh_quality_metrics(db, t)
                    else:
                        result = await refresh_production_stats(db, t)
                    results[f"{v}_{t}"] = result
                    print(f"  Documents: {result['documentsRefreshed']}")

        print("\n" + "-" * 60)
        print("Refresh Complete!")
        print("-" * 60)

        for key, value in results.items():
            if isinstance(value, dict) and 'documentsRefreshed' in value:
                print(f"  {key}: {value['documentsRefreshed']} documents")

        return results

    finally:
        await client.close()


async def run_scheduled():
    """
    Run as scheduled refresh job.

    Core pipelines every 15 minutes, analytics every 30 minutes.
    """
    import time

    print("Starting scheduled view refresh...")
    print("Core: every 15 minutes, Analytics: every 30 minutes")
    print("Press Ctrl+C to stop\n")

    iteration = 0

    while True:
        iteration += 1

        # Always refresh core
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running core refresh...")
        client = AsyncMongoClient(MONGODB_URI)
        db = client[MONGODB_DATABASE]

        try:
            await refresh_quality_metrics(db, "core")
            await refresh_production_stats(db, "core")
            print("  Core refresh complete")

            # Analytics every other iteration (30 min)
            if iteration % 2 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Running analytics refresh...")
                await refresh_quality_metrics(db, "analytics")
                await refresh_production_stats(db, "analytics")
                print("  Analytics refresh complete")

        finally:
            await client.close()

        # Wait 15 minutes
        print(f"Next refresh in 15 minutes...")
        await asyncio.sleep(15 * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Refresh materialized views for MES dashboard"
    )
    parser.add_argument(
        "--view",
        choices=["quality", "production", "all"],
        default="all",
        help="Which view to refresh"
    )
    parser.add_argument(
        "--type",
        choices=["core", "analytics", "all"],
        default="all",
        help="Which pipeline type to run"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run as scheduled job (continuous)"
    )

    args = parser.parse_args()

    if args.schedule:
        asyncio.run(run_scheduled())
    else:
        results = asyncio.run(refresh_views(args.view, args.type))


if __name__ == "__main__":
    main()
