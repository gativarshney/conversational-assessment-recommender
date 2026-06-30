import os
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class CatalogRetriever:
    """
    Handles indexing and similarity search for the SHL assessment catalog.
    Uses ChromaDB for vector storage and Sentence-Transformers for local embeddings.
    """
    def __init__(self, db_path: str, collection_name: str = "shl_assessments") -> None:
        self.db_path = db_path
        self.collection_name = collection_name
        
        # 1. Initialize persistent ChromaDB client
        logger.info(f"Connecting to ChromaDB at: {db_path}")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 2. Load local sentence embedding model
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # 3. Get or create the vector collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

    def _format_document_text(self, item: Dict[str, Any]) -> str:
        """Constructs a rich text representation of the assessment to generate accurate embeddings."""
        keys_str = ", ".join(item.get("keys", []))
        levels_str = ", ".join(item.get("job_levels", []))
        lang_str = ", ".join(item.get("languages", []))
        
        doc_parts = [
            f"Name: {item.get('name', '')}",
            f"Test Type: {item.get('test_type', '')}",
            f"Categories: {keys_str}",
            f"Target Levels: {levels_str}",
            f"Languages: {lang_str}",
            f"Duration: {item.get('duration', 'N/A')}",
            f"Description: {item.get('description', '')}"
        ]
        return "\n".join(doc_parts)

    def _serialize_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Converts lists and other complex properties into strings for ChromaDB metadata."""
        return {
            "entity_id": str(item.get("entity_id", "")),
            "name": str(item.get("name", "")),
            "link": str(item.get("link", "")),
            "test_type": str(item.get("test_type", "")),
            "description": str(item.get("description", "")),
            "keys_json": json.dumps(item.get("keys", [])),
            "job_levels_json": json.dumps(item.get("job_levels", [])),
            "languages_json": json.dumps(item.get("languages", [])),
            "duration": str(item.get("duration", "")),
            "remote": str(item.get("remote", "")),
            "adaptive": str(item.get("adaptive", ""))
        }

    def _deserialize_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Restores serialized lists back to standard lists."""
        return {
            "entity_id": meta.get("entity_id", ""),
            "name": meta.get("name", ""),
            "link": meta.get("link", ""),
            "description": meta.get("description", ""),
            "test_type": meta.get("test_type", ""),
            "keys": json.loads(meta.get("keys_json", "[]")),
            "job_levels": json.loads(meta.get("job_levels_json", "[]")),
            "languages": json.loads(meta.get("languages_json", "[]")),
            "duration": meta.get("duration", ""),
            "remote": meta.get("remote", ""),
            "adaptive": meta.get("adaptive", "")
        }

    def add_documents(self, items: List[Dict[str, Any]]) -> None:
        """Computes embeddings and stores catalog documents in the vector database."""
        if not items:
            return
            
        logger.info(f"Generating embeddings and indexing {len(items)} items...")
        
        ids = []
        documents = []
        metadatas = []
        
        for item in items:
            doc_text = self._format_document_text(item)
            meta = self._serialize_metadata(item)
            
            ids.append(meta["entity_id"])
            documents.append(doc_text)
            metadatas.append(meta)
            
        # Compute embeddings locally
        embeddings = self.model.encode(documents, show_progress_bar=False).tolist()
        
        # Insert or update in batches (Chroma handles upsert)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        logger.info("Catalog items successfully indexed.")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Queries the vector database for matching assessments."""
        if not query:
            return []
            
        logger.debug(f"Retrieving matching items for query: '{query}' (top_k={top_k})")
        # Embed the query string
        query_embedding = self.model.encode([query]).tolist()[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        retrieved_items = []
        if results and "metadatas" in results and results["metadatas"] and len(results["metadatas"][0]) > 0:
            metadatas = results["metadatas"][0]
            for meta in metadatas:
                retrieved_items.append(self._deserialize_metadata(meta))
                
        return retrieved_items

    def count(self) -> int:
        """Returns the number of documents currently stored in the collection."""
        return self.collection.count()
