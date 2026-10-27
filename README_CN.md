# Bilingual-exampass

将 PPTX、DOCX、PDF 课件整理为详细、全面的中英对照复习笔记。

[English](README.md)

## 使用

在 Codex 中调用 `$bilingual-exampass` 并提供课件。未指定输出时，先选择：

| 选项 | 交付 |
| --- | --- |
| 纯笔记 | PDF，保留双语知识卡、笔记内自测与答案、章末词汇表，便于平板批注 |
| 完整笔记 | HTML，包含双语笔记、全部原课件对照、全英文互动章节测验 |
| 两者都要 | 同一正文分别生成纯笔记 PDF 与完整 HTML |

同一批课件沿用所选模式；已经明确选择时不重复询问。

## 笔记标准

逐页核对正文、图表及备注，保留教学原例、条件、数值和限制，展开机制与步骤。所有讲解、自测和答案先中文后英文逐段对应，不添加独立语言标签行。沿用紧凑间距，章末独立列出英文术语和双语解释。独立章节测验及批改报告使用英文。

## 其他用途

- `$bilingual-exampass final <课程目录>`：生成期末或指定章节试卷，支持参考真题。
- `$bilingual-exampass graph <课程目录>`：生成交互式知识图谱。
- `$bilingual-exampass grade <答案JSON路径>`：批改完整HTML导出的作答。

## 目录

- `SKILL.md`：入口、输出选择及工作流程。
- `references/`：内容深度、排版和交付规则。
- `agents/`：各阶段写作及审查指导、技能显示信息。
- `scripts/`、`templates/`：提取、渲染和交互测验。
- `tests/`：现有功能检查；`requirements.txt`：Python依赖。
- `exampass-final.md`、`exampass-graph.md`、`exampass-writing.md`：模式专用指导，文件名作为内部引用保留。

Python依赖可用 `python -m pip install -r requirements.txt` 安装。PPTX整页转换需要本机可用的Microsoft PowerPoint。纯笔记PDF按当前PDF技能或可用本地工具导出；不会为了导出纯笔记额外生成独立题库。

本目录为唯一正式技能。具体执行以 `SKILL.md` 为准。基于原 [ExamPass Assistant](https://github.com/WUBING2023/ExamPass-Assistant) 开发，许可证保留在 `LICENSE`。本版本独立维护，增加详细中英对照笔记、三种输出选择、紧凑排版及英文测验与批改。
