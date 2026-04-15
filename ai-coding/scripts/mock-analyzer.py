"""
分析测试中的 Mock 使用，检测过度 Mock。
"""
import ast, sys

class MockVisitor(ast.NodeVisitor):
    def __init__(self):
        self.mocks = []
        self.functions = []

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if 'mock' in node.func.attr.lower():
                self.mocks.append({
                    'line': node.lineno,
                    'target': self._get_target(node.func),
                })
        self.generic_visit(node)

    def _get_target(self, node):
        if isinstance(node, ast.Attribute):
            return f"{self._get_target(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        return "?"

def analyze_mocks(test_file):
    with open(test_file) as f:
        tree = ast.parse(f.read())

    visitor = MockVisitor()
    visitor.visit(tree)

    print(f"[MOCK ANALYSIS] Found {len(visitor.mocks)} mocks in {len(visitor.functions)} tests")

    # 检测过度 Mock：阈值基于测试数量和依赖数
    mock_count = len(visitor.mocks)
    func_count = len(visitor.functions)
    if mock_count > func_count * 2:
        print(f"[MOCK ANALYSIS] WARNING: {mock_count} mocks for {func_count} tests")
        print(f"  -> Consider using integration tests or real implementations")

    # 检测标准库和常用库 Mock
    for mock in visitor.mocks:
        no_mock_libs = [
            'os', 'sys', 'json', 'datetime', 'time',
            'subprocess', 'collections', 'itertools', 'functools',
            'requests', 'http', 'socket', 'urllib',
            'pathlib', 'logging', 'configparser',
        ]
        for lib in no_mock_libs:
            if mock['target'].startswith(lib + '.') or mock['target'] == lib:
                print(f"[MOCK ANALYSIS] WARNING: Mocking library '{lib}' at line {mock['line']}")
                print(f"  -> Consider using real implementation or test double")

if __name__ == '__main__':
    analyze_mocks(sys.argv[1])
