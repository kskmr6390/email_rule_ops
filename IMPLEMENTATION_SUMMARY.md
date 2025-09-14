# Gmail Rule Operations - Implementation Summary

## Overview
This project implements a standalone Python script that integrates with Gmail API and performs rule-based operations on emails. The system fetches emails from Gmail, stores them in a database, and processes them based on configurable JSON rules.

## Architecture

### Core Components

1. **Gmail Authentication (`gmail_auth.py`)**
   - Handles OAuth2 authentication with Google's Gmail API
   - Manages token storage and refresh
   - Provides authenticated Gmail service object

2. **Email Fetcher (`email_fetcher.py`)**
   - Fetches emails from Gmail API
   - Extracts email details (headers, body, metadata)
   - Stores emails in database
   - Handles batch processing and error recovery

3. **Rule Engine (`rule_engine.py`)**
   - Loads rules from JSON configuration
   - Evaluates email conditions against rules
   - Executes actions (mark read/unread, move messages)
   - Logs rule executions for audit trail

4. **Database Models (`models.py`)**
   - Email model for storing Gmail messages
   - RuleExecution model for tracking rule processing
   - Database setup and session management

5. **Configuration (`config.py`)**
   - Centralized configuration management
   - Environment variable support
   - Database and API settings

6. **Main Script (`main.py`)**
   - Command-line interface
   - Orchestrates email fetching and rule processing
   - Comprehensive logging and error handling

## Features Implemented

### ✅ Gmail API Integration
- OAuth2 authentication with Google's official Python client
- Fetches emails from Gmail Inbox (not using IMAP)
- Handles authentication token management
- Supports Gmail API v1 with modify scope

### ✅ Database Storage
- Relational database support (PostgreSQL, SQLite)
- Email table with all required fields
- Rule execution tracking table
- Proper indexing and relationships

### ✅ Rule Engine
- JSON-based rule configuration
- Support for multiple field types (From, To, Subject, Message, Date)
- Multiple predicates for string fields (contains, does not contain, equals, does not equal)
- Date predicates (less than, greater than) with flexible time units
- Rule predicates (All, Any) for condition grouping

### ✅ Actions
- Mark as read/unread
- Move messages to folders/labels
- Action execution tracking
- Error handling and rollback

### ✅ Configuration Management
- Environment variable support
- JSON rules file
- Flexible database configuration
- Comprehensive logging

## Rule Configuration Format

```json
{
  "rules": [
    {
      "name": "Rule Name",
      "description": "Optional description",
      "predicate": "All|Any",
      "conditions": [
        {
          "field": "From|To|Subject|Message|Received Date/Time",
          "predicate": "contains|does not contain|equals|does not equal|less than|greater than",
          "value": "condition value"
        }
      ],
      "actions": [
        {
          "type": "mark as read|mark as unread|move message",
          "value": "action parameter"
        }
      ]
    }
  ]
}
```

## Database Schema

### Emails Table
```sql
CREATE TABLE emails (
    id VARCHAR PRIMARY KEY,           -- Gmail message ID
    thread_id VARCHAR NOT NULL,       -- Gmail thread ID
    from_address VARCHAR NOT NULL,    -- Sender email
    to_address VARCHAR,               -- Recipient email
    subject VARCHAR,                  -- Email subject
    message_body TEXT,                -- Email content
    received_date DATETIME NOT NULL,  -- When email was received
    is_read BOOLEAN DEFAULT FALSE,    -- Read status
    labels VARCHAR,                   -- Comma-separated labels
    snippet TEXT,                     -- Email snippet
    created_at DATETIME DEFAULT NOW,  -- Record creation time
    updated_at DATETIME DEFAULT NOW   -- Last update time
);
```

### Rule Executions Table
```sql
CREATE TABLE rule_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name VARCHAR NOT NULL,       -- Name of executed rule
    email_id VARCHAR NOT NULL,        -- Email ID that was processed
    executed_at DATETIME DEFAULT NOW, -- When rule was executed
    actions_taken TEXT,               -- JSON string of actions performed
    success BOOLEAN DEFAULT TRUE      -- Whether execution was successful
);
```

## Usage Examples

### Initial Setup
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp config/env.example config/.env
# Edit .env with your configuration

# Initialize database
python main.py --setup-db
```

### Fetch Emails
```bash
# Fetch emails from Gmail (opens browser for OAuth)
python main.py --fetch-emails --max-emails 100
```

### Process Rules
```bash
# Process stored emails against configured rules
python main.py --process-rules
```

### Run Everything
```bash
# Complete workflow
python main.py --all
```

## Testing

### Test Coverage
- **Unit Tests**: Individual component testing
  - Rule engine condition evaluation
  - Email fetcher functionality
  - Database model operations
  - Date parsing and comparison

- **Integration Tests**: End-to-end workflow testing
  - Complete email processing pipeline
  - Multiple rule matching scenarios
  - Error handling and recovery
  - Database transaction management

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_rule_engine.py

# Run with coverage
pytest --cov=. tests/
```

## Demo

A comprehensive demo script (`demo.py`) is provided that demonstrates all functionality without requiring actual Gmail API access:

```bash
python demo.py
```

The demo creates sample emails, applies rules, and shows the complete processing workflow.

## Security Considerations

- OAuth2 authentication with Google
- Secure token storage
- Environment variable configuration
- Database connection security
- Input validation and sanitization
- Error handling without information leakage

## Performance Features

- Batch email processing
- Database connection pooling
- Efficient rule evaluation
- Minimal API calls to Gmail
- Configurable batch sizes
- Memory-efficient email storage

## Error Handling

- Graceful API error handling
- Database transaction rollback
- Comprehensive logging
- Rule execution failure tracking
- Authentication error recovery
- Network timeout handling

## Extensibility

The system is designed for easy extension:

