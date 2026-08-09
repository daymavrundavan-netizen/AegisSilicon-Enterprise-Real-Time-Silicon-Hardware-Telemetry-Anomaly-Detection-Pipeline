"""
AegisSilicon Vector Store & RAG Knowledge Base.
Indexes hardware maintenance runbooks using vector embeddings for context-aware SDC diagnosis.
"""

from typing import List, Dict
from agent.hardware_runbooks import HARDWARE_RUNBOOKS

class RAGKnowledgeBase:
    """
    Vector search knowledge base for hardware runbooks.
    """

    def __init__(self):
        self.runbooks = HARDWARE_RUNBOOKS
        self.chroma_collection = None
        self._init_vector_store()

    def _init_vector_store(self):
        """Initialize ChromaDB collection if available."""
        try:
            import chromadb
            client = chromadb.Client()
            self.chroma_collection = client.get_or_create_collection("sdc_hardware_runbooks")
            
            ids = [r["id"] for r in self.runbooks]
            documents = [
                f"{r['title']} | Fault: {r['fault_category']} | Symptoms: {r['symptoms']} | Root Cause: {r['root_cause']}"
                for r in self.runbooks
            ]
            metadatas = [
                {"track": r["remediation_track"], "title": r["title"]}
                for r in self.runbooks
            ]
            
            self.chroma_collection.add(ids=ids, documents=documents, metadatas=metadatas)
            print("[AegisSilicon RAG] Vector store indexed successfully with ChromaDB.")
        except Exception as e:
            print(f"[AegisSilicon RAG] ChromaDB unavailable ({e}). Using semantic keyword fallback vector search.")
            self.chroma_collection = None

    def query_runbook(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Query vector store for relevant hardware runbooks matching symptom or anomaly payload.
        """
        if self.chroma_collection:
            try:
                results = self.chroma_collection.query(query_texts=[query], n_results=top_k)
                matched_ids = results["ids"][0]
                return [r for r in self.runbooks if r["id"] in matched_ids]
            except Exception as err:
                print(f"[Chroma Query Error] {err}")

        # Fallback keyword match score
        query_words = set(query.lower().split())
        scored = []
        for r in self.runbooks:
            doc_text = f"{r['title']} {r['symptoms']} {r['root_cause']} {r['fault_category']}".lower()
            score = sum(1 for word in query_words if word in doc_text)
            scored.append((score, r))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
