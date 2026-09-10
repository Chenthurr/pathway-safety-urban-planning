"""Pathway HTTP endpoints for city operations."""
import json

import pathway as pw
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


class CityOperationsAPI:
    """Expose the live Pathway tables and RAG answerer over HTTP."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.webserver = pw.io.http.PathwayWebserver(
            host=host, port=port, with_schema_endpoint=True, with_cors=True
        )

    def _rest(self, route: str, schema, methods):
        return pw.io.http.rest_connector(
            webserver=self.webserver,
            route=route,
            schema=schema,
            methods=methods,
            autocommit_duration_ms=50,
            delete_completed_queries=True,
        )

    def register_root_endpoint(self) -> None:
        class RootQuery(pw.Schema):
            pass

        queries, writer = self._rest("/", RootQuery, ("GET",))
        writer(queries.select(
            query_id=queries.id,
            result=(
                "Pathway Urban Safety & Planning\n"
                "STATUS: ONLINE\n"
                "Live data pipeline: running\n"
                "Safety anomaly detection: enabled\n"
                "Urban planning insights: enabled\n"
                "AI RAG assistant: enabled\n"
                "API: /healthz /safety/anomalies /planning/insights /v2/answer"
            ),
        ))

    def register_health_endpoint(self) -> None:
        class HealthQuery(pw.Schema):
            pass

        queries, writer = self._rest("/healthz", HealthQuery, ("GET",))
        writer(queries.select(query_id=queries.id, result="ok"))

    def register_safety_endpoints(self, anomalies: pw.Table) -> None:
        class Query(pw.Schema):
            severity: str = pw.column_definition(default_value="all")

        queries, writer = self._rest("/safety/anomalies", Query, ("POST",))

        all_anomalies = anomalies.select(
            timestamp=pw.this.timestamp,
            source=pw.this.source,
            anomaly_type=pw.this.anomaly_type,
            description=pw.this.description,
            severity="all",
            location_lat=pw.this.location_lat,
            location_lon=pw.this.location_lon,
            raw_data=pw.this.raw_data,
        )
        queryable = anomalies.select(
            timestamp=pw.this.timestamp,
            source=pw.this.source,
            anomaly_type=pw.this.anomaly_type,
            description=pw.this.description,
            severity=pw.this.severity,
            location_lat=pw.this.location_lat,
            location_lon=pw.this.location_lon,
            raw_data=pw.this.raw_data,
        ).concat_reindex(all_anomalies)

        joined = queries.join(queryable, queries.severity == queryable.severity)
        writer(joined.select(
            query_id=queries.id,
            result=pw.apply(
                lambda timestamp, source, anomaly_type, description, severity, lat, lon: json.dumps({
                    "timestamp": str(timestamp),
                    "source": source,
                    "anomaly_type": anomaly_type,
                    "description": description,
                    "severity": severity,
                    "location_lat": lat,
                    "location_lon": lon,
                }),
                queryable.timestamp,
                queryable.source,
                queryable.anomaly_type,
                queryable.description,
                queryable.severity,
                queryable.location_lat,
                queryable.location_lon,
            ),
        ))

    def register_planning_endpoints(self, insights: pw.Table) -> None:
        class Query(pw.Schema):
            category: str = pw.column_definition(default_value="all")

        queries, writer = self._rest("/planning/insights", Query, ("POST",))
        joined = queries.join(insights, queries.category == insights.category)
        writer(joined.select(
            query_id=queries.id,
            result=pw.apply(
                lambda timestamp, category, insight, confidence, action: json.dumps({
                    "timestamp": str(timestamp),
                    "category": category,
                    "insight": insight,
                    "confidence": confidence,
                    "recommended_action": action,
                }),
                insights.timestamp,
                insights.category,
                insights.insight,
                insights.confidence,
                insights.recommended_action,
            ),
        ))

        class StatusQuery(pw.Schema):
            pass

        status_queries, status_writer = self._rest("/planning/status", StatusQuery, ("GET",))
        status_writer(status_queries.select(
            query_id=status_queries.id, result="insights pipeline is running"
        ))

    def register_rag_endpoints(self, answerer: BaseRAGQuestionAnswerer) -> None:
        queries, writer = self._rest(
            "/v2/answer", answerer.AnswerQuerySchema, ("POST",)
        )
        writer(answerer.answer_query(queries))

        retrieve_queries, retrieve_writer = self._rest(
            "/v1/retrieve", answerer.RetrieveQuerySchema, ("POST",)
        )
        retrieve_writer(answerer.retrieve(retrieve_queries))

        stats_queries, stats_writer = self._rest(
            "/v1/statistics", answerer.StatisticsQuerySchema, ("GET", "POST")
        )
        stats_writer(answerer.statistics(stats_queries))

    def run(self) -> None:
        pw.run()
