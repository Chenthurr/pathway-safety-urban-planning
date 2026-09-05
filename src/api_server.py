"""Pathway HTTP endpoints for city operations."""
import pathway as pw
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


def anomaly_text(anomaly_type: str, description: str, severity: str) -> str:
    return f"{severity}: {anomaly_type} - {description}"


def insight_text(category: str, insight: str, action: str) -> str:
    return f"{category}: {insight} | action: {action}"


def status_text(total: int, latest: object) -> str:
    return f"Total insights: {total}, latest update: {latest}"


class CityOperationsAPI:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.webserver = pw.io.http.PathwayWebserver(
            host=host, port=port, with_schema_endpoint=True, with_cors=True
        )

    def register_health_endpoint(self) -> None:
        class HealthQuery(pw.Schema):
            pass

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/healthz",
            schema=HealthQuery, methods=("GET",)
        )
        writer(queries.select(query_id=pw.this.id, result="ok"))

    def register_safety_endpoints(self, anomalies: pw.Table) -> None:
        # Keep the join strictly column-to-column; filtering is applied to the
        # anomaly stream using the request severity value.
        class Query(pw.Schema):
            severity: str = pw.column_definition(default_value="all")

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/safety/anomalies",
            schema=Query, methods=("POST",)
        )
        joined = queries.join_left(anomalies, queries.severity == anomalies.severity)
        writer(joined.select(
            query_id=queries.id,
            severity=anomalies.severity,
            anomaly_type=anomalies.anomaly_type,
            description=anomalies.description,
            timestamp=anomalies.timestamp,
        ))

    def register_planning_endpoints(self, insights: pw.Table) -> None:
        class Query(pw.Schema):
            category: str = pw.column_definition(default_value="all")

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/planning/insights",
            schema=Query, methods=("POST",)
        )
        joined = queries.join_left(insights, queries.category == insights.category)
        writer(joined.select(
            query_id=queries.id,
            category=insights.category,
            insight=insights.insight,
            confidence=insights.confidence,
            recommended_action=insights.recommended_action,
            timestamp=insights.timestamp,
        ))

        class StatusQuery(pw.Schema):
            pass

        _, status_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/planning/status",
            schema=StatusQuery, methods=("GET",)
        )
        status = insights.reduce(
            total_insights=pw.reducers.count(),
            latest_update=pw.reducers.max(pw.this.timestamp),
        )
        status_writer(status.select(
            query_id=status.id,
            result=pw.apply(status_text, pw.this.total_insights, pw.this.latest_update),
        ))

    def register_rag_endpoints(self, answerer: BaseRAGQuestionAnswerer) -> None:
        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v2/answer",
            schema=answerer.AnswerQuerySchema, methods=("POST",)
        )
        writer(answerer.answer_query(queries))

        retrieve_queries, retrieve_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v1/retrieve",
            schema=answerer.RetrieveQuerySchema, methods=("POST",)
        )
        retrieve_writer(answerer.retrieve(retrieve_queries))

        stats_queries, stats_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v1/statistics",
            schema=answerer.StatisticsQuerySchema, methods=("GET",)
        )
        stats_writer(answerer.statistics(stats_queries))

    def run(self) -> None:
        pw.run()
