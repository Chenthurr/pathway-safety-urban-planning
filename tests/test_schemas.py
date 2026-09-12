"""Smoke tests for the streaming schema declarations."""

import pathway as pw

from src.schemas import (
    AnomalySchema,
    EnvironmentSchema,
    InsightSchema,
    IoTReadingSchema,
    SafetyAlertSchema,
    TrafficSchema,
    TransitSchema,
)


def test_schemas_are_pathway_schemas():
    schemas = [
        SafetyAlertSchema,
        IoTReadingSchema,
        TrafficSchema,
        TransitSchema,
        EnvironmentSchema,
        AnomalySchema,
        InsightSchema,
    ]

    assert all(issubclass(schema, pw.Schema) for schema in schemas)


def test_safety_alert_schema_contains_required_fields():
    columns = set(SafetyAlertSchema.__fields__.keys())

    assert {"timestamp", "source", "location_lat", "location_lon", "alert_type", "description", "severity"} <= columns
