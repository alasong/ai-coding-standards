"""
升级建议生成器，自动收集证据并生成报告。
"""
import json, sys, subprocess

def collect_metrics(checks):
    """Collect metrics for all upgrade checks."""
    results = {}
    for name, check in checks.items():
        cmd = check.get('query', '')
        if not cmd or any(c in cmd for c in (';', '|', '&', '`', '$(')):
            results[name] = {'error': 'invalid or empty query', 'passed': False}
            continue
        try:
            output = subprocess.check_output(cmd, shell=True, timeout=30).decode().strip()
            value = json.loads(output) if output else True
            results[name] = {
                'value': value,
                'threshold': check.get('threshold'),
                'passed': value >= check['threshold'] if isinstance(value, (int, float)) else value
            }
        except subprocess.TimeoutExpired:
            results[name] = {'error': 'query timed out', 'passed': False}
        except Exception as e:
            results[name] = {'error': str(e), 'passed': False}
    return results

def generate_report(results, target_level):
    all_passed = all(r.get('passed', False) for r in results.values())
    report = {
        'target_level': target_level,
        'all_checks_passed': all_passed,
        'details': results,
        'recommendation': 'APPROVE' if all_passed else 'REVIEW_NEEDED'
    }
    return report

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: upgrade-advisor.py <checks.json> <target_level>")
        sys.exit(1)
    try:
        with open(sys.argv[1]) as f:
            checks = json.load(f)
        target = sys.argv[2]
        metrics = collect_metrics(checks)
        report = generate_report(metrics, target)
        print(json.dumps(report, indent=2))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
