"""
按风险等级排序 PR，辅助人工审查优先级。
"""
import json, sys

def score_pr(pr):
    score = 0
    additions = pr.get('additions', 0)
    deletions = pr.get('deletions', 0)
    if additions + deletions > 500:
        score += 30
    elif additions + deletions > 100:
        score += 15
    core_files = ['auth/', 'config/', 'db/', 'api/']
    for f in pr.get('changed_files', []):
        if any(core in f for core in core_files):
            score += 20
    score += pr.get('self_correction_rounds', 0) * 15
    if pr.get('coverage_delta', 0) < 0:
        score += 25
    if pr.get('hallucination_flag', False):
        score += 50
    return score

def rank_prs(prs):
    for pr in prs:
        pr['risk_score'] = score_pr(pr)
    return sorted(prs, key=lambda x: x['risk_score'], reverse=True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: pr-risk-scorer.py <prs.json>")
        sys.exit(1)
    try:
        with open(sys.argv[1]) as f:
            prs = json.load(f)
        ranked = rank_prs(prs)
        for pr in ranked:
            print(f"  [{pr['risk_score']:3d}] #{pr.get('number', '?')} {pr.get('title', '?')}")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
