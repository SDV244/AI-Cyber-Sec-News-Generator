import os
from datetime import datetime
import json
import logging

from config import logger, TIMEZONE
import scraper
import ai_synthesizer
import pdf_generator
import whatsapp_formatter
from utils import NewsItem, deduplicate_items, get_week_label

def mock_scrape():
    # Only scrape 2 fast sources to test the pipeline quickly
    fast_sources = [
        s for s in scraper.GLOBAL_SOURCES + scraper.LATAM_SOURCES 
        if s['type'] in ('rss', 'telegram_public')
    ][:2]
    
    print(f"\n--- 1. Testing Scraper against subset of fast sources ---")
    all_items = []
    for source in fast_sources:
        items = scraper.fetch_source(source)
        all_items.extend(items)
        print(f"Scraped {len(items)} items from {source['name']}")
        
    valid_urls = sum(1 for i in all_items if i.url)
    print(f"Total valid URLs: {valid_urls} / {len(all_items)}")
    return deduplicate_items(all_items)

def test_pipeline():
    logger.setLevel(logging.DEBUG) # Verbose for test
    
    print("\nStarting Test Pipeline...")
    
    # 1. Scrape
    items = mock_scrape()
    if not items:
        # Provide fallback dummy data
        print("No items scraped from fast sources, using dummy data for rest of pipeline.")
        items = [
            NewsItem("Test Source", "Test Critical Vuln", "Summary of vuln", "https://example.com/1", datetime.now(), "CRITICAL", ["CVE-2025-001"], "Vulnerability", "en", "global"),
            NewsItem("Test Source", "Another Issue", "Summary info", "https://example.com/2", datetime.now(), "HIGH", ["CVE-2025-002"], "Vulnerability", "en", "global"),
        ]
        
    print(f"\n--- 2. Testing AI Synthesizer ---")
    test_subset = items[:3]
    print(f"Sending {len(test_subset)} items to Gemini...")
    newsletter_data = ai_synthesizer.synthesize(test_subset)
    
    # Debug schema
    print("AI Response Schema Validation Check:")
    required_keys = ['week_label', 'executive_summary', 'critical_alerts', "stats"]
    for k in required_keys:
        if k in newsletter_data:
             print(f"✓ Key '{k}' present.")
        else:
             print(f"✗ MISSING KEY '{k}'!")
             
    # Fallback to pure dummy data if no key present (e.g. no API key in env)
    if 'executive_summary' not in newsletter_data or newsletter_data.get('executive_summary', '').startswith('RAW DIGEST'):
         print("Using mock data to test PDF generation layout properly...")
         newsletter_data = {
            "week_label": f"Week of {get_week_label(TIMEZONE)}",
            "executive_summary": "This is a dummy executive summary for testing the layout of the PDF.",
            "critical_alerts": [
                {
                    "title": "Major Critical Flaw",
                    "severity": "CRITICAL",
                    "description": "Short description of flaw.",
                    "cve_ids": ["CVE-2025-1010"],
                    "affected_products": ["RouterOS"],
                    "source_name": "Test MSRC",
                    "source_url": "https://example.com/3"
                }
            ],
            "latam_venezuela_intelligence": [
                 {
                    "title": "Ataque detectado",
                    "description": "Descripcion breve.",
                    "source_name": "CIAC",
                    "source_url": "https://example.com/4",
                    "language": "es"
                }
            ],
            "vulnerabilities_and_patches": [],
            "breaches_and_incidents": [],
            "stats": {
                "total_items_analyzed": 5,
                "critical_count": 1,
                "high_count": 0,
                "medium_count": 0,
                "sources_scraped": 2,
                "cves_identified": 1
            }
         }
             
    print(f"\n--- 3. Testing PDF Generation ---")
    pdf_path = pdf_generator.generate(newsletter_data)
    print(f"PDF Output path: {pdf_path}")
    print(f"File exists: {os.path.exists(pdf_path)}")
    
    print(f"\n--- 4. Testing WhatsApp Formatter ---")
    wa_path = whatsapp_formatter.generate(newsletter_data)
    print(f"WhatsApp Output path: {wa_path}")
    print(f"File exists: {os.path.exists(wa_path)}")
    
    print("\n✅ Test Run Completed Successfully.")
    
if __name__ == "__main__":
    test_pipeline()
