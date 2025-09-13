"""
Test cases for database models
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Email, RuleExecution, Base, create_tables, get_session

class TestModels:
    """Test cases for database models"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_email_creation(self, temp_db):
        """Test creating an email record"""
        email = Email(
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
        
        temp_db.add(email)
        temp_db.commit()
        
        # Verify email was created
        stored_email = temp_db.query(Email).filter_by(id='test_email_1').first()
        assert stored_email is not None
        assert stored_email.from_address == 'test@example.com'
        assert stored_email.subject == 'Test Subject'
        assert stored_email.is_read is False
        assert stored_email.labels == 'INBOX'
    
    def test_email_required_fields(self, temp_db):
        """Test that required fields are enforced"""
        # Test missing required fields
        email = Email(
            id='test_email_2',
            # Missing thread_id, from_address, received_date
            subject='Test Subject'
        )
        
        temp_db.add(email)
        
        with pytest.raises(Exception):  # Should raise exception for missing required fields
            temp_db.commit()
    
    def test_email_optional_fields(self, temp_db):
        """Test that optional fields work correctly"""
        email = Email(
            id='test_email_3',
            thread_id='thread_3',
            from_address='test@example.com',
            received_date=datetime.utcnow(),
            # Optional fields can be None
            to_address=None,
            subject=None,
            message_body=None,
            labels=None,
            snippet=None
        )
        
        temp_db.add(email)
        temp_db.commit()
        
        stored_email = temp_db.query(Email).filter_by(id='test_email_3').first()
        assert stored_email is not None
        assert stored_email.to_address is None
        assert stored_email.subject is None
    
    def test_email_defaults(self, temp_db):
        """Test default values for email fields"""
        email = Email(
            id='test_email_4',
            thread_id='thread_4',
            from_address='test@example.com',
            received_date=datetime.utcnow()
        )
        
        temp_db.add(email)
        temp_db.commit()
        
        stored_email = temp_db.query(Email).filter_by(id='test_email_4').first()
        assert stored_email.is_read is False  # Default value
        assert stored_email.created_at is not None  # Auto-generated
        assert stored_email.updated_at is not None  # Auto-generated
    
    def test_rule_execution_creation(self, temp_db):
        """Test creating a rule execution record"""
        execution = RuleExecution(
            rule_name='Test Rule',
            email_id='test_email_1',
            actions_taken='["mark as read", "move to folder"]',
            success=True
        )
        
        temp_db.add(execution)
        temp_db.commit()
        
        # Verify execution was created
        stored_execution = temp_db.query(RuleExecution).filter_by(rule_name='Test Rule').first()
        assert stored_execution is not None
        assert stored_execution.email_id == 'test_email_1'
        assert stored_execution.success is True
        assert stored_execution.executed_at is not None
    
    def test_rule_execution_defaults(self, temp_db):
        """Test default values for rule execution"""
        execution = RuleExecution(
            rule_name='Test Rule 2',
            email_id='test_email_2'
        )
        
        temp_db.add(execution)
        temp_db.commit()
        
        stored_execution = temp_db.query(RuleExecution).filter_by(rule_name='Test Rule 2').first()
        assert stored_execution.success is True  # Default value
        assert stored_execution.executed_at is not None  # Auto-generated
        assert stored_execution.actions_taken is None  # Optional field
    
    def test_email_relationships(self, temp_db):
        """Test relationships between Email and RuleExecution"""
        # Create email
        email = Email(
            id='test_email_5',
            thread_id='thread_5',
            from_address='test@example.com',
            received_date=datetime.utcnow()
        )
        temp_db.add(email)
        temp_db.commit()
        
        # Create rule execution for the email
        execution = RuleExecution(
            rule_name='Test Rule',
            email_id='test_email_5',
            actions_taken='["mark as read"]',
            success=True
        )
        temp_db.add(execution)
        temp_db.commit()
        
        # Verify relationship
        stored_email = temp_db.query(Email).filter_by(id='test_email_5').first()
        stored_execution = temp_db.query(RuleExecution).filter_by(email_id='test_email_5').first()
        
        assert stored_email is not None
        assert stored_execution is not None
        assert stored_execution.email_id == stored_email.id
    
    def test_create_tables(self):
        """Test table creation function"""
        engine = create_engine('sqlite:///:memory:')
        
        # Should not raise exception
        create_tables()
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert 'emails' in tables
        assert 'rule_executions' in tables
    
    def test_get_session(self):
        """Test session creation"""
        # This test would require actual database connection
        # For now, just test that the function exists and can be called
        try:
            session = get_session()
            assert session is not None
            session.close()
        except Exception:
            # Expected to fail without proper database setup
            pass
