"""Urban planning real-time insights using Pathway aggregations + LLM.

Follows Pathway LLM App patterns with windowed aggregations
and BaseRAGQuestionAnswerer for holistic city insights.
"""
import pathway as pw
from pathway.xpacks.llm import llms

from src.schemas import TrafficSchema, TransitSchema, EnvironmentSchema, InsightSchema


class UrbanPlanningEngine:
    """
    Real-time urban planning assistant that aggregates
    transit, traffic, and environmental data and generates
    LLM-powered predictive insights.
    """

    def __init__(self, llm_config: dict):
        self.llm = llms.OpenAIChat(
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=llm_config.get("temperature", 0.3),
            max_tokens=llm_config.get("max_tokens", 1024)
        )

    def compute_traffic_insights(self, traffic_table: pw.Table) -> pw.Table:
        """Real-time traffic congestion analysis with windowed aggregation."""
        # Group by intersection and compute metrics
        windowed = traffic_table.groupby(
            pw.this.intersection_id
        ).reduce(
            intersection_id=pw.this.intersection_id,
            avg_speed=pw.reducers.avg(pw.this.avg_speed_kmh),
            total_vehicles=pw.reducers.sum(pw.this.vehicle_count),
            high_congestion_count=pw.reducers.count(pw.this.congestion_level == "high"),
            last_updated=pw.reducers.max(pw.this.timestamp)
        )

        # Generate insights
        insights = windowed.select(
            timestamp=windowed.last_updated,
            category="traffic",
            insight=pw.apply(
                lambda i, s, v, c:
                f"Intersection {i}: Avg speed {s:.1f} km/h, {v} vehicles, {c} high-congestion events",
                windowed.intersection_id, windowed.avg_speed,
                windowed.total_vehicles, windowed.high_congestion_count
            ),
            confidence=pw.apply(
                lambda s: min(1.0, max(0.0, (60.0 - float(s)) / 60.0)) if s is not None else 0.0,
                windowed.avg_speed
            ),
            recommended_action=pw.apply(
                lambda s, c: "Deploy traffic officers" if (s is not None and s < 20) or (c is not None and c > 3) else "Monitor",
                windowed.avg_speed, windowed.high_congestion_count
            )
        )

        return insights

    def compute_transit_insights(self, transit_table: pw.Table) -> pw.Table:
        """Public transit delay and load analysis."""
        windowed = transit_table.groupby(
            pw.this.route_id
        ).reduce(
            route_id=pw.this.route_id,
            avg_delay=pw.reducers.avg(pw.this.delay_minutes),
            full_load_count=pw.reducers.count(pw.this.passenger_load == "full"),
            vehicle_count=pw.reducers.count(pw.this.vehicle_id),
            last_updated=pw.reducers.max(pw.this.timestamp)
        )

        return windowed.select(
            timestamp=windowed.last_updated,
            category=pw.apply(lambda x: "transit", str),
            insight=pw.apply(
                lambda r, d, f, v:
                f"Route {r}: Avg delay {d:.1f} min, {f} full-load events across {v} vehicles",
                windowed.route_id, windowed.avg_delay,
                windowed.full_load_count, windowed.vehicle_count
            ),
            confidence=pw.apply(
                lambda d: min(1.0, float(d) / 30.0) if d is not None else 0.0,
                windowed.avg_delay
            ),
            recommended_action=pw.apply(
                lambda d, f: "Add extra buses" if (d is not None and d > 10) or (f is not None and f > 2) else "Normal service",
                windowed.avg_delay, windowed.full_load_count
            )
        )

    def compute_environment_insights(self, env_table: pw.Table) -> pw.Table:
        """Environmental quality monitoring."""
        latest = env_table.groupby(
            pw.this.timestamp
        ).reduce(
            temperature=pw.reducers.avg(pw.this.temperature_c),
            humidity=pw.reducers.avg(pw.this.humidity_percent),
            aqi=pw.reducers.avg(pw.this.air_quality_index),
            uv=pw.reducers.avg(pw.this.uv_index),
            last_updated=pw.reducers.max(pw.this.timestamp)
        )

        return latest.select(
            timestamp=latest.last_updated,
            category=pw.apply(lambda x: "environment", str),
            insight=pw.apply(
                lambda t, h, a, u:
                f"Environment: {t:.1f}C, {h:.0f}% humidity, AQI {a:.0f}, UV {u:.1f}",
                latest.temperature, latest.humidity, latest.aqi, latest.uv
            ),
            confidence=pw.apply(
                lambda a: min(1.0, float(a) / 200.0) if a is not None else 0.0,
                latest.aqi
            ),
            recommended_action=pw.apply(
                lambda a, u: "Issue health advisory" if (a is not None and a > 150) or (u is not None and u > 8) else "Normal conditions",
                latest.aqi, latest.uv
            )
        )

    def generate_llm_summary(
        self,
        traffic_insights: pw.Table,
        transit_insights: pw.Table,
        env_insights: pw.Table
    ) -> pw.Table:
        """
        Use LLM to generate holistic urban planning recommendations
        by combining all insight streams.
        """
        # Union all insights
        all_insights = traffic_insights.concat(
            transit_insights
        ).concat(
            env_insights
        )

        # Aggregate recent insights into context
        context = all_insights.reduce(
            summary=pw.reducers.concat_str(pw.this.insight, separator="\n")
        )

        prompt = pw.apply(
            lambda ctx:
            f"""You are an urban planning AI assistant. Based on the following real-time city data, provide a concise summary and 3 actionable recommendations for city operators:

{ctx}

Respond in this format:
Summary: [one paragraph]
Recommendations:
1. [action]
2. [action]
3. [action]""",
            context.summary
        )

        llm_response = self.llm(prompt)

        return all_insights.select(
            timestamp=pw.this.timestamp,
            category=pw.apply(lambda x: "planning_summary", str),
            insight=llm_response,
            confidence=pw.apply(lambda x: 0.95, float),
            recommended_action=pw.apply(lambda x: "See insight", str)
        )
