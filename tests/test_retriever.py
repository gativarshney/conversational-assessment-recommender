import os
import pytest
from app.core.config import settings
from app.retriever import CatalogRetriever

def test_retriever_initialization_and_search() -> None:
    """Tests that the CatalogRetriever initialized with the persistent database can query items."""
    # Ensure the database exists (it was created in build_vector_db.py)
    assert os.path.exists(settings.VECTOR_DB_DIR), "Vector database path does not exist."
    
    retriever = CatalogRetriever(db_path=settings.VECTOR_DB_DIR)
    
    # 1. Test database document count
    doc_count = retriever.count()
    assert doc_count >= 300, f"Vector database only has {doc_count} documents, expected >= 300."
    
    # 2. Test search capability
    query = "Java programming with REST api"
    top_k = 3
    results = retriever.retrieve(query, top_k=top_k)
    
    # Assertions
    assert len(results) == top_k, f"Expected {top_k} results, got {len(results)}."
    for item in results:
        # Schema field assertions
        assert "entity_id" in item
        assert "name" in item
        assert "link" in item
        assert "description" in item
        assert "test_type" in item
        assert "keys" in item
        assert "job_levels" in item
        assert "languages" in item
        assert "duration" in item
        assert "remote" in item
        assert "adaptive" in item
        
        # Datatypes should be correct
        assert isinstance(item["keys"], list)
        assert isinstance(item["job_levels"], list)
        assert isinstance(item["languages"], list)
        assert item["link"].startswith("https://www.shl.com/")
