import os
from datetime import datetime
from jinja2 import Environment, DictLoader
from weasyprint import HTML, CSS
from config import logger, OUTPUT_DIR, TIMEZONE
from utils import get_week_label

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cyber Intelligence Weekly</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
        
        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            color: #2D2D2D;
            background: #FFFFFF;
            font-size: 14px;
            line-height: 1.7;
        }
        
        @page {
            size: A4;
            margin: 40px 50px;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #888888;
                padding-top: 10px;
            }
        }
        
        .header {
            background-color: #0A0A0A;
            color: #FFFFFF;
            padding: 20px 30px;
            margin-bottom: 30px;
            border-radius: 4px;
        }
        
        .header h1 {
            font-weight: 900;
            font-size: 28px;
            margin: 0 0 5px 0;
            letter-spacing: 1px;
        }
        
        .header .subtitle {
            color: #C8102E;
            font-weight: 600;
            font-size: 14px;
            margin: 0;
        }
        
        .header .date {
            float: right;
            font-size: 12px;
            opacity: 0.8;
            margin-top: -25px;
        }
        
        .stats-bar {
            background: #1A1A2E;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        
        .stats-bar span {
            font-weight: 600;
        }
        
        .exec-summary {
            background: #F8F9FA;
            border-left: 4px solid #C8102E;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 4px 4px 0;
        }
        
        .exec-summary h2 {
            font-size: 14px;
            color: #888888;
            margin-top: 0;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        
        h3.section-header {
            font-size: 18px;
            color: #1A1A2E;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #E9ECEF;
        }
        
        h3.section-header.red { color: #C8102E; border-bottom-color: #C8102E; }
        h3.section-header.latam { color: #00247D; border-bottom: 1px solid #CF142B; }
        
        .card {
            background: #FFFFFF;
            border: 1px solid #E9ECEF;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 6px;
            page-break-inside: avoid;
        }
        
        .card h4 {
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 15px;
            color: #0A0A0A;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            color: white;
            margin-bottom: 10px;
        }
        
        .badge.critical { background: #FF3B30; }
        .badge.high { background: #FF6B35; }
        .badge.medium { background: #FFB020; }
        .badge.low { background: #34C759; }
        .badge.info { background: #0057B8; }
        
        .cve-pill {
            display: inline-block;
            background: #0A0A0A;
            color: white;
            font-family: monospace;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .source-url {
            display: block;
            margin-top: 15px;
            font-size: 11px;
            color: #0057B8;
            word-break: break-all;
            text-decoration: none;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #E9ECEF;
            font-size: 10px;
            color: #888888;
            text-align: center;
        }
        
        .two-col {
            column-count: 2;
            column-gap: 20px;
        }
        
        .two-col .card { margin-bottom: 20px; }
    </style>
</head>
<body>

    <div class="header">
        <h1>CYBER INTELLIGENCE</h1>
        <p class="subtitle">Weekly Security Intelligence Briefing</p>
        <p class="date">{{ data.week_label }}</p>
    </div>

    <div class="stats-bar">
        <span>Total Items: {{ data.stats.total_items_analyzed }}</span>
        <span>Critical: {{ data.stats.critical_count }}</span>
        <span>High: {{ data.stats.high_count }}</span>
        <span>CVEs: {{ data.stats.cves_identified }}</span>
        <span>Sources: {{ data.stats.sources_scraped }}</span>
    </div>

    <div class="exec-summary">
        <h2>EXECUTIVE SUMMARY</h2>
        <p>{{ data.executive_summary }}</p>
    </div>

    {% if data.critical_alerts %}
    <h3 class="section-header red">🚨 CRITICAL ALERTS</h3>
    {% for alert in data.critical_alerts %}
    <div class="card">
        <span class="badge {{ alert.severity|lower }}">{{ alert.severity }}</span>
        <h4>{{ alert.title }}</h4>
        <p>{{ alert.description }}</p>
        
        {% if alert.cve_ids %}
        <div style="margin-top: 10px;">
            {% for cve in alert.cve_ids %}
            <span class="cve-pill">{{ cve }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        <p style="font-size: 12px; color: #888888; margin-top: 10px;">
            Source: {{ alert.source_name }}
        </p>
        <a href="{{ alert.source_url }}" class="source-url">{{ alert.source_url }}</a>
    </div>
    {% endfor %}
    {% endif %}

    {% if data.latam_venezuela_intelligence %}
    <h3 class="section-header latam">🇻🇪 LATAM & VENEZUELA INTELLIGENCE</h3>
    {% for alert in data.latam_venezuela_intelligence %}
    <div class="card" style="border-left: 3px solid #CF142B;">
        <h4>{{ alert.title }}</h4>
        <p>{{ alert.description }}</p>
        <p style="font-size: 12px; color: #888888; margin-top: 10px;">
            Fuente: {{ alert.source_name }}
        </p>
        <a href="{{ alert.source_url }}" class="source-url">{{ alert.source_url }}</a>
    </div>
    {% endfor %}
    {% endif %}

    {% if data.vulnerabilities_and_patches %}
    <h3 class="section-header">🛡 VULNERABILITIES & PATCHES</h3>
    <div class="two-col">
    {% for vuln in data.vulnerabilities_and_patches %}
    <div class="card">
        <span class="badge {{ vuln.severity|lower }}">{{ vuln.severity }}</span>
        <h4>{{ vuln.title }}</h4>
        <p>{{ vuln.description }}</p>
        {% if vuln.cve_ids %}
        <div style="margin-top: 10px;">
            {% for cve in vuln.cve_ids %}
            <span class="cve-pill">{{ cve }}</span>
            {% endfor %}
        </div>
        {% endif %}
        <p style="font-size: 11px; color: #888888; margin-top: 10px;">
            Source: {{ vuln.source_name }}
        </p>
        <a href="{{ vuln.source_url }}" class="source-url">{{ vuln.source_url }}</a>
    </div>
    {% endfor %}
    </div>
    {% endif %}

    {% if data.breaches_and_incidents %}
    <h3 class="section-header">🏴‍☠️ BREACHES & INCIDENTS</h3>
    {% for breach in data.breaches_and_incidents %}
    <div class="card">
        <h4>{{ breach.title }}</h4>
        <p>{{ breach.description }}</p>
        <a href="{{ breach.source_url }}" class="source-url">{{ breach.source_url }}</a>
    </div>
    {% endfor %}
    {% endif %}

    <div class="footer">
        Generated by Cyber Intelligence Automation | {{ current_date }}<br>
        <strong>This report contains only information from verified public sources. No AI-generated claims.</strong>
    </div>

</body>
</html>
"""

def generate(newsletter_data: dict) -> str:
    """Generates the PDF and returns its file path."""
    logger.info("Generating PDF newsletter")
    
    # Setup Jinja environment
    env = Environment(loader=DictLoader({'newsletter.html': HTML_TEMPLATE}))
    template = env.get_template('newsletter.html')
    
    import pytz
    tz = pytz.timezone(TIMEZONE)
    current_date = datetime.now(tz).strftime('%B %d, %Y %H:%M %Z')
    
    html_out = template.render(data=newsletter_data, current_date=current_date)
    
    filename = f"cyber_newsletter_{get_week_label(TIMEZONE)}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        HTML(string=html_out).write_pdf(filepath)
        logger.info(f"PDF successfully written to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        # Fallback to plain text if WeasyPrint fails (system dependencies missing)
        fallback_path = filepath.replace(".pdf", ".txt")
        import json
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(newsletter_data, indent=2))
        logger.warning(f"Fallback text file generated at {fallback_path}")
        return fallback_path
