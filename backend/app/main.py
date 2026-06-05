"""
Manufacturing Group Manufacturing - OEMPartner Assembly Line MES
FastAPI Application Entry Point

MongoDB Time Series Demo with Anomaly Detection
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import MongoDB
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages MongoDB connection lifecycle.
    """
    # Startup
    await MongoDB.connect()
    yield
    # Shutdown
    await MongoDB.disconnect()


# Create FastAPI application
app = FastAPI(
    title="OEMPartner Assembly Line MES",
    description="""
    Manufacturing Execution System for Manufacturing Group Malaysia.

    ## Features
    - **Time Series Telemetry**: Real-time machine sensor data
    - **Quality Dashboard**: Defect rates, anomaly detection, quality scores
    - **Operations Dashboard**: Production stats, utilization, downtime analysis
    - **Anomaly Detection**: ML-powered anomaly detection on sensor data

    ## MongoDB Time Series
    Uses MongoDB Time Series collections for high-volume sensor data ingestion
    with efficient aggregation pipelines for cross-department analytics.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # SvelteKit dev server
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "OEMPartner Assembly Line MES",
        "version": "1.0.0",
        "company": "Manufacturing Group Malaysia",
        "description": "Manufacturing Execution System with MongoDB Time Series",
        "docs": "/docs",
        "api": settings.api_v1_prefix,
        "branding": {
            "OEMPartnerBlue": "#0033A0",
            "OEMPartnerRed": "#E60012",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verify database connection
        db = MongoDB.get_database()
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timezone": settings.timezone,
    }
