#!/usr/bin/env python3
"""
Main script for Gmail Rule Operations
This script fetches emails from Gmail and processes them based on configured rules
"""
import sys
import argparse
import logging
from datetime import datetime

from email_fetcher import EmailFetcher
from rule_engine import RuleEngine
from models import create_tables
from config import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database tables"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        sys.exit(1)

def fetch_emails(max_emails: int = None):
    """
    Fetch emails from Gmail and store in database
    Args:
        max_emails: Maximum number of emails to fetch
    """
    logger.info("Starting email fetch process...")
    
    fetcher = EmailFetcher()
    try:
        stored_count = fetcher.fetch_and_store_emails(max_emails)
        logger.info(f"Email fetch completed. Stored {stored_count} emails.")
    except Exception as e:
        logger.error(f"Error during email fetch: {e}")
    finally:
        fetcher.close()

def process_rules():
    """Process emails against configured rules"""
    logger.info("Starting rule processing...")
    
    engine = RuleEngine()
    try:
        stats = engine.process_emails()
        logger.info(f"Rule processing completed:")
        logger.info(f"  - Emails processed: {stats['emails_processed']}")
        logger.info(f"  - Rules matched: {stats['rules_matched']}")
        logger.info(f"  - Actions executed: {stats['actions_executed']}")
    except Exception as e:
        logger.error(f"Error during rule processing: {e}")
    finally:
        engine.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Gmail Rule Operations')
    parser.add_argument('--setup-db', action='store_true', 
                       help='Initialize database tables')
    parser.add_argument('--fetch-emails', action='store_true',
                       help='Fetch emails from Gmail')
    parser.add_argument('--process-rules', action='store_true',
                       help='Process emails against rules')
    parser.add_argument('--max-emails', type=int, default=None,
                       help='Maximum number of emails to fetch')
    parser.add_argument('--all', action='store_true',
                       help='Run all operations (setup, fetch, process)')
    
    args = parser.parse_args()
    
    if not any([args.setup_db, args.fetch_emails, args.process_rules, args.all]):
        parser.print_help()
        return
    
    logger.info("Gmail Rule Operations started")
    logger.info(f"Configuration: {config.RULES_FILE}, {config.DATABASE_URL}")
    
    try:
        if args.setup_db or args.all:
            setup_database()
        
        if args.fetch_emails or args.all:
            fetch_emails(args.max_emails)
        
        if args.process_rules or args.all:
            process_rules()
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    logger.info("Gmail Rule Operations completed")

if __name__ == "__main__":
    main()
