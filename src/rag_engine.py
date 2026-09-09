"""Unified city RAG index and question answering."""
import pathway as pw
from pathway.xpacks.llm import embedders, llms, splitters
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


def metadata_alert(alert_type: str, severity: str) -> str:
    return f"type:alert|alert_type:{alert_type}|severity:{severity}"


def metadata_insight(category: str, action: str) -> str:
    return f"type:insight|category:{category}|action:{action}"


class CityRAGEngine:
    def __init__(self, llm_config: dict):
        self.embedder = embedders.GeminiEmbedder(
            model=llm_config.get("embedding_model", "gemini-embedding-001")
        )
        self.llm = llms.LiteLLMChat(
            model=llm_config.get("model", "gemini/gemini-2.5-flash"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 1024),
        )
        self.splitter = splitters.TokenCountSplitter(max_tokens=400)

    def build_unified_index(self, alerts: pw.Table, insights: pw.Table) -> VectorStoreServer:
        alert_docs = alerts.select(
            data=pw.this.description,
            metadata=pw.apply(metadata_alert, pw.this.alert_type, pw.this.severity),
        )
        insight_docs = insights.select(
            data=pw.this.insight,
            metadata=pw.apply(metadata_insight, pw.this.category, pw.this.recommended_action),
        )
        docs = alert_docs.concat_reindex(insight_docs)
        return VectorStoreServer(docs, embedder=self.embedder, splitter=self.splitter)

    def create_rag_answerer(self, vector_server: VectorStoreServer) -> BaseRAGQuestionAnswerer:
        return BaseRAGQuestionAnswerer(
            llm=self.llm,
            indexer=vector_server,
            search_topk=5,
        )
