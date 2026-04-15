"""
架构分层约束检查器（STUB — Phase 2 实现）。

检测模块间的非法依赖（如表现层直接访问数据层）。

Phase 2 实现选项：
- Python: importlab, graphviz
- TypeScript: madge, dependency-cruiser
- Go: depguard, importgraph
"""
try:
    import yaml
except ImportError:
    print("[LAYER CHECK] Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    print("[LAYER CHECK] STUB: Phase 2 implementation needed", file=sys.stderr)
    sys.exit(2)  # NOT_IMPLEMENTED
