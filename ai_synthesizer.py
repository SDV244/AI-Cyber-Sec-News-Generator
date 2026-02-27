import json
import time
import google.generativeai as genai
from pydantic import ValidationError

from config import logger, GEMINI_API_KEY, GEMINI_MODEL, TIMEZONE
from utils import NewsItem, get_week_date_range

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. AI synthesis will fail or use fallback.")

SYSTEM_PROMPT = """
You are a professional cybersecurity intelligence analyst writing an executive weekly newsletter.

STRICT RULES — VIOLATIONS ARE NOT ACCEPTABLE:
1. You MUST only use information from the INPUT DATA provided. Never invent, infer, or supplement with your own knowledge.
2. Every claim, vulnerability, CVE, or incident MUST be traceable to an item in INPUT DATA.
3. If the INPUT DATA does not contain enough information to fill a section, write: "No significant events reported this week in this category."
4. Do NOT add commentary, predictions, or opinions unless explicitly part of a "Analyst Commentary" section clearly labeled as such.
5. All source URLs must be copied verbatim from the input data — never generate or modify URLs.
6. CVE IDs must be copied exactly as found in input data.
7. Severity ratings must match what is in the source — do not upgrade or downgrade.
8. Output ONLY valid JSON matching the schema provided. No markdown, no prose, no preamble.

INPUT DATA FORMAT: JSON array of news items with fields: source_name, title, summary, url, published_date, severity, cve_ids, category, language, region

OUTPUT SCHEMA (return only this JSON, nothing else):
{
  "week_label": "Week of [DATE_RANGE]",
  "executive_summary": "3-4 sentence summary of the most critical events this week. Only facts from input.",
  "critical_alerts": [
    {
      "title": "...",
      "severity": "CRITICAL|HIGH",
      "description": "1-2 sentences max. Facts only from input.",
      "cve_ids": ["CVE-XXXX-XXXX"],
      "affected_products": ["..."],
      "source_name": "...",
      "source_url": "..."
    }
  ],
  "vulnerabilities_and_patches": [
    {
      "title": "...",
      "severity": "MEDIUM|LOW",
      "description": "1-2 sentences max. Facts only from input.",
      "cve_ids": ["CVE-XXXX-XXXX"],
      "affected_products": ["..."],
      "source_name": "...",
      "source_url": "..."
    }
  ],
  "breaches_and_incidents": [
    {
      "title": "...",
      "description": "...",
      "impact": "...",
      "source_name": "...",
      "source_url": "..."
    }
  ],
  "latam_venezuela_intelligence": [
    {
      "title": "...",
      "description": "...",
      "source_name": "...",
      "source_url": "...",
      "language": "es"
    }
  ],
  "recommended_actions": [
    "Specific actionable recommendation — only if supported by input data"
  ],
  "stats": {
    "total_items_analyzed": 0,
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "sources_scraped": 0,
    "cves_identified": 0
  }
}
"""

def generate_fallback_digest(items: list[NewsItem]) -> dict:
    """Fallback if AI fails. Creates raw digest from items."""
    logger.warning("Using RAW DIGEST mode — AI synthesis unavailable")
    
    # Sort critical first
    sorted_items = sorted(items, key=lambda x: (
        0 if x.severity == "CRITICAL" else
        1 if x.severity == "HIGH" else
        2 if x.severity == "MEDIUM" else 3
    ))
    
    criticals = []
    vulns = []
    latam = []
    cves_set = set()
    
    for item in sorted_items:
        cves_set.update(item.cve_ids)
        entry = {
            "title": item.title,
            "severity": item.severity,
            "description": item.summary,
            "cve_ids": item.cve_ids,
            "affected_products": [],
            "source_name": item.source_name,
            "source_url": item.url
        }
        
        if item.region == "latam":
            latam.append(entry)
        elif item.severity in ["CRITICAL", "HIGH"]:
            criticals.append(entry)
        else:
            vulns.append(entry)

    return {
        "week_label": f"Week of {get_week_date_range(TIMEZONE)} (RAW DIGEST MODE)",
        "executive_summary": "RAW DIGEST — AI SYNTHESIS UNAVAILABLE.",
        "critical_alerts": criticals[:5],
        "vulnerabilities_and_patches": vulns[:5],
        "breaches_and_incidents": [],
        "latam_venezuela_intelligence": latam[:5],
        "recommended_actions": [],
        "stats": {
            "total_items_analyzed": len(items),
            "critical_count": sum(1 for i in items if i.severity == "CRITICAL"),
            "high_count": sum(1 for i in items if i.severity == "HIGH"),
            "medium_count": sum(1 for i in items if i.severity == "MEDIUM"),
            "sources_scraped": len(set(i.source_name for i in items)),
            "cves_identified": len(cves_set)
        }
    }


def analyze_with_ai(items: list[NewsItem], is_retry=False) -> dict:
    valid_items = [i for i in items if i.url] # Enforce rule: must have URL
    
    if not valid_items:
        logger.warning("No valid items with URLs given to AI Synthesizer.")
        return generate_fallback_digest([])

    input_json = json.dumps([i.to_dict() for i in valid_items], ensure_ascii=False)
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = SYSTEM_PROMPT + f"\n\nINPUT DATA:\n{input_json}\n\nOUTPUT SCHEMA ONLY JSON:"
        
        # We request strict JSON
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1 # Low temp = more factual
            )
        )
        
        # Parse JSON
        result = json.loads(response.text)
        
        # Validate post-check (Anti-Hallucination)
        all_input_urls = {i.url for i in valid_items}
        
        def filter_fabricated_urls(section):
            valid_entries = []
            for entry in result.get(section, []):
                # Only keep entries whose source_url we actually provided
                if entry.get("source_url") in all_input_urls:
                    valid_entries.append(entry)
                else:
                    logger.warning(f"HALLUCINATION DETECTED: Removed fabricated URL {entry.get('source_url')} from {section}")
            result[section] = valid_entries

        filter_fabricated_urls("critical_alerts")
        filter_fabricated_urls("vulnerabilities_and_patches")
        filter_fabricated_urls("breaches_and_incidents")
        filter_fabricated_urls("latam_venezuela_intelligence")
        
        return result
        
    except json.JSONDecodeError as de:
        logger.error(f"Failed to parse AI output as JSON: {de}")
        if not is_retry:
            logger.info("Retrying AI synthesis with stricter prompt...")
            time.sleep(30)
            return analyze_with_ai(valid_items, is_retry=True)
    except Exception as e:
        logger.error(f"Error during AI Synthesis: {e}")
        if not is_retry:
            logger.info("Retrying AI synthesis due to error...")
            time.sleep(30)
            return analyze_with_ai(valid_items, is_retry=True)
            
    # Fallback if both tries fail
    return generate_fallback_digest(valid_items)


def synthesize(items: list[NewsItem]) -> dict:
    """Main entrypoint for synthesis"""
    logger.info(f"Synthesizing {len(items)} items using Gemini AI")
    if not GEMINI_API_KEY:
        return generate_fallback_digest(items)
        
    return analyze_with_ai(items)
