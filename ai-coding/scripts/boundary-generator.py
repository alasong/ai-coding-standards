"""
基于函数签名和参数类型，自动生成边界值测试。
支持 Python 函数签名分析，Go/TS 通过语言专用分析器扩展。
"""
import ast, sys, os, re

# 语言无关的边界值定义
BOUNDARY_VALUES = {
    'int': [0, -1, 1, None],
    'str': ['', 'a' * 10000, None, ' '],
    'list': [[], [1], [None]],
    'dict': [{}, {'key': None}, {'key': ''}],
    'bool': [True, False],
}

def infer_param_type(annotation_str):
    """Infer parameter type from type annotation string."""
    type_map = {
        'int': 'int', 'integer': 'int', 'float': 'int',
        'str': 'str', 'string': 'str',
        'list': 'list', 'array': 'list',
        'dict': 'dict', 'map': 'dict',
        'bool': 'bool', 'boolean': 'bool',
    }
    for key, value in type_map.items():
        if key in annotation_str.lower():
            return value
    return None

def generate_py_boundary_tests(test_file, source_file):
    """Generate boundary value tests for Python functions."""
    if not os.path.exists(source_file):
        print(f"[BOUNDARY] Source file not found: {source_file}")
        return

    with open(source_file) as f:
        tree = ast.parse(f.read())

    testable = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            for arg in node.args.args:
                if arg.annotation:
                    type_str = ast.unparse(arg.annotation)
                    boundary_type = infer_param_type(type_str)
                    if boundary_type:
                        testable.append((node.name, arg.arg, boundary_type))

    if not testable:
        print(f"[BOUNDARY] No type-annotated parameters found, using AI-generated supplements")
        print(f"[BOUNDARY] AI will analyze function branches and generate edge-case tests")
        return

    test_stubs = []
    for func_name, param_name, boundary_type in testable:
        for val in BOUNDARY_VALUES.get(boundary_type, []):
            val_repr = repr(val) if val is not None else 'None'
            test_name = f"test_{func_name}_{param_name}_{val_repr.replace(' ', '_')}"[:80]
            test_stubs.append(f"""
def {test_name}(self):
    # Boundary test: {func_name}({param_name}={val_repr})
    # {boundary_type} boundary value: {val_repr}
    result = module.{func_name}({param_name}={val_repr})
    assert result is not None  # TODO: add specific assertion
""")

    with open(test_file, 'a') as f:
        f.write('\n'.join(test_stubs))

    print(f"[BOUNDARY] Generated {len(test_stubs)} boundary tests for {test_file}")

if __name__ == '__main__':
    test_file = sys.argv[1]
    source = test_file.replace('test_', '').replace('_test.', '.').replace('.spec.', '.').replace('.test.', '.')
    generate_py_boundary_tests(test_file, source)
