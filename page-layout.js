// Shared by the public pages and the editor iframe. The HTML remains the source
// for content that has not been edited or has since changed in the repository.
const pageNamePattern = /^[a-z0-9][a-z0-9-]*\.html$/;
const ignored = 'script, style, template, svg, dialog, form, button, input, select, textarea, [aria-hidden="true"], .visually-hidden, .sr-only';
const textElements = 'h1,h2,h3,h4,h5,h6,p,div,span,a,li,dt,dd,summary,small,strong,em,figcaption,address,blockquote,caption,th,td';
const layoutParents = 'main, section, article.long-article, .article-prose, .wrap, .feature, .callout, [class*="grid"], .rail-track, .news-track';
const layoutChildren = 'section,article,aside,details,div,nav.article-toc,h1,h2,h3,p,ul,ol,dl,blockquote,figure,a.button';

export const isSitePage = name => typeof name === 'string' && pageNamePattern.test(name);
export const blankLayout = () => ({ version: 1, fields: {}, order: {} });

export function readLayout(value) {
  if (value?.version !== 1) return blankLayout();
  return {
    version: 1,
    fields: { ...value.fields },
    order: { ...value.order },
  };
}

function safeAddress(value, base, image) {
  if (!value || value.length > 2048 || /[\s\\]/u.test(value)) return false;
  try {
    const url = new URL(value, base);
    if (url.username || url.password) return false;
    if (url.protocol === 'https:' || url.origin === new URL(base).origin) return true;
    return !image && ['mailto:', 'tel:'].includes(url.protocol);
  } catch {
    return false;
  }
}

function entryName(element) {
  const heading = element.matches('h1,h2,h3,h4,h5,h6')
    ? element : element.querySelector('h1,h2,h3,h4,h5,h6');
  return (heading?.textContent || element.getAttribute('alt') || element.textContent)
    .replace(/\s+/gu, ' ').trim().slice(0, 80) || 'Görsel';
}

function elementPart(element) {
  if (element.id) return element.localName + '#' + element.id;
  const link = element.matches('a') ? element : element.matches('article, .card')
    ? element.querySelector('h2 a, h3 a, a[href]') : null;
  const href = link?.getAttribute('href');
  const heading = element.matches('section, article, aside, .card')
    ? element.querySelector('h1,h2,h3,h4')?.textContent.trim().slice(0, 120) : '';
  return [element.localName, element.classList[0], href || heading].filter(Boolean).join(':');
}

export function indexLayout(doc) {
  const root = doc.querySelector('main');
  const entries = new Map();
  const elements = new WeakMap();
  const fields = new Map();
  const groups = new Map();

  function visit(element, key) {
    const entry = { key, element, fields: [] };
    entries.set(key, entry);
    elements.set(element, entry);

    function addField(suffix, label, base, write, valid = value => value.length <= 16000) {
      const id = key + '/' + suffix;
      const field = { id, label, base, current: base, write, valid };
      entry.fields.push(field);
      fields.set(id, field);
    }

    if (element.matches(textElements)) {
      const nodes = [...element.childNodes].filter(node => node.nodeType === 3 && node.data.trim());
      nodes.forEach((node, index) => {
        const label = nodes.length === 1 ? 'Metin' : 'Metin ' + (index + 1);
        addField('text-' + index, label, node.data, value => { node.data = value; });
      });
    }
    if (element.matches('a[href]')) {
      const base = element.getAttribute('href');
      addField('href', 'Bağlantı adresi', base, value => element.setAttribute('href', value),
        value => safeAddress(value, doc.baseURI, false));
    }
    if (element.matches('img[src]:not([srcset])') && !element.closest('picture')) {
      const base = element.getAttribute('src');
      addField('src', 'Görsel adresi', base, value => element.setAttribute('src', value),
        value => safeAddress(value, doc.baseURI, true));
      addField('alt', 'Görsel açıklaması', element.alt, value => { element.alt = value; },
        value => value.length <= 300);
    }

    const counts = new Map();
    const children = [];
    for (const child of element.children) {
      if (child.matches(ignored)) continue;
      const part = elementPart(child);
      const count = (counts.get(part) ?? 0) + 1;
      counts.set(part, count);
      children.push(visit(child, key + '/' + encodeURIComponent(part) + ':' + count));
    }
    if (element.matches(layoutParents)) {
      const blocks = children.filter(child => child.element.matches(layoutChildren));
      if (blocks.length > 1) {
        const group = { key, element, blocks };
        groups.set(key, group);
        blocks.forEach(block => { block.group = group; });
      }
    }
    return entry;
  }

  if (root) visit(root, 'main');
  return { doc, root, entries, elements, fields, groups };
}

export function blockName(entry) {
  return entryName(entry.element);
}

export function orderedBlocks(group, keys) {
  if (!Array.isArray(keys)) return group.blocks;
  const byKey = new Map(group.blocks.map(block => [block.key, block]));
  const known = [...new Set(keys)].filter(key => byKey.has(key));
  const moved = new Set(known);
  let position = 0;
  // Sections added by a later site build keep their original slots.
  return group.blocks.map(block => moved.has(block.key) ? byKey.get(known[position++]) : block);
}

export function applyLayout(index, settings) {
  for (const [id, field] of index.fields) {
    const change = Object.hasOwn(settings.fields, id) ? settings.fields[id] : null;
    const value = change?.base === field.base && typeof change.value === 'string' && field.valid(change.value)
      ? change.value : field.base;
    if (value !== field.current) {
      field.write(value);
      field.current = value;
    }
  }

  for (const [key, group] of index.groups) {
    const order = orderedBlocks(group, Object.hasOwn(settings.order, key) ? settings.order[key] : null);
    const members = new Set(group.blocks.map(block => block.element));
    const current = [...group.element.children].filter(child => members.has(child));
    if (order.every((block, i) => block.element === current[i])) continue;
    const slots = current.map(child => {
      const slot = index.doc.createComment('section');
      child.replaceWith(slot);
      return slot;
    });
    slots.forEach((slot, i) => slot.replaceWith(order[i].element));
  }
}

export async function showPublishedLayout() {
  if (window.parent !== window && new URLSearchParams(location.search).get('fa-panel-preview') === '1') return;
  const page = location.pathname === '/' ? 'index.html' : location.pathname.slice(1);
  if (!isSitePage(page)) return;

  await import('./panel/config.js');
  const { supabaseUrl, publishableKey } = window.faPanelConfig ?? {};
  if (!supabaseUrl || !publishableKey) return;
  const endpoint = new URL('/rest/v1/fa_panel_published_pages', supabaseUrl);
  endpoint.search = new URLSearchParams({ select: 'settings', page_path: 'eq.' + page });
  const result = await fetch(endpoint, {
    headers: { apikey: publishableKey },
    credentials: 'omit',
    cache: 'no-store',
    signal: AbortSignal.timeout(4500),
  });
  if (!result.ok) return;
  const [published] = await result.json();
  if (published) applyLayout(indexLayout(document), readLayout(published.settings));
}
