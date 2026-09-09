"""Real-time public safety anomaly detection using Pathway LLM App patterns.

Uses Gemini for all LLM-backed components so the unified Render deployment
only requires GOOGLE_API_KEY.
"""
import pathway as pw

from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


def anomaly_description(sensor: str, field: str, value: object, threshold: float) -> str:
    return f"Sensor {sensor}: {field}={value} exceeds threshold {threshold}"


def raw_sensor(sensor: str) -> str:
    return str(sensor)


def alert_metadata(alert_type: str, severity: str, lat: float, lon: float) -> str:
    return f"type:{alert_type}|severity:{severity}|lat:{lat}|lon:{lon}"


class SafetyAnomalyDetector:
    """Real-time anomaly detection with optional Pathway RAG support."""

    def __init__(self, llm_config: dict):
        self.embedder = embedders.GeminiEmbedder(
            model=llm_config.get("embedding_model", "models/text-embedding-004")
        )
        self.llm = llms.LiteLLMChat(
            model=llm_config.get("model", "gemini/gemini-2.5-flash"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 1024),
        )
        self.parser = parsers.UnstructuredParser()
        self.splitter = splitters.TokenCountSplitter(max_tokens=256)

    def apply_rules(self, iot_table: pw.Table, rules: list[dict]) -> pw.Table:
        """Apply configurable rule-based anomaly detection."""
        anomaly_tables = []
        for rule in rules:
            field = rule["field"]
            condition = rule["condition"]
            severity = rule["severity"]
            op, threshold_text = condition.split(maxsplit=1)
            threshold = float(threshold_text)

            if field == "temperature_c":
                value_expr = pw.this.temperature_c
                flagged = iot_table.filter(value_expr > threshold)
            elif field == "crowd_count":
                value_expr = pw.this.crowd_count
                flagged = iot_table.filter(value_expr > threshold)
            elif field == "decibel":
                value_expr = pw.this.decibel
                flagged = iot_table.filter(value_expr > threshold)
            else:
                continue

            anomaly_tables.append(flagged.select(
                timestamp=pw.this.timestamp,
                source=pw.this.sensor_id,
                anomaly_type=field,
                description=pw.apply(anomaly_description, pw.this.sensor_id, field, value_expr, threshold),
                severity=severity,
                location_lat=pw.this.location_lat,
                location_lon=pw.this.location_lon,
                raw_data=pw.apply(raw_sensor, pw.this.sensor_id),
            ))

        if not anomaly_tables:
            return iot_table.select(
                timestamp=pw.this.timestamp,
                source=pw.this.sensor_id,
                anomaly_type=pw.apply(lambda _: "", pw.this.sensor_id),
                description=pw.apply(lambda _: "", pw.this.sensor_id),
                severity=pw.apply(lambda _: "", pw.this.sensor_id),
                location_lat=pw.this.location_lat,
                location_lon=pw.this.location_lon,
                raw_data=pw.apply(lambda s: str(s), pw.this.sensor_id),
            ).filter(False)

        flagged_anomalies = anomaly_tables[0].concat_reindex(*anomaly_tables[1:])
        all_severity_copy = flagged_anomalies.select(
            timestamp=pw.this.timestamp,
            source=pw.this.source,
            anomaly_type=pw.this.anomaly_type,
            description=pw.this.description,
            severity="all",
            location_lat=pw.this.location_lat,
            location_lon=pw.this.location_lon,
            raw_data=pw.this.raw_data,
        )
        return flagged_anomalies.concat_reindex(all_severity_copy)

    def build_vector_store(self, alerts_table: pw.Table) -> VectorStoreServer:
        """Build a live vector index over safety alerts."""
        docs = alerts_table.select(
            data=pw.this.description,
            metadata=pw.apply(
                alert_metadata,
                pw.this.alert_type,
                pw.this.severity,
                pw.this.location_lat,
                pw.this.location_lon,
            ),
        )
        return VectorStoreServer(
            docs,
            embedder=self.embedder,
            splitter=self.splitter,
            parser=self.parser,
        )

    def create_rag_answerer(self, vector_server: VectorStoreServer) -> BaseRAGQuestionAnswerer:
        """Create a Pathway RAG question-answerer."""
        return BaseRAGQuestionAnswerer(
            llm=self.llm,
            indexer=vector_server,
            embedder=self.embedder,
            search_topk=5,
        )
