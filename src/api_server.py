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
                    "Gemini RAG assistant: enabled\n"
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
        """Return live anomaly rows using Pathway's id/result REST contract."""

        class Query(pw.Schema):
            severity: str = pw.column_definition(default_value="critical")

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/safety/anomalies",
            schema=Query,
            methods=("POST",),
        )

        joined = queries.join(anomalies, queries.severity == anomalies.severity)
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
                anomalies.timestamp,
                anomalies.source,
                anomalies.anomaly_type,
                anomalies.description,
                anomalies.severity,
                anomalies.location_lat,
                anomalies.location_lon,
            ),
        )
        writer(result)

    def register_planning_endpoints(self, insights: pw.Table) -> None:
        class Query(pw.Schema):
            category: str = pw.column_definition(default_value="traffic")

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

        stats_queries, stats_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/v1/statistics",
            schema=answerer.StatisticsQuerySchema,
            methods=("GET",),
        )
        stats_writer(answerer.statistics(stats_queries))

    def run(self) -> None:
        pw.run()
