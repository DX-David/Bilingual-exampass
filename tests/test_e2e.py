"""End-to-end tests — simulate real user scenarios with actual file structures."""

import os
import pytest
from conftest import create_sample_pptx, create_sample_docx, create_sample_pdf

from scanner import scan_and_group, get_group_name
from extractor import extract_file, merge_group_content
from knowledge_analyzer import build_knowledge_prompt, build_knowledge_markdown
from test_generator import build_test_prompt, split_test_and_answer, build_test_markdown, build_answer_markdown
from html_generator import generate_html
from utils import output_exists, safe_filename


class TestRealWorldScenario:
    """Simulate a real student's course directory with nested chapters."""

    def _setup_course_directory(self, base_dir):
        """Create a realistic course directory structure."""
        chapters = {
            "第一章-机器学习导论": {
                "slides": ("lecture1.pptx", lambda p: create_sample_pptx(p, include_image=True, include_table=True)),
                "notes": ("补充阅读.pdf", lambda p: create_sample_pdf(p, include_table=False)),
            },
            "第二章-监督学习": {
                "slides": ("lecture2.pptx", lambda p: create_sample_pptx(p)),
                "handout": ("handout.docx", lambda p: create_sample_docx(p)),
            },
            "第三章-深度学习": {
                "slides": ("lecture3.pdf", lambda p: create_sample_pdf(p, include_table=True)),
            },
        }

        for ch_name, files in chapters.items():
            ch_dir = os.path.join(base_dir, ch_name)
            os.makedirs(ch_dir)
            for desc, (fname, creator) in files.items():
                fpath = os.path.join(ch_dir, fname)
                creator(fpath)

        return chapters

    def test_full_e2e_scan_and_extract(self, temp_dir):
        """E2E: Scan nested directory, extract all chapters, verify output."""
        chapters = self._setup_course_directory(temp_dir)

        # 1. Scan
        groups = scan_and_group(temp_dir)
        assert len(groups) == 3  # Three chapters

        # 2. Extract each chapter
        for folder, files in groups.items():
            group_name = get_group_name(folder, temp_dir)
            assert group_name in chapters

            results = [extract_file(f) for f in files]
            merged = merge_group_content(results)
            assert len(merged) > 0

            # Verify content contains expected terms
            combined = ' '.join(r['text_summary'] for r in results)
            assert len(combined) > 100  # Should have substantial content

    def test_full_e2e_knowledge_list_generation(self, temp_dir):
        """E2E: Generate knowledge list PDFs for all chapters."""
        self._setup_course_directory(temp_dir)
        groups = scan_and_group(temp_dir)

        for folder, files in groups.items():
            group_name = get_group_name(folder, temp_dir)
            safe_name = safe_filename(group_name)

            # Extract
            results = [extract_file(f) for f in files]
            merged = merge_group_content(results)

            # Build knowledge list
            prompt = build_knowledge_prompt(merged)
            assert len(prompt) > 0

            # Simulate Claude analysis result
            simulated_analysis = f"""## 核心知识点
1. 知识点A — 这是从 {group_name} 提取的关键概念
2. 知识点B — 包含定义和公式

## 重点解题方法
1. 方法一：步骤1 → 步骤2 → 步骤3
2. 方法二：使用公式 $y = f(x)$

## 考试高频考点
| 考点 | 重要程度 | 出题形式 |
|------|---------|---------|
| 考点1 | ⭐⭐⭐ | 选择+简答 |
| 考点2 | ⭐⭐ | 填空 |
"""
            md = build_knowledge_markdown(simulated_analysis, group_name)

            # Convert to PDF
            output = os.path.join(folder, f"{safe_name}-知识清单.html")
            success = generate_html(md, output)
            assert success
            assert os.path.exists(output)
            assert os.path.getsize(output) > 100  # Should be a real PDF

    def test_full_e2e_test_generation(self, temp_dir):
        """E2E: Generate chapter tests for all chapters."""
        self._setup_course_directory(temp_dir)
        groups = scan_and_group(temp_dir)

        for folder, files in groups.items():
            group_name = get_group_name(folder, temp_dir)
            safe_name = safe_filename(group_name)

            results = [extract_file(f) for f in files]
            merged = merge_group_content(results)

            # Generate test
            test_prompt = build_test_prompt(merged, question_count=8)
            assert len(test_prompt) > 0

            # Simulate Claude output
            simulated = f"""## 题目

### 选择题
1. 题目一 ({group_name})
   A. 选项A  B. 选项B  C. 选项C  D. 选项D

### 填空题
2. 填空题目一：______

### 简答题
3. 简答题目一

## 答案与解析
1. **A** — 解析内容
2. 答案一
3. 详细解答步骤...
"""
            q, a = split_test_and_answer(simulated)
            assert q
            assert a

            # Generate PDFs
            q_md = build_test_markdown(q, group_name)
            a_md = build_answer_markdown(a, group_name)

            q_pdf = os.path.join(folder, f"{safe_name}-章节测试.html")
            a_pdf = os.path.join(folder, f"{safe_name}-章节测试-答案.html")

            assert generate_html(q_md, q_pdf)
            assert generate_html(a_md, a_pdf)

            assert os.path.exists(q_pdf)
            assert os.path.exists(a_pdf)
            assert os.path.getsize(q_pdf) > 100
            assert os.path.getsize(a_pdf) > 100

    def test_full_e2e_final_exam(self, temp_dir):
        """E2E: Generate final exam after all chapter PDFs are created."""
        from exam_generator import build_exam_prompt, split_exam_and_answer, build_exam_markdown, build_exam_answer_markdown

        self._setup_course_directory(temp_dir)
        groups = scan_and_group(temp_dir)

        # First generate knowledge lists
        all_content = []
        for folder, files in groups.items():
            results = [extract_file(f) for f in files]
            merged = merge_group_content(results)
            all_content.append(merged)

        combined = '\n\n---\n\n'.join(all_content)

        # Generate final exam
        prompt = build_exam_prompt(
            combined, "中等", 120,
            {"选择题": 30, "填空题": 20, "简答题": 30, "综合题": 20}
        )
        assert len(prompt) > 0

        # Simulate
        simulated = """## 试卷
# 机器学习 期末考试
时长：120分钟 满分：100分

### 一、选择题（30分）
1. (3分) 题目...

### 二、填空题（20分）
11. (2分) 题目...

### 三、简答题（30分）
16. (10分) 题目...

### 四、综合题（20分）
19. (20分) 题目...

## 答案与评分标准
1. B (3分) — 解析...
11. 答案 (2分) — 解析...
16. 参考答案...评分要点...
19. 综合评分标准...
"""
        exam, ans = split_exam_and_answer(simulated)

        exam_md = build_exam_markdown(exam, "机器学习", 120)
        ans_md = build_exam_answer_markdown(ans, "机器学习")

        exam_pdf = os.path.join(temp_dir, "期末考试-机器学习.html")
        ans_pdf = os.path.join(temp_dir, "期末考试-机器学习-答案.html")

        assert generate_html(exam_md, exam_pdf)
        assert generate_html(ans_md, ans_pdf)

        assert os.path.exists(exam_pdf)
        assert os.path.exists(ans_pdf)
        assert os.path.getsize(exam_pdf) > 100
        assert os.path.getsize(ans_pdf) > 100


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_chinese_special_chars_in_names(self, temp_dir):
        """Test with Chinese special characters in file/folder names."""
        ch_dir = os.path.join(temp_dir, "第1章 · 机器学习：理论与「实践」")
        os.makedirs(ch_dir)
        fpath = os.path.join(ch_dir, "课件（2024版）.pptx")
        create_sample_pptx(fpath, include_image=False, include_table=False)

        groups = scan_and_group(temp_dir)
        assert len(groups) == 1
        folder = list(groups.keys())[0]
        group_name = get_group_name(folder, temp_dir)
        safe = safe_filename(group_name)

        result = extract_file(fpath)
        md = build_knowledge_markdown("## Test", group_name)
        output = os.path.join(folder, f"{safe}-知识清单.html")
        success = generate_html(md, output)
        assert success
        assert os.path.exists(output)

    def test_single_deep_file(self, temp_dir):
        """Test with a single file buried deep in nested directories."""
        deep = os.path.join(temp_dir, "a", "b", "c", "d")
        os.makedirs(deep)
        fpath = os.path.join(deep, "hidden.pptx")
        create_sample_pptx(fpath, include_image=False, include_table=False)

        groups = scan_and_group(temp_dir)
        assert deep in groups
        assert len(groups[deep]) == 1

        result = extract_file(fpath)
        assert result['text_summary']

    def test_directory_with_mixed_file_types(self, temp_dir):
        """Test directory containing supported + unsupported files."""
        ch_dir = os.path.join(temp_dir, "Mixed")
        os.makedirs(ch_dir)
        create_sample_pptx(os.path.join(ch_dir, "ok.pptx"))
        create_sample_docx(os.path.join(ch_dir, "ok.docx"))
        create_sample_pdf(os.path.join(ch_dir, "ok.pdf"))
        open(os.path.join(ch_dir, "ignore.txt"), 'w').close()
        open(os.path.join(ch_dir, "ignore.jpg"), 'w').close()
        open(os.path.join(ch_dir, "ignore.py"), 'w').close()

        groups = scan_and_group(temp_dir)
        assert len(groups[ch_dir]) == 3  # Only supported files

    def test_output_exists_detection(self, temp_dir):
        """Test that output_exists correctly detects existing PDFs."""
        open(os.path.join(temp_dir, "第一章-知识清单.html"), 'w').close()
        existing = output_exists(temp_dir, "第一章")
        assert len(existing) >= 1

        nonexistent = output_exists(temp_dir, "第二章")
        assert len(nonexistent) == 0
