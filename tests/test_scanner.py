"""Tests for scanner.py."""

import os
import pytest
import tempfile
from scanner import scan_and_group, get_group_name, is_supported


class TestIsSupported:
    def test_pptx(self):
        assert is_supported("a.pptx")

    def test_docx(self):
        assert is_supported("b.docx")

    def test_pdf(self):
        assert is_supported("c.pdf")

    def test_unsupported(self):
        assert not is_supported("d.txt")
        assert not is_supported("e.jpg")
        assert not is_supported("f.py")

    def test_case_insensitive(self):
        assert is_supported("A.PPTX")
        assert is_supported("B.PDF")


class TestScanAndGroup:
    def test_empty_dir(self, temp_dir):
        groups = scan_and_group(temp_dir)
        assert groups == {}

    def test_single_file_in_root(self, temp_dir):
        path = os.path.join(temp_dir, "test.pptx")
        open(path, 'w').close()
        groups = scan_and_group(temp_dir)
        assert temp_dir in groups
        assert len(groups[temp_dir]) == 1

    def test_multiple_files_same_dir(self, temp_dir):
        open(os.path.join(temp_dir, "a.pptx"), 'w').close()
        open(os.path.join(temp_dir, "b.pdf"), 'w').close()
        open(os.path.join(temp_dir, "c.docx"), 'w').close()
        open(os.path.join(temp_dir, "ignore.txt"), 'w').close()
        groups = scan_and_group(temp_dir)
        assert len(groups[temp_dir]) == 3

    def test_nested_dirs(self, temp_dir):
        ch1 = os.path.join(temp_dir, "第一章")
        ch2 = os.path.join(temp_dir, "第二章")
        os.makedirs(ch1)
        os.makedirs(ch2)
        open(os.path.join(ch1, "lecture.pptx"), 'w').close()
        open(os.path.join(ch1, "reading.pdf"), 'w').close()
        open(os.path.join(ch2, "slides.docx"), 'w').close()
        groups = scan_and_group(temp_dir)
        assert ch1 in groups
        assert ch2 in groups
        assert len(groups[ch1]) == 2
        assert len(groups[ch2]) == 1

    def test_deep_nesting(self, temp_dir):
        deep = os.path.join(temp_dir, "a", "b", "c")
        os.makedirs(deep)
        open(os.path.join(deep, "deep_file.pdf"), 'w').close()
        groups = scan_and_group(temp_dir)
        assert deep in groups
        assert len(groups[deep]) == 1

    def test_mixed_supported_and_unsupported(self, temp_dir):
        open(os.path.join(temp_dir, "ok.pptx"), 'w').close()
        open(os.path.join(temp_dir, "not.txt"), 'w').close()
        open(os.path.join(temp_dir, "also_not.jpg"), 'w').close()
        groups = scan_and_group(temp_dir)
        assert len(groups[temp_dir]) == 1

    def test_chinese_filename(self, temp_dir):
        open(os.path.join(temp_dir, "机器学习课件.pptx"), 'w').close()
        groups = scan_and_group(temp_dir)
        assert len(groups[temp_dir]) == 1


class TestGetGroupName:
    def test_subfolder(self):
        assert get_group_name("/root/chapter1", "/root") == "chapter1"

    def test_root_folder(self):
        assert get_group_name("/root", "/root") == "root"

    def test_chinese_name(self):
        assert get_group_name("/root/第一章", "/root") == "第一章"
