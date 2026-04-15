"""
密钥脱敏器（STUB — Phase 2 实现）。

检测并脱敏发送到 AI 上下文中的密钥/Token。
"""
import sys, re

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})', '[REDACTED_API_KEY]'),
    (r'(?i)(secret[_-]?key|access[_-]?token)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{16,})', '[REDACTED_SECRET]'),
    (r'(?i)(password|passwd)\s*[:=]\s*["\']?[^\s"\']+', '[REDACTED_PASSWORD]'),
]

def redact_secrets(text):
    """Redact secrets from input text."""
    # TODO: Phase 2 — use gitleaks/trufflehog for structured detection
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = re.sub(pattern, f'\\1={replacement}', result)
    return result

if __name__ == '__main__':
    text = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1]).read()
    print(redact_secrets(text))
