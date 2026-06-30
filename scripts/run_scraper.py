import os
import json
import logging
from app.core.config import settings
from app.core.logging import setup_logging
from app.scraper import CatalogScraper

def main() -> None:
    """Executes the scraper and saves the cleaned catalog JSON."""
    setup_logging()
    logger = logging.getLogger("run_scraper")
    
    # Ensure local data directory exists
    os.makedirs("data", exist_ok=True)
    
    output_path = "data/shl_catalog_cleaned.json"
    
    logger.info(f"Initializing catalog scraper with URL: {settings.CATALOG_URL}")
    scraper = CatalogScraper(settings.CATALOG_URL)
    
    try:
        cleaned_items = scraper.run()
        
        # Save structured JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_items, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Catalog scraping completed: {len(cleaned_items)} items successfully saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Catalog scraper encountered an error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
