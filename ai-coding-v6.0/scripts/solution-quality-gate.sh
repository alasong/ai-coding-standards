#!/bin/bash
# solution-quality-gate.sh — Solution Quality Gate 检查脚本
# 用法：./solution-quality-gate.sh docs/solutions/{feature-id}-design.md

set -euo pipefail

DESIGN_FILE="${1:-}"
if [[ -z "$DESIGN_FILE" ]]; then
  echo "Usage: $0 <solution-design-file>"
  exit 1
fi

if [[ ! -f "$DESIGN_FILE" ]]; then
  echo "FAIL: Design file not found: $DESIGN_FILE"
  exit 1
fi

PASSED=0
FAILED=0

check() {
  local name="$1"
  local condition="$2"
  if eval "$condition"; then
    echo "PASS: $name"
    ((PASSED++))
  else
    echo "FAIL: $name"
    ((FAILED++))
  fi
}

# 1. 需求覆盖：设计文档包含验收标准引用
check "需求覆盖" "grep -qi 'AC-\\|验收标准\\|acceptance' '$DESIGN_FILE'"

# 2. 架构一致性：包含架构检查清单
check "架构一致性" "grep -qi '架构\\|ADR\\|architect' '$DESIGN_FILE'"

# 3. 接口完整性：包含接口定义
check "接口完整性" "grep -qi '接口\\|endpoint\\|API\\|输入.*输出' '$DESIGN_FILE'"

# 4. 数据模型：包含数据模型变更
check "数据模型正确" "grep -qi '数据模型\\|data.model\\|table\\|schema\\|迁移' '$DESIGN_FILE'"

# 5. 异常处理：包含异常处理策略
check "异常处理" "grep -qi '异常\\|error\\|exception\\|异常处理' '$DESIGN_FILE'"

# 6. 可测试性：包含测试策略
check "可测试性" "grep -qi '测试\\|test\\|测试策略' '$DESIGN_FILE'"

# 7. 依赖明确：包含依赖信息
check "依赖明确" "grep -qi '依赖\\|depend\\|版本' '$DESIGN_FILE'"

# 8. 风险评估：包含风险评估
check "风险评估" "grep -qi '风险\\|risk\\|缓解' '$DESIGN_FILE'"

echo ""
echo "=== Solution Quality Gate Result ==="
echo "Passed: $PASSED / 8"
echo "Failed: $FAILED / 8"

if [[ $FAILED -gt 0 ]]; then
  echo "GATE: FAILED — 请修复以上 $FAILED 项后再进入 Spec 生成阶段"
  exit 1
fi

echo "GATE: PASSED — 可进入 Spec 生成阶段"
exit 0
