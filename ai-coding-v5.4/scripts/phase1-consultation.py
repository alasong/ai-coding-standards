#!/usr/bin/env python3
"""
Phase 1 会诊模式 — 直接 LLM API 实现
每个角色 = 独立 system prompt + 独立输入文件 + 独立输出文件
Gate Checker = 读取所有角色输出后独立验证
"""

import os, sys, json, time, subprocess, concurrent.futures
from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHASE0_DIR = os.path.join(PROJECT_ROOT, "ipd", "phase-0")
PHASE1_DIR = os.path.join(PROJECT_ROOT, "ipd", "phase-1")
NORM_DIR = os.path.join(PROJECT_ROOT, "ai-coding-v5.4", ".normalized")

API_KEY = os.environ["SILICONFLOW_API_KEY"]
API_BASE = "https://api.siliconflow.cn/v1"
MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"

def call_llm(system_prompt, user_prompt, max_tokens=8192, temperature=0.3):
    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def gather_context_files(file_paths, max_chars=6000):
    """Read multiple files, smart truncate if too long, return as context string.
    Smart truncate: keep head (4000) + tail (2000) to avoid losing appended supplements."""
    parts = []
    for path in file_paths:
        if os.path.exists(path):
            content = read_file(path)
            if len(content) > max_chars:
                head = content[:4000]
                tail = content[-2000:]
                content = head + f"\n...[truncated {len(content)-6000} chars]...\n" + tail
            parts.append(f"## {os.path.basename(path)}\n{content}")
    return "\n\n".join(parts)

# ==================== Agent Definitions ====================

def analyst_agent():
    system = read_file(os.path.join(NORM_DIR, "analyst-rules.md"))
    context_files = [
        os.path.join(PHASE0_DIR, "01-market-insight.md"),
        os.path.join(PHASE0_DIR, "02-voice-of-customer.md"),
        os.path.join(PHASE0_DIR, "analyst-output.md"),
    ]
    context = gather_context_files(context_files)
    user = f"""你是 IPD Phase 1 的 Analyst Agent（需求视角）。
关注：Kano 模型评估（基本/期望/兴奋型需求）、Better/Worse 系数计算、伪需求排除。

## Phase 0 输入（市场洞察 + VOC + Analyst 验证）
{context}

## 任务
完成 Kano 评估，输出 ipd/phase-1/analyst-output.md

## 你必须做
1. 从 VOC 需求中提取并分类到 Kano 三类型（基本型/期望型/兴奋型）
2. 计算每项需求的 Better/Worse 系数
3. 检查是否有伪需求需要排除
4. 给出需求优先级排序建议
5. 输出完整的 Kano 评估报告"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE1_DIR, "analyst-output.md"), result)
    return "analyst", len(result)

def architect_agent():
    system = read_file(os.path.join(NORM_DIR, "architect-rules.md"))
    context_files = [
        os.path.join(PHASE0_DIR, "01-market-insight.md"),
        os.path.join(PHASE0_DIR, "competitor-scope-declaration.md"),
        os.path.join(PHASE0_DIR, "06-competitor-mechanism-deepdive.md"),
    ]
    context = gather_context_files(context_files)
    user = f"""你是 IPD Phase 1 的 Architect Agent（技术视角）。
关注：QFD 质量屋（客户需求→技术参数映射）、JTBD（用户场景分析）、技术方案可行性。

## Phase 0 输入（市场洞察 + 竞品分析）
{context}

## 任务
完成 QFD 质量屋矩阵 + JTBD 分析，输出 ipd/phase-1/architect-output.md

## 你必须做
1. 识别客户需求（WHAT）—— 从 VOC 中提取 10-15 项
2. 识别技术规格（HOW）—— 对应客户需求的技术实现指标 10-12 项
3. 构建关系矩阵（强/中/弱 = 9/3/1）
4. 构建屋顶矩阵（技术规格之间的正/负相关）
5. 进行竞争评估（竞品在技术规格上的表现）
6. 计算目标值和优先级
7. 定义 JTBD（Jobs To Be Done）—— 6-8 个核心用户场景
8. 输出完整的 QFD 质量屋 + JTBD 分析报告"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE1_DIR, "architect-output.md"), result)
    return "architect", len(result)

def researcher_agent():
    system = read_file(os.path.join(NORM_DIR, "researcher-rules.md"))
    context_files = [
        os.path.join(PHASE0_DIR, "01-market-insight.md"),
        os.path.join(PHASE0_DIR, "04-blm-analysis.md"),
        os.path.join(PHASE0_DIR, "05-strategic-targets.md"),
    ]
    context = gather_context_files(context_files)
    user = f"""你是 IPD Phase 1 的 Researcher Agent（主笔角色）。
关注：$APPEALS 8 维度竞争力评估、价值曲线/战略画布、概念定义。

## Phase 0 输入（市场洞察 + BLM + 战略目标）
{context}

## 任务
完成 $APPEALS 评估 + 价值曲线，输出 ipd/phase-1/researcher-output.md

## $APPEALS 8 维度
1. **Price**（价格/成本）
2. **Openness**（开放性）
3. **Performance**（性能）
4. **Packaging**（包装/易用性）
5. **Ease of Use**（使用便利性）
6. **Assurances**（保障/可靠性）
7. **Life Cycle**（生命周期/可扩展性）
8. **Social Acceptance**（社会接受度/生态）

## 你必须做
1. 对 SkillMesh 和 4 个竞品（LangGraph, Dify, Temporal, SkillClaw）进行 8 维度评分（1-5 分）
2. 识别差距和优先级
3. 绘制价值曲线（6 竞品 × 8 维度量化评分）
4. 给出战略建议（哪些维度要领先、哪些要跟随、哪些可以放弃）
5. 输出完整的 $APPEALS + 价值曲线分析报告"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE1_DIR, "researcher-output.md"), result)
    return "researcher", len(result)

def gate_checker_agent():
    system = read_file(os.path.join(NORM_DIR, "gate-checker-rules.md"))
    # Gate Checker reads ALL upstream outputs
    # Read only the 3 Stage 1 outputs (no old phase-1 docs to stay under token limit)
    stage1_files = [
        os.path.join(PHASE1_DIR, "analyst-output.md"),
        os.path.join(PHASE1_DIR, "architect-output.md"),
        os.path.join(PHASE1_DIR, "architect-output-supplement.md"),
        os.path.join(PHASE1_DIR, "researcher-output.md"),
        os.path.join(PHASE1_DIR, "core-competency.md"),
    ]
    context = gather_context_files(stage1_files)
    phase0_summary = """Phase 0 核心结论（摘要）:
- TAM $50B, SAM $630M-$850M, CAGR 40-55%
- 88% 企业无 AI 治理框架, 68% 写胶水代码
- 差异化: NLP→DAG 编译 + 混合执行 + 治理管线 + 技能自学习
- 6 项独占优势, 技术风险: API/MCP 覆盖率低、无分布式追踪
- DCP PASS, 深度评分 8/12"""
    context = phase0_summary + "\n\n---\n\n" + context
    user = f"""你是 IPD Phase 1 的 Gate Checker Agent（只读，独立裁定角色）。
你只关注"以上所有 Agent 的结论可信吗？证据链完整吗？"

## 上游产出
{context}

## 任务
1. 验证 DCP 检查清单的 13 项 — 每项独立给出 PASS/FAIL + 证据
2. 独立深度评分 — 四维度 0-3 分（**禁止引用上游任何 Agent 的自评分，必须从零开始自己评**）
3. 检查证据链完整性
4. 输出: ipd/phase-1/gate-report.md

## DCP 检查项（Phase 1 PDCP）
1. 需求分类覆盖 Kano 基本型  2. 覆盖 Kano 期望型  3. 覆盖 Kano 兴奋型
4. Kano Better/Worse 系数完整
5. QFD 质量屋矩阵完整（WHAT × HOW × 关系 × 屋顶 × 竞争评估 × 目标值）
6. JTBD 覆盖核心用户场景（≥6 个）
7. $APPEALS 8 维度评估完成（≥4 竞品评分）
8. 产品需求规格完整（MVP + NFR + 边界条件）
9. MVP 范围明确（基于 Kano + QFD 优先级）
10. 验收标准可测量（技术规格有目标值和验收方式）
11. 价值曲线/战略画布完整（量化评分 + 战略建议）
12. 核心竞争力综合识别完成（三层画像 + 竞品追赶预警 + 防守优先级）
13. P11 证据链完整（每个声明 ≥2 条可验证证据）

## 深度评分四维
①需求反例定义  ②潜在变量识别  ③场景覆盖度  ④伪需求排除

## 强制独立评分规则
- **禁止**引用 analyst-output.md / architect-output.md / researcher-output.md 中任何自评分
- **禁止**引用已有 depth-score 文件中的分数
- 必须逐维阅读原始文档内容，自己判断给分
- 你的评分可能与上游不同，以你的独立判断为准
- 检查 scored_by 必须为 "independent gate-checker"
- 检查 anomaly: 全3分→[DEPTH-SUSPECT], 全2分→[DEPTH-ROBOTIC], 评分与缺陷不一致→[DEPTH-INVALID]

## 格式
每项 PASS/FAIL + 独立证据引用。深度评分给出四维度分数+总分+anomaly_check。末尾给出最终裁定: PASS / FAIL / FAIL-WITH-FINDINGS"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE1_DIR, "gate-report.md"), result)
    return "gate-checker", len(result)

# ==================== Execution ====================

def main():
    print("=" * 60)
    print("Phase 1 会诊模式 — 直接 LLM API")
    print("=" * 60)

    # Stage 1: 3 agents 并行 (independent contexts)
    print("\n[Stage 1] 三角色并行会诊...")
    agents = [
        ("Analyst", analyst_agent),
        ("Architect", architect_agent),
        ("Researcher", researcher_agent),
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fn): name for name, fn in agents}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                print(f"  ✅ {result[0]}: {result[1]} chars")
            except Exception as e:
                print(f"  ❌ {name}: {e}")

    # Stage 2: Gate Checker (reads all upstream outputs)
    print("\n[Stage 2] Gate Checker 独立验证...")
    try:
        result = gate_checker_agent()
        print(f"  ✅ {result[0]}: {result[1]} chars")
    except Exception as e:
        print(f"  ❌ gate-checker: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Phase 1 会诊完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
