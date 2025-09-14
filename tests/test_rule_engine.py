"""
Test cases for the rule engine
"""
import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from rule_engine import RuleEngine
from models import Email, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestRuleEngine:
    """Test cases for RuleEngine class"""
    
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
    def sample_email(self):
        """Create sample email for testing"""
        return Email(
            id='test_email_1',
            thread_id='thread_1',
            from_address='test@example.com',
            to_address='user@example.com',
            subject='Test Subject',
            message_body='This is a test message',
            received_date=datetime.utcnow(),
            is_read=False,
            labels='INBOX',
            snippet='Test snippet'
        )
    
    @pytest.fixture
    def old_email(self):
        """Create old email for testing"""
        return Email(
            id='old_email_1',
            thread_id='thread_2',
            from_address='old@example.com',
            to_address='user@example.com',
            subject='Old Email',
            message_body='This is an old message',
            received_date=datetime.utcnow() - timedelta(days=35),
            is_read=False,
            labels='INBOX',
            snippet='Old snippet'
        )
    
    @pytest.fixture
    def newsletter_email(self):
        """Create newsletter email for testing"""
        return Email(
            id='newsletter_1',
            thread_id='thread_3',
            from_address='newsletter@company.com',
            to_address='user@example.com',
            subject='Weekly Newsletter',
            message_body='Check out our latest updates',
            received_date=datetime.utcnow(),
            is_read=False,
            labels='INBOX',
            snippet='Newsletter snippet'
        )
    
    def test_load_rules_success(self, temp_db):
        """Test successful rule loading"""
        rules_data = {
            "rules": [
                {
                    "name": "Test Rule",
                    "predicate": "All",
                    "conditions": [
                        {
                            "field": "From",
                            "predicate": "contains",
                            "value": "test"
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_data, f)
            temp_file = f.name
        
        try:
            with patch('rule_engine.config.RULES_FILE', temp_file):
                engine = RuleEngine()
                assert len(engine.rules) == 1
                assert engine.rules[0]['name'] == 'Test Rule'
        finally:
            os.unlink(temp_file)
    
    def test_load_rules_file_not_found(self, temp_db):
        """Test rule loading when file doesn't exist"""
        with patch('rule_engine.config.RULES_FILE', 'nonexistent.json'):
            engine = RuleEngine()
            assert engine.rules == []
    
    def test_load_rules_invalid_json(self, temp_db):
        """Test rule loading with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_file = f.name
        
        try:
            with patch('rule_engine.config.RULES_FILE', temp_file):
                engine = RuleEngine()
                assert engine.rules == []
        finally:
            os.unlink(temp_file)
    
    def test_evaluate_condition_contains(self, temp_db, sample_email):
        """Test condition evaluation with 'contains' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "From",
            "predicate": "contains",
            "value": "test"
        }
        
        result = engine._evaluate_condition(condition, sample_email)
        assert result is True
        
        condition["value"] = "nonexistent"
        result = engine._evaluate_condition(condition, sample_email)
        assert result is False
    
    def test_evaluate_condition_equals(self, temp_db, sample_email):
        """Test condition evaluation with 'equals' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "Subject",
            "predicate": "equals",
            "value": "test subject"
        }
        
        result = engine._evaluate_condition(condition, sample_email)
        assert result is True
        
        condition["value"] = "different subject"
        result = engine._evaluate_condition(condition, sample_email)
        assert result is False
    
    def test_evaluate_condition_does_not_contain(self, temp_db, sample_email):
        """Test condition evaluation with 'does not contain' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "Message",
            "predicate": "does not contain",
            "value": "nonexistent"
        }
        
        result = engine._evaluate_condition(condition, sample_email)
        assert result is True
        
        condition["value"] = "test"
        result = engine._evaluate_condition(condition, sample_email)
        assert result is False
    
    def test_evaluate_condition_date_less_than(self, temp_db, old_email):
        """Test condition evaluation with date 'less than' predicate"""
        engine = RuleEngine()
        
        condition = {
            "field": "Received Date/Time",
            "predicate": "less than",
            "value": "30 days"
        }
        
        result = engine._evaluate_condition(condition, old_email)
        assert result is True
        
        condition["value"] = "50 days"
        result = engine._evaluate_condition(condition, old_email)
        assert result is False
    
    
    def test_evaluate_rule_all_predicate(self, temp_db, newsletter_email):
        """Test rule evaluation with 'All' predicate"""
        engine = RuleEngine()
        
        rule = {
            "name": "Newsletter Rule",
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
            "actions": []
        }
        
        result = engine.evaluate_rule(rule, newsletter_email)
        assert result is True
        
        # Test with one condition failing
        rule["conditions"][1]["value"] = "nonexistent"
        result = engine.evaluate_rule(rule, newsletter_email)
        assert result is False
    
    def test_evaluate_rule_any_predicate(self, temp_db, newsletter_email):
        """Test rule evaluation with 'Any' predicate"""
        engine = RuleEngine()
        
        rule = {
            "name": "Newsletter Rule",
            "predicate": "Any",
            "conditions": [
                {
                    "field": "From",
                    "predicate": "contains",
                    "value": "newsletter"
                },
                {
                    "field": "Subject",
                    "predicate": "contains",
                    "value": "nonexistent"
                }
            ],
            "actions": []
        }
        
        result = engine.evaluate_rule(rule, newsletter_email)
        assert result is True  # First condition matches
        
        # Test with no conditions matching
        rule["conditions"][0]["value"] = "nonexistent"
        result = engine.evaluate_rule(rule, newsletter_email)
        assert result is False
    
    def test_mark_as_read(self, temp_db, sample_email):
        """Test marking email as read"""
        engine = RuleEngine()
        engine.session = temp_db
        
        temp_db.add(sample_email)
        temp_db.commit()
        
        result = engine._mark_as_read(sample_email)
        assert result is True
        assert sample_email.is_read is True
    
    def test_mark_as_unread(self, temp_db, sample_email):
        """Test marking email as unread"""
        engine = RuleEngine()
        engine.session = temp_db
        
        sample_email.is_read = True
        temp_db.add(sample_email)
        temp_db.commit()
        
        result = engine._mark_as_unread(sample_email)
        assert result is True
        assert sample_email.is_read is False
    
    def test_move_message(self, temp_db, sample_email):
        """Test moving email to different label"""
        engine = RuleEngine()
        engine.session = temp_db
        
        temp_db.add(sample_email)
        temp_db.commit()
        
        result = engine._move_message(sample_email, "Archive")
        assert result is True
        assert "Archive" in sample_email.labels
    
    def test_execute_actions(self, temp_db, sample_email):
        """Test executing actions on email"""
        engine = RuleEngine()
        engine.session = temp_db
        
        temp_db.add(sample_email)
        temp_db.commit()
        
        rule = {
            "name": "Test Rule",
            "actions": [
                {
                    "type": "mark as read",
                    "value": ""
                },
                {
                    "type": "move message",
                    "value": "Test Folder"
                }
            ]
        }
        
        actions = engine.execute_actions(rule, sample_email)
        assert len(actions) == 2
        assert sample_email.is_read is True
        assert "Test Folder" in sample_email.labels
    
    def test_get_field_value(self, temp_db, sample_email):
        """Test getting field values from email"""
        engine = RuleEngine()
        
        assert engine._get_field_value(sample_email, 'From') == 'test@example.com'
        assert engine._get_field_value(sample_email, 'Subject') == 'Test Subject'
        assert engine._get_field_value(sample_email, 'Message') == 'This is a test message'
        assert engine._get_field_value(sample_email, 'Received Date/Time') == sample_email.received_date
        assert engine._get_field_value(sample_email, 'Nonexistent') == ''
    
    def test_compare_dates_invalid_format(self, temp_db):
        """Test date comparison with invalid format"""
        engine = RuleEngine()
        
        result = engine._compare_dates(datetime.utcnow(), "invalid format", "less")
        assert result is False
    

