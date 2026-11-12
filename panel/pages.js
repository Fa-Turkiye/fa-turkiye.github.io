import {
  applyLayout, blankLayout, blockName, indexLayout, isSitePage, orderedBlocks, readLayout,
} from '../page-layout.js';

const byId = id => document.getElementById(id);
const list = byId('page-list');
const search = byId('page-search');
const frame = byId('page-preview');
const heading = byId('page-title');
const status = byId('page-status');
const save = byId('page-save');
const publish = byId('page-publish');
const properties = byId('page-properties');
const fields = byId('page-fields');
const moveUp = byId('page-up');
const moveDown = byId('page-down');
const sectionSelect = byId('page-section');
const orderList = byId('page-order');

function unwrap({ data, error }) {
  if (error) throw error;
  return data;
}

export function createPageWorkspace(client) {
  const drafts = new Map();
  let pages = [];
  let request = 0;
  let opened = false;
  let loading = false;
  let pending = false;
  let selected = null;
  let index = null;
  let fieldEntry = null;
  let block = null;
  let orderGroup = null;
  let drag = null;
  let dropBlock = null;

  function say(text) {
    status.textContent = text;
  }

  function controls() {
    save.disabled = !index || pending || !selected?.dirty;
    publish.disabled = !index || pending || !selected ||
      (!selected.dirty && (selected.revision === null || selected.revision === selected.published));
    properties.inert = pending;
    list.inert = pending;
    orderList.inert = pending;

    const order = block ? orderedBlocks(block.group, selected.settings.order[block.group.key]) : [];
    const position = order.indexOf(block);
    moveUp.disabled = pending || position < 1;
    moveDown.disabled = pending || position < 0 || position === order.length - 1;
  }

  function describe() {
    if (selected.dirty) say('Kaydedilmemiş değişiklikler var.');
    else if (selected.revision === null) say('Sitedeki mevcut görünüm.');
    else if (selected.revision === selected.published) say('Bu düzen yayında.');
    else say('Taslak kaydedildi. Yayın için Düzeni yayımla düğmesini kullan.');
  }

  function renderList() {
    const query = search.value.trim().toLocaleLowerCase('tr-TR');
    const visible = pages.filter(page => (page.title + ' ' + page.path).toLocaleLowerCase('tr-TR').includes(query));
    const items = visible.map(page => {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.path = page.path;
      button.textContent = page.title;
      if (page.path === selected?.page.path) button.setAttribute('aria-current', 'page');
      button.addEventListener('click', () => openPage(page));
      item.append(button);
      return item;
    });
    if (!items.length) {
      const item = document.createElement('li');
      item.textContent = 'Eşleşen sayfa yok.';
      items.push(item);
    }
    list.replaceChildren(...items);
  }

  function clearSelection() {
    block?.element.removeAttribute('data-fa-selected');
    fieldEntry?.element.removeAttribute('data-fa-field-selected');
    block = null;
    fieldEntry = null;
    fields.replaceChildren();
    properties.hidden = true;
    sectionSelect.value = '';
    byId('page-selection-note').hidden = false;
  }

  function markChange() {
    selected.dirty = true;
    describe();
    controls();
  }

  function selectEntry(entry, focus = false) {
    clearSelection();
    fieldEntry = entry.fields.length ? entry : null;
    for (let target = entry.element; target && !block; target = target.parentElement) {
      const candidate = index.elements.get(target);
      if (candidate?.group) block = candidate;
    }
    if (block) orderGroup = block.group;
    block?.element.setAttribute('data-fa-selected', '');
    fieldEntry?.element.setAttribute('data-fa-field-selected', '');
    sectionSelect.value = block?.key ?? '';
    byId('page-selection-note').hidden = true;
    properties.hidden = false;
    byId('page-selected-label').textContent = blockName(entry);
    byId('page-move').hidden = !block;

    for (const field of entry.fields) {
      const label = document.createElement('label');
      label.textContent = field.label;
      const input = document.createElement(field.label.startsWith('Metin') ? 'textarea' : 'input');
      const change = selected.settings.fields[field.id];
      input.value = change?.base === field.base && typeof change.value === 'string' && field.valid(change.value)
        ? change.value : field.base;
      if (input.tagName === 'TEXTAREA') input.rows = input.value.length > 90 ? 4 : 2;
      input.maxLength = field.label.endsWith('adresi') ? 2048 : 16000;
      input.addEventListener('input', () => {
        const value = input.value;
        const valid = field.valid(value);
        input.setCustomValidity(valid ? '' : 'Geçerli bir adres veya metin gir.');
        if (!valid) return;
        const previous = selected.settings.fields[field.id];
        if (previous?.value === value || (!previous && value === field.base)) return;
        if (value === field.base) delete selected.settings.fields[field.id];
        else selected.settings.fields[field.id] = { base: field.base, value };
        field.write(value);
        field.current = value;
        markChange();
      });
      label.append(input);
      fields.append(label);
    }

    renderOrder();
    controls();
    if (focus) (fields.querySelector('textarea, input') ?? byId('page-selected-label')).focus();
  }

  function renderOrder() {
    byId('page-order-region').hidden = !orderGroup;
    orderList.replaceChildren();
    if (!orderGroup) return;
    const entries = orderedBlocks(orderGroup, selected.settings.order[orderGroup.key]);
    let source = null;
    for (const entry of entries) {
      const item = document.createElement('li');
      const handle = document.createElement('button');
      handle.type = 'button';
      handle.draggable = true;
      handle.textContent = blockName(entry);
      if (entry === block) handle.setAttribute('aria-current', 'true');
      handle.addEventListener('click', () => {
        entry.element.scrollIntoView({ block: 'center', inline: 'nearest' });
        selectEntry(entry, true);
      });
      handle.addEventListener('dragstart', event => {
        source = entry;
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', blockName(entry));
      });
      handle.addEventListener('dragend', () => { source = null; });
      item.addEventListener('dragover', event => {
        if (!source || source === entry) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
      });
      item.addEventListener('drop', event => {
        if (!source || source === entry) return;
        event.preventDefault();
        move(source, entry, entries.indexOf(source) < entries.indexOf(entry));
      });
      item.append(handle);
      orderList.append(item);
    }
  }

  function move(source, target, after) {
    if (pending || !source || !target || source === target || source.group !== target.group) return;
    const group = source.group;
    const order = orderedBlocks(group, selected.settings.order[group.key]).filter(entry => entry !== source);
    order.splice(order.indexOf(target) + Number(after), 0, source);
    if (order.every((entry, i) => entry === group.blocks[i])) delete selected.settings.order[group.key];
    else selected.settings.order[group.key] = order.map(entry => entry.key);
    applyLayout(index, selected.settings);
    renderOrder();
    markChange();
  }

  function moveSelected(direction) {
    if (!block) return;
    const order = orderedBlocks(block.group, selected.settings.order[block.group.key]);
    const position = order.indexOf(block);
    const target = order[position + direction];
    if (!target) return;
    move(block, target, direction > 0);
    const next = direction < 0 ? moveUp : moveDown;
    (next.disabled ? (direction < 0 ? moveDown : moveUp) : next).focus();
  }

  function clearDrag() {
    drag?.element.removeAttribute('data-fa-dragging');
    dropBlock?.element.removeAttribute('data-fa-drop');
    drag = null;
    dropBlock = null;
  }

  function attachEditing(doc) {
    const css = doc.createElement('link');
    css.rel = 'stylesheet';
    css.href = new URL('./preview.css', location.href).href;
    doc.head.append(css);

    const options = [new Option('Bölüm seç', '')];
    for (const entry of index.entries.values()) {
      if (entry.fields.length || entry.group) {
        entry.element.dataset.faEditable = '';
        if (entry.fields.length && !entry.element.hasAttribute('tabindex')) entry.element.tabIndex = 0;
      }
      if (entry.group) {
        entry.element.draggable = true;
        entry.element.dataset.faBlock = '';
        options.push(new Option(blockName(entry), entry.key));
      } else if (entry.element.matches('a, img')) entry.element.draggable = false;
    }
    sectionSelect.replaceChildren(...options);

    function pick(event) {
      const target = event.target.closest?.('[data-fa-editable]');
      if (event.target.closest?.('a') || target) event.preventDefault();
      if (!target || pending) return;
      const summary = event.target.closest('summary');
      if (summary?.parentElement.matches('details')) summary.parentElement.open = true;
      selectEntry(index.elements.get(target), true);
    }

    doc.addEventListener('click', pick, true);
    doc.addEventListener('keydown', event => {
      if ((event.key === 'Enter' || event.key === ' ') && event.target.closest?.('[data-fa-editable]')) pick(event);
    }, true);
    doc.addEventListener('submit', event => event.preventDefault(), true);
    doc.addEventListener('dragstart', event => {
      const entry = index.elements.get(event.target);
      if (pending || !entry?.group) return;
      drag = entry;
      entry.element.setAttribute('data-fa-dragging', '');
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', blockName(entry));
    });
    doc.addEventListener('dragover', event => {
      if (!drag) return;
      dropBlock?.element.removeAttribute('data-fa-drop');
      dropBlock = null;
      for (let target = event.target; target; target = target.parentElement) {
        const candidate = index.elements.get(target);
        if (candidate?.group !== drag.group) continue;
        if (candidate !== drag) {
          dropBlock = candidate;
          candidate.element.setAttribute('data-fa-drop', '');
          event.preventDefault();
          event.dataTransfer.dropEffect = 'move';
        }
        break;
      }
    });
    doc.addEventListener('drop', event => {
      if (!drag || !dropBlock) return;
      event.preventDefault();
      const source = drag;
      const target = dropBlock;
      const box = target.element.getBoundingClientRect();
      const sourceBox = source.element.getBoundingClientRect();
      const sameRow = Math.abs(box.top - sourceBox.top) < 12 && box.left !== sourceBox.left;
      const after = sameRow ? event.clientX > box.left + box.width / 2 : event.clientY > box.top + box.height / 2;
      clearDrag();
      move(source, target, after);
      selectEntry(source);
    });
    doc.addEventListener('dragend', clearDrag);
  }

  function attachPreview() {
    if (!selected || index || !opened) return;
    const doc = frame.contentDocument;
    if (!doc || doc.readyState !== 'complete' || doc.location.pathname !== '/' + selected.page.path) return;
    index = indexLayout(doc);
    if (!index.root) {
      index = null;
      say('Bu sayfanın önizlemesi açılamadı.');
      return;
    }

    const defaultHome = ['Karşılama', 'Son Haberler', 'FA’yı keşfet', 'Topluluk'];
    const homeBlocks = index.groups.get('main')?.blocks;
    if (selected.legacy && homeBlocks?.length === defaultHome.length &&
        selected.legacy.some((name, i) => name !== defaultHome[i]) &&
        selected.legacy.every(name => defaultHome.includes(name))) {
      selected.settings.order.main = selected.legacy.map(name => homeBlocks[defaultHome.indexOf(name)].key);
      selected.dirty = true;
    }
    selected.legacy = null;
    applyLayout(index, selected.settings);
    attachEditing(doc);
    orderGroup = index.groups.get('main') ?? [...index.groups.values()].at(-1) ?? null;
    renderOrder();
    controls();
    describe();
  }

  async function openPage(page) {
    if (pending || !opened || page.path === selected?.page.path) return;
    const version = ++request;
    clearDrag();
    clearSelection();
    orderGroup = null;
    renderOrder();
    selected = null;
    index = null;
    sectionSelect.replaceChildren(new Option('Bölüm seç', ''));
    controls();
    heading.textContent = page.title;
    say('Sayfa açılıyor.');
    const url = new URL('/' + page.path, location.origin);
    url.searchParams.set('fa-panel-preview', '1');
    frame.src = url.href;

    try {
      let state = drafts.get(page.path);
      if (!state) {
        const [draft, release, legacy] = await Promise.all([
          client.from('fa_panel_page_drafts').select('settings,revision').eq('page_path', page.path).maybeSingle().then(unwrap),
          client.from('fa_panel_published_pages').select('revision').eq('page_path', page.path).maybeSingle().then(unwrap),
          page.path === 'index.html'
            ? client.from('fa_panel_layout').select('sections').eq('id', 1).maybeSingle().then(unwrap) : null,
        ]);
        if (version !== request) return;
        state = {
          page, settings: draft ? readLayout(draft.settings) : blankLayout(),
          revision: draft?.revision ?? null, published: release?.revision ?? null,
          legacy: draft ? null : legacy?.sections,
          dirty: false,
        };
        drafts.set(page.path, state);
      }
      selected = state;
      renderList();
      attachPreview();
    } catch {
      if (version === request) say('Sayfa taslağı açılamadı. Sayfayı yeniden seçip dene.');
    }
  }

  async function storePage(makePublic) {
    if (!selected || !index || pending || !properties.reportValidity()) return;
    const state = selected;
    const version = request;
    pending = true;
    controls();
    say(makePublic ? 'Düzen yayımlanıyor.' : 'Taslak kaydediliyor.');
    try {
      if (state.dirty) {
        const query = client.from('fa_panel_page_drafts');
        const patch = { settings: state.settings };
        const result = state.revision === null
          ? await query.insert({ ...patch, page_path: state.page.path }).select('revision').single()
          : await query.update(patch).eq('page_path', state.page.path).eq('revision', state.revision).select('revision').maybeSingle();
        if (version !== request) return;
        if ((!result.error && !result.data) || result.error?.code === '23505') {
          say('Başka bir oturum taslağı değiştirdi. Metnini kopyalayıp paneli yenile.');
          return;
        }
        state.revision = unwrap(result).revision;
        state.dirty = false;
      }
      if (makePublic) {
        state.published = unwrap(await client.rpc('fa_panel_publish_page', {
          target_path: state.page.path,
          expected_revision: state.revision,
        }));
      }
      if (version === request) describe();
    } catch (error) {
      if (version !== request) return;
      if (error?.code === '40001') say('Başka bir oturum taslağı değiştirdi. Paneli yenile.');
      else if (makePublic && !state.dirty) say('Taslak kaydedildi. Yayın tamamlanamadı. Tekrar dene.');
      else say('Taslak kaydedilemedi. Bağlantıyı kontrol edip tekrar dene.');
    } finally {
      if (version === request) {
        pending = false;
        controls();
      }
    }
  }

  frame.addEventListener('load', attachPreview);
  search.addEventListener('input', renderList);
  save.addEventListener('click', () => storePage(false));
  publish.addEventListener('click', () => storePage(true));
  moveUp.addEventListener('click', () => moveSelected(-1));
  moveDown.addEventListener('click', () => moveSelected(1));
  properties.addEventListener('submit', event => event.preventDefault());
  sectionSelect.addEventListener('change', () => {
    const entry = index?.entries.get(sectionSelect.value);
    if (!entry) {
      clearSelection();
      controls();
      return;
    }
    entry.element.scrollIntoView({ block: 'center', inline: 'nearest' });
    selectEntry(entry, true);
  });
  window.addEventListener('beforeunload', event => {
    if (![...drafts.values()].some(state => state.dirty)) return;
    event.preventDefault();
    event.returnValue = '';
  });

  return {
    async open() {
      opened = true;
      if (selected || loading) return;
      if (pages.length) return openPage(pages[0]);
      loading = true;
      const version = request;
      try {
        const response = await fetch('./pages.json', { cache: 'no-cache' });
        if (!response.ok) throw new Error('Page list unavailable');
        const catalog = await response.json();
        if (request !== version) return;
        pages = catalog.filter(page => isSitePage(page.path) && typeof page.title === 'string');
        if (!pages.length) throw new Error('Page list empty');
        loading = false;
        renderList();
        await openPage(pages[0]);
      } catch {
        if (request === version) say('Sayfa listesi yüklenemedi. Paneli yenile.');
      } finally {
        if (request === version) loading = false;
      }
    },
    clear() {
      request++;
      opened = false;
      pending = false;
      loading = false;
      drafts.clear();
      selected = null;
      index = null;
      clearDrag();
      clearSelection();
      orderGroup = null;
      renderOrder();
      search.value = '';
      frame.removeAttribute('src');
      sectionSelect.replaceChildren(new Option('Bölüm seç', ''));
      heading.textContent = 'Sayfalar';
      renderList();
      controls();
    },
  };
}
