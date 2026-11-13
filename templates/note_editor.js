(() => {
  'use strict';

  const toolbar = document.getElementById('epa-note-editor');
  const notes = toolbar?.parentElement.querySelector('.study-notes');
  if (!notes) return;

  // The initial shell retains the quiz, slide rail, styles and executable scripts.
  // Only the persistent notes are replaced at export time.
  const shell = document.documentElement.cloneNode(true);
  const noteId = document.querySelector('meta[name="epa-note-id"]').content;
  let diskRevision = document.querySelector('meta[name="epa-note-revision"]').content;
  const toggle = toolbar.querySelector('[data-action="toggle"]');
  const dirtyBadge = toolbar.querySelector('[data-editor-dirty]');
  const status = toolbar.querySelector('[data-editor-status]');
  const selectionTools = toolbar.querySelector('[data-editor-selection]');
  const dialog = toolbar.querySelector('dialog');
  const form = dialog.querySelector('form');
  const headingInput = form.elements.namedItem('heading');
  const bodyInput = form.elements.namedItem('body');
  const deleteCommentButton = form.querySelector('[data-dialog-delete]');
  const bodyBlocks = 'p,li,td,th,dt,dd,figcaption,pre,div,blockquote,section,article';
  const structural = bodyBlocks + ',h1,h2,h3,h4,h5,h6,header,nav,details,summary,table,ul,ol,dl,figure,hr';
  const fixed = '.pg-chip,.tag-must,.tag-key,.tag-freq,.tag-info,.kc-index,.section-number,[data-section-menu],'
    + '[data-epa-math],math,mjx-container,img,picture,svg,video,iframe,button,input,textarea,select';
  let editing = false;
  let changes = 0;
  let savedChanges = 0;
  let busy = false;
  let handle;
  let lastDeletion;
  let selectedRange;
  let dialogSubmit;
  let dialogDelete;
  let consumedComments = [];

  function node(tag, attrs = {}, text) {
    const element = document.createElement(tag);
    for (const [name, value] of Object.entries(attrs)) element.setAttribute(name, value);
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function markChanged() {
    changes++;
    dirtyBadge.hidden = false;
    setStatus('');
  }

  function headings() {
    return [...notes.querySelectorAll('h2[id],h3[id]')].filter(heading => !heading.closest('.toc'));
  }

  function headingLabel(heading) {
    const label = heading.querySelector('[data-epa-heading-text]').cloneNode(true);
    restoreMath(label);
    return label.textContent.trim() || '未命名小节';
  }

  function sectionFor(heading) {
    const selector = heading.tagName === 'H2' ? '.note-section' : '.kc-card';
    return heading.closest(selector);
  }

  function sectionMenu(heading) {
    if (!sectionFor(heading)) return;
    const menu = node('details', { 'data-section-menu': '', hidden: '' });
    menu.append(node('summary', { 'aria-label': headingLabel(heading) + '：小节菜单' }, '小节菜单'));
    for (const [action, label] of [['add', '在下方添加小节'], ['remove', '删除本节']]) {
      menu.append(node('button', { type: 'button', 'data-section-action': action }, label));
    }
    heading.after(menu);
  }

  function prepareHeadings() {
    for (const heading of headings()) {
      if (!heading.querySelector('[data-epa-heading-text]')) {
        const label = node('span', { 'data-epa-heading-text': '', 'data-epa-editable': '' });
        const children = [...heading.childNodes].filter(child => (
          child.nodeType !== Node.ELEMENT_NODE || !child.matches(fixed)
        ));
        label.append(...children);
        heading.prepend(label);
      }
      if (!heading.nextElementSibling?.matches('[data-section-menu]')) sectionMenu(heading);
    }
  }

  function prepareMath(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    const tex = /\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([^\n]+?\\\)|(?<!\\)\$(?:\\.|[^$\n])+?(?<!\\)\$/g;
    for (const text of textNodes) {
      if (text.parentElement.closest('.toc,code,pre,kbd,samp,script,style,' + fixed)) continue;
      const matches = [...text.data.matchAll(tex)];
      if (!matches.length) continue;
      const fragment = document.createDocumentFragment();
      let offset = 0;
      for (const match of matches) {
        const source = match[0];
        fragment.append(text.data.slice(offset, match.index), node('span', { 'data-epa-math': source }, source));
        offset = match.index + source.length;
      }
      fragment.append(text.data.slice(offset));
      text.replaceWith(fragment);
    }
  }

  function prepareBody(root) {
    for (const block of root.querySelectorAll(bodyBlocks)) {
      if (block.closest('.toc,[data-epa-editable],' + fixed)) continue;
      if (!block.querySelector(structural)) {
        if (block.textContent.trim() || block.matches('p,li,td,th,dt,dd')) {
          block.setAttribute('data-epa-editable', '');
        }
        continue;
      }
      // A block can contain both loose prose and nested lists or paragraphs.
      // Give that prose its own editing host so a deletion can't join blocks.
      let run = [];
      function wrapRun() {
        if (run.some(child => child.textContent.trim())) {
          const span = node('span', { 'data-epa-editable': '' });
          run[0].before(span);
          span.append(...run);
        }
        run = [];
      }
      for (const child of [...block.childNodes]) {
        if (child.nodeType === Node.ELEMENT_NODE && child.matches(structural)) wrapRun();
        else if (child.nodeType !== Node.COMMENT_NODE) run.push(child);
      }
      wrapRun();
    }
  }

  function refreshControls() {
    toggle.textContent = editing ? '完成编辑' : '编辑笔记';
    toggle.setAttribute('aria-pressed', editing);
    for (const host of notes.querySelectorAll('[data-epa-editable]')) {
      if (editing) host.contentEditable = 'true';
      else host.removeAttribute('contenteditable');
    }
    for (const element of notes.querySelectorAll(fixed)) {
      if (editing && element.parentElement.closest('[data-epa-editable]')) element.contentEditable = 'false';
      else element.removeAttribute('contenteditable');
    }
    for (const menu of notes.querySelectorAll('[data-section-menu]')) {
      menu.hidden = !editing;
      if (!editing) menu.open = false;
    }
    toolbar.querySelector('[data-action="add-first"]').hidden = !editing || headings().some(sectionFor);
    toolbar.querySelector('[data-action="undo"]').hidden = !lastDeletion;
  }

  function refreshOutline() {
    let toc = notes.querySelector(':scope > .toc');
    const open = new Set(toc ? [...toc.querySelectorAll('details[open]')]
      .map(group => group.querySelector('summary a')?.getAttribute('href') || '') : []);
    const groups = [];
    for (const heading of headings()) {
      if (heading.tagName === 'H2') groups.push({ heading, children: [] });
      else {
        if (!groups.length) groups.push({ heading: null, children: [] });
        groups.at(-1).children.push(heading);
      }
    }
    if (!groups.length) {
      toc?.remove();
      return;
    }
    if (!toc) {
      toc = node('nav', { class: 'toc', 'aria-label': '章节目录' });
      notes.prepend(toc);
    }
    const link = heading => node('a', { href: '#' + heading.id }, headingLabel(heading));
    toc.replaceChildren(node('div', { class: 'toc-title' }, '章节导航 / Chapter outline'));
    for (const { heading, children } of groups) {
      if (!children.length) {
        const group = node('div', { class: 'toc-group' });
        group.append(link(heading));
        toc.append(group);
        continue;
      }
      const group = node('details', { class: 'toc-group' });
      group.open = open.has(heading ? '#' + heading.id : '');
      const summary = node('summary');
      summary.append(heading ? link(heading) : '知识点 / Concepts',
        node('span', { class: 'toc-count' }, children.length + ' 个知识点 / concepts'));
      const list = node('ul');
      for (const child of children) {
        const item = node('li');
        item.append(link(child));
        list.append(item);
      }
      group.append(summary, list);
      toc.append(group);
    }
  }

  function promptDialog({ title, message = '', heading = false, bodyLabel = '', body = '',
    submit, confirm, remove }) {
    if (dialog.open) dialog.close();
    dialog.returnValue = '';
    form.reset();
    dialog.querySelector('h2').textContent = title;
    form.querySelector('[data-dialog-message]').textContent = message;
    headingInput.closest('label').hidden = !heading;
    headingInput.disabled = !heading;
    const bodyField = bodyInput.closest('label');
    bodyField.hidden = !bodyLabel;
    bodyField.querySelector('span').textContent = bodyLabel;
    bodyInput.value = body;
    form.querySelector('[data-dialog-submit]').textContent = submit;
    deleteCommentButton.hidden = !remove;
    dialogSubmit = confirm;
    dialogDelete = remove;
    dialog.showModal();
    if (heading) headingInput.focus();
    else if (bodyLabel) bodyInput.focus();
    else form.querySelector('[data-dialog-close]').focus();
  }

  function addSection(after, title, body) {
    const isCard = after?.matches('.kc-card');
    const section = node(isCard ? 'article' : 'section', { class: isCard ? 'kc-card' : 'note-section' });
    const header = node('header', { class: isCard ? 'kc-header' : 'section-heading' });
    const heading = node(isCard ? 'h3' : 'h2', { id: 'note-heading-' + crypto.randomUUID() }, title);
    header.append(heading);
    const content = isCard ? node('div', { class: 'kc-content' }) : section;
    section.append(header);
    if (isCard) section.append(content);
    for (const paragraph of body.trim().split(/\n\s*\n/)) {
      const element = node('p');
      paragraph.split('\n').forEach((line, index) => {
        if (index) element.append(node('br'));
        element.append(line);
      });
      content.append(element);
    }
    if (after) after.after(section);
    else notes.append(section);
    prepareHeadings();
    prepareMath(section);
    prepareBody(section);
    refreshOutline();
    refreshControls();
    markChanged();
    heading.querySelector('[data-epa-heading-text]').focus();
    window.MathJax?.typesetPromise?.([section]).catch(() => {});
  }

  function askAdd(after) {
    promptDialog({
      title: after ? '在下方添加小节' : '添加小节', heading: true, bodyLabel: '正文', submit: '添加小节',
      confirm: () => {
        const title = headingInput.value.trim();
        if (!title) {
          headingInput.focus();
          return;
        }
        const body = bodyInput.value;
        dialog.close();
        addSection(after, title, body);
      }
    });
  }

  function askDelete(heading, section) {
    const title = headingLabel(heading);
    promptDialog({
      title: '删除本节', message: '将删除「' + title + '」及本节内容。', submit: '删除本节',
      confirm: () => {
        dialog.close();
        lastDeletion?.placeholder.remove();
        const placeholder = document.createComment('epa-deleted-section');
        section.replaceWith(placeholder);
        lastDeletion = { placeholder, section };
        refreshOutline();
        refreshControls();
        markChanged();
        setStatus('已删除「' + title + '」。');
        toolbar.querySelector('[data-action="undo"]').focus();
      }
    });
  }

  function undoDelete() {
    if (!lastDeletion) return;
    lastDeletion.placeholder.replaceWith(lastDeletion.section);
    lastDeletion = null;
    refreshOutline();
    refreshControls();
    markChanged();
    setStatus('已撤销删除。');
  }

  function elementAt(container) {
    return container.nodeType === Node.ELEMENT_NODE ? container : container.parentElement;
  }

  function bodyText(element) {
    return notes.contains(element) && !element.closest('.toc,h1,h2,h3,summary,' + fixed);
  }

  function textSlices(range) {
    if (!range || range.collapsed || !notes.contains(range.commonAncestorContainer)) return [];
    const root = range.commonAncestorContainer;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const slices = [];
    for (let text = root.nodeType === Node.TEXT_NODE ? root : walker.nextNode(); text; text = walker.nextNode()) {
      if (!bodyText(text.parentElement) || !range.intersectsNode(text)) continue;
      const from = range.startContainer === text ? range.startOffset : 0;
      const to = range.endContainer === text ? range.endOffset : text.length;
      if (to > from) slices.push({ text, from, to });
    }
    return slices;
  }

  function hideSelectionTools() {
    selectedRange = null;
    selectionTools.hidden = true;
  }

  function showSelectionTools() {
    if (dialog.open || selectionTools.contains(document.activeElement)) return;
    const selection = window.getSelection();
    const range = selection.rangeCount ? selection.getRangeAt(0) : null;
    if (!editing || !range || !bodyText(elementAt(range.startContainer))
        || !bodyText(elementAt(range.endContainer))
        || !textSlices(range).some(({ text, from, to }) => text.data.slice(from, to).trim())) {
      hideSelectionTools();
      return;
    }
    selectedRange = range.cloneRange();
    selectionTools.hidden = false;
    const rect = range.getClientRects()[0] || range.getBoundingClientRect();
    const x = Math.max(6, Math.min(rect.left, innerWidth - selectionTools.offsetWidth - 6));
    const height = selectionTools.offsetHeight;
    const y = Math.max(6, Math.min(rect.top - height - 5 < 6 ? rect.bottom + 5 : rect.top - height - 5,
      innerHeight - height - 6));
    selectionTools.style.left = x + 'px';
    selectionTools.style.top = y + 'px';
  }

  function wrapSlices(range, attrs, skipSelector) {
    let count = 0;
    for (const { text, from, to } of textSlices(range).reverse()) {
      if (!text.data.slice(from, to).trim() || (skipSelector && text.parentElement.closest(skipSelector))) continue;
      const slice = document.createRange();
      slice.setStart(text, from);
      slice.setEnd(text, to);
      slice.surroundContents(node('span', attrs));
      count++;
    }
    return count;
  }

  function removeHighlights(range) {
    const marks = [...notes.querySelectorAll('[data-epa-highlight]')].filter(mark => range.intersectsNode(mark));
    const replacements = [];
    for (const mark of marks) {
      const middle = document.createRange();
      middle.selectNodeContents(mark);
      if (mark.contains(range.startContainer)) middle.setStart(range.startContainer, range.startOffset);
      if (mark.contains(range.endContainer)) middle.setEnd(range.endContainer, range.endOffset);
      if (middle.collapsed) continue;
      const prefix = middle.cloneRange();
      prefix.setStart(mark, 0);
      prefix.setEnd(middle.startContainer, middle.startOffset);
      const suffix = middle.cloneRange();
      suffix.setStart(middle.endContainer, middle.endOffset);
      suffix.setEnd(mark, mark.childNodes.length);
      const left = mark.cloneNode();
      const right = mark.cloneNode();
      left.append(prefix.cloneContents());
      right.append(suffix.cloneContents());
      let unmarked = middle.cloneContents();
      // Range.cloneContents omits the common ancestor and its parents.
      // Restore inline formatting and comment marks inside the highlight.
      for (let parent = elementAt(middle.commonAncestorContainer); parent !== mark; parent = parent.parentElement) {
        const copy = parent.cloneNode();
        copy.append(unmarked);
        unmarked = copy;
      }
      replacements.push([mark, left.textContent ? left : '', unmarked, right.textContent ? right : '']);
    }
    for (const [mark, ...parts] of replacements) mark.replaceWith(...parts);
    return replacements.length;
  }

  function commentPieces(id) {
    return [...notes.querySelectorAll('[data-epa-comment]')].filter(mark => mark.dataset.epaComment === id);
  }

  function dropCommentMark(mark) {
    mark.replaceWith(...mark.childNodes);
  }

  function askComment(range, existing) {
    const id = existing?.dataset.epaComment || crypto.randomUUID();
    const pieces = existing ? commentPieces(id) : [];
    if (!existing && textSlices(range).some(({ text }) => text.parentElement.closest('[data-epa-comment]'))) {
      setStatus('选区已有批注。点击批注标记查看或编辑。');
      return;
    }
    const quote = existing ? pieces.map(mark => mark.textContent).join(' ') : range.toString().trim();
    promptDialog({
      title: existing ? '查看和编辑批注' : '添加批注',
      message: '「' + (quote.length > 180 ? quote.slice(0, 180) + '…' : quote) + '」',
      bodyLabel: '批注', body: existing?.dataset.epaCommentText || '', submit: '保存批注',
      confirm: () => {
        const text = bodyInput.value.trim();
        if (!text) {
          bodyInput.focus();
          return;
        }
        dialog.close();
        if (existing) {
          for (const piece of pieces) piece.dataset.epaCommentText = text;
          markChanged();
        } else if (wrapSlices(range, {
          'data-epa-comment': id, 'data-epa-comment-text': text, tabindex: '0', role: 'button',
          'aria-label': '查看批注'
        })) {
          markChanged();
        }
      },
      remove: existing && (() => {
        dialog.close();
        for (const piece of pieces) dropCommentMark(piece);
        markChanged();
      })
    });
  }

  function cleanEmptyMarks(root) {
    for (const mark of root.querySelectorAll('[data-epa-comment],[data-epa-highlight]')) {
      if (!mark.textContent.trim()) dropCommentMark(mark);
    }
  }

  function restoreMath(root) {
    for (const math of root.querySelectorAll('[data-epa-math]')) math.textContent = math.dataset.epaMath;
  }

  function exportHtml(id, revision) {
    const page = shell.cloneNode(true);
    const content = notes.cloneNode(true);
    for (const item of content.querySelectorAll('[data-section-menu]')) item.remove();
    for (const item of content.querySelectorAll('[contenteditable]')) item.removeAttribute('contenteditable');
    for (const item of content.querySelectorAll('details[open]')) item.open = false;
    restoreMath(content);
    const comments = document.createTreeWalker(content, NodeFilter.SHOW_COMMENT);
    const placeholders = [];
    while (comments.nextNode()) {
      if (comments.currentNode.data === 'epa-deleted-section') placeholders.push(comments.currentNode);
    }
    for (const placeholder of placeholders) placeholder.remove();
    cleanEmptyMarks(content);
    page.querySelector('.study-notes').replaceWith(content);
    page.querySelector('meta[name="epa-note-id"]').content = id;
    page.querySelector('meta[name="epa-note-revision"]').content = revision;
    return '<!DOCTYPE html>\n' + page.outerHTML;
  }

  function setBusy(value) {
    busy = value;
    for (const action of ['save', 'download']) toolbar.querySelector('[data-action="' + action + '"]').disabled = value;
  }

  async function verifyFile(target) {
    const file = await target.getFile();
    const currentName = location.protocol === 'file:' ? decodeURIComponent(location.pathname.split('/').pop()) : '';
    if (!/\.html$/i.test(file.name) || (currentName && currentName.toLowerCase() !== file.name.toLowerCase())) {
      throw new Error('请选择当前笔记对应的 HTML 文件。所选文件：' + file.name + '。');
    }
    // Read only the metadata at the start, without parsing or loading the target's resources.
    const header = await file.slice(0, 8192).text();
    const id = header.match(/<meta name="epa-note-id" content="([\w-]+)">/)?.[1];
    const revision = header.match(/<meta name="epa-note-revision" content="([\w-]+)">/)?.[1];
    if (id !== noteId) throw new Error('所选文件与当前笔记不匹配：' + file.name + '。');
    if (revision !== diskRevision) throw new Error('磁盘上的笔记已更新，请重新打开原文件。');
  }

  function saveFailed(error, choosing = false) {
    const message = error.name === 'AbortError' ? (choosing ? '已取消保存到原文件。' : '写入文件已中止。')
      : error.name === 'NotAllowedError' ? '未获得文件写入权限。'
      : error.name === 'SecurityError' ? '浏览器阻止了本地文件访问。'
      : error.name === 'NoModificationAllowedError' ? '另一个页面正在写入该文件，请稍后重试。'
      : error.message || '写入文件失败。';
    setStatus(message + ' 当前编辑已保留，可使用「另存为 HTML」。');
    setBusy(false);
  }

  async function writeOriginal(target) {
    let stream;
    try {
      const permissions = { mode: 'readwrite' };
      if (await target.queryPermission(permissions) !== 'granted'
          && await target.requestPermission(permissions) !== 'granted') {
        throw new DOMException('Write permission denied', 'NotAllowedError');
      }
      stream = await target.createWritable({ mode: 'exclusive' });
      await verifyFile(target);
      const revision = crypto.randomUUID();
      const writtenChanges = changes;
      const html = exportHtml(noteId, revision);
      setStatus('正在写入 ' + target.name + '…');
      await stream.write(html);
      await stream.close();
      handle = target;
      diskRevision = revision;
      savedChanges = writtenChanges;
      dirtyBadge.hidden = savedChanges === changes;
      setStatus('已保存到原文件：' + target.name);
      setBusy(false);
    } catch (error) {
      if (stream) await stream.abort().catch(() => {});
      saveFailed(error);
    }
  }

  async function saveOriginal() {
    if (busy) return;
    if (typeof window.showOpenFilePicker !== 'function') {
      setStatus('此浏览器不支持保存到原文件。请使用「另存为 HTML」。');
      return;
    }
    setBusy(true);
    if (handle) {
      await writeOriginal(handle);
      return;
    }
    try {
      const [target] = await window.showOpenFilePicker({
        id: 'epa-original-notes',
        excludeAcceptAllOption: true,
        types: [{ description: 'HTML 笔记', accept: { 'text/html': ['.html'] } }]
      });
      await verifyFile(target);
      promptDialog({
        title: '保存到原文件', message: '目标文件：' + target.name, submit: '确认写入',
        confirm: () => {
          dialog.close('write');
          void writeOriginal(target);
        }
      });
      dialog.addEventListener('close', () => {
        if (dialog.returnValue !== 'write') saveFailed(new DOMException('Canceled', 'AbortError'), true);
      }, { once: true });
    } catch (error) {
      saveFailed(error, true);
    }
  }

  function downloadCopy() {
    const title = document.title.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').trim() || '复习笔记';
    const html = exportHtml(crypto.randomUUID(), crypto.randomUUID());
    const url = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }));
    const link = node('a', { href: url, download: title + '-副本.html' });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
    setStatus('已发起副本下载。');
  }

  function printNotes() {
    if (document.body.hasAttribute('data-epa-print-notes')) return;
    const answers = notes.querySelectorAll('details.cp-answer:not([open])');
    for (const answer of answers) answer.open = true;
    document.body.setAttribute('data-epa-print-notes', '');
    window.addEventListener('afterprint', () => {
      for (const answer of answers) answer.open = false;
      document.body.removeAttribute('data-epa-print-notes');
    }, { once: true });
    window.print();
  }

  prepareHeadings();
  prepareMath(notes);
  prepareBody(notes);
  refreshControls();

  form.addEventListener('submit', event => {
    event.preventDefault();
    dialogSubmit?.();
  });
  deleteCommentButton.addEventListener('click', () => dialogDelete?.());
  form.querySelector('[data-dialog-close]').addEventListener('click', () => dialog.close('cancel'));
  dialog.addEventListener('close', hideSelectionTools);
  selectionTools.addEventListener('pointerdown', event => event.preventDefault());
  document.addEventListener('selectionchange', showSelectionTools);
  window.addEventListener('resize', showSelectionTools);
  window.addEventListener('scroll', showSelectionTools, { passive: true });

  toolbar.addEventListener('click', event => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (action === 'toggle') {
      editing = !editing;
      hideSelectionTools();
      refreshControls();
    } else if (action === 'add-first') askAdd(null);
    else if (action === 'undo') undoDelete();
    else if (action === 'save') void saveOriginal();
    else if (action === 'download') downloadCopy();
    else if (action === 'print') printNotes();
    else if (editing && selectedRange && ['highlight', 'unhighlight', 'comment'].includes(action)) {
      const range = selectedRange;
      hideSelectionTools();
      if (action === 'comment') askComment(range);
      else {
        const changed = action === 'highlight'
          ? wrapSlices(range, { 'data-epa-highlight': '' }, '[data-epa-highlight]')
          : removeHighlights(range);
        if (changed) markChanged();
        window.getSelection().removeAllRanges();
      }
    }
  });

  notes.addEventListener('click', event => {
    const action = event.target.closest('[data-section-action]');
    if (editing && action) {
      const menu = action.closest('[data-section-menu]');
      const heading = menu.previousElementSibling;
      menu.open = false;
      const section = sectionFor(heading);
      if (action.dataset.sectionAction === 'add') askAdd(section);
      else askDelete(heading, section);
      return;
    }
    const comment = event.target.closest('[data-epa-comment]');
    if (comment && window.getSelection().isCollapsed) askComment(null, comment);
  });
  notes.addEventListener('keydown', event => {
    if (event.target === document.activeElement && event.target.matches('[data-epa-comment]')
        && ['Enter', ' '].includes(event.key)) {
      event.preventDefault();
      askComment(null, event.target);
    }
  });

  function recordReplacement(host, target) {
    consumedComments = [];
    if (target && (!host.contains(target.startContainer) || !host.contains(target.endContainer))) return false;
    if (target && !target.collapsed) {
      const range = document.createRange();
      range.setStart(target.startContainer, target.startOffset);
      range.setEnd(target.endContainer, target.endOffset);
      if ([...host.querySelectorAll(fixed)].some(element => range.intersectsNode(element))) {
        return false;
      }
      consumedComments = [...host.querySelectorAll('[data-epa-comment]')].filter(mark => {
        const walker = document.createTreeWalker(mark, NodeFilter.SHOW_TEXT);
        const first = walker.nextNode();
        if (!first) return false;
        let last = first;
        while (walker.nextNode()) last = walker.currentNode;
        const markRange = document.createRange();
        markRange.setStart(first, 0);
        markRange.setEnd(last, last.length);
        return range.compareBoundaryPoints(Range.START_TO_START, markRange) <= 0
          && range.compareBoundaryPoints(Range.END_TO_END, markRange) >= 0;
      });
    }
    return true;
  }

  notes.addEventListener('beforeinput', event => {
    if (!editing) return;
    const host = event.target.closest('[data-epa-editable]');
    if (!host) return;
    if (!recordReplacement(host, event.getTargetRanges?.()[0])) {
      event.preventDefault();
      return;
    }
    if (event.inputType === 'insertParagraph' || event.inputType === 'insertLineBreak') {
      event.preventDefault();
      if (!host.matches('[data-epa-heading-text]')) {
        document.execCommand('insertLineBreak');
      }
    } else if (event.inputType.startsWith('format') || event.inputType === 'insertFromDrop') {
      event.preventDefault();
    }
  });
  notes.addEventListener('paste', event => {
    const host = event.target.closest('[data-epa-editable]');
    if (!editing || !host) return;
    event.preventDefault();
    const value = event.clipboardData.getData('text/plain');
    const range = window.getSelection().rangeCount ? window.getSelection().getRangeAt(0) : null;
    if (!recordReplacement(host, range)) return;
    if (!value) return;
    if (host.matches('[data-epa-heading-text]') || !/[\r\n]/.test(value)) {
      document.execCommand('insertText', false,
        host.matches('[data-epa-heading-text]') ? value.replace(/\s+/g, ' ') : value);
      return;
    }
    const text = node('span');
    value.split(/\r\n?|\n/).forEach((line, index) => {
      if (index) text.append(node('br'));
      text.append(line);
    });
    document.execCommand('insertHTML', false, text.innerHTML);
  });
  notes.addEventListener('input', event => {
    if (!editing || !event.target.closest('[data-epa-editable]')) return;
    for (const mark of consumedComments) {
      if (notes.contains(mark)) dropCommentMark(mark);
    }
    consumedComments = [];
    cleanEmptyMarks(event.target);
    const heading = event.target.closest('h2,h3');
    if (heading) {
      heading.nextElementSibling?.querySelector('summary')?.setAttribute('aria-label', headingLabel(heading) + '：小节菜单');
      refreshOutline();
    }
    markChanged();
  });
  window.addEventListener('beforeunload', event => {
    if (changes === savedChanges) return;
    event.preventDefault();
    event.returnValue = true;
  });
})();
