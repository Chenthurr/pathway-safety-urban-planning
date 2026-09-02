"""Pathway schemas for type-safe streaming data."""
import pathway as pw


class SafetyAlertSchema(pw.Schema):
    """Schema for public safety alerts."""
    timestamp: pw.DateTimeUtc
    source: str
    location_lat: float
    location_lon: float
    alert_type: str
    description: str
    severity: str
    metadata: str = pw.column_definition(default_value="")


class IoTReadingSchema(pw.Schema):
    """Schema for IoT sensor readings."""
    timestamp: pw.DateTimeUtc
    sensor_id: str
    location_lat: float
    location_lon: float
    temperature_c: float
    crowd_count: int
    decibel: float
    air_quality_index: int


class TrafficSchema(pw.Schema):
    """Schema for traffic data."""
    timestamp: pw.DateTimeUtc
    intersection_id: str
    location_lat: float
    location_lon: float
    vehicle_count: int
    avg_speed_kmh: float
    congestion_level: str


class TransitSchema(pw.Schema):
    """Schema for public transit data."""
    timestamp: pw.DateTimeUtc
    route_id: str
    vehicle_id: str
    location_lat: float
    location_lon: float
    delay_minutes: float
    passenger_load: str


class EnvironmentSchema(pw.Schema):
    """Schema for environmental data."""
    timestamp: pw.DateTimeUtc
    temperature_c: float
    humidity_percent: float
    air_quality_index: int
    uv_index: float


class AnomalySchema(pw.Schema):
    """Schema for detected anomalies."""
    timestamp: pw.DateTimeUtc
    source: str
    anomaly_type: str
    description: str
    severity: str
    location_lat: float
    location_lon: float
    raw_data: str


class InsightSchema(pw.Schema):
    """Schema for LLM-generated insights."""
    timestamp: pw.DateTimeUtc
    category: str
    insight: str
    confidence: float
    recommended_action: str
