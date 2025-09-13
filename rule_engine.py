"""
Rule Engine for Gmail Email Processing
Handles rule evaluation and action execution
"""
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Email, RuleExecution, get_session
from config import config

class RuleEngine:
    """Engine for processing email rules"""
    
    def __init__(self):
        self.session = get_session()
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict]:
        """
        Load rules from JSON configuration file
        Returns:
            List of rule dictionaries
        """
        try:
            with open(config.RULES_FILE, 'r') as f:
                rules_data = json.load(f)
                return rules_data.get('rules', [])
        except FileNotFoundError:
            print(f"Rules file not found: {config.RULES_FILE}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing rules file: {e}")
            return []
    
    def evaluate_rule(self, rule: Dict, email: Email) -> bool:
        """
        Evaluate if an email matches a rule
        Args:
            rule: Rule dictionary
            email: Email object
        Returns:
            True if email matches rule, False otherwise
        """
        conditions = rule.get('conditions', [])
        predicate = rule.get('predicate', 'All')  # 'All' or 'Any'
        
        if not conditions:
            return False
        
        results = []
        for condition in conditions:
            result = self._evaluate_condition(condition, email)
            results.append(result)
        
        if predicate == 'All':
            return all(results)
        else:  # 'Any'
            return any(results)
    
    def _evaluate_condition(self, condition: Dict, email: Email) -> bool:
        """
        Evaluate a single condition against an email
        Args:
            condition: Condition dictionary
            email: Email object
        Returns:
            True if condition matches, False otherwise
        """
        field = condition.get('field')
        predicate = condition.get('predicate')
        value = condition.get('value')
        
        if not all([field, predicate, value]):
            return False
        
        # Get field value from email
        field_value = self._get_field_value(email, field)
        
        # Evaluate based on predicate
        if predicate == 'contains':
            return value.lower() in field_value.lower()
        elif predicate == 'does not contain':
            return value.lower() not in field_value.lower()
        elif predicate == 'equals':
            return field_value.lower() == value.lower()
        elif predicate == 'does not equal':
            return field_value.lower() != value.lower()
        elif predicate == 'less than':
            return self._compare_dates(field_value, value, 'less')
        elif predicate == 'greater than':
            return self._compare_dates(field_value, value, 'greater')
        else:
            return False
    
    def _get_field_value(self, email: Email, field: str) -> str:
        """
        Get field value from email object
        Args:
            email: Email object
            field: Field name
        Returns:
            Field value as string
        """
        field_mapping = {
            'From': email.from_address or '',
            'To': email.to_address or '',
            'Subject': email.subject or '',
            'Message': email.message_body or '',
            'Received Date/Time': email.received_date
        }
        
        return field_mapping.get(field, '')
    
    def _compare_dates(self, email_date: datetime, condition_value: str, operator: str) -> bool:
        """
        Compare email date with condition value
        Args:
            email_date: Email received date
            condition_value: Condition value (e.g., "7 days", "1 month")
            operator: 'less' or 'greater'
        Returns:
            True if condition matches, False otherwise
        """
        try:
            # Parse condition value (e.g., "7 days", "1 month")
            parts = condition_value.strip().split()
            if len(parts) != 2:
                return False
            
            number = int(parts[0])
            unit = parts[1].lower()
            
            # Calculate threshold date
            if unit in ['day', 'days']:
                threshold = datetime.utcnow() - timedelta(days=number)
            elif unit in ['month', 'months']:
                threshold = datetime.utcnow() - timedelta(days=number * 30)  # Approximate
            else:
                return False
            
            if operator == 'less':
                return email_date < threshold
            else:  # greater
                return email_date > threshold
                
        except (ValueError, AttributeError):
            return False
    
    def execute_actions(self, rule: Dict, email: Email) -> List[str]:
        """
        Execute actions for a matched email
        Args:
            rule: Rule dictionary
            email: Email object
        Returns:
            List of actions performed
        """
        actions = rule.get('actions', [])
        performed_actions = []
        
        for action in actions:
            action_type = action.get('type')
            action_value = action.get('value')
            
            if action_type == 'mark as read':
                if self._mark_as_read(email):
                    performed_actions.append(f"Marked as read: {email.id}")
            
            elif action_type == 'mark as unread':
                if self._mark_as_unread(email):
                    performed_actions.append(f"Marked as unread: {email.id}")
            
            elif action_type == 'move message':
                if self._move_message(email, action_value):
                    performed_actions.append(f"Moved to {action_value}: {email.id}")
        
        return performed_actions
    
    def _mark_as_read(self, email: Email) -> bool:
        """
        Mark email as read in database
        Args:
            email: Email object
        Returns:
            True if successful, False otherwise
        """
        try:
            email.is_read = True
            email.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error marking email as read: {e}")
            self.session.rollback()
            return False
    
    def _mark_as_unread(self, email: Email) -> bool:
        """
        Mark email as unread in database
        Args:
            email: Email object
        Returns:
            True if successful, False otherwise
        """
        try:
            email.is_read = False
            email.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error marking email as unread: {e}")
            self.session.rollback()
            return False
    
    def _move_message(self, email: Email, label: str) -> bool:
        """
        Move email to specified label (folder)
        Args:
            email: Email object
            label: Target label/folder
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update labels in database
            current_labels = email.labels.split(',') if email.labels else []
            if label not in current_labels:
                current_labels.append(label)
                email.labels = ','.join(current_labels)
                email.updated_at = datetime.utcnow()
                self.session.commit()
            return True
        except Exception as e:
            print(f"Error moving email: {e}")
            self.session.rollback()
            return False
    
    def process_emails(self) -> Dict[str, int]:
        """
        Process all emails against all rules
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'emails_processed': 0,
            'rules_matched': 0,
            'actions_executed': 0
        }
        
        # Get all emails
        emails = self.session.query(Email).all()
        stats['emails_processed'] = len(emails)
        
        for email in emails:
            for rule in self.rules:
                try:
                    if self.evaluate_rule(rule, email):
                        stats['rules_matched'] += 1
                        
                        # Execute actions
                        actions = self.execute_actions(rule, email)
                        stats['actions_executed'] += len(actions)
                        
                        # Log rule execution
                        self._log_rule_execution(rule.get('name', 'Unnamed Rule'), 
                                               email.id, actions, True)
                        
                except Exception as e:
                    print(f"Error processing rule for email {email.id}: {e}")
                    self._log_rule_execution(rule.get('name', 'Unnamed Rule'), 
                                           email.id, [str(e)], False)
        
        return stats
    
    def _log_rule_execution(self, rule_name: str, email_id: str, 
                          actions: List[str], success: bool):
        """
        Log rule execution to database
        Args:
            rule_name: Name of the rule
            email_id: Email ID
            actions: List of actions performed
            success: Whether execution was successful
        """
        try:
            execution = RuleExecution(
                rule_name=rule_name,
                email_id=email_id,
                actions_taken=json.dumps(actions),
                success=success
            )
            self.session.add(execution)
            self.session.commit()
        except Exception as e:
            print(f"Error logging rule execution: {e}")
            self.session.rollback()
    
    def close(self):
        """Close database session"""
        self.session.close()
