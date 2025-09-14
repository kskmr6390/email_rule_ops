# Gmail Rule Operations

## Overview

A standalone Python script that integrates with Gmail API and performs rule-based operations on emails. This tool allows you to automatically process emails based on configurable rules, such as marking emails as read/unread, moving emails to specific folders, and more.

## Features

- **Gmail API Integration**: Authenticates with Gmail using OAuth2
- **Email Storage**: Stores emails in a relational database (PostgreSQL/SQLite)
- **Rule Engine**: Processes emails based on configurable JSON rules
- **Flexible Conditions**: Support for various field types and predicates
- **Multiple Actions**: Mark as read/unread, move messages to folders
- **Comprehensive Logging**: Detailed logging of all operations
- **Database Tracking**: Tracks rule executions and actions taken

## Requirements

- Python 3.7+
- Gmail account with API access
- Google Cloud Console project with Gmail API enabled
- Database (PostgreSQL, or SQLite)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kskmr6390/email_rule_ops.git
   ```
   
   ```bash
   cd emails_rule_ops
   ```

2. ** Create a virtual env & Install dependencies**:
   ```bash
   python3 -m venv venv
   ```
   
   ```bash
   source venv/bin/activate
   ```
   
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials JSON file and save it as `credentials.json`

4. **Configure environment**:
   ```bash
   cp config/env.example config/.env
   # Edit .env file with your configuration
   ```

5. **Set up database**:
   - **Default (SQLite)**: No setup required, will create `gmail_rules.db` automatically
   - **PostgreSQL**: Create a database and set `DATABASE_URL` in `.env` for production use

## Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json

# Database Configuration
# Default: SQLite (no setup required)
# DATABASE_URL=sqlite:///gmail_rules.db

# For PostgreSQL (production):
# DATABASE_URL=postgresql://username:password@localhost:5432/gmail_rules

# Email Processing Configuration
MAX_EMAILS_TO_FETCH=100
EMAIL_BATCH_SIZE=10

# Rules Configuration
RULES_FILE=rules.json

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=gmail_rules.log
```

### Rules Configuration

Rules are defined in `rules.json`. Each rule has:

- **name**: Descriptive name for the rule
- **description**: Optional description
- **predicate**: "All" (all conditions must match) or "Any" (at least one condition must match)
- **conditions**: List of conditions to evaluate
- **actions**: List of actions to perform when conditions match

#### Supported Fields:
- `From`: Sender email address
- `To`: Recipient email address
- `Subject`: Email subject
- `Message`: Email body content
- `Received Date/Time`: When the email was received

#### Supported Predicates:
- **String fields** (From, To, Subject, Message):
  - `contains`: Field contains the value
  - `does not contain`: Field does not contain the value
  - `equals`: Field equals the value exactly
  - `does not equal`: Field does not equal the value

- **Date field** (Received Date/Time):
  - `less than`: Email is older than specified time (e.g., "7 days", "1 month")
  - `greater than`: Email is newer than specified time

#### Supported Actions:
- `mark as read`: Mark the email as read
- `mark as unread`: Mark the email as unread
- `move message`: Move email to specified label/folder

#### Example Rule:
```json
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
}
```

## Usage

### Command Line Options

```bash
python main.py [options]
```

**Options:**
- `--setup-db`: Initialize database tables
- `--fetch-emails`: Fetch emails from Gmail and store in database
- `--process-rules`: Process stored emails against configured rules
- `--max-emails N`: Limit number of emails to fetch (default: 100)
- `--all`: Run all operations (setup, fetch, process)

### Examples

1. **Initial setup** (run once):
   ```bash
   python main.py --setup-db
   ```

2. **Fetch emails**:
   ```bash
   python main.py --fetch-emails --max-emails 50
   ```

3. **Process rules**:
   ```bash
   python main.py --process-rules
   ```

4. **Run everything**:
   ```bash
   python main.py --all
   ```

### First Run

1. **Set up database**:
   ```bash
   python main.py --setup-db
   ```

2. **Fetch emails** (this will open browser for OAuth):
   ```bash
   python main.py --fetch-emails
   ```

3. **Process rules**:
   ```bash
   python main.py --process-rules
   ```
## Flow Diagram

```mermaid
flowchart TD
   A([Start]) --> B[Initialize Application]
   B --> C[Load Configuration]
   C --> D[Authenticate with Gmail API]
   D --> E[Fetch Emails]
   E --> F[Store Emails in Database]
   F --> G[Load Rules from JSON]
   G --> H[Evaluate Rules]
   H --> I[Execute Actions]
   I --> J[Log Rule Execution]
   J --> K([End])

   subgraph Error_Handling [Error Handling]
      D -.-> L[Handle Authentication Errors]
      E -.-> M[Handle API Errors]
      F -.-> N[Handle Database Errors]
      H -.-> O[Handle Rule Evaluation Errors]
      I -.-> P[Handle Action Execution Errors]
   end
```

## Database Schema

### Emails Table
- `id`: Gmail message ID (primary key)
- `thread_id`: Gmail thread ID
- `from_address`: Sender email
- `to_address`: Recipient email
- `subject`: Email subject
- `message_body`: Email content
- `received_date`: When email was received
- `is_read`: Read status
- `labels`: Comma-separated list of labels
- `snippet`: Email snippet
- `created_at`: Record creation time
- `updated_at`: Record last update time

### Rule Executions Table
- `id`: Auto-increment primary key
- `rule_name`: Name of executed rule
- `email_id`: Email ID that was processed
- `executed_at`: When rule was executed
- `actions_taken`: JSON string of actions performed
- `success`: Whether execution was successful

## Testing

Run the test suite:

```bash
pytest tests/
```

## Logging

The application logs all operations to both console and file (`gmail_rules.log` by default). Log levels can be configured via the `LOG_LEVEL` environment variable.

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   - Ensure `credentials.json` is in the project root
   - Check that Gmail API is enabled in Google Cloud Console
   - Delete `token.json` and re-authenticate

2. **Database Connection Error**:
   - Verify database credentials in `.env`
   - Ensure database server is running
   - Check database exists (for PostgreSQL)

3. **Permission Errors**:
   - Ensure Gmail API has necessary scopes
   - Check that the OAuth consent screen is configured

4. **Rule Processing Issues**:
   - Validate `rules.json` syntax
   - Check field names and predicates are correct
   - Review logs for specific error messages

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python main.py --process-rules
```

## Security Considerations

- Keep `credentials.json` and `token.json` secure
- Use environment variables for sensitive configuration
- Regularly rotate OAuth tokens
- Limit Gmail API scopes to minimum required

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue with detailed information about your setup and the problem
