import time
import feedparser
import requests
from bs4 import BeautifulSoup
from lxml import etree
from dateutil import parser as date_parser
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

from config import logger, GLOBAL_SOURCES, LATAM_SOURCES, TIMEZONE
from utils import NewsItem, is_current_week, extract_cves

def fetch_rss(url: str, source: dict) -> list[NewsItem]:
    items = []
    try:
        # Feedparser can handle both RSS and Atom
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Try multiple date formats sometimes provided by feeds
            pub_date_str = entry.get('published', entry.get('updated', None))
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = date_parser.parse(pub_date_str)
                except Exception as e:
                    logger.warning(f"Could not parse date '{pub_date_str}' for RSS item in {source['name']}: {e}")
            
            # Filter by current week
            if pub_date is None or not is_current_week(pub_date, TIMEZONE):
                continue
            
            title = entry.get('title', 'Unknown Title')
            link = entry.get('link', None)
            summary = entry.get('summary', entry.get('description', ''))
            
            # Skip if no link
            if not link:
                continue
                
            # Attempt to infer CVEs and Severity from title/summary if not explicit in feed fields
            cves = extract_cves(title + " " + summary)
            
            # Simple heuristic for severity if not provided by feed extensions
            severity = "UNKNOWN"
            text_desc = (title + " " + summary).upper()
            if "CRITICAL" in text_desc: severity = "CRITICAL"
            elif "HIGH" in text_desc: severity = "HIGH"
            elif "MEDIUM" in text_desc: severity = "MEDIUM"
            elif "LOW" in text_desc: severity = "LOW"
            elif "INFO" in text_desc: severity = "INFO"

            items.append(NewsItem(
                source_name=source['name'],
                title=title,
                summary=BeautifulSoup(summary, 'html.parser').get_text()[:500], # clean HTML tags
                url=link,
                published_date=pub_date,
                severity=severity,
                cve_ids=cves,
                category="Advisory", # Default
                language=source.get('language', 'en'),
                region="global" if source in GLOBAL_SOURCES else "latam"
            ))
            
    except Exception as e:
        logger.error(f"Error fetching RSS from {source['name']} ({url}): {e}")
        
    return items

def fetch_xml(url: str, source: dict) -> list[NewsItem]:
    # Similar to RSS but maybe more manual if it's a custom XML like VMware's
    items = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Simple extraction using lxml. Adapt based on actual schema if needed.
        # Fallback to feedparser because often .xml is just RSS/Atom.
        # If feedparser fails or we know it's a specific schema, do manual extraction here.
        # Let's try feedparser first:
        return fetch_rss(url, source)
    except Exception as e:
        logger.error(f"Error fetching XML from {source['name']} ({url}): {e}")
    return items

def fetch_telegram_public(url: str, source: dict) -> list[NewsItem]:
    items = []
    try:
        # Convert t.me/ciberciac to t.me/s/ciberciac
        if "t.me/" in url and "t.me/s/" not in url:
            url = url.replace("t.me/", "t.me/s/")
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all message widgets
        messages = soup.find_all('div', class_='tgme_widget_message')
        
        for msg in messages:
            try:
                # Extract text
                text_div = msg.find('div', class_='tgme_widget_message_text')
                if not text_div:
                    continue
                text = text_div.get_text(separator=' ', strip=True)
                
                # Extract URL
                date_link = msg.find('a', class_='tgme_widget_message_date')
                if not date_link:
                    continue
                msg_url = date_link.get('href')
                
                # Extract Date
                time_node = date_link.find('time')
                if not time_node:
                    continue
                datetime_str = time_node.get('datetime')
                pub_date = date_parser.parse(datetime_str)
                
                if not is_current_week(pub_date, TIMEZONE):
                    continue
                    
                # Summarize/Title
                lines = text.split('\n')
                title = lines[0][:100] + "..." if len(lines[0]) > 100 else lines[0]
                if "•" in title: title = title.split("•")[0].strip()
                
                cves = extract_cves(text)
                
                severity = "UNKNOWN"
                text_desc = text.upper()
                if "CRÍTIC" in text_desc or "CRITICA" in text_desc: severity = "CRITICAL"
                elif "ALTA" in text_desc: severity = "HIGH"
                elif "MEDIA" in text_desc: severity = "MEDIUM"
                elif "BAJA" in text_desc: severity = "LOW"

                items.append(NewsItem(
                    source_name=source['name'],
                    title=title,
                    summary=text[:500],
                    url=msg_url,
                    published_date=pub_date,
                    severity=severity,
                    cve_ids=cves,
                    category="Threat Intelligence",
                    language=source.get('language', 'es'),
                    region="latam"
                ))
            except Exception as e_inner:
                logger.debug(f"Error parsing Telegram message in {source['name']}: {e_inner}")

    except Exception as e:
        logger.error(f"Error fetching Telegram from {source['name']} ({url}): {e}")
    return items

def fetch_html_playwright(url: str, source: dict) -> list[NewsItem]:
    items = []
    logger.info(f"Using Playwright to scrape {source['name']}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3) # Extra wait for JS frameworks
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # We need specific CSS selectors for specific sites if we wanted full fidelity
                # However, since this is a generalized scraper, we will look for common patterns
                # like <article>, or links containing "advisory" or date elements.
                # For a robust implementation, these would be customized per source (Broadcom, Fortiguard, etc)
                
                # Default generic fallback: grab all links that look like articles.
                # Since we don't have the exact layout, this generic fallback might return fewer items.
                logger.warning(f"Playwright fallback scraping for {source['name']} - implement specific CSS selectors for better results")
                
                # Example rough logic assuming there's a list context
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if not href or href.startswith('#') or href.startswith('javascript'):
                        continue
                        
                    text = a.get_text(strip=True)
                    if not text or len(text) < 15:
                        continue
                        
                    # Roughly try to find a date near the link
                    parent = a.find_parent()
                    date_node = parent.find(string=lambda s: len(s) > 8 and any(m in s for m in ["Jan", "Feb", "2024", "2025", "2026", "-", "/"])) if parent else None
                    if date_node:
                         try:
                             # Try to parse roughly
                             import re
                             date_str = re.sub(r'[^a-zA-Z0-9\-\/\s]', '', date_node)
                             pub_date = date_parser.parse(date_str, fuzzy=True)
                             
                             if is_current_week(pub_date, TIMEZONE):
                                full_url = href if href.startswith('http') else '/'.join(url.split('/')[:3]) + href
                                items.append(NewsItem(
                                    source_name=source['name'],
                                    title=text,
                                    summary="",
                                    url=full_url,
                                    published_date=pub_date,
                                    severity="UNKNOWN",
                                    language=source.get('language', 'en'),
                                    region="global" if source in GLOBAL_SOURCES else "latam"
                                ))
                         except Exception:
                             pass
                
            except Exception as e_page:
                logger.error(f"Playwright page error on {source['name']}: {e_page}")
            finally:
                browser.close()
                
    except Exception as e:
        logger.error(f"Error initializing Playwright for {source['name']} ({url}): {e}")
    return items

def fetch_html_requests(url: str, source: dict) -> list[NewsItem]:
    # Non-JS HTML scraping
    items = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Site-specific logic goes here for Infodefensa, Suscerte, Telefonica, etc.
        # This generic logic behaves similar to the playwright fallback
        logger.warning(f"Requests fallback scraping for {source['name']} - implement specific CSS selectors for better results")
        
    except Exception as e:
        logger.error(f"Error fetching HTML from {source['name']} ({url}): {e}")
    return items

def fetch_source(source: dict) -> list[NewsItem]:
    logger.info(f"Fetching from {source['name']} ({source['type']})")
    
    # URL to fetch, default to RSS if available, otherwise base URL
    fetch_url = source.get('rss') or source.get('url')
    
    if source['type'] == 'rss':
        return fetch_rss(fetch_url, source)
    elif source['type'] == 'xml':
        return fetch_xml(fetch_url, source)
    elif source['type'] == 'telegram_public':
        return fetch_telegram_public(fetch_url, source)
    elif source['type'] == 'html':
        # Certain sites need Playwright
        playwright_sites = ["Broadcom", "Stellar Cyber", "Fortinet"]
        if any(ps in source['name'] for ps in playwright_sites):
            return fetch_html_playwright(fetch_url, source)
        else:
            return fetch_html_requests(fetch_url, source)
    else:
        logger.warning(f"Unknown source type '{source['type']}' for {source['name']}")
        return []

def collect_all_sources() -> list[NewsItem]:
    all_items = []
    sources = GLOBAL_SOURCES + LATAM_SOURCES
    
    for source in sources:
        items = fetch_source(source)
        logger.info(f"Collected {len(items)} items from {source['name']}")
        all_items.extend(items)
        
    return all_items
