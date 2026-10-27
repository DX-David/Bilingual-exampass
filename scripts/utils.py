"""ExamPass shared utilities."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

SUPPORTED_EXTENSIONS = {'.pptx', '.ppt', '.docx', '.doc', '.pdf'}
OUTPUT_SUFFIX_KNOWLEDGE = '-知识清单'
OUTPUT_SUFFIX_TEST = '-章节测试'
OUTPUT_SUFFIX_ANSWER = '-章节测试-答案'
FINAL_EXAM_PREFIX = '期末考试'


def is_supported(filepath: str) -> bool:
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS


def make_temp_dir(prefix: str = "exampass_") -> str:
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp(tmpdir: str) -> None:
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir, ignore_errors=True)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def safe_filename(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, '_')
    return name.strip()


def output_exists(directory: str, basename: str) -> List[str]:
    existing = []
    patterns = [
        f"{basename}{OUTPUT_SUFFIX_KNOWLEDGE}.html",
        f"{basename}{OUTPUT_SUFFIX_TEST}.html",
        f"{basename}{OUTPUT_SUFFIX_ANSWER}.html",
    ]
    for p in patterns:
        full = os.path.join(directory, p)
        if os.path.exists(full):
            existing.append(full)
    return existing
