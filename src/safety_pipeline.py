"""Real-time public safety anomaly detection using Pathway LLM App patterns.

Uses BaseRAGQuestionAnswerer, VectorStoreServer, and OpenAIChat
following the exact patterns from pathwaycom/llm-app templates.
"""
import pathway as pw
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer

from src.schemas import SafetyAlertSchema, IoTReadingSchema, AnomalySchema


class SafetyAnomalyDetector:
    """
    Real-time anomaly detection combining rule-based filters
    with LLM-powered semantic analysis via Pathway's dynamic RAG.

    Follows the llm-app pattern: VectorStoreServer for indexing,
    BaseRAGQuestionAnswerer for RAG queries.
    """

    def __init__(self, llm_config: dict):
        self.embedder = embedders.OpenAIEmbedder(
            model=llm_config.get("embedding_model", "text-embedding-3-small")
        )
        self.llm = llms.OpenAIChat(
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 512)
        )
        self.parser = parsers.UnstructuredParser()
        self.splitter = splitters.TokenCountSplitter(max_tokens=256)

    def apply_rules(self, iot_table: pw.Table, rules: list[dict]) -> pw.Table:
        """Apply configurable rule-based anomaly detection."""
        # Build anomaly table incrementally
        all_anomalies = None

        for rule in rules:
            field = rule["field"]
            condition = rule["condition"]
            severity = rule["severity"]

            # Parse condition (e.g., "> 80")
            op = condition.split()[0]
            threshold = float(condition.split()[1])

            if field == "temperature_c":
                flagged = iot_table.filter(pw.this.temperature_c > threshold)
            elif field == "crowd_count":
                flagged = iot_table.filter(pw.this.crowd_count > threshold)
            elif field == "decibel":
                flagged = iot_table.filter(pw.this.decibel > threshold)
            else:
                continue

            # Enrich with anomaly metadata matching AnomalySchema
            flagged = flagged.select(
                timestamp=pw.this.timestamp,
                source=pw.apply(lambda x: f"IoT-{x}", pw.this.sensor_id),
                anomaly_type=pw.apply(lambda x: x, field),
                description=pw.apply(
                    lambda s, v, t: f"Sensor {s}: {field}={v} exceeds threshold {t}",
                    pw.this.sensor_id, pw.this[field], threshold
                ),
                severity=pw.apply(lambda x: x, severity),
                location_lat=pw.this.location_lat,
                location_lon=pw.this.location_lon,
                raw_data=pw.this
            )

            if all_anomalies is None:
                all_anomalies = flagged
            else:
                all_anomalies = all_anomalies.concat(flagged)

        return all_anomalies if all_anomalies is not None else iot_table.filter(False)

    def build_vector_store(self, alerts_table: pw.Table) -> VectorStoreServer:
        """
        Build a live vector index over safety alerts.
        Pathway updates this automatically as new alerts arrive.
        Follows the llm-app VectorStoreServer pattern.
        """
        # Prepare documents for embedding
        docs = alerts_table.select(
            data=pw.this.description,
            metadata=pw.apply(
                lambda t, s, lat, lon: f"type:{t}|severity:{s}|lat:{lat}|lon:{lon}",
                pw.this.alert_type, pw.this.severity, pw.this.location_lat, pw.this.location_lon
            )
        )

        # Create live vector store server with built-in usearch index
        # This is the exact pattern from llm-app templates
        vector_server = VectorStoreServer(
            docs,
            embedder=self.embedder,
            splitter=self.splitter,
            parser=self.parser
        )

        return vector_server

    def create_rag_answerer(self, vector_server: VectorStoreServer) -> BaseRAGQuestionAnswerer:
        """
        Create a RAG question-answerer following llm-app BaseRAGQuestionAnswerer pattern.
        Provides /v2/answer endpoint automatically.
        """
        rag = BaseRAGQuestionAnswerer(
            llm=self.llm,
            indexer=vector_server,
            embedder=self.embedder,
            search_topk=5
        )
        return rag
