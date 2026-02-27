import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- LLM Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# --- Gmail Configuration ---
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENTS = [email.strip() for email in os.getenv("GMAIL_RECIPIENTS", "").split(",") if email.strip()]
SEND_EMAIL = os.getenv("SEND_EMAIL", "true").lower() == "true"

# --- General Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
TIMEZONE = os.getenv("TIMEZONE", "America/Caracas")

# Ensure output directory exists (relative to where script is run, usually project root)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

# --- Logging Configuration ---
from logging.handlers import RotatingFileHandler

def setup_logger(name="cyber_newsletter"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler (rotating logs max 5 files x 5MB each)
    file_handler = RotatingFileHandler(
        "logs/cyber_newsletter.log", maxBytes=5*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

# --- Sources Configuration ---
GLOBAL_SOURCES = [
    {
        "name": "Microsoft Security Response Center",
        "url": "https://msrc.microsoft.com/update-guide/",
        "rss": "https://api.msrc.microsoft.com/update-guide/rss",
        "type": "rss",
        "language": "en"
    },
    {
        "name": "Red Hat Security Advisories",
        "url": "https://access.redhat.com/security/security-updates/",
        "rss": "https://access.redhat.com/security/data/metrics/rhsa.rss",
        "type": "rss",
        "language": "en"
    },
    {
        "name": "Red Hat Security Data",
        "url": "https://access.redhat.com/security/data",
        "type": "html",
        "language": "en"
    },
    {
        "name": "Broadcom Security Advisories",
        "url": "https://support.broadcom.com/group/ecx/security-advisories",
        "type": "html",
        "language": "en"
    },
    {
        "name": "VMware Security Advisories",
        "url": "https://www.vmware.com/security/advisories.xml",
        "type": "xml",
        "language": "en"
    },
    {
        "name": "Fortinet FortiGuard PSIRT",
        "url": "https://www.fortiguard.com/psirt",
        "type": "html",
        "language": "en"
    },
    {
        "name": "Stellar Cyber Support",
        "url": "https://stellarcyber.ai/support/",
        "type": "html",
        "language": "en"
    },
    {
        "name": "Stellar Cyber Trust Center",
        "url": "https://stellarcyber.ai/trust-center/",
        "type": "html",
        "language": "en"
    }
]

LATAM_SOURCES = [
    {
        "name": "CIAC Venezuela (Telegram)",
        "url": "https://t.me/ciberciac",
        "type": "telegram_public",
        "language": "es"
    },
    {
        "name": "InfoDefensa CIAC",
        "url": "https://www.infodefensa.com/tag/ciac",
        "type": "html",
        "language": "es"
    },
    {
        "name": "VenCERT / SUSCERTE Boletines",
        "url": "https://vencert.suscerte.gob.ve/boletines/",
        "type": "html",
        "language": "es"
    },
    {
        "name": "Telefónica Tech Boletín Ciberseguridad",
        "url": "https://telefonicatech.com/blog/boletin-ciberseguridad",
        "type": "html",
        "language": "es",
        "note": "Always get the most recent weekly bulletin available"
    }
]
