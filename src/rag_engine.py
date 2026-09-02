"""Unified city RAG index and question answering."""
import pathway as pw
from pathway.xpacks.llm import embedders, llms, splitters
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


class CityRAGEngine:
    def __init__(self, llm_config: dict):
        self.embedder = embedders.OpenAIEmbedder(
            model=llm_config.get("embedding_model", "text-embedding-3-small")
        )
        self.llm = llms.OpenAIChat(
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 1024),
        )
        self.splitter = splitters.TokenCountSplitter(max_tokens=400)

    def build_unified_index(self, alerts: pw.Table, insights: pw.Table) -> VectorStoreServer:
        alert_docs = alerts.select(
            data=pw.this.description,
            metadata=pw.apply(
                lambda alert_type, severity: f"type:alert|alert_type:{alert_type}|severity:{severity}",
                pw.this.alert_type, pw.this.severity,
            ),
        )
        insight_docs = insights.select(
            data=pw.this.insight,
            metadata=pw.apply(
                lambda category, action: f"type:insight|category:{category}|action:{action}",
                pw.this.category, pw.this.recommended_action,
            ),
        )
        docs = alert_docs.concat_reindex(insight_docs)
        return VectorStoreServer(docs, embedder=self.embedder, splitter=self.splitter)

    def create_rag_answerer(self, vector_server: VectorStoreServer) -> BaseRAGQuestionAnswerer:
        return BaseRAGQuestionAnswerer(
            llm=self.llm,
            indexer=vector_server,
            embedder=self.embedder,
            search_topk=5,
        )
