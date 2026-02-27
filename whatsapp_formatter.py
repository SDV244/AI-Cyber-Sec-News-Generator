import os
from config import logger, OUTPUT_DIR, TIMEZONE
from utils import get_week_label

def truncate_text(text: str, max_len: int = 150) -> str:
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text

def generate(data: dict) -> str:
    """Generates a WhatsApp-formatted text summary."""
    logger.info("Generating WhatsApp summary text")
    
    lines = []
    
    # Header
    week = data.get('week_label', 'Current Week')
    lines.append(f"*🔐 CYBER INTEL WEEKLY — {week}*")
    lines.append("_Powered by verified public sources only_")
    lines.append("─────────────────────────────\n")
    
    # Critical Alerts
    criticals = data.get('critical_alerts', [])
    if criticals:
        lines.append("*🚨 ALERTAS CRÍTICAS / CRITICAL ALERTS*")
        for i, alert in enumerate(criticals, 1):
            if i > 5: # Limit top alerts to fit WA length
                break
            lines.append(f"\n*{i}. {alert.get('title')}*")
            lines.append(f"Severidad: *{alert.get('severity')}*")
            
            cves = alert.get('cve_ids', [])
            if cves:
                cve_str = ", ".join([f"`{c}`" for c in cves])
                lines.append(f"CVEs: {cve_str}")
                
            lines.append(truncate_text(alert.get('description', '')))
            lines.append(f"🔗 {alert.get('source_url')}")
            
        lines.append("\n─────────────────────────────\n")
        
    # LATAM Section
    latams = data.get('latam_venezuela_intelligence', [])
    if latams:
        lines.append("*🇻🇪 VENEZUELA / LATAM*\n")
        for i, item in enumerate(latams, 1):
            if i > 5:
                break
            lines.append(f"*{item.get('title')}*")
            lines.append(truncate_text(item.get('description', '')))
            lines.append(f"🔗 {item.get('source_url')}\n")
            
        lines.append("─────────────────────────────\n")
        
    # Stats
    stats = data.get('stats', {})
    lines.append("*📊 ESTADÍSTICAS DE LA SEMANA*")
    lines.append(f"Total alertas: {stats.get('total_items_analyzed', 0)} | Críticas: {stats.get('critical_count', 0)} | CVEs: {stats.get('cves_identified', 0)}\n")
    
    lines.append("─────────────────────────────")
    lines.append("_⚠️ Solo información de fuentes públicas verificadas._")
    lines.append("_No generado con información fabricada por IA._")
    
    text = "\n".join(lines)
    
    # Split if too long (WhatsApp limit is ~4096)
    if len(text) > 4000:
        logger.warning("WhatsApp text exceeds 4000 chars. Truncating.")
        text = text[:3900] + "\n\n...[TRUNCATED ALERTS, SEE FULL PDF]...\n\n_⚠️ Solo información de fuentes públicas verificadas._"

    filename = f"whatsapp_cyber_{get_week_label(TIMEZONE)}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)
        
    logger.info(f"WhatsApp text generated at {filepath}")
    return filepath
