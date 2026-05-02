"""
反向验证：对每个测试，尝试破坏对应的实现代码，
确认测试能捕获失败。如果测试仍然通过，说明断言无效。

流程：
1. 找到测试对应的实现文件
2. 读取测试中的断言，推断被测试的函数
3. 复制实现文件到临时目录
4. 注入破坏（return None, raise Exception 等）
5. 运行测试，确认应该失败
6. 如果测试仍通过 → 断言可疑
7. 恢复原始实现文件（不保留任何修改）
"""
import subprocess, sys, os, shutil, tempfile, re

def find_source_file(test_file):
    """Find the source file corresponding to a test file."""
    mapping = {
        '_test.go': '.go',
        '.spec.ts': '.ts',
        '.test.ts': '.ts',
        'test_': '',
        '_test.py': '.py',
    }
    for suffix, replacement in mapping.items():
        if suffix in test_file:
            return test_file.replace(suffix, replacement).replace('test_', '')
    return None

def extract_tested_functions(test_file):
    """Extract function names being tested from test function names."""
    with open(test_file) as f:
        content = f.read()
    functions = []
    functions += re.findall(r'Test(\w+)', content)
    functions += re.findall(r'def\s+test_(\w+)', content)
    functions += re.findall(r"describe\(['\"](\w+)", content)
    return functions

def mutate_source(source_path, function_name):
    """Inject a simple mutation into the source file for a given function."""
    with open(source_path) as f:
        content = f.read()

    if source_path.endswith('.py'):
        pattern = rf'(def\s+{function_name}\s*\([^)]*\)\s*:\s*\n)(\s+)'
        match = re.search(pattern, content)
        if match:
            indent = match.group(2)
            mutated = content[:match.start(2)] + match.group(2) + \
                      f'{indent}# MUTATION: reverse validation\n{indent}return "__MUTATED__"\n' + \
                      content[match.end():]
            return mutated
    elif source_path.endswith('.ts'):
        pattern = rf'(export\s+(?:async\s+)?function\s+{function_name}\s*\([^)]*\)\s*[:\w\s,]*\{{)\s*\n'
        match = re.search(pattern, content)
        if match:
            mutated = content[:match.end()] + \
                      f'  return "__MUTATED__"; // MUTATION\n' + \
                      content[match.end():]
            return mutated
    elif source_path.endswith('.go'):
        pattern = rf'(func\s+\(\s*\w+\s+\*?\w*\s*\)\s*{function_name}\s*\([^)]*\)\s*[^{{]*\{{)\s*\n'
        match = re.search(pattern, content)
        if match:
            mutated = content[:match.end()] + \
                      f'\tpanic("__MUTATED__") // MUTATION\n' + \
                      content[match.end():]
            return mutated

    return None

def reverse_validate(test_file, test_cmd='make test'):
    source = find_source_file(test_file)
    if not source or not os.path.exists(source):
        print(f"[REVERSE] No source file found for {test_file}")
        return []

    tested_functions = extract_tested_functions(test_file)
    suspicious = []

    # Work on a temp copy to ensure safe recovery even on crash
    tmp_dir = tempfile.mkdtemp()
    tmp_source = os.path.join(tmp_dir, os.path.basename(source))
    shutil.copy2(source, tmp_source)

    try:
        for func in tested_functions:
            print(f"[REVERSE] Testing function '{func}'")
            mutated = mutate_source(tmp_source, func)
            if not mutated:
                print(f"  → Cannot mutate '{func}', skipping")
                continue

            with open(tmp_source, 'w') as f:
                f.write(mutated)

            result = subprocess.run(
                test_cmd, shell=True,
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                suspicious.append(func)
                print(f"  → SUSPICIOUS: Test passed despite mutation in '{func}'")
            else:
                print(f"  → OK: Test correctly failed with mutation in '{func}'")

            # Restore for next mutation
            shutil.copy2(source, tmp_source)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"[REVERSE] Temp files cleaned: {tmp_dir}")

    if suspicious:
        print(f"\n[REVERSE RESULT] {len(suspicious)} suspicious assertions: {suspicious}")
    else:
        print(f"\n[REVERSE RESULT] All assertions validated successfully")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: reverse-validate.py <test_file> [test_cmd]")
        sys.exit(1)
    test_file = sys.argv[1]
    test_cmd = sys.argv[2] if len(sys.argv) > 2 else 'make test'
    reverse_validate(test_file, test_cmd)
