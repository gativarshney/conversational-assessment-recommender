import os
import json
import logging
from typing import Optional
from app.core.config import settings
from app.retriever import CatalogRetriever
from app.agent import RecommendationAgent

logger = logging.getLogger(__name__)

_retriever: Optional[CatalogRetriever] = None
_agent: Optional[RecommendationAgent] = None

def get_retriever() -> CatalogRetriever:
    """Dependency provider yielding the singleton CatalogRetriever client instance."""
    global _retriever
    if _retriever is None:
        _retriever = CatalogRetriever(db_path=settings.VECTOR_DB_DIR)
        
        # Cold start self-healing: automatically indexes the cleaned JSON catalog if vector DB is empty
        if _retriever.count() == 0:
            cleaned_file = "data/shl_catalog_cleaned.json"
            logger.info("ChromaDB vector store is empty on startup. Initiating self-healing population...")
            if os.path.exists(cleaned_file):
                try:
                    with open(cleaned_file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                    _retriever.add_documents(items)
                    logger.info(f"Successfully auto-indexed {len(items)} catalog items.")
                except Exception as e:
                    logger.error(f"Self-healing database build failed: {e}", exc_info=True)
            else:
                logger.warning(f"Could not find cleaned dataset file at '{cleaned_file}'. Skipping auto-populate.")
    return _retriever

def get_agent() -> RecommendationAgent:
    """Dependency provider yielding the singleton RecommendationAgent client instance."""
    global _agent
    if _agent is None:
        retriever = get_retriever()
        _agent = RecommendationAgent(retriever=retriever)
    return _agent
