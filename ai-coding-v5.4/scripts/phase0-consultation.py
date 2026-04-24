#!/usr/bin/env python3
"""
Phase 0 会诊模式 — 直接 LLM API 实现
每个角色 = 独立 system prompt + 独立输入文件 + 独立输出文件
Gate Checker = 读取所有角色输出后独立验证
"""

import os, sys, json, time, subprocess, concurrent.futures
from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHASE0_DIR = os.path.join(PROJECT_ROOT, "ipd", "phase-0")
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

def gather_context_files(file_paths):
    """Read multiple files, truncate if too long, return as context string"""
    parts = []
    for path in file_paths:
        if os.path.exists(path):
            content = read_file(path)
            if len(content) > 12000:
                content = content[:12000] + "\n...[truncated]"
            parts.append(f"## {os.path.basename(path)}\n{content}")
    return "\n\n".join(parts)

# ==================== Agent Definitions ====================

def researcher_agent():
    system = read_file(os.path.join(NORM_DIR, "researcher-rules.md"))
    context_files = [
        os.path.join(PHASE0_DIR, "02-voice-of-customer.md"),
        os.path.join(PHASE0_DIR, "03-tech-radar.md"),
        os.path.join(PHASE0_DIR, "competitor-scope-declaration.md"),
        os.path.join(PHASE0_DIR, "06-competitor-mechanism-deepdive.md"),
    ]
    context = gather_context_files(context_files)
    user = f"""你是 IPD Phase 0 的 Researcher Agent（主笔角色）。
关注"五看"：看行业、看市场、看客户、看竞争、看自己。

## 已有上下文（来自补充文档）
{context}

## 任务
完成五看三定分析，输出 ipd/phase-0/researcher-output.md

## 格式要求
- 每个声明标注 [证据1] [证据2]
- 竞品范围必须 ≥3 维度，每个维度 ≥1 代表，至少 1 个非直接竞品
- 末尾给出 Go/No-Go 初步建议（非最终判定）

## 输出
将完整分析写入 ipd/phase-0/researcher-output.md"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE0_DIR, "researcher-output.md"), result)
    return "researcher", len(result)

def explorer_agent():
    system = read_file(os.path.join(NORM_DIR, "explorer-rules.md"))
    user = """你是 IPD Phase 0 的 Explorer Agent，关注"看自己"维度。
你只关注代码基线的客观事实。

## 当前代码基线（已采集数据）
- Go 文件: 196 个 (生产+测试), 测试文件: 86 个
- 总行数: 50,756 行
- 内部包: 18 个
- 数据库迁移: 28 次 (001-028)
- Feature Specs: 15 个 (F001-F015)
- 测试: 全部 18 包 PASS (race + short)
- 覆盖率高包: builder(95%), matcher(92%), quality(99%), model(94%), tools(95%)
- 覆盖率中包: graph(82%), governance(79%), validator(86%), engine(60%), middleware(63%), config(100%), database(53%), repository(52%), compiler(54%)
- 覆盖率低包: mcp(34%), registry(22%), api(20%)
- 总覆盖率: ~49% (低于 80% 目标)
- 安全: 无硬编码密钥, bearer token auth 已配置
- Tenant ID "default" 硬编码在 internal/api/auth_handler.go:81
- 架构: cmd → api → compiler → engine → model → repository
- 并发安全: mutex, context cancellation, circuit breaker 已实现
- 最近工作: Skill 自泛化、语义匹配、MCP 集成、治理管线、Web UI i18n

## 任务
分析以上代码基线数据，输出 ipd/phase-0/explorer-output.md

## 格式要求
- 每个发现必须有可验证证据
- 不得做市场/竞品/需求分析，只陈述客观事实
- 包含：代码统计、测试覆盖率、架构强弱项、安全扫描、代码健康、能力自评与缺口"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE0_DIR, "explorer-output.md"), result)
    return "explorer", len(result)

def analyst_agent():
    system = read_file(os.path.join(NORM_DIR, "analyst-rules.md"))
    context_files = [
        os.path.join(PHASE0_DIR, "02-voice-of-customer.md"),
        os.path.join(PHASE0_DIR, "07-boundary-scenarios.md"),
    ]
    context = gather_context_files(context_files)
    user = f"""你是 IPD Phase 0 的 Analyst Agent（需求视角）。
关注：伪需求检测、VOC 需求翻译、需求优先级排序。

## 输入（VOC + 边界场景）
{context}

## 任务
从客户需求角度独立验证 Phase 0 市场洞察的结论，输出 ipd/phase-0/analyst-output.md

## 你必须做
1. 验证 VOC 数据源的可信度和偏差
2. 检查是否排除了伪需求
3. 验证需求优先级排序（Top 10）是否合理
4. 边界场景是否覆盖核心用户路径
5. 输出独立验证报告，给出 PASS/FAIL 建议"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE0_DIR, "analyst-output.md"), result)
    return "analyst", len(result)

def gate_checker_agent():
    system = read_file(os.path.join(NORM_DIR, "gate-checker-rules.md"))
    # Gate Checker reads ALL upstream outputs
    context_files = [
        os.path.join(PHASE0_DIR, "01-market-insight.md"),
        os.path.join(PHASE0_DIR, "researcher-output.md"),
        os.path.join(PHASE0_DIR, "explorer-output.md"),
        os.path.join(PHASE0_DIR, "analyst-output.md"),
        os.path.join(PHASE0_DIR, "04-blm-analysis.md"),
        os.path.join(PHASE0_DIR, "05-strategic-targets.md"),
        os.path.join(PHASE0_DIR, "competitor-scope-declaration.md"),
    ]
    context = gather_context_files(context_files)
    user = f"""你是 IPD Phase 0 的 Gate Checker Agent（只读，独立裁定角色）。
你只关注"以上所有 Agent 的结论可信吗？证据链完整吗？"

## 上游产出
{context}

## 任务
1. 验证 DCP 检查清单的 14 项 — 每项独立给出 PASS/FAIL + 证据
2. 独立深度评分 — 四维度 0-3 分（**禁止引用上游任何 Agent 的自评分，必须从零开始自己评**）
3. 检查证据链完整性
4. 输出: ipd/phase-0/gate-report.md

## DCP 检查项
1. 五看验证 — 看行业  2. 看市场  3. 看客户  4. 看竞争  5. 看自己
6. 排除了伪需求  7. 明确差异化定位
8. 竞品范围 ≥3 维度  9. ≥1 非直接竞品
10. 技术趋势雷达  11. BLM 模型  12. 量化目标（三定）
13. 深度评分 ≥60%  14. P11 证据链完整

## 深度评分四维
①竞品机制拆解  ②用户边界场景  ③差异化批判  ④自身盲区识别

## 强制独立评分规则
- **禁止**引用 researcher-output.md / explorer-output.md / analyst-output.md 中任何自评分
- **禁止**引用 depth-score-P0.json 中的分数
- 必须逐维阅读原始文档内容，自己判断给分
- 你的评分可能与上游不同，以你的独立判断为准
- 检查 scored_by 必须为 "independent gate-checker"
- 检查 anomaly: 全3分→[DEPTH-SUSPECT], 全2分→[DEPTH-ROBOTIC], 评分与缺陷不一致→[DEPTH-INVALID]

## 格式
每项 PASS/FAIL + 独立证据引用。深度评分给出四维度分数+总分+anomaly_check。末尾给出最终裁定: PASS / FAIL / FAIL-WITH-FINDINGS"""
    result = call_llm(system, user)
    write_file(os.path.join(PHASE0_DIR, "gate-report.md"), result)
    return "gate-checker", len(result)

# ==================== Execution ====================

def main():
    print("=" * 60)
    print("Phase 0 会诊模式 — 直接 LLM API")
    print("=" * 60)

    # Stage 1: 3 agents 并行 (independent contexts)
    print("\n[Stage 1] 三角色并行会诊...")
    agents = [
        ("Researcher", researcher_agent),
        ("Explorer", explorer_agent),
        ("Analyst", analyst_agent),
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
    print("Phase 0 会诊完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
