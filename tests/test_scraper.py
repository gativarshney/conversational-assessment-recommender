import os
import json
import pytest
from app.scraper import CatalogScraper

def test_scraper_clean_and_validate() -> None:
    """Tests the scraper's de-duplication, cleaning, URL validation, and filtering rules."""
    raw_mock = [
        {
            "entity_id": "4001",
            "name": "Microsoft \n    365 (New)",
            "link": "https://www.shl.com/products/product-catalog/view/microsoft-excel-365-new/",
            "description": "Mock description with \t tabs.",
            "keys": ["Knowledge & Skills", "Simulations"]
        },
        {
            "entity_id": "4002",
            "name": "Pre-packaged Sales Solution",
            "link": "https://www.shl.com/products/product-catalog/view/pre-packaged-sales-solution/",
            "description": "Job solution",
            "keys": ["Competencies"]
        },
        {
            "entity_id": "4003",
            "name": "Duplicate Item",
            "link": "https://www.shl.com/products/product-catalog/view/duplicate-link/",
            "keys": ["Ability & Aptitude"]
        },
        {
            "entity_id": "4004",
            "name": "Duplicate Item",
            "link": "https://www.shl.com/products/product-catalog/view/duplicate-link/",
            "keys": ["Ability & Aptitude"]
        },
        {
            "entity_id": "4005",
            "name": "Invalid URL Item",
            "link": "http://invalid-url.com/view/invalid/",
            "keys": ["Ability & Aptitude"]
        }
    ]
    
    scraper = CatalogScraper("https://dummy.com")
    # Patch raw data fetching with mock data
    scraper.fetch_raw_data = lambda: raw_mock
    
    cleaned = scraper.run()
    
    # 1. Clean Specific Catalog Anomalies (Excel 365 name/newline issue and tabs/spaces cleaning)
    excel_item = next(item for item in cleaned if item["link"] == "https://www.shl.com/products/product-catalog/view/microsoft-excel-365-new/")
    assert excel_item["name"] == "Microsoft Excel 365 (New)"
    assert excel_item["test_type"] == "K,S"
    assert "tabs." in excel_item["description"]
    assert "\t" not in excel_item["description"]
    
    # 2. Excluded Pre-packaged Job Solution
    assert not any(item["name"] == "Pre-packaged Sales Solution" for item in cleaned)
    
    # 3. Avoided Duplicate Entries (same link)
    duplicate_items = [item for item in cleaned if item["link"] == "https://www.shl.com/products/product-catalog/view/duplicate-link/"]
    assert len(duplicate_items) == 1
    
    # 4. Excluded Invalid URL
    assert not any(item["name"] == "Invalid URL Item" for item in cleaned)
    
    # Total items should be 2 (cleaned Excel 365 and one duplicate item)
    assert len(cleaned) == 2

def test_cleaned_file_exists_and_valid() -> None:
    """Verifies that the generated file exists, is valid JSON, and meets PDF guidelines."""
    output_path = "data/shl_catalog_cleaned.json"
    assert os.path.exists(output_path), "Dataset JSON was not created."
    
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert len(data) > 300, "Cleaned dataset should have over 300 entries."
    for item in data:
        assert "entity_id" in item
        assert "name" in item
        assert "link" in item
        assert "description" in item
        assert "test_type" in item
        assert item["link"].startswith("https://www.shl.com/"), f"Invalid link: {item['link']}"
        assert not item["name"].endswith("Solution"), f"Job Solution found: {item['name']}"
        assert not item["name"].endswith("Solutions"), f"Job Solution found: {item['name']}"
