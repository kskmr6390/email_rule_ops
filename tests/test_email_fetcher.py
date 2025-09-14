"""
Test cases for the email fetcher
"""
import pytest
import base64
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from email_fetcher import EmailFetcher
from models import Email, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestEmailFetcher:
    """Test cases for EmailFetcher class"""
    
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
    def mock_gmail_service(self):
        """Mock Gmail service"""
        service = Mock()
        return service
    
    def test_parse_date_valid(self, temp_db):
        """Test parsing valid date string"""
        fetcher = EmailFetcher()
        date_str = "Mon, 1 Jan 2024 12:00:00 +0000"
        result = fetcher._parse_date(date_str)
        assert isinstance(result, datetime)
    
    def test_parse_date_invalid(self, temp_db):
        """Test parsing invalid date string"""
        fetcher = EmailFetcher()
        date_str = "invalid date"
        result = fetcher._parse_date(date_str)
        assert isinstance(result, datetime)  # Should return current time as fallback
    
    def test_extract_message_body_plain_text(self, temp_db):
        """Test extracting plain text message body"""
        fetcher = EmailFetcher()
        
        payload = {
            'mimeType': 'text/plain',
            'body': {
                'data': base64.urlsafe_b64encode(b'Test message body').decode('utf-8')
            }
        }
        
        result = fetcher._extract_message_body(payload)
        assert result == 'Test message body'
    
    def test_extract_message_body_html(self, temp_db):
        """Test extracting HTML message body"""
        fetcher = EmailFetcher()
        
        payload = {
            'mimeType': 'text/html',
            'body': {
                'data': base64.urlsafe_b64encode(b'<p>Test HTML body</p>').decode('utf-8')
            }
        }
        
        result = fetcher._extract_message_body(payload)
        assert result == '<p>Test HTML body</p>'
    
    def test_extract_message_body_multipart(self, temp_db):
        """Test extracting message body from multipart email"""
        fetcher = EmailFetcher()
        
        payload = {
            'mimeType': 'multipart/alternative',
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': base64.urlsafe_b64encode(b'Plain text version').decode('utf-8')
                    }
                },
                {
                    'mimeType': 'text/html',
                    'body': {
                        'data': base64.urlsafe_b64encode(b'<p>HTML version</p>').decode('utf-8')
                    }
                }
            ]
        }
        
        result = fetcher._extract_message_body(payload)
        assert result == 'Plain text version'
    
    def test_extract_message_body_no_data(self, temp_db):
        """Test extracting message body when no data is available"""
        fetcher = EmailFetcher()
        
        payload = {
            'mimeType': 'text/plain',
            'body': {}
        }
        
        result = fetcher._extract_message_body(payload)
        assert result == ''
    
    @patch('email_fetcher.get_gmail_service')
    def test_fetch_email_details_success(self, mock_get_service, temp_db):
        """Test successful email details fetching"""
        fetcher = EmailFetcher()
        
        # Mock the Gmail service response
        mock_message = {
            'id': 'test_message_id',
            'threadId': 'test_thread_id',
            'snippet': 'Test snippet',
            'labelIds': ['INBOX', 'UNREAD'],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'To', 'value': 'user@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'}
                ],
                'mimeType': 'text/plain',
                'body': {
                    'data': base64.urlsafe_b64encode(b'Test message body').decode('utf-8')
                }
            }
        }

        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get.return_value.execute.return_value = mock_message

        fetcher.service = mock_service

        result = fetcher._fetch_email_details('test_message_id')
        
        assert result is not None
        assert result['id'] == 'test_message_id'
        assert result['from_address'] == 'test@example.com'
        assert result['subject'] == 'Test Subject'
        assert result['is_read'] is False  # UNREAD label present
        assert result['message_body'] == 'Test message body'
    
    
    def test_store_emails_new_email(self, temp_db):
        """Test storing new emails"""
        fetcher = EmailFetcher()
        fetcher.session = temp_db
        
        email_data = {
            'id': 'test_email_1',
            'thread_id': 'thread_1',
            'from_address': 'test@example.com',
            'to_address': 'user@example.com',
            'subject': 'Test Subject',
            'message_body': 'Test message',
            'received_date': datetime.utcnow(),
            'is_read': False,
            'labels': 'INBOX',
            'snippet': 'Test snippet'
        }
        
        result = fetcher.store_emails([email_data])
        assert result == 1
        
        # Verify email was stored
        stored_email = temp_db.query(Email).filter_by(id='test_email_1').first()
        assert stored_email is not None
        assert stored_email.from_address == 'test@example.com'
    
    def test_store_emails_update_existing(self, temp_db):
        """Test updating existing emails"""
        fetcher = EmailFetcher()
        fetcher.session = temp_db
        
        # Create existing email
        existing_email = Email(
            id='test_email_1',
            thread_id='thread_1',
            from_address='old@example.com',
            to_address='user@example.com',
            subject='Old Subject',
            message_body='Old message',
            received_date=datetime.utcnow(),
            is_read=False,
            labels='INBOX',
            snippet='Old snippet'
        )
        temp_db.add(existing_email)
        temp_db.commit()
        
        # Update email data
        email_data = {
            'id': 'test_email_1',
            'thread_id': 'thread_1',
            'from_address': 'new@example.com',
            'to_address': 'user@example.com',
            'subject': 'New Subject',
            'message_body': 'New message',
            'received_date': datetime.utcnow(),
            'is_read': True,
            'labels': 'INBOX,READ',
            'snippet': 'New snippet'
        }
        
        result = fetcher.store_emails([email_data])
        assert result == 1
        
        # Verify email was updated
        updated_email = temp_db.query(Email).filter_by(id='test_email_1').first()
        assert updated_email.from_address == 'new@example.com'
        assert updated_email.subject == 'New Subject'
        assert updated_email.is_read is True
    
    def test_store_emails_error_handling(self, temp_db):
        """Test error handling during email storage"""
        fetcher = EmailFetcher()
        fetcher.session = temp_db
        
        # Invalid email data (missing required fields)
        email_data = {
            'id': 'test_email_1',
            # Missing required fields
        }
        
        result = fetcher.store_emails([email_data])
        assert result == 0  # Should handle error gracefully
    
    @patch('email_fetcher.get_gmail_service')
    def test_fetch_emails_success(self, mock_get_service, temp_db):
        """Test successful email fetching"""
        # Mock Gmail service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock list messages response
        mock_list_response = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'}
            ]
        }
        mock_service.users().messages().list.return_value.execute.return_value = mock_list_response
        
        # Mock individual message responses
        mock_message = {
            'id': 'msg1',
            'threadId': 'thread1',
            'snippet': 'Test snippet',
            'labelIds': ['INBOX'],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'To', 'value': 'user@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'}
                ],
                'mimeType': 'text/plain',
                'body': {
                    'data': base64.urlsafe_b64encode(b'Test message').decode('utf-8')
                }
            }
        }
        mock_service.users().messages().get.return_value.execute.return_value = mock_message
        
        fetcher = EmailFetcher()
        result = fetcher.fetch_emails(max_results=2)
        
        assert len(result) == 2
        assert result[0]['id'] == 'msg1'
    
    @patch('email_fetcher.get_gmail_service')
    def test_fetch_emails_error(self, mock_get_service, temp_db):
        """Test email fetching with error"""
        # Mock service to raise exception
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().list.return_value.execute.side_effect = Exception("API Error")
        
        fetcher = EmailFetcher()
        result = fetcher.fetch_emails()
        
        assert result == []
