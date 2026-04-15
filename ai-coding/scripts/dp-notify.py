"""
Decision Point 通知发送器（STUB — Phase 2 实现）。

发送 DP1/DP2 确认通知到 Slack/邮件。
"""
import argparse

def notify(dp_type, title, context, channel):
    """Send DP notification to configured channel."""
    # TODO: Phase 2 implementation
    print(f"[DP NOTIFY] STUB: {dp_type} - {title}")
    print(f"[DP NOTIFY] Channel: {channel}")

if __name__ == '__main__':
    print("[DP NOTIFY] STUB: Phase 2 implementation needed", file=sys.stderr)
    sys.exit(2)  # NOT_IMPLEMENTED
