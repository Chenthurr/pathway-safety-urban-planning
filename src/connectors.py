"""Real-time data connectors following Pathway LLM App patterns."""
import pathway as pw
from src.schemas import (
    SafetyAlertSchema, IoTReadingSchema,
    TrafficSchema, TransitSchema, EnvironmentSchema
)


def create_safety_alert_table(path: str) -> pw.Table:
    """Create a live table from safety alert CSV stream."""
    return pw.io.csv.read(
        path,
        schema=SafetyAlertSchema,
        mode="streaming"
    )


def create_iot_table(path: str) -> pw.Table:
    """Create a live table from IoT sensor CSV stream."""
    return pw.io.csv.read(
        path,
        schema=IoTReadingSchema,
        mode="streaming"
    )


def create_traffic_table(path: str) -> pw.Table:
    """Create a live table from traffic CSV stream."""
    return pw.io.csv.read(
        path,
        schema=TrafficSchema,
        mode="streaming"
    )


def create_transit_table(path: str) -> pw.Table:
    """Create a live table from transit CSV stream."""
    return pw.io.csv.read(
        path,
        schema=TransitSchema,
        mode="streaming"
    )


def create_environment_table(path: str) -> pw.Table:
    """Create a live table from environment CSV stream."""
    return pw.io.csv.read(
        path,
        schema=EnvironmentSchema,
        mode="streaming"
    )
