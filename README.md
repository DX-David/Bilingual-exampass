# Bilingual-exampass

Create detailed Chinese-English study notes from PPTX, DOCX, and PDF course materials.

[中文](README_CN.md)

## Use

Invoke `$bilingual-exampass` in Codex and provide course materials. If no output was specified, choose one of three options:

| Option | Deliverable |
| --- | --- |
| Notes only | An annotatable PDF with bilingual cards, in-note checks and expanded answers, and a glossary |
| Complete notes | HTML with bilingual notes, all original slide pages, and an English interactive quiz |
| Both | A notes-only PDF and complete HTML sharing the same notes source |

An explicit choice is used directly; the same batch reuses its confirmed selection.

## Content and layout

Review original text, figures, tables, and speaker notes page by page. Preserve teaching examples, conditions, values, limitations, and mechanisms. Pair every Chinese explanation with its English counterpart without standalone language-label rows. Use the established compact spacing. End each chapter with a bilingual glossary. Independent quizzes and grading reports use English.

## Other modes

- `$bilingual-exampass final <course directory>`: final or chapter exams, optionally referencing a past paper.
- `$bilingual-exampass graph <course directory>`: interactive knowledge graphs.
- `$bilingual-exampass grade <answers JSON>`: grade answers exported from complete HTML.

## Files

`SKILL.md` is the entry point. `references/` contains output, depth, and layout rules. `agents/` contains stage guidance and display metadata. `scripts/` and `templates/` support extraction and rendering; `tests/` retains functional checks. Internal mode references keep the filenames `exampass-final.md`, `exampass-graph.md`, and `exampass-writing.md`.

Install Python dependencies with `python -m pip install -r requirements.txt` when needed. Full-slide PPTX conversion requires local Microsoft PowerPoint. Export notes-only PDFs using the available PDF skill or local PDF tools without requiring an independent question bank.

This folder is the sole official skill. Follow `SKILL.md` for the current workflow. Derived from [ExamPass Assistant](https://github.com/WUBING2023/ExamPass-Assistant); the original license is retained in `LICENSE`. This independently maintained adaptation adds detailed Chinese-English notes, three output choices, compact layouts, and English quizzes and grading.
