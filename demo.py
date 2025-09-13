#!/usr/bin/env python3
"""
Demo script for Gmail Rule Operations
This script demonstrates the functionality without requiring actual Gmail API access
"""
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from models import Email, RuleExecution, create_tables
from rule_engine import RuleEngine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_demo_database():
    """Create in-memory database for demo"""
    engine = create_engine('sqlite:///:memory:')
    # Create tables directly instead of using create_tables() which uses config
    from models import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def create_demo_emails(session):
    """Create sample emails for demo"""
    emails = [
        Email(
            id='newsletter_1',
            thread_id='thread_1',
            from_address='newsletter@techcompany.com',
            to_address='user@example.com',
            subject='Weekly Tech Newsletter',
            message_body='Check out our latest technology updates and news',
            received_date=datetime.utcnow(),
            is_read=False,
            labels='INBOX',
            snippet='Weekly tech updates...'
        ),
        Email(
            id='old_email_1',
            thread_id='thread_2',
            from_address='oldfriend@example.com',
            to_address='user@example.com',
            subject='Remember me?',
            message_body='Hey, it has been a while since we talked',
            received_date=datetime.utcnow() - timedelta(days=35),
            is_read=False,
            labels='INBOX',
            snippet='Old message from friend...'
        ),
        Email(
            id='urgent_1',
            thread_id='thread_3',
            from_address='boss@company.com',
            to_address='user@example.com',
            subject='URGENT: Project Deadline',
            message_body='This is urgent! We need to finish the project by tomorrow',
            received_date=datetime.utcnow(),
            is_read=False,
            labels='INBOX',
            snippet='Urgent project deadline...'
        ),
        Email(
            id='social_1',
            thread_id='thread_4',
            from_address='notifications@facebook.com',
            to_address='user@example.com',
            subject='New friend request',
            message_body='You have a new friend request on Facebook',
            received_date=datetime.utcnow(),
            is_read=False,
            labels='INBOX',
            snippet='New friend request...'
        )
    ]
    
    for email in emails:
        session.add(email)
    session.commit()
    
    return emails

def create_demo_rules():
    """Create demo rules configuration"""
    return {
        "rules": [
            {
                "name": "Newsletter Auto-Archive",
                "description": "Automatically archive newsletters",
                "predicate": "All",
                "conditions": [
                    {
                        "field": "From",
                        "predicate": "contains",
                        "value": "newsletter"
                    },
                    {
                        "field": "Subject",
                        "predicate": "contains",
                        "value": "newsletter"
                    }
                ],
                "actions": [
                    {
                        "type": "mark as read",
                        "value": ""
                    },
                    {
                        "type": "move message",
                        "value": "Newsletters"
                    }
                ]
            },
            {
                "name": "Old Unread Emails",
                "description": "Mark old unread emails as read",
                "predicate": "Any",
                "conditions": [
                    {
                        "field": "Received Date/Time",
                        "predicate": "less than",
                        "value": "30 days"
                    }
                ],
                "actions": [
                    {
                        "type": "mark as read",
                        "value": ""
                    }
                ]
            },
            {
                "name": "Important Emails",
                "description": "Mark urgent emails as unread and move to Important folder",
                "predicate": "Any",
                "conditions": [
                    {
                        "field": "Subject",
                        "predicate": "contains",
                        "value": "urgent"
                    },
                    {
                        "field": "Message",
                        "predicate": "contains",
                        "value": "urgent"
                    }
                ],
                "actions": [
                    {
                        "type": "mark as unread",
                        "value": ""
                    },
                    {
                        "type": "move message",
                        "value": "Important"
                    }
                ]
            },
            {
                "name": "Social Media Notifications",
                "description": "Archive social media notifications",
                "predicate": "Any",
                "conditions": [
                    {
                        "field": "From",
                        "predicate": "contains",
                        "value": "facebook"
                    },
                    {
                        "field": "From",
                        "predicate": "contains",
                        "value": "twitter"
                    },
                    {
                        "field": "From",
                        "predicate": "contains",
                        "value": "linkedin"
                    }
                ],
                "actions": [
                    {
                        "type": "mark as read",
                        "value": ""
                    },
                    {
                        "type": "move message",
                        "value": "Social Media"
                    }
                ]
            }
        ]
    }

def print_email_status(session, title):
    """Print current email status"""
    print(f"\n{title}")
    print("=" * 50)
    
    emails = session.query(Email).all()
    for email in emails:
        read_status = "READ" if email.is_read else "UNREAD"
        labels = email.labels if email.labels else "No labels"
        print(f"ID: {email.id}")
        print(f"From: {email.from_address}")
        print(f"Subject: {email.subject}")
        print(f"Status: {read_status}")
        print(f"Labels: {labels}")
        print("-" * 30)

def print_rule_executions(session):
    """Print rule execution history"""
    print("\nRule Execution History")
    print("=" * 50)
    
    executions = session.query(RuleExecution).all()
    for execution in executions:
        success_status = "SUCCESS" if execution.success else "FAILED"
        print(f"Rule: {execution.rule_name}")
        print(f"Email ID: {execution.email_id}")
        print(f"Status: {success_status}")
        print(f"Actions: {execution.actions_taken}")
        print(f"Executed: {execution.executed_at}")
        print("-" * 30)

def main():
    """Main demo function"""
    print("Gmail Rule Operations - Demo")
    print("=" * 50)
    print("This demo shows how the rule engine processes emails based on configured rules.")
    print("No actual Gmail API access is required for this demonstration.\n")
    
    # Create demo database and session
    session = create_demo_database()
    
    # Create demo emails
    print("Creating demo emails...")
    emails = create_demo_emails(session)
    print(f"Created {len(emails)} demo emails")
    
    # Show initial email status
    print_email_status(session, "Initial Email Status")
    
    # Create demo rules file
    rules_data = create_demo_rules()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(rules_data, f)
        temp_file = f.name
    
    try:
        # Process rules
        print("\nProcessing emails against rules...")
        with patch('rule_engine.config.RULES_FILE', temp_file), \
             patch('rule_engine.get_session', return_value=session):
            engine = RuleEngine()
            
            stats = engine.process_emails()
            
            print(f"\nProcessing Results:")
            print(f"- Emails processed: {stats['emails_processed']}")
            print(f"- Rules matched: {stats['rules_matched']}")
            print(f"- Actions executed: {stats['actions_executed']}")
            
            # Don't close the engine session as we're using our demo session
        
        # Show final email status
        print_email_status(session, "Final Email Status After Rule Processing")
        
        # Show rule execution history
        print_rule_executions(session)
        
        print("\nDemo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("1. Email storage in database")
        print("2. Rule evaluation with multiple conditions")
        print("3. Action execution (mark as read/unread, move messages)")
        print("4. Rule execution logging")
        print("5. Support for different predicates (All/Any)")
        print("6. Date-based conditions")
        print("7. String matching conditions")
        
    finally:
        os.unlink(temp_file)
        session.close()

if __name__ == "__main__":
    main()
