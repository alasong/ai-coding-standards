#!/usr/bin/env python3
"""
Spec Validation Gate — 机器可执行的 Spec 合规检查。

CI Gate 检查项（对应 01-core-specification.md 第 5.5 节）：
  1. problem_statement 非空
  2. origin 合法（PRD / user-feedback / poc-assumption / tech-debt）
  3. origin 为 PRD 时 prd_user_story_refs 非空
  4. gherkin 代码块存在
  5. non_problem 字段非空
  6. experimental 字段存在

exit 0 = pass, exit 1 = fail.
输出 JSON 格式结果。
"""
import sys
import re
import json
import glob
import os

VALID_ORIGINS = {"PRD", "user-feedback", "poc-assumption", "tech-debt"}


def parse_frontmatter(content):
    """Parse YAML-like frontmatter from spec file."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm = content[3:end].strip()
    result = {}
    for line in fm.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Strip inline comments (but not inside strings)
        if not value.startswith('"') and not value.startswith("["):
            if "#" in value:
                value = value[:value.index("#")].strip()
        # Unquote strings
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        result[key] = value
    return result


def validate_spec(filepath):
    """Validate a single spec file. Returns (passed, issues)."""
    with open(filepath) as f:
        content = f.read()

    fm = parse_frontmatter(content)
    issues = []
    warnings = []

    # 1. problem_statement non-empty
    ps = fm.get("problem_statement", "")
    if not ps:
        issues.append("problem_statement is empty or missing")

    # 2. origin valid
    origin = fm.get("origin", "")
    if not origin:
        issues.append("origin is empty (must be: " + ", ".join(sorted(VALID_ORIGINS)) + ")")
    elif origin not in VALID_ORIGINS:
        issues.append(f"origin '{origin}' is invalid; must be one of: {', '.join(sorted(VALID_ORIGINS))}")

    # 3. PRD origin requires prd_user_story_refs (unless experimental)
    if origin == "PRD":
        exp = fm.get("experimental", "").lower()
        if exp != "true":
            refs = fm.get("prd_user_story_refs", "")
            if not refs or refs == "[]":
                issues.append("origin is PRD but prd_user_story_refs is empty")

    # 4. experimental flag must exist
    if "experimental" not in fm:
        issues.append("experimental field missing (must be true or false)")
    else:
        exp = fm.get("experimental", "").lower()
        if exp not in ("true", "false"):
            issues.append(f"experimental must be 'true' or 'false', got '{exp}'")

    # 5. non_problem non-empty
    np_val = fm.get("non_problem", "")
    if not np_val:
        issues.append("non_problem is empty or missing")

    # 6. Gherkin blocks exist
    if "```gherkin" not in content:
        issues.append("No gherkin code blocks found (AC must use gherkin format)")

    # 7. Given/When/Then structure in gherkin
    gherkin_blocks = re.findall(r"```gherkin(.*?)```", content, re.DOTALL)
    for i, block in enumerate(gherkin_blocks):
        if "Given" not in block or "When" not in block or "Then" not in block:
            issues.append(f"Gherkin block {i+1} missing Given/When/Then structure")

    passed = len(issues) == 0
    return passed, {"file": filepath, "passed": passed, "issues": issues, "warnings": warnings}


def main():
    spec_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "specs")
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = sorted(glob.glob(os.path.join(spec_dir, "F*.md")))

    results = []
    all_passed = True
    for f in files:
        if os.path.basename(f) == "F000-template.md":
            continue  # Skip template
        passed, result = validate_spec(f)
        results.append(result)
        if not passed:
            all_passed = False

    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Summary
    total = len(results)
    ok = sum(1 for r in results if r["passed"])
    fail = total - ok
    print(f"\nSpec Validation: {ok}/{total} passed, {fail} failed")

    if not all_passed:
        print("\nFailed specs:")
        for r in results:
            if not r["passed"]:
                for issue in r["issues"]:
                    print(f"  {r['file']}: {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
