"""
Configuration file for Gmail Rule Operations
All parameters are loaded from environment variables or defaults
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gmail API Configuration
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'config/credentials.json')
GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'config/token.json')

# Database Configuration
# Default to SQLite for easier development and testing
# For production, set DATABASE_URL environment variable to PostgreSQL connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///gmail_rules.db')

# PostgreSQL configuration example (uncomment and set as DATABASE_URL for production):
# DATABASE_URL = 'postgresql://user:password@localhost:5432/gmail_rules'

# Email Processing Configuration
MAX_EMAILS_TO_FETCH = int(os.getenv('MAX_EMAILS_TO_FETCH', '100'))
EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', '10'))

# Rules Configuration
RULES_FILE = os.getenv('RULES_FILE', 'config/rules.json')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/gmail_rules.log')


#647480647423-sev9m4or96hkog7i0ebhfa9o1qjppasq.apps.googleusercontent.com


