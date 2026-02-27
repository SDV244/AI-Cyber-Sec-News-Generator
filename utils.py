import pytz
from datetime import datetime, date
from dataclasses import dataclass, field
import hashlib
from typing import List, Optional
import re

@dataclass
class NewsItem:
    source_name: str
    title: str
    summary: str
    url: str
    published_date: datetime
    severity: str
    cve_ids: List[str] = field(default_factory=list)
    category: str = "UNKNOWN"
    language: str = "en"
    region: str = "global"

    def to_dict(self):
        return {
            "source_name": self.source_name,
            "title": self.title,
            "summary": self.summary[:500] if self.summary else "",
            "url": self.url, # Original source URL — REQUIRED, never None
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "severity": self.severity,
            "cve_ids": self.cve_ids,
            "category": self.category,
            "language": self.language,
            "region": self.region
        }

def is_current_week(pub_date: datetime, tz_name: str) -> bool:
    """
    Checks if a given datetime falls within the current ISO week in the configured timezone.
    Monday 00:00:00 to Sunday 23:59:59 local time.
    """
    if pub_date is None:
        return False
        
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.UTC
        
    # Ensure pub_date is timezone-aware
    if pub_date.tzinfo is None:
        pub_date = pytz.UTC.localize(pub_date)
        
    # Convert to local timezone
    local_pub_date = pub_date.astimezone(tz)
    
    # Get current time in local timezone
    now_local = datetime.now(tz)
    
    # Compare ISO calendar week (year, week_num, weekday)
    pub_iso = local_pub_date.isocalendar()
    now_iso = now_local.isocalendar()
    
    return pub_iso[0] == now_iso[0] and pub_iso[1] == now_iso[1]

def deduplicate_items(items: List[NewsItem]) -> List[NewsItem]:
    """
    Deduplicates NewsItems based on URL and Title.
    """
    seen_hashes = set()
    deduped = []
    
    for item in items:
        if not item.url:
            continue
            
        digest_str = f"{item.url}_{item.title}".encode('utf-8')
        item_hash = hashlib.md5(digest_str).hexdigest()
        
        if item_hash not in seen_hashes:
            seen_hashes.add(item_hash)
            deduped.append(item)
            
    return deduped

def extract_cves(text: str) -> List[str]:
    """
    Helper to extract CVE IDs from text. E.g. CVE-2025-1234
    """
    if not text:
        return []
    cve_pattern = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
    matches = cve_pattern.findall(text)
    # Deduplicate and uppercase
    return list(set(m.upper() for m in matches))

def get_week_label(tz_name: str) -> str:
    tz = pytz.timezone(tz_name)
    now_local = datetime.now(tz)
    return f"{now_local.strftime('%Y')}-W{now_local.isocalendar()[1]:02d}"

def get_week_date_range(tz_name: str) -> str:
    from dateutil.relativedelta import relativedelta, MO, SU
    tz = pytz.timezone(tz_name)
    now_local = datetime.now(tz)
    
    # Get Monday and Sunday of the current week
    monday = now_local + relativedelta(weekday=MO(-1))
    sunday = now_local + relativedelta(weekday=SU(1))
    
    return f"{monday.strftime('%b %d')} - {sunday.strftime('%b %d, %Y')}"
