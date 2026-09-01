"""Unified REST API server using Pathway's native HTTP connector.

Follows the exact pattern from pathwaycom/llm-app:
- PathwayWebserver for the HTTP server
- rest_connector for endpoints
- BaseRAGQuestionAnswerer for /v2/answer
- VectorStoreServer for /v1/retrieve and /v1/statistics

No FastAPI/Flask needed - everything is native Pathway.
"""
import pathway as pw
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


class CityOperationsAPI:
    """
    Real-time API server powered by Pathway's native HTTP connector.

    Provides endpoints:
    - POST /v2/answer       - RAG Q&A over city data
    - POST /v1/retrieve    - Vector similarity search
    - GET  /v1/statistics  - Index health stats
    - POST /safety/anomalies - Get current anomalies
    - POST /planning/insights - Get city insights
    - GET  /planning/status   - City health dashboard
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.webserver = pw.io.http.PathwayWebserver(
            host=host,
            port=port,
            with_schema_endpoint=True,   # Auto OpenAPI docs at /_schema
            with_cors=True               # Allow cross-origin requests
        )

    def register_safety_endpoints(self, anomaly_table: pw.Table):
        """Register public safety REST endpoints."""

        # POST /safety/anomalies - Get current anomalies
        class AnomalyQuerySchema(pw.Schema):
            severity: str = pw.ColumnDefinition(default_value="all")
            limit: int = pw.ColumnDefinition(default_value=10)

        queries, response_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/safety/anomalies",
            schema=AnomalyQuerySchema,
            methods=("POST",)
        )

        # Filter anomalies by severity
        filtered = anomaly_table.filter(
            pw.this.severity == queries.severity
            if queries.severity != "all"
            else True
        )

        results = filtered.select(
            query_id=pw.this.id,
            result=pw.apply(lambda x: str(x), pw.this)
        ).limit(queries.limit)

        response_writer(results)

    def register_planning_endpoints(self, insights_table: pw.Table):
        """Register urban planning REST endpoints."""

        # POST /planning/insights - Get current city insights
        class InsightQuerySchema(pw.Schema):
            category: str = pw.ColumnDefinition(default_value="all")
            limit: int = pw.ColumnDefinition(default_value=20)

        queries, response_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/planning/insights",
            schema=InsightQuerySchema,
            methods=("POST",)
        )

        filtered = insights_table.filter(
            pw.this.category == queries.category
            if queries.category != "all"
            else True
        )

        results = filtered.select(
            query_id=pw.this.id,
            result=pw.apply(lambda x: str(x), pw.this)
        ).limit(queries.limit)

        response_writer(results)

        # GET /planning/status - City health dashboard
        class StatusQuerySchema(pw.Schema):
            pass

        status_queries, status_writer = pw.io.http.rest_connector(
            webserver=self.webserver,
            route="/planning/status",
            schema=StatusQuerySchema,
            methods=("GET",)
        )

        # Aggregate latest metrics
        status = insights_table.reduce(
            total_insights=pw.reducers.count(pw.this),
            latest_update=pw.reducers.max(pw.this.timestamp),
            categories=pw.reducers.tuple(pw.this.category)
        )

        status_results = status.select(
            query_id=status.id,
            result=pw.apply(
                lambda t, c, cats: f"Total insights: {t}, Latest: {c}, Categories: {set(cats)}",
                status.total_insights, status.latest_update, status.categories
            )
        )

        status_writer(status_results)

    def register_rag_endpoints(
        self,
        rag_answerer: BaseRAGQuestionAnswerer,
        vector_server: VectorStoreServer
    ):
        """
        Register RAG endpoints following llm-app pattern.
        BaseRAGQuestionAnswerer automatically provides /v2/answer.
        VectorStoreServer provides /v1/retrieve and /v1/statistics.
        """
        # The BaseRAGQuestionAnswerer handles /v2/answer internally
        # when connected to the webserver
        rag_answerer.answer_query(self.webserver)

        # Vector store retrieval endpoint
        vector_server.run_server(
            host=self.host,
            port=self.port,
            threaded=True  # Run in same process
        )

    def run(self):
        """Start the Pathway computation."""
        pw.run()
