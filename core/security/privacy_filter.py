"""
Privacy filter to detect and mask sensitive information in user inputs.
"""
import re
import logging

logger = logging.getLogger(__name__)

class PrivacyFilter:
    def __init__(self, enable_filter=True):
        self.enable_filter = enable_filter
        
        # Regular expressions for different types of sensitive information
        self.patterns = {
            # Email addresses
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            
            # Phone numbers (various formats)
            'phone': r'\b(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            
            # Credit card numbers
            'credit_card': r'\b(?:\d{4}[\s-]?){4}|\d{16}\b',
            
            # Social security numbers
            'ssn': r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
            
            # IP addresses
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            
            # API keys (common patterns)
            'api_key': r'\b[A-Za-z0-9_-]{20,60}\b',
            
            # URLs containing credentials
            'url_with_credentials': r'https?://[^:]+:[^@]+@[^\s]+'
        }
        
    def enable(self):
        """Enable the privacy filter"""
        self.enable_filter = True
        
    def disable(self):
        """Disable the privacy filter"""
        self.enable_filter = False
        
    def filter_text(self, text):
        """
        Filter sensitive information from text - ONLY APPLIED TO USER INPUTS
        
        Args:
            text (str): The input text to filter
            
        Returns:
            tuple: (filtered_text, has_sensitive_data)
        """
        if not self.enable_filter:
            return text, False
            
        original_text = text
        has_sensitive_data = False
        filtered_text = text
        
        # Apply each pattern and replace matches with mask
        for category, pattern in self.patterns.items():
            # Count matches before filtering
            matches = re.findall(pattern, filtered_text)
            if matches:
                has_sensitive_data = True
                
                # Replace with appropriate mask
                if category == 'email':
                    filtered_text = re.sub(pattern, '[EMAIL REDACTED]', filtered_text)
                elif category == 'phone':
                    filtered_text = re.sub(pattern, '[PHONE REDACTED]', filtered_text)
                elif category == 'credit_card':
                    filtered_text = re.sub(pattern, '[CREDIT CARD REDACTED]', filtered_text)
                elif category == 'ssn':
                    filtered_text = re.sub(pattern, '[SSN REDACTED]', filtered_text)
                elif category == 'ip_address':
                    filtered_text = re.sub(pattern, '[IP ADDRESS REDACTED]', filtered_text)
                elif category == 'api_key':
                    filtered_text = re.sub(pattern, '[API KEY REDACTED]', filtered_text)
                elif category == 'url_with_credentials':
                    filtered_text = re.sub(pattern, '[URL WITH CREDENTIALS REDACTED]', filtered_text)
                
                logger.info(f"Detected and masked {category} in user input")
        
        if has_sensitive_data:
            logger.warning("Sensitive information detected and filtered")
            
        return filtered_text, has_sensitive_data
    
    def get_sensitivity_report(self, text):
        """
        Generate a report of sensitive information found in text
        
        Args:
            text (str): The input text to analyze
            
        Returns:
            dict: A dictionary with counts of each type of sensitive information
        """
        report = {}
        
        for category, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                report[category] = len(matches)
                
        return report