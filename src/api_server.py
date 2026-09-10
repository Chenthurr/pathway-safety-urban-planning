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

    def register_root_endpoint(self) -> None:
        class RootQuery(pw.Schema):
            pass

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/", schema=RootQuery, methods=("GET",)
        )
        writer(
            queries.select(
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
            )
        )

    def register_health_endpoint(self) -> None:
        class HealthQuery(pw.Schema):
            pass

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/healthz",
            schema=HealthQuery,
            methods=("GET",),
        )
        writer(queries.select(query_id=queries.id, result="ok"))

    def register_safety_endpoints(self, anomalies: pw.Table) -> None:
        """Return live anomaly rows and support both a severity and an all query."""

        class Query(pw.Schema):
            severity: str = pw.column_definition(default_value="all")

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/safety/anomalies",
            schema=Query,
            methods=("POST",),
        )

        # Add an explicit `all` category so the dashboard can request the whole
        # live anomaly stream without relying on a non-equality join condition.
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
        queryable_anomalies = anomalies.select(
            timestamp=pw.this.timestamp,
            source=pw.this.source,
            anomaly_type=pw.this.anomaly_type,
            description=pw.this.description,
            severity=pw.this.severity,
            location_lat=pw.this.location_lat,
            location_lon=pw.this.location_lon,
            raw_data=pw.this.raw_data,
        ).concat_reindex(all_anomalies)

        joined = queries.join(queryable_anomalies, queries.severity == queryable_anomalies.severity)
        result = joined.select(
            query_id=queries.id,
            result=pw.apply(
                lambda timestamp, source, anomaly_type, description, severity, lat, lon: json.dumps(
                    {
                        "timestamp": str(timestamp),
                        "source": source,
                        "anomaly_type": anomaly_type,
                        "description": description,
                        "severity": severity,
                        "location_lat": lat,
                        "location_lon": lon,
                    }
                ),
                queryable_anomalies.timestamp,
                queryable_anomalies.source,
                queryable_anomalies.anomaly_type,
                queryable_anomalies.description,
                queryable_anomalies.severity,
                queryable_anomalies.location_lat,
                queryable_anomalies.location_lon,
            ),
        )
        writer(result)

    def register_planning_endpoints(self, insights: pw.Table) -> None:
        class Query(pw.Schema):
            category: str = pw.column_definition(default_value="all")

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/planning/insights",
            schema=Query,
            methods=("POST",),
        )

        joined = queries.join(insights, queries.category == insights.category)
        result = joined.select(
            query_id=queries.id,
            result=pw.apply(
                lambda timestamp, category, insight, confidence, action: json.dumps(
                    {
                        "timestamp": str(timestamp),
                        "category": category,
                        "insight": insight,
                        "confidence": confidence,
                        "recommended_action": action,
                    }
                ),
                insights.timestamp,
                insights.category,
                insights.insight,
                insights.confidence,
                insights.recommended_action,
            ),
        )
        writer(result)

        class StatusQuery(pw.Schema):
            pass

        status_queries, status_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/planning/status",
            schema=StatusQuery,
            methods=("GET",),
        )
        status_writer(
            status_queries.select(
                query_id=status_queries.id,
                result="insights pipeline is running",
            )
        )

    def register_rag_endpoints(self, answerer: BaseRAGQuestionAnswerer) -> None:
        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/v2/answer",
            schema=answerer.AnswerQuerySchema,
            methods=("POST",),
        )
        writer(answerer.answer_query(queries))

        retrieve_queries, retrieve_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/v1/retrieve",
            schema=answerer.RetrieveQuerySchema,
            methods=("POST",),
        )
        retrieve_writer(answerer.retrieve(retrieve_queries))

        # Pathway's RAG statistics endpoint is a POST endpoint in the current
        # question-answering API. The browser clients use the same contract.
        stats_queries, stats_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/v1/statistics",
            schema=answerer.StatisticsQuerySchema,
            methods=("POST",),
        )
        stats_writer(answerer.statistics(stats_queries))

    def run(self) -> None:
        pw.run()
