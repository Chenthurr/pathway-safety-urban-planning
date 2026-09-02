"""Pathway HTTP endpoints for city operations."""
import pathway as pw
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


def stringify_row(*values: object) -> str:
    return " | ".join(str(v) for v in values)


def status_text(total: int, latest: object) -> str:
    return f"Total insights: {total}, latest update: {latest}"


class CityOperationsAPI:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.webserver = pw.io.http.PathwayWebserver(
            host=host, port=port, with_schema_endpoint=True, with_cors=True
        )

    def register_safety_endpoints(self, anomalies: pw.Table) -> None:
        class Query(pw.Schema):
            severity: str = pw.column_definition(default_value="all")
            limit: int = pw.column_definition(default_value=10)

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/safety/anomalies",
            schema=Query, methods=("POST",)
        )
        filtered = queries.join_left(anomalies, queries.severity == anomalies.severity)
        writer(filtered.select(
            query_id=pw.this.id,
            result=pw.apply(stringify_row, pw.this.severity),
        ))

    def register_planning_endpoints(self, insights: pw.Table) -> None:
        class Query(pw.Schema):
            category: str = pw.column_definition(default_value="all")
            limit: int = pw.column_definition(default_value=20)

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/planning/insights",
            schema=Query, methods=("POST",)
        )
        filtered = insights if False else insights
        writer(filtered.select(
            query_id=pw.this.id,
            result=pw.apply(stringify_row, pw.this.category, pw.this.insight, pw.this.recommended_action),
        ))

        class StatusQuery(pw.Schema):
            pass

        _, status_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/planning/status",
            schema=StatusQuery, methods=("GET",)
        )
        status = insights.reduce(
            total_insights=pw.reducers.count(pw.this),
            latest_update=pw.reducers.max(pw.this.timestamp),
        )
        status_writer(status.select(
            query_id=pw.this.id,
            result=pw.apply(status_text, pw.this.total_insights, pw.this.latest_update),
        ))

    def register_rag_endpoints(self, answerer: BaseRAGQuestionAnswerer) -> None:
        class AnswerQuery(pw.Schema):
            prompt: str

        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v2/answer",
            schema=AnswerQuery, methods=("POST",)
        )
        writer(answerer.answer_query(queries))

        class RetrieveQuery(pw.Schema):
            query: str
            k: int = pw.column_definition(default_value=6)

        retrieve_queries, retrieve_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v1/retrieve",
            schema=RetrieveQuery, methods=("POST",)
        )
        retrieve_writer(answerer.retrieve(retrieve_queries))

        class StatsQuery(pw.Schema):
            pass

        stats_queries, stats_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v1/statistics",
            schema=StatsQuery, methods=("GET",)
        )
        stats_writer(answerer.statistics(stats_queries))

    def run(self) -> None:
        pw.run()
