"""Deterministic real-time urban planning insights using Pathway aggregations."""
import pathway as pw
from src.schemas import InsightSchema


def traffic_insight(intersection: str, speed: float, vehicles: int) -> str:
    return f"Intersection {intersection}: average speed {speed:.1f} km/h across {vehicles} vehicles"


def traffic_confidence(speed: float) -> float:
    return max(0.0, min(1.0, (60.0 - speed) / 60.0))


def traffic_action(speed: float) -> str:
    return "Deploy traffic officers" if speed < 20 else "Monitor"


def transit_insight(route: str, delay: float, loads: int, vehicles: int) -> str:
    return f"Route {route}: average delay {delay:.1f} min, {loads} full-load events across {vehicles} vehicles"


def transit_confidence(delay: float) -> float:
    return max(0.0, min(1.0, delay / 30.0))


def transit_action(delay: float, loads: int) -> str:
    return "Add extra buses" if delay > 10 or loads > 2 else "Normal service"


def environment_insight(temp: float, humidity: float, aqi: float, uv: float) -> str:
    return f"Environment: {temp:.1f}C, {humidity:.0f}% humidity, AQI {aqi:.0f}, UV {uv:.1f}"


def environment_confidence(aqi: float) -> float:
    return max(0.0, min(1.0, aqi / 200.0))


def environment_action(aqi: float, uv: float) -> str:
    return "Issue health advisory" if aqi > 150 or uv > 8 else "Normal conditions"


class UrbanPlanningEngine:
    def __init__(self, llm_config: dict | None = None):
        self.llm_config = llm_config or {}

    def compute_traffic_insights(self, traffic_table: pw.Table) -> pw.Table:
        grouped = traffic_table.groupby(pw.this.intersection_id).reduce(
            intersection_id=pw.this.intersection_id,
            avg_speed=pw.reducers.avg(pw.this.avg_speed_kmh),
            total_vehicles=pw.reducers.sum(pw.this.vehicle_count),
            last_updated=pw.reducers.max(pw.this.timestamp),
        )
        return grouped.select(
            timestamp=pw.this.last_updated,
            category="traffic",
            insight=pw.apply(traffic_insight, pw.this.intersection_id, pw.this.avg_speed, pw.this.total_vehicles),
            confidence=pw.apply(traffic_confidence, pw.this.avg_speed),
            recommended_action=pw.apply(traffic_action, pw.this.avg_speed),
        )

    def compute_transit_insights(self, transit_table: pw.Table) -> pw.Table:
        grouped = transit_table.groupby(pw.this.route_id).reduce(
            route_id=pw.this.route_id,
            avg_delay=pw.reducers.avg(pw.this.delay_minutes),
            full_load_count=pw.reducers.count(pw.this.passenger_load),
            vehicle_count=pw.reducers.count(pw.this.vehicle_id),
            last_updated=pw.reducers.max(pw.this.timestamp),
        )
        return grouped.select(
            timestamp=pw.this.last_updated,
            category="transit",
            insight=pw.apply(transit_insight, pw.this.route_id, pw.this.avg_delay, pw.this.full_load_count, pw.this.vehicle_count),
            confidence=pw.apply(transit_confidence, pw.this.avg_delay),
            recommended_action=pw.apply(transit_action, pw.this.avg_delay, pw.this.full_load_count),
        )

    def compute_environment_insights(self, env_table: pw.Table) -> pw.Table:
        grouped = env_table.reduce(
            avg_temperature=pw.reducers.avg(pw.this.temperature_c),
            avg_humidity=pw.reducers.avg(pw.this.humidity_percent),
            avg_aqi=pw.reducers.avg(pw.this.air_quality_index),
            avg_uv=pw.reducers.avg(pw.this.uv_index),
            last_updated=pw.reducers.max(pw.this.timestamp),
        )
        return grouped.select(
            timestamp=pw.this.last_updated,
            category="environment",
            insight=pw.apply(environment_insight, pw.this.avg_temperature, pw.this.avg_humidity, pw.this.avg_aqi, pw.this.avg_uv),
            confidence=pw.apply(environment_confidence, pw.this.avg_aqi),
            recommended_action=pw.apply(environment_action, pw.this.avg_aqi, pw.this.avg_uv),
        )

    def generate_llm_summary(self, traffic_insights: pw.Table, transit_insights: pw.Table, env_insights: pw.Table) -> pw.Table:
        return traffic_insights.concat_reindex(transit_insights, env_insights)
