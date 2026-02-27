import argparse
import sys
from apscheduler.schedulers.blocking import BlockingScheduler

import config
from config import logger, TIMEZONE
import scraper
import ai_synthesizer
import pdf_generator
import whatsapp_formatter
import gmail_sender
from utils import deduplicate_items

def run_weekly_newsletter():
    logger.info("=== Starting Weekly Cyber Newsletter Generation ===")
    
    try:
        # Step 1: Scrape all sources
        raw_items = scraper.collect_all_sources()
        logger.info(f"Collected {len(raw_items)} raw items from sources")
        
        # Deduplicate
        all_items = deduplicate_items(raw_items)
        logger.info(f"After deduplication: {len(all_items)} unique items")

        # Step 2: Validate
        if len(all_items) == 0:
            logger.warning("No items collected for this week. Proceeding with empty report generation to notify stakeholders.")
        
        # Step 3: AI synthesis
        newsletter_data = ai_synthesizer.synthesize(all_items)
        
        # Step 4: Generate PDF
        pdf_path = pdf_generator.generate(newsletter_data)
        logger.info(f"PDF generated: {pdf_path}")
        
        # Step 5: Generate WhatsApp version
        wa_path = whatsapp_formatter.generate(newsletter_data)
        logger.info(f"WhatsApp text generated: {wa_path}")
        
        # Step 6: Send email (if enabled)
        if config.SEND_EMAIL:
            gmail_sender.send(pdf_path, newsletter_data)
        else:
            logger.info(f"Email sending disabled in config. PDF saved at: {pdf_path}")
            
    except Exception as e:
        logger.exception(f"FATAL ERROR inside main execution loop: {e}")
        
    logger.info("=== Newsletter Generation Complete ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cybersecurity Newsletter Automation")
    parser.add_argument("--run-now", action="store_true", help="Run the newsletter generation immediately once.")
    args = parser.parse_args()

    if args.run_now:
        run_weekly_newsletter()
        sys.exit(0)

    # Schedule setup
    logger.info(f"Starting APScheduler... Timezone configured: {TIMEZONE}")
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    
    # Schedule: Every Monday at 08:00 local time
    scheduler.add_job(run_weekly_newsletter, 'cron', day_of_week='mon', hour=8, minute=0)
    
    logger.info("Scheduler is running. Press Ctrl+C to exit. Next run scheduled for next Monday at 08:00.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shuts down.")
