"""Tests for extract_pptx.py."""

import os
import pytest
from conftest import create_sample_pptx
from extract_pptx import extract_pptx, build_text_summary, extract_text_from_shape


class TestExtractPPTX:
    def test_basic_extraction(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=False, include_table=False)
        data = extract_pptx(pptx_path)
        assert data['total_slides'] >= 1
        assert 'slides' in data
        assert data['filename'] == "test.pptx"

    def test_slide_structure(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=False, include_table=False)
        data = extract_pptx(pptx_path)
        for slide in data['slides']:
            assert 'number' in slide
            assert isinstance(slide['number'], int)
            assert 'text' in slide
            assert 'tables' in slide
            assert 'image_count' in slide
            assert 'notes' in slide

    def test_title_extraction(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path)
        data = extract_pptx(pptx_path)
        titles = [s['title'] for s in data['slides'] if s['title']]
        assert len(titles) >= 1

    def test_table_extraction(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=False, include_table=True)
        data = extract_pptx(pptx_path)
        tables_found = any(s['tables'] for s in data['slides'])
        assert tables_found

    def test_image_count(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=True, include_table=False)
        data = extract_pptx(pptx_path)
        total_images = sum(s['image_count'] for s in data['slides'])
        assert total_images >= 1

    def test_all_content(self, temp_dir):
        """Test with both images and tables."""
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=True, include_table=True)
        data = extract_pptx(pptx_path)
        assert data['total_slides'] >= 4

    def test_text_summary(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path)
        data = extract_pptx(pptx_path)
        summary = build_text_summary(data)
        assert len(summary) > 0
        assert data['filename'] in summary


class TestCorruptedFile:
    def test_nonexistent_file(self):
        with pytest.raises(Exception):
            extract_pptx("/nonexistent/file.pptx")
