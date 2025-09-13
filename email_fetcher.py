"""
Email fetching and storage module
Handles fetching emails from Gmail API and storing them in the database
"""
import base64
import email
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from gmail_auth import get_gmail_service
from models import Email, get_session
from config import config

class EmailFetcher:
    """Class to handle email fetching and storage operations"""
    
    def __init__(self):
        self.service = get_gmail_service()
        self.session = get_session()
    
    def fetch_emails(self, max_results: int = None) -> List[Dict]:
        """
        Fetch emails from Gmail inbox
        Args:
            max_results: Maximum number of emails to fetch
        Returns:
            List of email dictionaries
        """
        if max_results is None:
            max_results = config.MAX_EMAILS_TO_FETCH
        
        try:
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me', 
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self._fetch_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def _fetch_email_details(self, message_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific email
        Args:
            message_id: Gmail message ID
        Returns:
            Dictionary with email details or None if error
        """
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Extract email data
            email_data = {
                'id': message['id'],
                'thread_id': message['threadId'],
                'from_address': header_dict.get('From', ''),
                'to_address': header_dict.get('To', ''),
                'subject': header_dict.get('Subject', ''),
                'received_date': self._parse_date(header_dict.get('Date', '')),
                'is_read': 'UNREAD' not in message.get('labelIds', []),
                'labels': ','.join(message.get('labelIds', [])),
                'snippet': message.get('snippet', ''),
                'message_body': self._extract_message_body(message['payload'])
            }
            
            return email_data
            
        except Exception as e:
            print(f"Error fetching email details for {message_id}: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse email date string to datetime object
        Args:
            date_str: Date string from email header
        Returns:
            datetime object
        """
        try:
            # Parse RFC 2822 date format
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            return parsed_date
        except Exception:
            # Fallback to current time if parsing fails
            return datetime.utcnow()
    
    def _extract_message_body(self, payload: Dict) -> str:
        """
        Extract message body from email payload
        Args:
            payload: Email payload from Gmail API
        Returns:
            Message body as string
        """
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body:
                    # Use HTML if no plain text found
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            if payload['mimeType'] in ['text/plain', 'text/html']:
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def store_emails(self, emails: List[Dict]) -> int:
        """
        Store emails in the database
        Args:
            emails: List of email dictionaries
        Returns:
            Number of emails successfully stored
        """
        stored_count = 0
        
        for email_data in emails:
            try:
                # Check if email already exists
                existing_email = self.session.query(Email).filter_by(id=email_data['id']).first()
                
                if existing_email:
                    # Update existing email
                    for key, value in email_data.items():
                        if hasattr(existing_email, key):
                            setattr(existing_email, key, value)
                    existing_email.updated_at = datetime.utcnow()
                else:
                    # Create new email record
                    email_obj = Email(**email_data)
                    self.session.add(email_obj)
                
                stored_count += 1
                
            except IntegrityError as e:
                print(f"Integrity error storing email {email_data.get('id', 'unknown')}: {e}")
                self.session.rollback()
            except Exception as e:
                print(f"Error storing email {email_data.get('id', 'unknown')}: {e}")
                self.session.rollback()
        
        try:
            self.session.commit()
        except Exception as e:
            print(f"Error committing email storage: {e}")
            self.session.rollback()
            stored_count = 0
        
        return stored_count
    
    def fetch_and_store_emails(self, max_results: int = None) -> int:
        """
        Fetch emails from Gmail and store them in database
        Args:
            max_results: Maximum number of emails to fetch
        Returns:
            Number of emails successfully stored
        """
        print("Fetching emails from Gmail...")
        emails = self.fetch_emails(max_results)
        print(f"Fetched {len(emails)} emails")
        
        if emails:
            print("Storing emails in database...")
            stored_count = self.store_emails(emails)
            print(f"Successfully stored {stored_count} emails")
            return stored_count
        
        return 0
    
    def close(self):
        """Close database session"""
        self.session.close()
