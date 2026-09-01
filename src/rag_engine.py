"""Dynamic RAG engine for unified city operations.

Uses Pathway LLM App patterns:
- VectorStoreServer for live document indexing
- BaseRAGQuestionAnswerer for RAG Q&A
- Follows the exact structure from pathwaycom/llm-app templates
"""
import pathway as pw
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer


class CityRAGEngine:
    """
    Real-time RAG system that indexes both safety alerts
    and urban planning insights. Automatically updates
    as new data arrives.

    Pattern: Document ingestion -> VectorStoreServer -> BaseRAGQuestionAnswerer
    """

    def __init__(self, llm_config: dict):
        self.embedder = embedders.OpenAIEmbedder(
            model=llm_config.get("embedding_model", "text-embedding-3-small")
        )
        self.llm = llms.OpenAIChat(
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 1024)
        )
        self.parser = parsers.UnstructuredParser()
        self.splitter = splitters.TokenCountSplitter(max_tokens=400)

    def build_unified_index(
        self,
        alerts_table: pw.Table,
        insights_table: pw.Table
    ) -> VectorStoreServer:
        """
        Build a unified live vector index from safety alerts and planning insights.
        Pathway automatically updates embeddings when data changes.
        """
        # Convert alerts to documents
        alert_docs = alerts_table.select(
            data=pw.this.description,
            metadata=pw.apply(
                lambda t, s, lat, lon: f"type:alert|alert_type:{t}|severity:{s}|lat:{lat}|lon:{lon}",
                pw.this.alert_type, pw.this.severity, pw.this.location_lat, pw.this.location_lon
            )
        )

        # Convert insights to documents
        insight_docs = insights_table.select(
            data=pw.this.insight,
            metadata=pw.apply(
                lambda c, a: f"type:insight|category:{c}|action:{a}",
                pw.this.category, pw.this.recommended_action
            )
        )

        # Union all documents
        all_docs = alert_docs.concat(insight_docs)

        # Build vector store server - exact llm-app pattern
        server = VectorStoreServer(
            all_docs,
            embedder=self.embedder,
            splitter=self.splitter,
            parser=self.parser
        )

        return server

    def create_rag_answerer(self, vector_server: VectorStoreServer) -> BaseRAGQuestionAnswerer:
        """
        Create a RAG question-answerer following llm-app pattern.
        Exposes /v2/answer endpoint for city operations queries.
        """
        rag = BaseRAGQuestionAnswerer(
            llm=self.llm,
            indexer=vector_server,
            embedder=self.embedder,
            search_topk=5
        )
        return rag
