"""
幻觉检测置信度评分系统。

评分方向：confidence 越高 = 检测结果越可信
- 对"无幻觉"结果的置信度：各项验证通过则分数高
- 对"有幻觉"结果的置信度：多项验证同时失败则分数高

输出：
- auto_pass:  高置信度无幻觉（80-100），自动放行
- auto_block: 高置信度确认幻觉（80-100），自动拦截
- human_review: 中置信度（50-79），人工确认
- human_review_required: 低置信度（0-49），必须人工审核
"""
import json, sys

# 各检测维度的权重（总和 100）
WEIGHTS = {
    'compiles':             25,
    'symbols_resolved':     25,
    'dependencies_verified': 20,
    'api_exists':           15,
    'semantic_consistent':  15,
}

def score_confidence(result):
    """
    计算对检测结果的置信度。

    输入 result 示例:
    {
      "hallucination": false,
      "compiles": true,
      "unresolved_symbols": 0,
      "dependencies_verified": true,
      "api_exists": true,
      "semantic_consistent": true
    }

    评分逻辑：
    - 每个验证维度通过则获得对应权重分
    - 未解析符号按数量扣分（每个扣 5 分，最多扣完该维度权重）
    - 最终分数 = 所有维度得分之和
    """
    score = 0

    # 编译检查
    if result.get('compiles', False):
        score += WEIGHTS['compiles']

    # 符号解析（0 个未解析 = 满分，每多一个扣 5 分）
    unresolved = result.get('unresolved_symbols', 0)
    symbol_score = max(0, WEIGHTS['symbols_resolved'] - unresolved * 5)
    score += symbol_score

    # 依赖验证
    if result.get('dependencies_verified', False):
        score += WEIGHTS['dependencies_verified']

    # API 存在性
    if result.get('api_exists', False):
        score += WEIGHTS['api_exists']

    # 语义一致性
    if result.get('semantic_consistent', False):
        score += WEIGHTS['semantic_consistent']

    return min(100, score)

def classify(results):
    for r in results:
        r['confidence'] = score_confidence(r)
        is_hallucination = r.get('hallucination', False)

        if r['confidence'] >= 80:
            r['action'] = 'auto_block' if is_hallucination else 'auto_pass'
        elif r['confidence'] >= 50:
            r['action'] = 'human_review'
        else:
            r['action'] = 'human_review_required'
    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: hallucination-confidence-scorer.py <results.json>")
        sys.exit(1)
    try:
        with open(sys.argv[1]) as f:
            results = json.load(f)
        if not isinstance(results, list):
            print("Error: input must be a JSON array of results", file=sys.stderr)
            sys.exit(1)
        classified = classify(results)
        for r in classified:
            print(f"  [{r['confidence']:3d}] hallucination={r.get('hallucination')} -> {r['action']}")
        print(json.dumps(classified, indent=2))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
