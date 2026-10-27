"""Structure legacy flat note fragments without changing their learning content.

Uses only the standard library; explicit note-section/kc-card markup is retained.
"""
from html.parser import HTMLParser

_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
         'link', 'meta', 'param', 'source', 'track', 'wbr'}
_LABELS = {
    '引入': ('先想一想', 'Start here'),
    'Hook': ('先想一想', 'Start here'),
    '一句话结论': ('核心结论', 'Key takeaway'),
    '为什么重要': ('为什么重要', 'Why it matters'),
    '是什么': ('概念与定义', 'Concept and definition'),
    '怎么用': ('应用与步骤', 'Application and steps'),
    '易错': ('易错提醒', 'Common mistake'),
}


class _Node:
    def __init__(self, tag, attrs=None, children=None, opening=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = list(children or [])
        self.opening = opening

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()

    def render(self):
        if not self.tag:
            return ''.join(_render(c) for c in self.children)
        opening = self.opening or '<' + self.tag + ''.join(
            ' ' + k + '="' + v + '"' for k, v in self.attrs.items()) + '>'
        return opening + ('' if self.tag in _VOID or opening.rstrip().endswith('/>') else
                          ''.join(_render(c) for c in self.children) + '</' + self.tag + '>')


def _render(node):
    return node.render() if isinstance(node, _Node) else node


class _FragmentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = _Node('')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, opening=self.get_starttag_text())
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_entityref(self, name):
        self.handle_data('&' + name + ';')

    def handle_charref(self, name):
        self.handle_data('&#' + name + ';')

    def handle_comment(self, data):
        self.handle_data('<!--' + data + '-->')


def _box(tag, cls, children):
    return _Node(tag, [('class', cls)], children)


def _contains_class(node, name):
    return node.has_class(name) or any(
        _contains_class(child, name) for child in node.children if isinstance(child, _Node))


def _pair_paragraphs(node):
    """Group adjacent Chinese/English paragraphs, preserving all inline markup."""
    if node.has_class('bilingual-pair'):
        return
    for child in node.children:
        if isinstance(child, _Node):
            _pair_paragraphs(child)
    out, i = [], 0
    while i < len(node.children):
        zh = node.children[i]
        j = i + 1
        while j < len(node.children) and isinstance(node.children[j], str) and not node.children[j].strip():
            j += 1
        en = node.children[j] if j < len(node.children) else None
        if (isinstance(zh, _Node) and zh.tag == 'p' and
                zh.attrs.get('lang', '').lower().startswith('zh') and
                isinstance(en, _Node) and en.tag == 'p' and
                en.attrs.get('lang', '').lower().startswith('en')):
            label = None
            first = next((c for c in zh.children if isinstance(c, _Node)), None)
            if first is not None and first.tag == 'strong':
                text = ''.join(c for c in first.children if isinstance(c, str)).strip().rstrip('：: ')
                label = _LABELS.get(text)
            pair = _box('div', 'bilingual-pair', [zh, en])
            if label:
                zh.children.remove(first)
                first_en = next((c for c in en.children if isinstance(c, _Node)), None)
                if first_en is not None and first_en.tag == 'strong':
                    en_label = ''.join(c for c in first_en.children if isinstance(c, str)).strip().rstrip('：: ').lower()
                    if en_label in {'hook', 'takeaway', 'key takeaway', 'why it matters',
                                    'what it is', 'how to use it', 'common mistake'}:
                        en.children.remove(first_en)
                pair = _box('div', 'note-block', [
                    _box('div', 'note-label', [label[0] + ' / ' + label[1]]), pair])
            out.append(pair)
            i = j + 1
        else:
            out.append(zh)
            i += 1
    node.children = out


def structure_notes(fragment):
    """Return a scoped note container with sections, knowledge cards and pairs."""
    parser = _FragmentParser()
    parser.feed(fragment)
    parser.close()
    root = parser.root
    # Existing explicit layout is authored by the notes agent; do not nest cards.
    explicit = _contains_class(root, 'kc-card') or _contains_class(root, 'note-section')
    if not explicit:
        out, section, card = [], None, None
        section_number = kc_number = 0
        for node in root.children:
            if isinstance(node, _Node) and node.tag == 'h2':
                section_number += 1
                section = _box('section', 'note-section', [
                    _box('header', 'section-heading', [
                        _box('span', 'section-number', [f'{section_number:02}']), node])])
                out.append(section)
                card = None
            elif isinstance(node, _Node) and node.tag == 'h3':
                kc_number += 1
                content = _box('div', 'kc-content', [])
                article = _box('article', 'kc-card', [
                    _box('header', 'kc-header', [
                        _box('div', 'kc-index', [f'知识点 {kc_number:02} / Knowledge point']), node]), content])
                (section.children if section is not None else out).append(article)
                card = content
            elif isinstance(node, _Node) and node.has_class('checkpoint'):
                # Chapter checks belong to the section, rather than the last KC.
                (section.children if section is not None else out).append(node)
                card = None
            else:
                target = card.children if card is not None else section.children if section is not None else out
                if isinstance(node, _Node) and node.tag == 'table':
                    node = _box('div', 'table-scroll', [node])
                target.append(node)
        root.children = out
    _pair_paragraphs(root)
    rendered = root.render()
    if not _contains_class(root, 'study-notes'):
        rendered = '<div class="study-notes">' + rendered + '</div>'
    return rendered
