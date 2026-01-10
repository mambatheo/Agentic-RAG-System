import re
from typing import Dict, List, Tuple

class SafetyValidator:
    """Input validation and output sanitization"""
    
    MALICIOUS_PATTERNS = [
        r'(?i)(ignore\s+previous|disregard\s+all)',
        r'(?i)(system\s+prompt|override\s+instructions)',
        r'(?i)(<script|javascript:|onerror=)',
        r'(?i)(union\s+select|drop\s+table|delete\s+from)',
        r'(?i)(exec\s*\(|eval\s*\(|__import__)',
    ]
    
    UNSAFE_CONTENT = [
        r'(?i)(how\s+to\s+(make|build|create)\s+(bomb|weapon|explosive))',
        r'(?i)(illegal\s+(drugs|hacking|fraud))',
        r'(?i)(personal\s+(ssn|credit\s+card|password))',
    ]
    
    MAX_QUERY_LENGTH = 2000
    MIN_QUERY_LENGTH = 3
    
    @classmethod
    def validate_input(cls, query: str) -> Tuple[bool, List[str]]:
        issues = []
        
        if len(query) < cls.MIN_QUERY_LENGTH:
            issues.append("Query too short")
        if len(query) > cls.MAX_QUERY_LENGTH:
            issues.append("Query exceeds maximum length")
        
        for pattern in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, query):
                issues.append(f"Potential injection detected")
        
        for pattern in cls.UNSAFE_CONTENT:
            if re.search(pattern, query):
                issues.append("Query requests potentially unsafe content")
        
        special_char_ratio = sum(not c.isalnum() and not c.isspace() for c in query) / len(query)
        if special_char_ratio > 0.3:
            issues.append("Excessive special characters detected")
        
        return len(issues) == 0, issues
    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """Sanitize output to prevent XSS and injection attacks"""
    # Remove script tags and dangerous HTML
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<iframe.*?</iframe>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Redact SQL injection patterns
        text = re.sub(r'(?i)(drop\s+table|delete\s+from|insert\s+into)', '[REDACTED]', text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Optional: Escape HTML if displaying in web (uncomment if needed)
        # text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        return text.strip()
        
    
    
    @classmethod
    def validate_retrieved_docs(cls, docs: List[str]) -> List[str]:
        safe_docs = []
        for doc in docs:
            if len(doc) > 10000:
                continue
            if not any(pattern in doc.lower() for pattern in ['confidential', 'internal only', 'classified']):
                safe_docs.append(doc)
        return safe_docs