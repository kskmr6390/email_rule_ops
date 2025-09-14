"""
Integration tests for the complete Gmail Rule Operations system
"""
import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from email_fetcher import EmailFetcher
from rule_engine import RuleEngine
from models import Email, RuleExecution, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_rules(self):
        """Sample rules for testing"""
        return {
            "rules": [
                {
                    "name": "Newsletter Rule",
                    "description": "Archive newsletters",
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
                    "name": "Old Email Rule",
                    "description": "Mark old emails as read",
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
                }
            ]
        }
    
    def test_end_to_end_newsletter_processing(self, temp_db, sample_rules):
        """Test complete end-to-end processing of newsletter emails"""
        # Create temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_rules, f)
            temp_file = f.name
        
        try:
            with patch('rule_engine.config.RULES_FILE', temp_file):
                # Create sample emails
                newsletter_email = Email(
                    id='newsletter_1',
                    thread_id='thread_1',
                    from_address='newsletter@company.com',
                    to_address='user@example.com',
                    subject='Weekly Newsletter Update',
                    message_body='Check out our latest news',
                    received_date=datetime.utcnow(),
                    is_read=False,
                    labels='INBOX',
                    snippet='Newsletter snippet'
                )
                
                regular_email = Email(
                    id='regular_1',
                    thread_id='thread_2',
                    from_address='friend@example.com',
                    to_address='user@example.com',
                    subject='Hello there',
                    message_body='Just saying hi',
                    received_date=datetime.utcnow(),
                    is_read=False,
                    labels='INBOX',
                    snippet='Regular email snippet'
                )
                
                # Add emails to database
                temp_db.add(newsletter_email)
                temp_db.add(regular_email)
                temp_db.commit()
                
                # Process rules
                engine = RuleEngine()
                engine.session = temp_db
                
                stats = engine.process_emails()
                
                # Verify results
                assert stats['emails_processed'] == 2
                assert stats['rules_matched'] >= 1  # Newsletter rule should match
                assert stats['actions_executed'] >= 1
                
                # Verify newsletter email was processed
                updated_newsletter = temp_db.query(Email).filter_by(id='newsletter_1').first()
                assert updated_newsletter.is_read is True
                assert 'Newsletters' in updated_newsletter.labels
                
                # Verify regular email was not affected by newsletter rule
                updated_regular = temp_db.query(Email).filter_by(id='regular_1').first()
                assert updated_regular.is_read is False
                assert 'Newsletters' not in updated_regular.labels
                
                # Verify rule execution was logged
                executions = temp_db.query(RuleExecution).filter_by(email_id='newsletter_1').all()
                assert len(executions) >= 1
                
                engine.close()
                
        finally:
            os.unlink(temp_file)
    
    def test_end_to_end_old_email_processing(self, temp_db, sample_rules):
        """Test complete end-to-end processing of old emails"""
        # Create temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_rules, f)
            temp_file = f.name
        
        try:
            with patch('rule_engine.config.RULES_FILE', temp_file):
                # Create old email
                old_email = Email(
                    id='old_email_1',
                    thread_id='thread_1',
                    from_address='old@example.com',
                    to_address='user@example.com',
                    subject='Old Message',
                    message_body='This is an old message',
                    received_date=datetime.utcnow() - timedelta(days=35),
                    is_read=False,
                    labels='INBOX',
                    snippet='Old email snippet'
                )
                
                # Add email to database
                temp_db.add(old_email)
                temp_db.commit()
                
                # Process rules
                engine = RuleEngine()
                engine.session = temp_db
                
                stats = engine.process_emails()
                
                # Verify results
                assert stats['emails_processed'] == 1
                assert stats['rules_matched'] >= 1  # Old email rule should match
                assert stats['actions_executed'] >= 1
                
                # Verify old email was marked as read
                updated_old_email = temp_db.query(Email).filter_by(id='old_email_1').first()
                assert updated_old_email.is_read is True
                
                engine.close()
                
        finally:
            os.unlink(temp_file)
    
    def test_multiple_rules_same_email(self, temp_db, sample_rules):
        """Test that multiple rules can match the same email"""
        # Create temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_rules, f)
            temp_file = f.name
        
        try:
            with patch('rule_engine.config.RULES_FILE', temp_file):
                # Create email that matches both rules (old newsletter)
                old_newsletter = Email(
                    id='old_newsletter_1',
                    thread_id='thread_1',
                    from_address='newsletter@company.com',
                    to_address='user@example.com',
                    subject='Old Newsletter',
                    message_body='Old newsletter content',
                    received_date=datetime.utcnow() - timedelta(days=35),
                    is_read=False,
                    labels='INBOX',
                    snippet='Old newsletter snippet'
                )
                
                # Add email to database
                temp_db.add(old_newsletter)
                temp_db.commit()
                
                # Process rules
                engine = RuleEngine()
                engine.session = temp_db
                
                stats = engine.process_emails()
                
                # Verify results - should match both rules
                assert stats['emails_processed'] == 1
                assert stats['rules_matched'] == 2  # Both rules should match
                assert stats['actions_executed'] >= 2  # Actions from both rules
                
                # Verify email was processed by both rules
                updated_email = temp_db.query(Email).filter_by(id='old_newsletter_1').first()
                assert updated_email.is_read is True  # From old email rule
                assert 'Newsletters' in updated_email.labels  # From newsletter rule
                
                # Verify both rule executions were logged
                executions = temp_db.query(RuleExecution).filter_by(email_id='old_newsletter_1').all()
                assert len(executions) == 2
                
                engine.close()
                
        finally:
            os.unlink(temp_file)
    
    def test_no_matching_rules(self, temp_db, sample_rules):
        """Test processing when no rules match"""
        # Create temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_rules, f)
            temp_file = f.name
        
        try:
            with patch('rule_engine.config.RULES_FILE', temp_file):
                # Create email that doesn't match any rules
                regular_email = Email(
                    id='regular_1',
                    thread_id='thread_1',
                    from_address='friend@example.com',
                    to_address='user@example.com',
                    subject='Hello',
                    message_body='Just a regular message',
                    received_date=datetime.utcnow() - timedelta(days=5),  # Not old enough
                    is_read=False,
                    labels='INBOX',
                    snippet='Regular email snippet'
                )
                
                # Add email to database
                temp_db.add(regular_email)
                temp_db.commit()
                
                # Process rules
                engine = RuleEngine()
                engine.session = temp_db
                
                stats = engine.process_emails()
                
                # Verify results - no rules should match
                assert stats['emails_processed'] == 1
                assert stats['rules_matched'] == 0
                assert stats['actions_executed'] == 0
                
                # Verify email was not modified
                unchanged_email = temp_db.query(Email).filter_by(id='regular_1').first()
                assert unchanged_email.is_read is False
                assert unchanged_email.labels == 'INBOX'
                
                # Verify no rule executions were logged
                executions = temp_db.query(RuleExecution).filter_by(email_id='regular_1').all()
                assert len(executions) == 0
                
                engine.close()
                
        finally:
            os.unlink(temp_file)
    
