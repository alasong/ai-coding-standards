"""
PII 脱敏器（STUB — Phase 2 实现）。

检测并脱敏发送到 AI 上下文中的个人身份信息。
"""
import sys, re

PII_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]'),
    (r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '[REDACTED_EMAIL]'),
    (r'\b\d{11}\b', '[REDACTED_PHONE]'),
]

def redact_pii(text):
    """Redact PII from input text."""
    result = text
    for pattern, replacement in PII_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result

if __name__ == '__main__':
    text = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1]).read()
    print(redact_pii(text))
