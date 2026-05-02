#!/usr/bin/env python3
"""ipd-sm.py — IPD 可执行状态机（Phase A 最小可用版本）

定位：IPD 流程的进度追踪器 + 状态边界验证器
Phase A 范围：文件存在性检查 + DCP checklist 验证 + 基础测试状态检查
不做：独立 Agent 验证、实时操作拦截、深度评分

用法:
    python ipd-sm.py status          # 查看当前状态
    python ipd-sm.py verify          # 验证 exit conditions
    python ipd-sm.py next            # 转换到下一个状态
    python ipd-sm.py reset STATE     # 重置到指定状态
    python ipd-sm.py history         # 查看状态历史
    python ipd-sm.py init            # 初始化 .ipd/ 目录和初始文件
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 路径约定
# ---------------------------------------------------------------------------
# 脚本位于 ai-coding-v5.4/scripts/，项目根目录在脚本上方两级
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # 项目根目录
IPD_DIR = PROJECT_ROOT / ".ipd"
STATE_FILE = IPD_DIR / "state.json"
CONFIG_FILE = IPD_DIR / "state-machine.yaml"
BLOCKED_FILE = IPD_DIR / "blocked.json"
HISTORY_FILE = IPD_DIR / "state-history.json"

# ---------------------------------------------------------------------------
# 内嵌默认状态定义（当 state-machine.yaml 不存在时使用）
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "version": "1.0",
    "states": {
        "IDLE": {
            "description": "空闲 — 等待新需求输入",
            "permissions": {
                "allow": ["read"],
                "deny": ["write_docs", "write_code", "edit_tests"],
                "scope": [],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": ".ipd/requirements/input.md"},
            ],
            "next_states": ["PHASE_0_INSIGHT"],
        },
        "PHASE_0_INSIGHT": {
            "description": "市场洞察 — 五看三定 / BLM / 竞品分析",
            "permissions": {
                "allow": ["read", "write_docs"],
                "deny": ["write_code", "edit_tests"],
                "scope": ["ipd/phase-0/"],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": "ipd/phase-0/market-insight.md"},
                {"type": "dcp_checklist", "phase": 0},
            ],
            "next_states": ["PHASE_1_CONCEPT"],
        },
        "PHASE_1_CONCEPT": {
            "description": "概念定义 — Kano / QFD / JTBD / 核心竞争力画像",
            "permissions": {
                "allow": ["read", "write_docs"],
                "deny": ["write_code", "edit_tests"],
                "scope": ["ipd/phase-1/"],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": "ipd/phase-1/concept-definition.md"},
                {"type": "dcp_checklist", "phase": 1},
            ],
            "next_states": ["PHASE_2_PLAN"],
        },
        "PHASE_2_PLAN": {
            "description": "详细规划 — DFX / ATA / WBS / 风险矩阵",
            "permissions": {
                "allow": ["read", "write_docs"],
                "deny": ["write_code", "edit_tests"],
                "scope": ["ipd/phase-2/"],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": "ipd/phase-2/solution-design.md"},
                {"type": "dcp_checklist", "phase": 2},
            ],
            "next_states": ["PHASE_2.5_SPEC_GEN"],
        },
        "PHASE_2.5_SPEC_GEN": {
            "description": "Spec 生成 — 从方案设计生成 Feature Spec",
            "permissions": {
                "allow": ["read", "write_docs"],
                "deny": ["write_code", "edit_tests"],
                "scope": ["specs/"],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": "specs/", "min_files": 1, "pattern": r"^specs/F\d+-.*\.md$"},
                {"type": "spec_validated"},
            ],
            "next_states": ["PHASE_3_DISPATCH"],
        },
        "PHASE_3_DISPATCH": {
            "description": "开发分派 — 按 WBS 拆 Feature → Task 队列",
            "permissions": {
                "allow": ["read", "write_docs"],
                "deny": ["write_code"],
                "scope": ["ipd/phase-3/"],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": "ipd/phase-3/task-queue.json"},
            ],
            "next_states": ["TDD_RED"],
        },
        "TDD_RED": {
            "description": "TDD Red — 编写测试并确认首次失败",
            "permissions": {
                "allow": ["read", "edit_tests"],
                "deny": ["write_code"],
                "scope": ["tests/"],
            },
            "exit_conditions": [
                {"type": "test_fail"},
            ],
            "next_states": ["TDD_GREEN"],
        },
        "TDD_GREEN": {
            "description": "TDD Green — 编写实现使测试通过",
            "permissions": {
                "allow": ["read", "write_code"],
                "deny": ["edit_tests"],
                "scope": ["src/"],
            },
            "exit_conditions": [
                {"type": "test_pass"},
            ],
            "next_states": ["TDD_REFACTOR"],
        },
        "TDD_REFACTOR": {
            "description": "TDD Refactor — 重构代码，保持测试通过",
            "permissions": {
                "allow": ["read", "write_code"],
                "deny": ["edit_tests"],
                "scope": ["src/"],
            },
            "exit_conditions": [
                {"type": "test_pass"},
                {"type": "lint_pass"},
            ],
            "next_states": ["SPEC_ALIGN_CHECK"],
        },
        "SPEC_ALIGN_CHECK": {
            "description": "Spec-Test 对齐验证 — 对照者角色切换",
            "permissions": {
                "allow": ["read"],
                "deny": ["write_code", "edit_tests", "write_docs"],
                "scope": [],
            },
            "exit_conditions": [
                {"type": "spec_align_pass"},
            ],
            "next_states": ["TASK_GATE"],
        },
        "TASK_GATE": {
            "description": "任务 Gate — 幻觉检测 + 安全检查",
            "permissions": {
                "allow": ["read"],
                "deny": ["write_code", "edit_tests", "write_docs"],
                "scope": [],
            },
            "exit_conditions": [
                {"type": "gate_report_pass"},
            ],
            "next_states": ["NEXT_TASK_OR_PHASE_3_COMPLETE"],
        },
        "PHASE_3_COMPLETE": {
            "description": "全量验证",
            "permissions": {
                "allow": ["read"],
                "deny": ["write_code", "edit_tests", "write_docs"],
                "scope": [],
            },
            "exit_conditions": [
                {"type": "all_tests_pass"},
                {"type": "gate_report_exists", "path": ".gate/gate-report.md"},
            ],
            "next_states": ["PR_CREATE"],
        },
        "PR_CREATE": {
            "description": "创建 PR",
            "permissions": {
                "allow": ["read", "write_docs"],
                "deny": ["write_code", "edit_tests"],
                "scope": ["specs/", ".gate/"],
            },
            "exit_conditions": [
                {"type": "file_exists", "path": ".ipd/pr/", "min_files": 1},
            ],
            "next_states": ["IDLE"],
        },
    },
}

# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------
@dataclass
class ValidationResult:
    passed: bool
    description: str
    detail: Optional[str] = None


@dataclass
class StateMachine:
    config: dict
    state: dict

    # -- 加载 ----------------------------------------------------------------
    @classmethod
    def load(cls, project_root: Optional[Path] = None) -> "StateMachine":
        root = project_root or PROJECT_ROOT
        ipd_dir = root / ".ipd"
        state_file = ipd_dir / "state.json"
        config_file = ipd_dir / "state-machine.yaml"

        # 加载配置
        if config_file.exists():
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
            except ImportError:
                config = DEFAULT_CONFIG
        else:
            config = DEFAULT_CONFIG

        # 加载状态
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
        else:
            state = {
                "current_state": "IDLE",
                "state_history": [],
                "task_queue": [],
                "current_task_index": -1,
                "self_correction_count": 0,
                "blocked": None,
            }

        return cls(config=config, state=state)

    def save(self):
        IPD_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    # -- 核心操作 ------------------------------------------------------------
    def cmd_status(self):
        """输出当前状态和权限窗口"""
        current = self.state["current_state"]
        state_def = self.config["states"].get(current)
        if not state_def:
            print(f"[ERROR] 未知状态: {current}")
            return

        perms = state_def["permissions"]
        print(f"[STATE] {current}")
        print(f"[DESCRIPTION] {state_def['description']}")
        print(f"[ALLOW] {', '.join(perms['allow'])}")
        print(f"[DENY]  {', '.join(perms['deny'])}")
        print(f"[SCOPE] {', '.join(perms['scope']) if perms['scope'] else '(无限制)'}")

        # exit conditions 预览
        print(f"[EXIT CONDITIONS]")
        for cond in state_def.get("exit_conditions", []):
            result = self._check_condition(cond)
            icon = "✅" if result.passed else "❌"
            print(f"  {icon} {result.description}")
            if result.detail:
                print(f"     {result.detail}")

        # next states
        nexts = state_def.get("next_states", [])
        print(f"[NEXT] {', '.join(nexts)}")

        # blocked?
        if self.state.get("blocked"):
            print(f"[BLOCKED] 是 — 查看 .ipd/blocked.json")
        else:
            print(f"[BLOCKED] 无")

    def cmd_verify(self) -> bool:
        """验证当前状态的退出条件"""
        current = self.state["current_state"]
        state_def = self.config["states"].get(current)
        if not state_def:
            print(f"[ERROR] 未知状态: {current}")
            return False

        print(f"[VERIFY] {current}")
        all_passed = True
        for cond in state_def.get("exit_conditions", []):
            result = self._check_condition(cond)
            icon = "✅" if result.passed else "❌"
            print(f"  {icon} {result.description}")
            if result.detail:
                print(f"     {result.detail}")
            if not result.passed:
                all_passed = False

        print()
        if all_passed:
            nexts = state_def.get("next_states", [])
            print(f"[RESULT] PASS — 可以转换到: {', '.join(nexts)}")
        else:
            print(f"[RESULT] FAIL — 状态保持 {current}")
            print(f"[ACTION] 修复上述失败项后再尝试转换")
        return all_passed

    def cmd_next(self) -> bool:
        """验证并转换到下一个状态"""
        current = self.state["current_state"]
        state_def = self.config["states"].get(current)
        if not state_def:
            print(f"[ERROR] 未知状态: {current}")
            return False

        # 先验证
        all_passed = True
        for cond in state_def.get("exit_conditions", []):
            result = self._check_condition(cond)
            if not result.passed:
                all_passed = False
                print(f"  ❌ {result.description}: {result.detail}")

        if not all_passed:
            print(f"\n[RESULT] FAIL — 无法转换，先修复上述失败项")
            return False

        # 转换
        next_states = state_def.get("next_states", [])
        if not next_states:
            print(f"[RESULT] 状态 {current} 无下一状态")
            return False

        # 特殊处理: NEXT_TASK_OR_PHASE_3_COMPLETE
        if "NEXT_TASK_OR_PHASE_3_COMPLETE" in next_states:
            next_state = self._resolve_task_next()
        else:
            next_state = next_states[0]

        # 记录历史
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "state": current,
            "entered_at": self._find_entry_time(current),
            "exited_at": now,
            "exit_result": "PASS",
        }
        self.state["state_history"].append(entry)
        self.state["current_state"] = next_state
        self.save()

        print(f"[TRANSITION] {current} → {next_state}")
        print(f"[RESULT] 状态已转换")
        return True

    def cmd_reset(self, target_state: str):
        """重置到指定状态"""
        state_def = self.config["states"].get(target_state)
        if not state_def:
            print(f"[ERROR] 未知状态: {target_state}")
            print(f"可用状态: {', '.join(self.config['states'].keys())}")
            return

        now = datetime.now(timezone.utc).isoformat()
        old = self.state["current_state"]
        self.state["state_history"].append({
            "state": old,
            "exited_at": now,
            "exit_result": "MANUAL_RESET",
        })
        self.state["current_state"] = target_state
        self.state["blocked"] = None
        self.state["self_correction_count"] = 0
        self.save()
        print(f"[RESET] {old} → {target_state}")

    def cmd_history(self):
        """查看状态历史"""
        history = self.state.get("state_history", [])
        if not history:
            print("[HISTORY] 无历史记录")
            return

        print(f"[HISTORY] 当前状态: {self.state['current_state']}")
        print()
        for entry in history:
            state = entry.get("state", "?")
            entered = entry.get("entered_at", "?")[:19]
            exited = entry.get("exited_at", "?")[:19]
            result = entry.get("exit_result", "?")
            print(f"  {state:25s} {entered} → {exited}  [{result}]")

    def cmd_init(self):
        """初始化 .ipd/ 目录和初始文件"""
        # .ipd/ 存放状态文件
        IPD_DIR.mkdir(parents=True, exist_ok=True)
        (IPD_DIR / "requirements").mkdir(exist_ok=True)

        # ipd/ 存放 IPD 产出物（P2 规范约定）
        ipd_output = PROJECT_ROOT / "ipd"
        ipd_output.mkdir(exist_ok=True)
        (ipd_output / "phase-0").mkdir(exist_ok=True)
        (ipd_output / "phase-1").mkdir(exist_ok=True)
        (ipd_output / "phase-2").mkdir(exist_ok=True)
        (ipd_output / "phase-3").mkdir(exist_ok=True)

        # 写入 state.json（如果不存在）
        if not STATE_FILE.exists():
            self.save()
            print(f"[INIT] 已创建 {STATE_FILE}")
        else:
            print(f"[INIT] {STATE_FILE} 已存在")

        # 写入 .gitignore
        gitignore = PROJECT_ROOT / ".gitignore"
        ignore_entries = [".ipd/state.json", ".ipd/blocked.json"]
        if gitignore.exists():
            content = gitignore.read_text()
            missing = [e for e in ignore_entries if e not in content]
            if missing:
                with open(gitignore, "a") as f:
                    f.write("\n# IPD state machine\n")
                    for e in missing:
                        f.write(f"{e}\n")
                print(f"[INIT] 已更新 .gitignore")
        else:
            with open(gitignore, "w") as f:
                f.write("# IPD state machine\n")
                for e in ignore_entries:
                    f.write(f"{e}\n")
            print(f"[INIT] 已创建 .gitignore")

        # 写入 requirements/input.md 模板
        input_md = IPD_DIR / "requirements" / "input.md"
        if not input_md.exists():
            input_md.write_text("# 需求输入\n\n在此描述新功能需求...\n")
            print(f"[INIT] 已创建 {input_md}")

        print("[INIT] 完成")

    # -- 条件验证 ------------------------------------------------------------
    def _check_condition(self, cond: dict) -> ValidationResult:
        cond_type = cond.get("type", "")

        if cond_type == "file_exists":
            return self._check_file_exists(cond)
        elif cond_type == "dcp_checklist":
            return self._check_dcp_checklist(cond)
        elif cond_type == "spec_align_pass":
            return self._check_spec_align_pass(cond)
        elif cond_type == "spec_validated":
            return self._check_spec_validated(cond)
        elif cond_type == "test_fail":
            return self._check_test_fail(cond)
        elif cond_type == "test_pass":
            return self._check_test_pass(cond)
        elif cond_type == "lint_pass":
            return self._check_lint_pass(cond)
        elif cond_type == "gate_report_pass":
            return self._check_gate_report_pass(cond)
        elif cond_type == "all_tests_pass":
            return self._check_all_tests_pass(cond)
        elif cond_type == "gate_report_exists":
            return self._check_gate_report_exists(cond)
        else:
            return ValidationResult(
                passed=False,
                description=f"unknown condition type: {cond_type}",
                detail="请检查 state-machine.yaml 配置",
            )

    def _check_file_exists(self, cond: dict) -> ValidationResult:
        path = cond["path"]
        full_path = PROJECT_ROOT / path

        # 目录检查（带 min_files / pattern）
        if full_path.is_dir():
            min_files = cond.get("min_files", 0)
            pattern = cond.get("pattern")
            files = list(full_path.iterdir())
            if pattern:
                files = [f for f in files if re.match(pattern, str(f.relative_to(PROJECT_ROOT)))]
            count = len([f for f in files if f.is_file()])
            if count >= min_files:
                return ValidationResult(
                    passed=True,
                    description=f"file_exists: {path} ({count} 个文件)",
                )
            else:
                return ValidationResult(
                    passed=False,
                    description=f"file_exists: {path} (需要 ≥{min_files} 个文件，当前 {count})",
                    detail="文件数量不足",
                )

        if full_path.exists():
            return ValidationResult(passed=True, description=f"file_exists: {path}")
        return ValidationResult(
            passed=False,
            description=f"file_exists: {path}",
            detail=f"文件不存在: {full_path}",
        )

    def _check_dcp_checklist(self, cond: dict) -> ValidationResult:
        phase = cond["phase"]
        checklist_path = PROJECT_ROOT / f"ipd/phase-{phase}/dcp-checklist.md"
        if not checklist_path.exists():
            return ValidationResult(
                passed=False,
                description=f"dcp_checklist: phase-{phase}",
                detail=f"文件不存在: {checklist_path}",
            )

        content = checklist_path.read_text()
        # 检查是否包含 FAIL 标记
        if "FAIL" in content and "PASS" not in content:
            return ValidationResult(
                passed=False,
                description=f"dcp_checklist: phase-{phase}",
                detail="DCP checklist 包含 FAIL 项",
            )
        if "PASS" in content:
            return ValidationResult(
                passed=True,
                description=f"dcp_checklist: phase-{phase} (已记录)",
            )
        # 文件存在但没有 PASS/FAIL 标记 — 视为空模板
        return ValidationResult(
            passed=False,
            description=f"dcp_checklist: phase-{phase}",
            detail="文件存在但未记录检查结果",
        )

    def _check_spec_validated(self, cond: dict) -> ValidationResult:
        """检查 specs/ 目录下是否有状态为 validated 或 ready 的 Spec"""
        specs_dir = PROJECT_ROOT / "specs"
        if not specs_dir.exists():
            return ValidationResult(
                passed=False,
                description="spec_validated",
                detail="specs/ 目录不存在",
            )

        for f in specs_dir.iterdir():
            if f.name.startswith("F") and f.suffix == ".md":
                content = f.read_text()
                if "status:" in content and any(
                    s in content for s in ["validated", "ready", "in-progress"]
                ):
                    return ValidationResult(
                        passed=True,
                        description=f"spec_validated: {f.name}",
                    )

        return ValidationResult(
            passed=False,
            description="spec_validated",
            detail="未找到状态为 validated/ready/in-progress 的 Spec 文件",
        )

    def _check_spec_align_pass(self, cond: dict) -> ValidationResult:
        """检查 Spec-Test 对齐报告是否存在且通过"""
        gate_dir = PROJECT_ROOT / ".gate"
        if not gate_dir.exists():
            return ValidationResult(
                passed=False,
                description="spec_align_pass",
                detail=".gate/ 目录不存在",
            )

        for f in gate_dir.iterdir():
            if f.name.startswith("spec-align") and f.suffix == ".json":
                try:
                    data = json.loads(f.read_text())
                    if data.get("status") == "pass":
                        return ValidationResult(
                            passed=True,
                            description=f"spec_align_pass: {f.name}",
                        )
                    else:
                        return ValidationResult(
                            passed=False,
                            description=f"spec_align_pass: {f.name}",
                            detail=f"报告状态: {data.get('status', 'unknown')}",
                        )
                except json.JSONDecodeError:
                    return ValidationResult(
                        passed=False,
                        description=f"spec_align_pass: {f.name}",
                        detail="JSON 格式错误",
                    )

        return ValidationResult(
            passed=False,
            description="spec_align_pass",
            detail="未找到 .gate/spec-align-*.json 报告",
        )

    def _check_test_fail(self, cond: dict) -> ValidationResult:
        """检查测试是否存在且首次运行失败 (Red 阶段)"""
        return self._run_tests_and_check(
            expect_fail=True,
            description="test_fail (Red 阶段)",
        )

    def _check_test_pass(self, cond: dict) -> ValidationResult:
        """检查测试是否通过 (Green/Refactor 阶段)"""
        return self._run_tests_and_check(
            expect_fail=False,
            description="test_pass",
        )

    def _run_tests_and_check(self, expect_fail: bool, description: str) -> ValidationResult:
        """通用测试检查"""
        import subprocess

        # 尝试多种测试命令
        test_commands = [
            ["pytest", "-x", "--tb=short", "-q"],
            ["go", "test", "./..."],
            ["npm", "test", "--", "--run"],
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd, cwd=PROJECT_ROOT,
                    capture_output=True, text=True, timeout=60,
                )
                failed = result.returncode != 0
                if failed == expect_fail:
                    status = "失败" if failed else "通过"
                    return ValidationResult(
                        passed=True,
                        description=f"{description} (测试{status})",
                    )
                else:
                    expected = "失败" if expect_fail else "通过"
                    actual = "失败" if failed else "通过"
                    return ValidationResult(
                        passed=False,
                        description=f"{description} (预期{expected}，实际{actual})",
                        detail=result.stdout or result.stderr or "",
                    )
            except FileNotFoundError:
                continue  # 该工具不存在，尝试下一个
            except subprocess.TimeoutExpired:
                return ValidationResult(
                    passed=False,
                    description=f"{description}",
                    detail="测试超时 (>60s)",
                )

        return ValidationResult(
            passed=False,
            description=f"{description}",
            detail="未找到可用的测试工具 (pytest/go test/npm test)",
        )

    def _check_lint_pass(self, cond: dict) -> ValidationResult:
        import subprocess

        lint_commands = [
            ["ruff", "check", "."],
            ["flake8", "."],
            ["golangci-lint", "run"],
            ["eslint", "."],
        ]

        for cmd in lint_commands:
            try:
                result = subprocess.run(
                    cmd, cwd=PROJECT_ROOT,
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode == 0:
                    return ValidationResult(
                        passed=True,
                        description="lint_pass",
                    )
                return ValidationResult(
                    passed=False,
                    description="lint_pass",
                    detail=result.stdout or result.stderr or "",
                )
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                return ValidationResult(
                    passed=False,
                    description="lint_pass",
                    detail="lint 超时 (>60s)",
                )

        return ValidationResult(
            passed=False,
            description="lint_pass",
            detail="未找到可用的 lint 工具",
        )

    def _check_gate_report_pass(self, cond: dict) -> ValidationResult:
        """检查 .gate/ 下是否有 PASS 的 Gate 报告"""
        gate_dir = PROJECT_ROOT / ".gate"
        if not gate_dir.exists():
            return ValidationResult(
                passed=False,
                description="gate_report_pass",
                detail=".gate/ 目录不存在",
            )

        for f in gate_dir.iterdir():
            if f.is_file() and "gate-report" in f.name.lower() and f.suffix in (".md", ".json"):
                content = f.read_text().lower()
                if "pass" in content:
                    return ValidationResult(
                        passed=True,
                        description=f"gate_report_pass: {f.name}",
                    )

        return ValidationResult(
            passed=False,
            description="gate_report_pass",
            detail="未找到包含 PASS 的 Gate 报告",
        )

    def _check_all_tests_pass(self, cond: dict) -> ValidationResult:
        """运行全量测试"""
        return self._run_tests_and_check(
            expect_fail=False,
            description="all_tests_pass",
        )

    def _check_gate_report_exists(self, cond: dict) -> ValidationResult:
        path = cond.get("path", ".gate/gate-report.md")
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            return ValidationResult(passed=True, description=f"gate_report_exists: {path}")
        return ValidationResult(
            passed=False,
            description=f"gate_report_exists: {path}",
            detail="文件不存在",
        )

    # -- 辅助 ----------------------------------------------------------------
    def _resolve_task_next(self) -> str:
        """处理 NEXT_TASK_OR_PHASE_3_COMPLETE 特殊逻辑"""
        task_queue = self.state.get("task_queue", [])
        current_idx = self.state.get("current_task_index", -1)
        next_idx = current_idx + 1

        if next_idx >= len(task_queue):
            return "PHASE_3_COMPLETE"
        else:
            # 下一个 task 回到 TDD_RED
            self.state["current_task_index"] = next_idx
            self.save()
            return "TDD_RED"

    def _find_entry_time(self, state_name: str) -> str:
        history = self.state.get("state_history", [])
        for entry in reversed(history):
            if entry.get("state") == state_name:
                return entry.get("entered_at", "?")
        return "?"


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("用法: python ipd-sm.py <command> [args]")
        print()
        print("命令:")
        print("  status          查看当前状态")
        print("  verify          验证 exit conditions")
        print("  next            转换到下一个状态")
        print("  reset STATE     重置到指定状态")
        print("  history         查看状态历史")
        print("  init            初始化 .ipd/ 目录")
        sys.exit(1)

    cmd = sys.argv[1]
    sm = StateMachine.load()

    if cmd == "status":
        sm.cmd_status()
    elif cmd == "verify":
        ok = sm.cmd_verify()
        sys.exit(0 if ok else 1)
    elif cmd == "next":
        ok = sm.cmd_next()
        sys.exit(0 if ok else 1)
    elif cmd == "reset":
        if len(sys.argv) < 3:
            print("用法: python ipd-sm.py reset <STATE>")
            sys.exit(1)
        sm.cmd_reset(sys.argv[2])
    elif cmd == "history":
        sm.cmd_history()
    elif cmd == "init":
        sm.cmd_init()
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
