"""
Pydantic models for OEMPartner Assembly Line MES
Defines schemas for telemetry data, machines, and dashboard views
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.utils.objectid import PyObjectId


class TelemetryMetrics(BaseModel):
    """Machine metrics from sensor readings"""
    temperature: float = Field(..., description="Temperature in Celsius")
    vibration: float = Field(..., description="Vibration in mm/s")
    powerConsumption: float = Field(..., description="Power consumption in kW")
    cycleTime: float = Field(..., description="Cycle time in seconds")
    outputCount: int = Field(..., description="Units produced this cycle")


class Alert(BaseModel):
    """Alert generated from threshold breach"""
    code: str = Field(..., description="Alert code (e.g., TEMP_HIGH)")
    severity: str = Field(..., description="Alert severity: info, warning, error, critical")
    value: float = Field(..., description="Actual value that triggered alert")
    threshold: float = Field(..., description="Threshold that was breached")


class TelemetryMetadata(BaseModel):
    """Metadata fields for time series document"""
    machineId: str
    lineId: str
    lineName: str
    machineType: str


class AnomalyInfo(BaseModel):
    """Anomaly injection info for ML training"""
    injected: bool = False
    type: Optional[str] = None


class TelemetryReading(BaseModel):
    """
    Machine telemetry reading from time series collection
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    timestamp: datetime
    metadata: TelemetryMetadata
    metrics: TelemetryMetrics
    status: str = Field(..., description="Machine status: running, idle, maintenance, error")
    alerts: List[Alert] = Field(default_factory=list)
    operatorId: str
    shiftId: str
    anomaly: Optional[AnomalyInfo] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PyObjectId: lambda v: str(v),
        }


class MachineSpecifications(BaseModel):
    """Machine operational specifications"""
    baseCycleTime: float
    baseTemperature: float
    baseVibration: float
    basePower: float


class MachineThresholds(BaseModel):
    """Alert thresholds for machine"""
    tempWarning: float
    tempCritical: float
    vibWarning: float
    vibCritical: float
    powerWarning: float


class Machine(BaseModel):
    """Machine reference document"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    machineId: str
    machineName: str
    machineType: str
    lineId: str
    lineName: str
    specifications: MachineSpecifications
    thresholds: MachineThresholds
    installedDate: datetime
    lastMaintenance: datetime
    status: str = "active"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class QualityMetricsCore(BaseModel):
    """Core quality metrics"""
    totalReadings: int
    alertCount: int
    criticalAlerts: int
    warningAlerts: int
    anomalyCount: int
    qualityScore: float
    defectRate: float


class TemperatureStats(BaseModel):
    """Temperature statistics"""
    avg: float
    max: float


class VibrationStats(BaseModel):
    """Vibration statistics"""
    avg: float
    max: float


class StatusCounts(BaseModel):
    """Status counts"""
    errorCount: int
    runningCount: int


class QualityMetrics(BaseModel):
    """Quality department materialized view document"""
    lineId: str
    lineName: str
    shiftId: str
    date: str
    hour: Optional[int] = None
    metrics: QualityMetricsCore
    temperature: TemperatureStats
    vibration: VibrationStats
    status: StatusCounts
    refreshedAt: datetime
    viewType: str

    class Config:
        populate_by_name = True


class ProductionCounts(BaseModel):
    """Production counts"""
    unitsProduced: int
    targetUnits: int


class CycleTimeStats(BaseModel):
    """Cycle time statistics"""
    avg: float
    min: float
    max: float


class PowerStats(BaseModel):
    """Power consumption statistics"""
    avgConsumption: float
    totalConsumption: float


class UtilizationStats(BaseModel):
    """Utilization statistics"""
    rate: float
    runningMinutes: int
    idleMinutes: int
    idleRate: float


class DowntimeStats(BaseModel):
    """Downtime statistics"""
    rate: float
    maintenanceMinutes: int
    errorMinutes: int


class ProductionStats(BaseModel):
    """Operations department materialized view document"""
    lineId: str
    lineName: str
    shiftId: str
    date: str
    machineCount: int
    production: ProductionCounts
    cycleTime: CycleTimeStats
    power: PowerStats
    utilization: UtilizationStats
    downtime: DowntimeStats
    refreshedAt: datetime
    viewType: str

    class Config:
        populate_by_name = True


class AnomalyDetection(BaseModel):
    """Anomaly detection result from ML model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    machineId: str
    lineId: str
    timestamp: datetime
    detectedAt: datetime
    anomalyType: str
    confidence: float = Field(..., ge=0, le=1)
    severity: str
    features: dict
    modelVersion: str
    acknowledged: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# Request/Response models
class TelemetryQuery(BaseModel):
    """Query parameters for telemetry endpoint"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    machine_id: Optional[str] = None
    line_id: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    skip: int = Field(default=0, ge=0)


class DashboardSummary(BaseModel):
    """Dashboard summary response"""
    qualityScore: float
    defectRate: float
    anomalyCount: int
    totalAlerts: int
    criticalAlerts: int
    unitsProduced: int
    utilizationRate: float
    avgCycleTime: float
    lastUpdated: datetime


class RefreshResponse(BaseModel):
    """Materialized view refresh response"""
    collection: str
    type: str
    documentsRefreshed: int
    refreshedAt: str
