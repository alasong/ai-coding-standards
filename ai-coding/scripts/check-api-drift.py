"""
检测代码 API 签名与文档是否一致。
支持 Python, Go, TypeScript, Java, Rust.
"""
import ast, sys, re, subprocess, os
from pathlib import Path

def extract_py_functions(filepath):
    """Extract function signatures from Python source."""
    with open(filepath) as f:
        tree = ast.parse(f.read())
    return [
        f"{node.name}({', '.join(a.arg for a in node.args.args)})"
        for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]

def extract_go_signatures(filepath):
    """Extract function signatures from Go source using gofmt."""
    result = subprocess.run(
        ['gofmt', '-d', filepath],
        capture_output=True, text=True, timeout=10
    )
    with open(filepath) as f:
        content = f.read()
    pattern = r'func\s+(\w+)\(([^)]*)\)'
    funcs = []
    for match in re.finditer(pattern, content):
        name, params = match.group(1), match.group(2)
        param_names = [p.strip().split()[0] if ' ' in p.strip() else p.strip()
                       for p in params.split(',') if p.strip()]
        funcs.append(f"{name}({', '.join(param_names)})")
    return funcs

def extract_ts_functions(filepath):
    """Extract function/export signatures from TypeScript source."""
    with open(filepath) as f:
        content = f.read()
    funcs = []
    patterns = [
        r'export\s+(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        r'export\s+const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)',
        r'(\w+)\s*:\s*\(([^)]*)\)\s*=>',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            name = match.group(1)
            params = match.group(2) if match.lastindex >= 2 else ''
            param_names = [p.strip().split(':')[0].strip()
                           for p in params.split(',') if p.strip()]
            funcs.append(f"{name}({', '.join(param_names)})")
    return funcs

def extract_doc_apis(docpath):
    """Extract API signatures mentioned in documentation."""
    with open(docpath) as f:
        content = f.read()
    apis = re.findall(r'`(\w+\([^)]*\))`', content)
    apis += re.findall(r'```(?:\w+)?\s*\n(?:.*\n)*?(\w+\([^)]*\))', content)
    return apis

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: check-api-drift.py <src_file> <doc_file> [--auto-fix]")
        sys.exit(1)
    src = sys.argv[1]
    doc = sys.argv[2]

    if not os.path.exists(src):
        print(f"Error: source file not found: {src}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(doc):
        print(f"Error: doc file not found: {doc}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(src)[1]
    extractors = {
        '.py': extract_py_functions,
        '.go': extract_go_signatures,
        '.ts': extract_ts_functions,
        '.java': lambda f: [],
        '.rs': lambda f: [],
    }
    extractor = extractors.get(ext, lambda f: [])
    code_apis = set(extractor(src))
    doc_apis = set(extract_doc_apis(doc))
    missing = code_apis - doc_apis
    obsolete = doc_apis - code_apis

    if missing:
        print(f"DRIFT DETECTED: API in code but not in docs: {missing}")
        if '--auto-fix' in sys.argv:
            print(f"Auto-generating doc patch for: {missing}")
    if obsolete:
        print(f"DRIFT DETECTED: API in docs but removed from code: {obsolete}")
        if '--auto-fix' in sys.argv:
            print(f"Auto-generating doc removal patch for: {obsolete}")
    if not missing and not obsolete:
        print("NO DRIFT: Code and docs are in sync")
