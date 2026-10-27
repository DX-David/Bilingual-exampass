"""Tests for extractor.py — unified extraction dispatcher."""

import os
import pytest
from conftest import create_sample_pptx, create_sample_docx, create_sample_pdf
from extractor import extract_file, merge_group_content


class TestExtractFile:
    def test_pptx(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path)
        result = extract_file(pptx_path)
        assert result['type'] == '.pptx'
        assert len(result['text_summary']) > 0

    def test_docx(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path)
        result = extract_file(docx_path)
        assert result['type'] == '.docx'
        assert len(result['text_summary']) > 0

    def test_pdf(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        result = extract_file(pdf_path)
        assert result['type'] == '.pdf'
        assert len(result['text_summary']) > 0

    def test_unsupported_type(self, temp_dir):
        txt_path = os.path.join(temp_dir, "test.txt")
        open(txt_path, 'w').close()
        with pytest.raises(ValueError):
            extract_file(txt_path)

    def test_with_images(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=True)
        images_dir = os.path.join(temp_dir, "extracted_images")
        os.makedirs(images_dir)
        result = extract_file(pptx_path, image_output_dir=images_dir)
        assert result['type'] == '.pptx'
        assert 'images' in result

    def test_without_image_dir(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path)
        result = extract_file(pptx_path)  # no image_output_dir
        assert result['images'] == []


class TestMergeGroupContent:
    def test_single_file(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path)
        r1 = extract_file(pptx_path)
        merged = merge_group_content([r1])
        assert len(merged) > 0

    def test_multiple_files(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "a.pptx")
        create_sample_pptx(pptx_path, include_image=False)
        docx_path = os.path.join(temp_dir, "b.docx")
        create_sample_docx(docx_path, include_image=False, include_table=False)
        pdf_path = os.path.join(temp_dir, "c.pdf")
        create_sample_pdf(pdf_path)

        r1 = extract_file(pptx_path)
        r2 = extract_file(docx_path)
        r3 = extract_file(pdf_path)
        merged = merge_group_content([r1, r2, r3])
        assert len(merged) > len(r1['text_summary'])
        assert '---' in merged
