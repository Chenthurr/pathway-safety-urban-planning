"""Unified REST API server using Pathway's native HTTP connector."""
import pathway as pw
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


class CityOperationsAPI:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.webserver = pw.io.http.PathwayWebserver(
            host=host, port=port, with_schema_endpoint=True, with_cors=True
        )

    def register_safety_endpoints(self, anomaly_table: pw.Table):
        class AnomalyQuerySchema(pw.Schema):
            severity: str = pw.column_definition(default_value="all")
            limit: int = pw.column_definition(default_value=10)
        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/safety/anomalies",
            schema=AnomalyQuerySchema, methods=("POST",)
        )
        filtered = anomaly_table.filter(
            (pw.this.severity == queries.severity) if queries.severity != "all" else True
        )
        writer(filtered.select(
            query_id=pw.this.id, result=pw.apply(lambda x: str(x), pw.this)
        ).limit(queries.limit))

    def register_planning_endpoints(self, insights_table: pw.Table):
        class InsightQuerySchema(pw.Schema):
            category: str = pw.column_definition(default_value="all")
            limit: int = pw.column_definition(default_value=20)
        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/planning/insights",
            schema=InsightQuerySchema, methods=("POST",)
        )
        filtered = insights_table.filter(
            (pw.this.category == queries.category) if queries.category != "all" else True
        )
        writer(filtered.select(
            query_id=pw.this.id, result=pw.apply(lambda x: str(x), pw.this)
        ).limit(queries.limit))

        class StatusQuerySchema(pw.Schema):
            pass
        _, status_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/planning/status",
            schema=StatusQuerySchema, methods=("GET",)
        )
        status = insights_table.reduce(
            total_insights=pw.reducers.count(pw.this),
            latest_update=pw.reducers.max(pw.this.timestamp),
            categories=pw.reducers.tuple(pw.this.category),
        )
        status_writer(status.select(
            query_id=status.id,
            result=pw.apply(
                lambda t, c, cats: f"Total insights: {t}, Latest: {c}, Categories: {set(cats)}",
                status.total_insights, status.latest_update, status.categories
            )
        ))

    def register_rag_endpoints(self, rag_answerer: BaseRAGQuestionAnswerer,
                               vector_server: VectorStoreServer):
        class AnswerQuerySchema(pw.Schema):
            prompt: str
        queries, writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v2/answer",
            schema=AnswerQuerySchema, methods=("POST",)
        )
        writer(rag_answerer.answer_query(queries))

        class RetrieveQuerySchema(pw.Schema):
            query: str
            k: int = pw.column_definition(default_value=6)
        retrieve_queries, retrieve_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v1/retrieve",
            schema=RetrieveQuerySchema, methods=("POST",)
        )
        retrieve_writer(rag_answerer.retrieve(retrieve_queries))

        class StatisticsQuerySchema(pw.Schema):
            pass
        statistics_queries, statistics_writer = pw.io.http.rest_connector(
            webserver=self.webserver, route="/v1/statistics",
            schema=StatisticsQuerySchema, methods=("GET",)
        )
        statistics_writer(rag_answerer.statistics(statistics_queries))

    def run(self):
        pw.run()
