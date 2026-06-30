import os
import json
import logging
from app.core.config import settings
from app.core.logging import setup_logging
from app.retriever import CatalogRetriever

def main() -> None:
    """Indexes the cleaned catalog JSON into persistent ChromaDB and runs a test query."""
    setup_logging()
    logger = logging.getLogger("build_vector_db")
    
    cleaned_catalog_file = "data/shl_catalog_cleaned.json"
    
    if not os.path.exists(cleaned_catalog_file):
        logger.error(f"Cleaned catalog file not found at: {cleaned_catalog_file}. Please run the scraper first.")
        return
        
    # Initialize the retriever client
    retriever = CatalogRetriever(db_path=settings.VECTOR_DB_DIR)
    
    # Load items
    logger.info(f"Loading cleaned catalog dataset from {cleaned_catalog_file}...")
    with open(cleaned_catalog_file, "r", encoding="utf-8") as f:
        items = json.load(f)
        
    # Index documents
    logger.info(f"Indexing {len(items)} catalog items into vector store...")
    retriever.add_documents(items)
    
    # Verify DB count
    doc_count = retriever.count()
    logger.info(f"Vector store now contains {doc_count} documents.")
    
    # Run a test query
    test_query = "Java developer with spring and sql backend knowledge"
    logger.info(f"Running test similarity query: '{test_query}'")
    matches = retriever.retrieve(test_query, top_k=3)
    
    print("\n=== TOP 3 MATCHES ===")
    for idx, match in enumerate(matches):
        print(f"{idx+1}. {match['name']} (test_type: {match['test_type']})")
        print(f"   URL: {match['link']}")
        print(f"   Keys: {match['keys']}")
        print(f"   Snippet: {match['description'][:120]}...\n")

if __name__ == "__main__":
    main()
