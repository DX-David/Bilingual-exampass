"""Render every chapter into a combined page (knowledge list + PPT rail + quiz).

This is the canonical Phase-4 render for the default flow: the PPT
cross-reference rail is ON by default, sourced from each chapter's
`source_files` recorded in chapter_manifest.json.

Usage: python scripts/render_chapters.py <target_dir> [full|key|none]
"""

import sys, os, json
import base64
import mimetypes
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slide_renderer import build_chapter_slides
from template_engine import save_combined_html


def main(target_dir, density='key'):
    target = os.path.abspath(target_dir)
    epa_work = os.path.join(target, '.epa_work')
    epa_dir = os.path.join(target, 'EPA')
    os.makedirs(epa_dir, exist_ok=True)

    with open(os.path.join(epa_work, 'chapter_manifest.json'), encoding='utf-8-sig') as f:
        manifest = json.load(f)
    skeleton_path = os.path.join(epa_work, 'knowledge_skeleton.json')
    skeleton = None
    if os.path.exists(skeleton_path):
        with open(skeleton_path, encoding='utf-8-sig') as f:
            skeleton = json.load(f)

    # Map skeleton chapter label -> kcs (for heading page chips)
    kcs_by_label = {}
    if skeleton:
        for ch in skeleton.get('chapters', []):
            kcs_by_label[ch.get('label', '')] = ch.get('kcs', [])

    notes_dir = os.path.join(epa_work, 'notes')
    q_dir = os.path.join(epa_work, 'questions')

    made = []
    for ch_label, info in manifest['chapters'].items():
        # notes/questions are keyed by chapter id (ch1..) or label; try both.
        note_path = _find(notes_dir, ch_label, '.html')
        q_path = _find(q_dir, ch_label, '.json')
        if not note_path or not q_path:
            print(f'[skip] {ch_label}: missing notes or questions')
            continue

        note = _embed_local_images(Path(note_path).read_text(encoding='utf-8'), Path(note_path).parent)
        qd = json.load(open(q_path, encoding='utf-8-sig'))
        questions = qd.get('questions', qd if isinstance(qd, list) else [])

        # Full-slide rail accepts PDFs and PowerPoint files from the manifest.
        slide_sources = [p for p in info.get('source_files', []) if p.lower().endswith(('.pdf', '.pptx'))]
        slides = None
        if slide_sources and density != 'none':
            sd = os.path.join(info['work_dir'], '_slides')
            try:
                slides = build_chapter_slides(slide_sources, sd, density=density,
                                              skeleton=skeleton, chapter_label=ch_label)
            except Exception as e:
                print(f'[warn] {ch_label}: slide render failed ({e})')

        kcs = _match_kcs(kcs_by_label, ch_label)
        out = os.path.join(epa_dir, f'{ch_label}.html')
        save_combined_html(note, questions, out, ch_label,
                           slides=slides, kcs=kcs,
                           subtitle=f'{len(questions)} questions')
        made.append((ch_label, len(questions), len(slides) if slides else 0))
        print(f'[ok] {ch_label}: {len(questions)} 题, {len(slides) if slides else 0} 幻灯片')

    print(f'\nRendered {len(made)} combined pages -> {epa_dir}')


def _embed_local_images(note, source_dir):
    """Embed local note illustrations alongside the already embedded slide rail."""
    def replace_src(match):
        prefix, quote, src = match.groups()
        path = Path(src)
        if not path.is_absolute():
            url = urlsplit(src)
            if url.scheme == 'file':
                path = Path(url2pathname(url.path))
            elif url.scheme or url.netloc:
                return match.group()
            else:
                path = source_dir / unquote(url.path)
        media_type, _ = mimetypes.guess_type(path)
        if not media_type or not media_type.startswith('image/'):
            return match.group()
        try:
            encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        except OSError:
            return match.group()
        return f'{prefix}{quote}data:{media_type};base64,{encoded}{quote}'

    return re.sub(r"""(<img\b[^>]*?\s+src\s*=\s*)(["'])(.*?)\2""", replace_src, note,
                  flags=re.IGNORECASE | re.DOTALL)


def _find(d, label, ext):
    """Find a file by chapter label or by a chN id fallback."""
    if not os.path.isdir(d):
        return None
    cand = os.path.join(d, label + ext)
    if os.path.exists(cand):
        return cand
    # fallback: any file whose stem matches a number in the label
    m = re.match(r'\s*(\d+)', label)
    if m:
        cid = 'ch' + m.group(1)
        cand = os.path.join(d, cid + ext)
        if os.path.exists(cand):
            return cand
    return None


def _match_kcs(kcs_by_label, ch_label):
    for label, kcs in kcs_by_label.items():
        if label and (label in ch_label or ch_label in label):
            return kcs
    return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python render_chapters.py <target_dir> [full|key|none]')
        sys.exit(1)
    density = sys.argv[2] if len(sys.argv) > 2 else 'full'
    main(sys.argv[1], density)
