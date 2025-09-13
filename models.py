"""
Database models for Gmail Rule Operations
"""
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import config

Base = declarative_base()

class Email(Base):
    """Email model to store Gmail messages"""
    __tablename__ = 'emails'
    
    id = Column(String, primary_key=True)  # Gmail message ID
    thread_id = Column(String, nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    message_body = Column(Text, nullable=True)
    received_date = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False)
    labels = Column(String, nullable=True)  # Comma-separated list of labels
    snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RuleExecution(Base):
    """Model to track rule executions"""
    __tablename__ = 'rule_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String, nullable=False)
    email_id = Column(String, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    actions_taken = Column(Text, nullable=True)  # JSON string of actions performed
    success = Column(Boolean, default=True)

# Database setup
def get_database_engine():
    """Create and return database engine"""
    return create_engine(config.DATABASE_URL)

def get_session():
    """Create and return database session"""
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def create_tables():
    """Create all database tables"""
    engine = get_database_engine()
    Base.metadata.create_all(engine)
