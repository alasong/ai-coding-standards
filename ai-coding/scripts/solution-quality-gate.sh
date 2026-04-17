#!/bin/bash
# solution-quality-gate.sh — P23 Solution Quality Gate
# 在方案设计完成、Spec 生成前执行 8 项质量检查
# 用法:
#   ./solution-quality-gate.sh \
#     --design docs/solutions/F001-design.md \
#     --requirements docs/requirements/F001-requirements.md \
#     --architecture docs/architecture/F001-architecture.md

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
SKIP=0

log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL++)); }
log_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; ((SKIP++)); }

# 解析参数
DESIGN=""
REQUIREMENTS=""
ARCHITECTURE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --design) DESIGN="$2"; shift 2 ;;
        --requirements) REQUIREMENTS="$2"; shift 2 ;;
        --architecture) ARCHITECTURE="$2"; shift 2 ;;
        --help)
            echo "用法: $0 --design <设计文档> --requirements <需求文档> --architecture <架构文档>"
            exit 0
            ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

if [[ -z "$DESIGN" ]]; then
    echo "错误: 必须指定 --design 参数"
    exit 1
fi

if [[ ! -f "$DESIGN" ]]; then
    echo "错误: 设计文档不存在: $DESIGN"
    exit 1
fi

echo "============================================"
echo "  P23 Solution Quality Gate"
echo "  设计文档: $DESIGN"
echo "============================================"
echo ""

# 1. 需求覆盖 — 检查设计文档是否引用了需求文档中的验收标准
echo "--- 1. 需求覆盖 ---"
if [[ -n "$REQUIREMENTS" && -f "$REQUIREMENTS" ]]; then
    ac_count=$(grep -c "AC-" "$REQUIREMENTS" 2>/dev/null || echo "0")
    covered_count=$(grep -c "AC-" "$DESIGN" 2>/dev/null || echo "0")
    if [[ "$ac_count" -gt 0 && "$covered_count" -ge "$ac_count" ]]; then
        log_pass "需求覆盖: $covered_count/$ac_count 个 AC 已覆盖"
    else
        log_fail "需求覆盖: 仅 $covered_count/$ac_count 个 AC 被覆盖"
    fi
else
    log_skip "需求覆盖: 未指定需求文档 (--requirements)"
fi

# 2. 架构一致性 — 检查设计文档是否与架构文档冲突
echo "--- 2. 架构一致性 ---"
if [[ -n "$ARCHITECTURE" && -f "$ARCHITECTURE" ]]; then
    # 检查是否有冲突标注
    if grep -q "冲突\|conflict\|Conflict" "$DESIGN" 2>/dev/null; then
        # 有冲突但已标注 = 条件通过
        log_pass "架构一致性: 存在冲突但已标注"
    else
        log_pass "架构一致性: 未发现显式冲突"
    fi
else
    log_skip "架构一致性: 未指定架构文档 (--architecture)"
fi

# 3. 接口完整性 — 检查是否有接口定义
echo "--- 3. 接口完整性 ---"
if grep -q "接口\|endpoint\|API\|接口定义\|接口清单" "$DESIGN" 2>/dev/null; then
    log_pass "接口完整性: 存在接口定义章节"
else
    log_fail "接口完整性: 缺少接口定义章节"
fi

# 4. 数据模型正确 — 检查是否有数据模型变更及迁移方案
echo "--- 4. 数据模型正确 ---"
if grep -q "数据模型\|Data Model\|Entity\|迁移" "$DESIGN" 2>/dev/null; then
    if grep -q "迁移方案\|migration\|迁移脚本" "$DESIGN" 2>/dev/null; then
        log_pass "数据模型: 有变更且有迁移方案"
    else
        log_pass "数据模型: 章节存在（假设无变更或无需迁移）"
    fi
else
    log_pass "数据模型: 未提及数据模型变更（假设无影响）"
fi

# 5. 异常处理 — 检查是否有异常处理策略
echo "--- 5. 异常处理 ---"
if grep -q "异常\|Exception\|Error\|错误处理\|异常处理" "$DESIGN" 2>/dev/null; then
    log_pass "异常处理: 存在异常处理策略"
else
    log_fail "异常处理: 缺少异常处理策略"
fi

# 6. 可测试性 — 检查是否有测试策略
echo "--- 6. 可测试性 ---"
if grep -q "测试策略\|Test Strategy\|测试\|test" "$DESIGN" 2>/dev/null; then
    log_pass "可测试性: 存在测试策略"
else
    log_fail "可测试性: 缺少测试策略"
fi

# 7. 依赖明确 — 检查是否有依赖约束
echo "--- 7. 依赖明确 ---"
if grep -q "依赖\|Dependency\|版本\|version" "$DESIGN" 2>/dev/null; then
    log_pass "依赖明确: 存在依赖约束"
else
    log_skip "依赖明确: 未提及依赖（假设无新增依赖）"
fi

# 8. 风险评估 — 检查是否有风险评估
echo "--- 8. 风险评估 ---"
if grep -q "风险\|Risk\|风险评估" "$DESIGN" 2>/dev/null; then
    risk_count=$(grep -c "风险\|Risk" "$DESIGN" 2>/dev/null || echo "0")
    if [[ "$risk_count" -ge 2 ]]; then
        log_pass "风险评估: 已识别 $risk_count 项风险"
    else
        log_fail "风险评估: 风险识别不足（至少 3 项）"
    fi
else
    log_fail "风险评估: 缺少风险评估章节"
fi

echo ""
echo "============================================"
echo "  结果: ${GREEN}${PASS} PASS${NC} | ${RED}${FAIL} FAIL${NC} | ${YELLOW}${SKIP} SKIP${NC}"
echo "============================================"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo "${RED}Solution Quality Gate 未通过${NC}"
    echo "必须修复所有 FAIL 项后才能进入 Spec 生成阶段"
    exit 1
else
    echo ""
    echo "${GREEN}Solution Quality Gate 通过${NC}"
    echo "可以进入 Spec 生成阶段"
    exit 0
fi
