"""
Spec 质量评估系统，自动评分。
支持 Markdown 格式的 Spec 文件（与 #3 Spec 生成器格式一致）。
通过解析 Markdown 结构提取用户故事、验收标准等字段。
"""
import sys, re, json

class SpecQualityChecker:
    def __init__(self, spec_file):
        with open(spec_file) as f:
            self.content = f.read()
        self.score = 100
        self.issues = []

    def check_completeness(self):
        """检查完整性：所有必填章节存在。"""
        required_sections = [
            ('title', r'^#\s+.+'),
            ('user_stories', r'##?\s+.*[Uu]ser\s+[Ss]tor'),
            ('acceptance_criteria', r'##?\s+.*[Aa]cceptance|[Cc]riteria|Scenario'),
            ('technical_constraints', r'##?\s+.*[Cc]onstraint|[Tt]echnical'),
            ('out_of_scope', r'##?\s+.*[Oo]ut\s+[Oo]f\s+[Ss]cope|[Nn]on-[Gg]oal'),
        ]
        for field, pattern in required_sections:
            if not re.search(pattern, self.content, re.MULTILINE):
                self.score -= 10
                self.issues.append(f"Missing required section: {field}")

    def check_ac_coverage(self):
        """检查 AC 覆盖率：每个用户故事有 >= 2 个验收标准。"""
        stories = re.findall(r'[Aa]s a\s+.+?\s+so that\s+.+?\.', self.content, re.DOTALL)
        scenarios = re.findall(r'Scenario:', self.content)
        story_count = max(len(stories), 1)
        ac_count = len(scenarios)
        if ac_count < story_count * 2:
            self.score -= 15
            self.issues.append(
                f"Only {ac_count} ACs (Scenario:) for {story_count} stories "
                f"(need >= {story_count * 2})"
            )

    def check_ambiguity(self):
        """检查歧义：无模糊词。"""
        ambiguous = ['可能', '大概', '尽量', 'maybe', 'approximately', 'usually']
        for word in ambiguous:
            if re.search(rf'\b{word}\b', self.content, re.IGNORECASE):
                self.score -= 5
                self.issues.append(f"Ambiguous word found: '{word}'")

    def check_boundary_coverage(self):
        """检查边界覆盖：包含异常路径。"""
        has_error_path = bool(re.search(
            r'(?i)(error|invalid|fail|exception|malformed|empty|null|boundary)',
            self.content
        ))
        has_edge_case = bool(re.search(
            r'(?i)(empty|null|zero|max|min|overflow|boundary|edge)',
            self.content
        ))
        if not has_error_path:
            self.score -= 10
            self.issues.append("No error path ACs found")
        if not has_edge_case:
            self.score -= 10
            self.issues.append("No boundary condition ACs found")

    def check_testability(self):
        """检查可测试性：每个 AC 包含 Given/When/Then 结构。"""
        scenarios = re.findall(r'Scenario:.*?(?=Scenario:|$)', self.content, re.DOTALL)
        if scenarios:
            untestable = [s for s in scenarios
                          if 'Given' not in s or 'When' not in s or 'Then' not in s]
            if untestable:
                self.score -= 5 * len(untestable)
                self.issues.append(
                    f"{len(untestable)} scenarios missing Given/When/Then structure"
                )

    def evaluate(self):
        self.check_completeness()
        self.check_ac_coverage()
        self.check_ambiguity()
        self.check_boundary_coverage()
        self.check_testability()

        self.score = max(0, self.score)

        if self.score >= 90:
            grade = "HIGH"
        elif self.score >= 70:
            grade = "MEDIUM"
        else:
            grade = "LOW"

        return {
            'score': self.score,
            'grade': grade,
            'issues': self.issues,
            'action': 'auto_pass' if grade == 'HIGH' else 'human_review'
        }

if __name__ == '__main__':
    checker = SpecQualityChecker(sys.argv[1])
    result = checker.evaluate()
    print(json.dumps(result, indent=2))
