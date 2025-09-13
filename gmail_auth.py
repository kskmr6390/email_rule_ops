"""
Gmail API Authentication Module
Handles OAuth authentication with Google's Gmail API
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import config

def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth2
    Returns authenticated service object
    """
    creds = None
    
    # Check if token file exists
    if os.path.exists(config.GMAIL_TOKEN_FILE):
        with open(config.GMAIL_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(config.GMAIL_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Credentials file not found: {config.GMAIL_CREDENTIALS_FILE}. "
                    "Please download it from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GMAIL_CREDENTIALS_FILE, 
                config.GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(config.GMAIL_TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_gmail_service():
    """
    Get authenticated Gmail service object
    """
    from googleapiclient.discovery import build
    
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    return service
