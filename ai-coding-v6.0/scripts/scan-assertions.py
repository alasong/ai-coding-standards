"""
扫描测试断言质量，标记可疑断言供人工审核。
支持：
- 空断言检测（assert True 等无意义断言）
- Spec AC 映射检查（断言是否覆盖 Spec 中的验收标准）
- 断言严格度检查（是否检查了具体值还是只检查了类型）
"""
import re, sys, os

SUSPICIOUS_PATTERNS = [
    (r'assert\s+True\b', 'Empty assertion: always passes'),
    (r'expect\(.*\)\.toBe\(true\)', 'Boolean assertion: may not test anything'),
    (r'expect\(.*\)\.toBeDefined\(\)', 'Weak assertion: consider checking the value'),
    (r'assert\s+isinstance\([^,]+,\s*(type|NoneType)\)', 'Type-only assertion: consider checking value'),
    (r'return\s+True\s*$', 'Test function always returns True'),
    (r'assert\s+.*==\s*(True|None|0)\s*$', 'Trivial assertion: may not validate behavior'),
]

def load_spec_ac_mapping(test_file):
    """Load AC mapping from corresponding Spec file."""
    spec_dir = 'specs/'
    if not os.path.exists(spec_dir):
        return {}
    spec_files = [f for f in os.listdir(spec_dir) if f.endswith('.md')]
    ac_map = {}
    for sf in spec_files:
        with open(os.path.join(spec_dir, sf)) as f:
            content = f.read()
        scenarios = re.findall(r'Scenario:\s+(.+)', content)
        ac_map[sf] = [s.strip() for s in scenarios]
    return ac_map

def scan_assertions(test_file, check_empty=True, check_spec_mapping=True, check_strictness=True):
    if not os.path.exists(test_file):
        print(f"[ASSERTION SCAN] File not found: {test_file}")
        return
    with open(test_file) as f:
        lines = f.readlines()

    suspicious = []
    for i, line in enumerate(lines, 1):
        for pattern, reason in SUSPICIOUS_PATTERNS:
            if re.search(pattern, line):
                suspicious.append((i, line.strip(), reason))

    if check_spec_mapping:
        ac_map = load_spec_ac_mapping(test_file)
        if ac_map:
            test_content = ''.join(lines)
            ac_referenced = any(
                re.search(re.escape(sc), test_content, re.IGNORECASE)
                for scs in ac_map.values() for sc in scs
            )
            if not ac_referenced:
                print(f"[SPEC MAPPING] No AC scenarios referenced in this test")
                print(f"  -> Test may not be linked to any Spec acceptance criteria")

    if suspicious:
        print(f"[ASSERTION SCAN] {len(suspicious)} suspicious assertions found:")
        for line_no, code, reason in suspicious:
            print(f"  Line {line_no}: {code}")
            print(f"    -> {reason}")
    else:
        print("[ASSERTION SCAN] All assertions look good")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('test_file', help='Path to test file')
    parser.add_argument('--no-check-empty', action='store_false', dest='check_empty',
                        help='Disable empty assertion detection')
    parser.add_argument('--no-check-spec-mapping', action='store_false', dest='check_spec_mapping',
                        help='Disable Spec AC mapping check')
    parser.add_argument('--no-check-strictness', action='store_false', dest='check_strictness',
                        help='Disable assertion strictness check')
    args = parser.parse_args()
    scan_assertions(
        args.test_file,
        check_empty=args.check_empty,
        check_spec_mapping=args.check_spec_mapping,
        check_strictness=args.check_strictness
    )
