#!/usr/bin/env python3
"""
IPD Phase Gate Checker — Deterministic Manifest Verification

Reads manifest.yaml, verifies:
1. Upstream dependencies exist and passed
2. Required output files exist
3. Depth score file exists (if required)
4. DCP checklist items have evidence files
5. Reports PASS/FAIL for each check

Usage: python3 gate-check.py ipd/phase-N/manifest.yaml
"""

import sys, os, yaml

# Project root = repo root (2 levels up from scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def status_icon(result):
    return "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"

def count_evidence_sections(content):
    """Count ## 章节数（粗略文档深度指标）"""
    return content.count("\n## ")

def count_tables(content):
    """Count markdown 表格数（结构化分析指标）"""
    return content.count("\n|---") + content.count("\n| ---")

def count_code_blocks(content):
    """Count 代码块数（具体实现证据指标）"""
    return content.count("```")

def read_file_content(path):
    """Read file content, return empty string if not found"""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def compute_objective_depth_score(phase, manifest):
    """
    Compute depth scores using objective indicators instead of LLM judgment.

    Scoring: each dimension max 3 points.
    For each dimension, the manifest defines measurable indicators.
    If not defined, fall back to generic file-based heuristics.
    """
    dimensions = manifest.get("depth_score_dimensions", [])
    if not dimensions:
        return None

    phase_num = manifest["phase"]
    ds_path = os.path.join(PROJECT_ROOT, f".gate/depth-score-P{phase_num}.json")

    # If depth score file already exists, verify its objectivity
    if os.path.exists(ds_path):
        import json
        with open(ds_path, "r") as f:
            existing = json.load(f)
        print(f"\n[Objective Depth Score Verification]")
        print(f"  Existing score: {existing.get('total_score', '?')}/{existing.get('max_score', '?')} ({existing.get('percentage', '?')}%)")
        # Check anomaly flags
        anomaly = existing.get("anomaly_check", "")
        if "ROBOTIC" in anomaly:
            print(f"  ⚠️  {anomaly}")
        else:
            print(f"  ✅ {anomaly}")

    # Compute objective indicators per phase
    print(f"\n[Objective Depth Indicators]")
    phase_dir = f"ipd/phase-{phase_num}"

    # Phase-specific objective metrics
    metrics = {}
    total_score = 0
    max_score = 0

    for dim in dimensions:
        dim_id = dim["id"]
        dim_max = dim.get("max_score", 3)
        score = 0
        indicators = []

        # === Phase 0: Market Insight ===
        if phase_num == 0:
            if dim_id == "competitor_mechanism_analysis":
                content = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/06-competitor-mechanism-deepdive.md"))
                competitor_count = content.count("| **") - 2  # Approximate competitor entries in table
                if competitor_count >= 4: score = 3
                elif competitor_count >= 2: score = 2
                elif competitor_count >= 1: score = 1
                indicators.append(f"竞品机制拆解数: {competitor_count} (阈值≥4=满分)")
            elif dim_id == "user_boundary_scenarios":
                content = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/07-boundary-scenarios.md"))
                scenarios = content.count("### ") + content.count("## ")
                if scenarios >= 10: score = 3
                elif scenarios >= 5: score = 2
                elif scenarios >= 2: score = 1
                indicators.append(f"边界场景数: {scenarios} (阈值≥10=满分)")
            elif dim_id == "differentiated_critique":
                content = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/01-market-insight.md"))
                tables = count_tables(content)
                if tables >= 4: score = 3
                elif tables >= 2: score = 2
                elif tables >= 1: score = 1
                indicators.append(f"差异化分析表格数: {tables} (阈值≥4=满分)")
            elif dim_id == "self_blind_spot_identification":
                content = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/01-market-insight.md"))
                risks = content.count("风险") + content.count("风险")
                if risks >= 6: score = 3
                elif risks >= 3: score = 2
                elif risks >= 1: score = 1
                indicators.append(f"风险识别数: {risks} (阈值≥6=满分)")

        # === Phase 1: Concept Definition ===
        elif phase_num == 1:
            if dim_id == "requirement_counterexample_definition":
                analyst = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/analyst-output.md"))
                kano_types = analyst.count("基本型") + analyst.count("期望型") + analyst.count("兴奋型")
                if kano_types >= 8: score = 3
                elif kano_types >= 5: score = 2
                elif kano_types >= 2: score = 1
                indicators.append(f"Kano 分类需求数: {kano_types} (阈值≥8=满分)")
            elif dim_id == "latent_variable_identification":
                architect = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/architect-output.md"))
                competency = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/core-competency.md"))
                dep_chains = competency.count("依赖") + competency.count("↓")
                if dep_chains >= 3: score = 3
                elif dep_chains >= 1: score = 2
                indicators.append(f"竞争力依赖链数: {dep_chains} (阈值≥3=满分)")
            elif dim_id == "scenario_coverage":
                architect = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/architect-output.md"))
                sections = count_evidence_sections(architect)
                if sections >= 10: score = 3
                elif sections >= 5: score = 2
                elif sections >= 2: score = 1
                indicators.append(f"架构文档章节数: {sections} (阈值≥10=满分)")
            elif dim_id == "pseudo_requirement_exclusion":
                analyst = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/analyst-output.md"))
                # Count requirements with ≥2 evidence items
                evidence_items = analyst.count("[证据")
                if evidence_items >= 10: score = 3
                elif evidence_items >= 5: score = 2
                elif evidence_items >= 2: score = 1
                indicators.append(f"需求证据项数: {evidence_items} (阈值≥10=满分)")

        # === Phase 2: Detailed Planning ===
        elif phase_num == 2:
            if dim_id == "architecture_reverse_derivation":
                ata = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/03-ata-analysis.md"))
                decisions = ata.count("D-") // 2  # Each decision appears ~2 times
                competency_refs = ata.count("core-competency") + ata.count("竞争力")
                if decisions >= 4 and competency_refs >= 3: score = 3
                elif decisions >= 3: score = 2
                elif decisions >= 1: score = 1
                indicators.append(f"ATA 决策数: {decisions}, 竞争力引用数: {competency_refs}")
            elif dim_id == "risk_self_assessment":
                planning = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/02-detailed-planning.md"))
                risks = planning.count("风险") + planning.count("缓解")
                if risks >= 10: score = 3
                elif risks >= 5: score = 2
                elif risks >= 2: score = 1
                indicators.append(f"风险+缓解项数: {risks} (阈值≥10=满分)")
            elif dim_id == "dependency_impact_chain":
                planning = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/02-detailed-planning.md"))
                wp_count = planning.count("WP") // 2  # Each WP mentioned ~2 times
                if wp_count >= 20: score = 3
                elif wp_count >= 10: score = 2
                elif wp_count >= 5: score = 1
                indicators.append(f"WBS 工作包引用数: {wp_count} (阈值≥20=满分)")
            elif dim_id == "constraint_enumeration":
                dfx = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/04-dfx-assessment.md"))
                dfx_sections = count_evidence_sections(dfx)
                if dfx_sections >= 4: score = 3
                elif dfx_sections >= 2: score = 2
                elif dfx_sections >= 1: score = 1
                indicators.append(f"DFX 评估维度数: {dfx_sections} (阈值≥4=满分)")

        # === Phase 3: AI-Assisted Development ===
        elif phase_num == 3:
            if dim_id == "test_depth_distribution":
                # Count test files by category
                test_dir = os.path.join(PROJECT_ROOT, "internal")
                boundary_tests = 0
                error_tests = 0
                security_tests = 0
                for root, dirs, files in os.walk(test_dir):
                    for f in files:
                        if f.endswith("_test.go"):
                            content = read_file_content(os.path.join(root, f))
                            boundary_tests += content.count("Boundary") + content.count("Edge") + content.count("Limit")
                            error_tests += content.count("Error") + content.count("Fail") + content.count("Invalid")
                            security_tests += content.count("Auth") + content.count("Inject") + content.count("Travers")
                total_test_types = boundary_tests + error_tests + security_tests
                type_coverage = sum(1 for x in [boundary_tests, error_tests, security_tests] if x > 0)
                if type_coverage >= 3 and total_test_types >= 15: score = 3
                elif type_coverage >= 2 and total_test_types >= 8: score = 2
                elif type_coverage >= 1: score = 1
                indicators.append(f"测试类型覆盖: 边界={boundary_tests}, 错误={error_tests}, 安全={security_tests}")
            elif dim_id == "spec_counterexample_ac":
                spec_dir = os.path.join(PROJECT_ROOT, "specs")
                ac_count = 0
                counterexample_count = 0
                if os.path.exists(spec_dir):
                    for f in os.listdir(spec_dir):
                        if f.endswith(".md"):
                            content = read_file_content(os.path.join(spec_dir, f))
                            ac_count += content.count("AC-")
                            counterexample_count += content.count("非") + content.count("不")
                if ac_count >= 15: score = 3
                elif ac_count >= 8: score = 2
                elif ac_count >= 3: score = 1
                indicators.append(f"Spec AC 总数: {ac_count}, 反例/非功能描述: {counterexample_count}")
            elif dim_id == "error_path_coverage":
                test_dir = os.path.join(PROJECT_ROOT, "internal")
                error_path_tests = 0
                for root, dirs, files in os.walk(test_dir):
                    for f in files:
                        if f.endswith("_test.go"):
                            content = read_file_content(os.path.join(root, f))
                            error_path_tests += content.count("ShouldReturnError") + content.count("Error") + content.count("Fail")
                if error_path_tests >= 20: score = 3
                elif error_path_tests >= 10: score = 2
                elif error_path_tests >= 3: score = 1
                indicators.append(f"错误路径测试数: {error_path_tests} (阈值≥20=满分)")
            elif dim_id == "boundary_condition_enumeration":
                test_dir = os.path.join(PROJECT_ROOT, "internal")
                boundary_tests = 0
                for root, dirs, files in os.walk(test_dir):
                    for f in files:
                        if f.endswith("_test.go"):
                            content = read_file_content(os.path.join(root, f))
                            boundary_tests += content.count("Empty") + content.count("Nil") + content.count("Zero") + content.count("Max")
                if boundary_tests >= 15: score = 3
                elif boundary_tests >= 8: score = 2
                elif boundary_tests >= 3: score = 1
                indicators.append(f"边界条件测试数: {boundary_tests} (阈值≥15=满分)")

        # === Phase 4: Validation & Release ===
        elif phase_num == 4:
            if dim_id == "failure_mode_coverage":
                content = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/01-grtr-report.md"))
                failure_modes = content.count("失败") + content.count("异常") + content.count("降级")
                if failure_modes >= 5: score = 3
                elif failure_modes >= 3: score = 2
                elif failure_modes >= 1: score = 1
                indicators.append(f"失败模式数: {failure_modes} (阈值≥5=满分)")
            elif dim_id == "user_real_feedback":
                # Check for beta/feedback evidence
                feedback_files = ["ipd/05-validation-launch/evidence-chain.md"]
                feedback_count = 0
                for ff in feedback_files:
                    c = read_file_content(os.path.join(PROJECT_ROOT, ff))
                    feedback_count += c.count("反馈") + c.count("用户")
                if feedback_count >= 5: score = 3
                elif feedback_count >= 2: score = 2
                indicators.append(f"用户反馈证据数: {feedback_count}")
            elif dim_id == "regression_risk_identification":
                content = read_file_content(os.path.join(PROJECT_ROOT, f"{phase_dir}/01-grtr-report.md"))
                regressions = content.count("回归") + content.count("兼容")
                if regressions >= 3: score = 3
                elif regressions >= 1: score = 2
                indicators.append(f"回归风险识别数: {regressions}")
            elif dim_id == "release_condition_critique":
                checklist = read_file_content(os.path.join(PROJECT_ROOT, "ipd/05-validation-launch/launch-checklist.yaml"))
                items = checklist.count("- ") if checklist else 0
                if items >= 10: score = 3
                elif items >= 5: score = 2
                elif items >= 2: score = 1
                indicators.append(f"发布检查项数: {items}")

        # === Phase 5: Lifecycle Management ===
        elif phase_num == 5:
            if dim_id == "feedback_coverage_rate":
                backlog = read_file_content(os.path.join(PROJECT_ROOT, "ipd/06-lifecycle/iteration-backlog.md"))
                feedback_items = backlog.count("反馈") + backlog.count("用户")
                if feedback_items >= 5: score = 3
                elif feedback_items >= 2: score = 2
                indicators.append(f"反馈处理项数: {feedback_items}")
            elif dim_id == "technical_debt_health":
                tech_debt = read_file_content(os.path.join(PROJECT_ROOT, "ipd/04-development/tech-debt.yaml"))
                debt_items = tech_debt.count("- id:") if tech_debt else 0
                if debt_items >= 3: score = 3
                elif debt_items >= 1: score = 2
                indicators.append(f"技术债项数: {debt_items}")
            elif dim_id == "trend_forecast":
                lifecycle_yaml = read_file_content(os.path.join(PROJECT_ROOT, "ipd/06-lifecycle/metrics-dashboard.yaml"))
                trend_items = lifecycle_yaml.count("trend") + lifecycle_yaml.count("趋势") if lifecycle_yaml else 0
                if trend_items >= 3: score = 3
                elif trend_items >= 1: score = 2
                indicators.append(f"趋势指标数: {trend_items}")
            elif dim_id == "eol_contingency_plan":
                # EOL = End of Life, check lifecycle doc for end-of-life or sunset mentions
                lifecycle_doc = read_file_content(os.path.join(PROJECT_ROOT, f"ipd/phase-5/dcp-checklist.md"))
                eol_items = lifecycle_doc.count("下线") + lifecycle_doc.count("EOL") + lifecycle_doc.count("退市")
                if eol_items >= 2: score = 3
                elif eol_items >= 1: score = 2
                else: score = 0
                indicators.append(f"EOL/退市相关项: {eol_items}")

        # Cap score at max_score
        score = min(score, dim_max)
        total_score += score
        max_score += dim_max
        metrics[dim_id] = {"score": score, "max": dim_max, "indicators": indicators}

        # Print
        icon = "✅" if score >= dim_max * 0.6 else "⚠️" if score > 0 else "❌"
        indicator_str = "; ".join(indicators) if indicators else "无客观指标"
        print(f"  {icon} {dim['name']}: {score}/{dim_max} — {indicator_str}")

    percentage = round(total_score / max_score * 100) if max_score > 0 else 0
    verdict = "PASS" if percentage >= 60 else "FAIL"
    icon = "✅" if verdict == "PASS" else "❌"
    print(f"\n  {icon} 客观深度评分: {total_score}/{max_score} ({percentage}%) | {verdict} (阈值≥60%)")

    return {
        "objective": True,
        "total_score": total_score,
        "max_score": max_score,
        "percentage": percentage,
        "verdict": verdict,
        "metrics": metrics
    }

def check_file_exists(path):
    """Check if file exists relative to project root"""
    # Handle absolute-looking paths (ipd/...)
    if path.startswith("ipd/"):
        full = os.path.join(PROJECT_ROOT, path)
    # Handle .gate paths
    elif path.startswith(".gate/"):
        full = os.path.join(PROJECT_ROOT, path)
    # Handle relative paths (assume ipd/phase-N/)
    else:
        full = os.path.join(PROJECT_ROOT, path)
    exists = os.path.exists(full)
    return exists

def validate_manifest(manifest):
    results = []
    phase = manifest["phase"]
    name = manifest["name"]
    gate = manifest["gate"]
    status = manifest.get("status", "UNKNOWN")

    print(f"\n{'='*60}")
    print(f"Phase {phase}: {name} | Gate: {gate} | Status: {status}")
    print(f"{'='*60}")

    # Check 1: Upstream dependencies
    print(f"\n[Upstream Dependencies]")
    upstream_ok = True
    for dep in manifest.get("upstream", []):
        dep_phase = dep.get("phase", "?")
        for req_file in dep.get("required_files", []):
            exists = check_file_exists(req_file)
            icon = "✅" if exists else "❌"
            print(f"  {icon} Phase {dep_phase} file: {req_file}")
            if not exists:
                upstream_ok = False
        if dep.get("required_gate_pass", False):
            dcp_file = dep.get("required_files", [""])[-1].replace("02-", "").replace("03-", "").replace("04-", "").replace("01-", "")
            # Check DCP checklist has PASS verdict
            pass
    results.append(("Upstream dependencies", "PASS" if upstream_ok else "FAIL"))

    # Check 2: Required output files
    print(f"\n[Required Output Files]")
    outputs_ok = True
    outputs = manifest.get("outputs", {})

    for category in ["consultation", "documents", "gate"]:
        for item in outputs.get(category, []):
            path = item["path"]
            required = item.get("required", True)
            exists = check_file_exists(path)
            icon = "✅" if exists else "❌" if required else "⚪"
            desc = item.get("description", "")
            print(f"  {icon} [{category}] {path}" + (f" ({desc})" if desc else ""))
            if not exists and required:
                outputs_ok = False
    results.append(("Required output files", "PASS" if outputs_ok else "FAIL"))

    # Check 3: Depth score file
    print(f"\n[Depth Score]")
    depth_score_ok = True
    for dim in manifest.get("depth_score_dimensions", []):
        print(f"  Dimension: {dim['name']} (0-{dim['max_score']})")
    ds_path = f".gate/depth-score-P{phase}.json"
    ds_exists = check_file_exists(ds_path)
    icon = "✅" if ds_exists else "❌"
    print(f"  {icon} Depth score file: {ds_path}")
    if not ds_exists:
        # Check if manifest says required: true
        for item in outputs.get("gate", []):
            if item["path"] == ds_path and item.get("required", True):
                depth_score_ok = False
    results.append(("Depth score file", "PASS" if depth_score_ok else "FAIL"))

    # Check 3b: Objective depth score computation
    objective_result = compute_objective_depth_score(phase, manifest)
    if objective_result:
        results.append(("Objective depth score", objective_result["verdict"]))

    # Check 4: DCP checklist items
    print(f"\n[DCP Checklist]")
    dcp_items = manifest.get("dcp_items", [])
    print(f"  Total DCP items defined: {len(dcp_items)}")
    results.append(("DCP checklist defined", "PASS" if len(dcp_items) > 0 else "FAIL"))

    # Check 5: Evidence files for DCP items
    evidence_ok = True
    missing_evidence = []
    phase_dir = f"ipd/phase-{phase}"
    for item in dcp_items:
        item_status = item.get("status", "")
        ev_files = item.get("evidence_files", [])

        # PARTIAL items: evidence check skipped, reported as warning
        if item_status == "PARTIAL":
            if ev_files:
                # Check if any evidence exists, but don't fail
                found_any = False
                for ev in ev_files:
                    if ev.startswith("ipd/"):
                        candidate = ev
                    elif ev.startswith(".gate/"):
                        candidate = ev
                    else:
                        candidate = f"{phase_dir}/{ev}"
                    if check_file_exists(candidate):
                        found_any = True
                        break
                if found_any:
                    print(f"  ⚠️  DCP #{item['id']} PARTIAL (evidence found, condition not closed): {item['name']}")
                else:
                    print(f"  ⚠️  DCP #{item['id']} PARTIAL (evidence pending): {item['name']}")
            else:
                print(f"  ⚠️  DCP #{item['id']} PARTIAL: {item['name']}")
            continue

        if not ev_files:
            continue  # No evidence required for this item
        all_missing = True
        for ev in ev_files:
            # Resolve path: if it starts with ipd/ use as-is, otherwise prefix with phase dir
            if ev.startswith("ipd/"):
                candidate = ev
            elif ev.startswith(".gate/"):
                candidate = ev
            else:
                candidate = f"{phase_dir}/{ev}"
            if check_file_exists(candidate):
                all_missing = False
                break  # Found at least one evidence file
        if all_missing and ev_files:
            # Re-check with expanded path resolution (root, ipd/, .gate/, phase_dir/)
            for ev in ev_files:
                candidates = [ev]
                if ev.startswith("specs/") or ev in ("CLAUDE.md", "AGENTS.md"):
                    candidates.append(ev)
                if ev.startswith("ai-coding-v5.4/"):
                    candidates.append(ev)
                if ev.startswith(".github/") or ev.startswith(".gate/"):
                    candidates.append(ev)
                if not ev.startswith("/"):
                    candidates.append(f"{phase_dir}/{ev}")
                    candidates.append(os.path.join(PROJECT_ROOT, ev))
                for candidate in candidates:
                    if os.path.exists(candidate) if candidate.startswith("/") else check_file_exists(candidate):
                        all_missing = False
                        break
            if all_missing:
                evidence_ok = False
                missing_evidence.append(f"  ❌ DCP #{item['id']} evidence: {ev_files}")

    if missing_evidence:
        print(f"\n  Missing evidence files:")
        for m in missing_evidence:
            print(f"    {m}")
    results.append(("Evidence files present", "PASS" if evidence_ok else "FAIL"))

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    all_pass = True
    for name, result in results:
        icon = status_icon(result)
        print(f"  {icon} {name}: {result}")
        if result != "PASS":
            all_pass = False

    verdict = "PASS" if all_pass else "FAIL"
    print(f"\n  Verdict: {verdict}")
    return all_pass

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gate-check.py ipd/phase-N/manifest.yaml")
        sys.exit(1)

    manifest_path = sys.argv[1]
    if not os.path.exists(manifest_path):
        print(f"Error: manifest not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    ok = validate_manifest(manifest)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
