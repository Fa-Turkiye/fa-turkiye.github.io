const byId = id => document.getElementById(id);
const panelUrl = 'https://fa-turkiye.github.io/panel/';
const roleLabels = { author: 'Yazar', editor: 'Editör', admin: 'Yönetici' };
const statusLabels = { draft: 'Taslak', review: 'İncelemede', approved: 'Yayına hazır' };
const storyColumns = 'id,title,author_id,status,revision,reviewed_at,updated_at';
const storyForm = byId('story');
const workspace = byId('workspace');
const preview = byId('preview');

let client;
let account = null;
let role = null;
let authCheck = 0;
let workspaceVersion = 0;
let busy = false;
let page = 'news';
let editing = null;
let draftId;
let stories = [];
let members = [];
let layout = null;

const canReview = () => role === 'editor' || role === 'admin';

function message(text) {
  byId('status').textContent = text;
}

function unwrap({ data, error }) {
  if (error) throw error;
  return data;
}

function button(text, action) {
  const item = document.createElement('button');
  item.type = 'button';
  item.textContent = text;
  item.addEventListener('click', action);
  return item;
}

function formData(form) {
  return Object.fromEntries([...new FormData(form)].map(([key, value]) => [key, value.trim()]));
}

function validSource(value) {
  if (!value.startsWith('https://') || /[\s\\]/.test(value)) return false;
  try {
    const url = new URL(value);
    return url.hostname && !url.username && !url.password;
  } catch {
    return false;
  }
}

function openStory(record = null) {
  storyForm.reset();
  editing = record;
  draftId = record?.id ?? crypto.randomUUID();
  const readOnly = Boolean(record && (record.status !== 'draft' || record.author_id !== account?.id));

  for (const field of storyForm.elements) {
    if (!field.name) continue;
    field.value = record?.[field.name] ?? '';
    field.readOnly = readOnly;
  }

  byId('story-heading').textContent = record ? statusLabels[record.status] : 'Haber yaz';
  byId('save-button').disabled = readOnly;
  byId('submit-button').disabled = readOnly;
}

function clearWorkspace() {
  workspaceVersion++;
  busy = false;
  workspace.removeAttribute('aria-busy');
  workspace.hidden = true;
  role = null;
  page = 'news';
  stories = [];
  members = [];
  layout = null;
  openStory();
  byId('invite').reset();
  byId('stories').replaceChildren();
  byId('sections').replaceChildren();
  byId('invitations').replaceChildren();
  if (preview.open) preview.close();
  preview.querySelector('article').replaceChildren();
}

async function runAction(control, task, errorMessage) {
  if (busy || !role) return;

  const version = workspaceVersion;
  const stillActive = () => version === workspaceVersion;
  busy = true;
  control.setAttribute('aria-disabled', 'true');
  workspace.setAttribute('aria-busy', 'true');

  try {
    await task(stillActive);
  } catch {
    if (stillActive()) message(errorMessage);
  } finally {
    control.removeAttribute('aria-disabled');
    if (stillActive()) {
      busy = false;
      workspace.removeAttribute('aria-busy');
    }
  }
}

async function fetchStories() {
  const rows = [];
  const pageSize = 250;
  for (let offset = 0; ; offset += pageSize) {
    const batch = unwrap(await client.from('fa_panel_stories')
      .select(storyColumns).order('updated_at', { ascending: false }).order('id')
      .range(offset, offset + pageSize - 1));
    rows.push(...batch);
    if (batch.length < pageSize) return rows;
  }
}

async function fetchWorkspace() {
  return Promise.all([
    fetchStories(),
    canReview() ? client.from('fa_panel_layout').select().eq('id', 1).single().then(unwrap) : null,
    role === 'admin' ? client.from('fa_panel_members').select('user_id,email,role').order('email').then(unwrap) : [],
  ]);
}

function refresh(control, note = 'Haber akışı güncellendi.') {
  return runAction(control, async active => {
    const next = await fetchWorkspace();
    if (!active()) return;
    [stories, layout, members] = next;
    render();
    message(note);
  }, 'Panel verileri yenilenemedi. Tekrar dene.');
}

async function syncSession(session) {
  const check = ++authCheck;
  const nextAccount = session?.user ?? null;
  if (!nextAccount || account?.id !== nextAccount.id) clearWorkspace();

  account = nextAccount;
  byId('sign-in').hidden = Boolean(account);
  byId('session').hidden = !account;
  byId('identity').textContent = account?.email ?? '';
  if (!account) {
    if (byId('status').textContent === 'Panel bağlantısı kontrol ediliyor.') message('');
    return;
  }

  try {
    const membership = unwrap(await client.from('fa_panel_members').select('role')
      .eq('user_id', account.id).maybeSingle());
    if (check !== authCheck) return;

    if (!membership || !Object.hasOwn(roleLabels, membership.role)) {
      clearWorkspace();
      message('Bu e-posta adresi için panel erişimi tanımlı değil.');
      return;
    }

    if (role === membership.role && !workspace.hidden) {
      byId('identity').textContent = account.email + ' · ' + roleLabels[role];
      return;
    }

    clearWorkspace();
    role = membership.role;
    const next = await fetchWorkspace();
    if (check !== authCheck) return;

    [stories, layout, members] = next;
    byId('identity').textContent = account.email + ' · ' + roleLabels[role];
    render();
    workspace.hidden = false;
    message('');
  } catch {
    if (check !== authCheck) return;
    clearWorkspace();
    message('Panel erişimi doğrulanamadı. Yenile veya yeniden giriş yap.');
  }
}

function recordStory(record) {
  stories = [record, ...stories.filter(story => story.id !== record.id)];
  renderStories();
}

function saveStory(control, status) {
  if (busy || !role) return;
  const record = editing;
  const id = draftId;
  if (record && (record.status !== 'draft' || record.author_id !== account?.id)) return;
  const data = formData(storyForm);
  if (status === 'review' && (!data.title || !data.summary || !data.body || !data.source || !validSource(data.url))) {
    message('İnceleme için başlık, özet, haber metni ve HTTPS birincil kaynak adresi gerekli.');
    return;
  }
  if (status === 'review' && data.image && (!validSource(data.image) || !data.alt)) {
    message('Görsel eklemek için HTTPS adresi ve görsel açıklaması gerekli.');
    return;
  }

  return runAction(control, async active => {
    const query = client.from('fa_panel_stories');
    const change = { ...data, status };
    let result = record
      ? await query.update(change).eq('id', record.id).eq('revision', record.revision).select().maybeSingle()
      : await query.insert({ ...change, id }).select().single();

    if (!active()) return;
    if (!record && result.error?.code === '23505') {
      result = await client.from('fa_panel_stories').select().eq('id', id).maybeSingle();
      const saved = unwrap(result);
      if (!active()) return;
      if (saved) {
        recordStory(saved);
        message('Bu haber önceki istekte kaydedildi. Haber akışından son sürümü aç.');
      }
      return;
    }

    const saved = unwrap(result);
    if (!active()) return;
    if (!saved) {
      message('Haber başka bir oturumda değişti. Akışı yenileyip son sürümü aç.');
      return;
    }

    openStory(saved);
    recordStory(saved);
    message(status === 'review' ? 'Haber editör incelemesine gönderildi.' : 'Haber taslağı kaydedildi.');
  }, 'Haber kaydedilemedi. Erişimini ve bağlantını kontrol edip tekrar dene.');
}

function openSavedStory(control, id) {
  return runAction(control, async active => {
    const record = unwrap(await client.from('fa_panel_stories').select().eq('id', id).maybeSingle());
    if (!active()) return;
    if (!record) {
      message('Bu haber açılamadı. Akışı yenile.');
      return;
    }

    openStory(record);
    byId('story-heading').focus();
    message('');
  }, 'Haber açılamadı. Tekrar dene.');
}

function reviewStory(control, record, status) {
  return runAction(control, async active => {
    const saved = unwrap(await client.from('fa_panel_stories').update({ status })
      .eq('id', record.id).eq('revision', record.revision).select().maybeSingle());
    if (!active()) return;
    if (!saved) {
      message('Haber başka bir oturumda değişti. Akışı yenile.');
      return;
    }

    if (editing?.id === saved.id) openStory(saved);
    recordStory(saved);
    const titleButton = byId('stories').querySelector('[data-story-id="' + saved.id + '"]');
    titleButton?.focus();
    message(status === 'approved' ? 'Kaynak kontrolü kaydedildi. Haber yayına hazır.' : 'Haber yazara düzeltme için geri gönderildi.');
  }, 'İnceleme kaydedilemedi. Akışı yenileyip tekrar dene.');
}

function renderStories() {
  const list = byId('stories');
  list.replaceChildren();
  byId('flow-note').textContent = stories.length ? 'Taslağı veya inceleme durumunu görmek için haberi aç.' : 'Henüz haber taslağı yok.';

  for (const record of stories) {
    const item = document.createElement('li');
    const title = button(record.title || 'Başlıksız taslak', event => openSavedStory(event.currentTarget, record.id));
    title.dataset.storyId = record.id;
    const state = document.createElement('span');
    state.className = 'story-state';
    state.textContent = statusLabels[record.status];
    if (record.reviewed_at) {
      state.textContent += ' · Kaynak kontrolü ' + new Intl.DateTimeFormat('tr-TR', {
        dateStyle: 'short',
        timeZone: 'Europe/Istanbul',
      }).format(new Date(record.reviewed_at));
    }
    item.append(title, state);
    if (canReview() && record.status === 'review') {
      item.append(button('Düzeltmeye gönder', event => reviewStory(event.currentTarget, record, 'draft')));
      item.append(button('Kaynağı kontrol ettim, onayla', event => reviewStory(event.currentTarget, record, 'approved')));
    }
    list.append(item);
  }
}

function renderLayout() {
  const sections = byId('sections');
  sections.replaceChildren();
  if (!layout) return;

  layout.sections.forEach((name, index) => {
    const row = document.createElement('li');
    row.textContent = name;
    for (const [direction, label] of [[-1, 'Yukarı taşı'], [1, 'Aşağı taşı']]) {
      const target = index + direction;
      const move = button(label, event => runAction(event.currentTarget, async active => {
        const order = [...layout.sections];
        [order[index], order[target]] = [order[target], order[index]];
        const saved = unwrap(await client.from('fa_panel_layout').update({ sections: order })
          .eq('id', 1).eq('revision', layout.revision).select().maybeSingle());
        if (!active()) return;
        if (!saved) {
          message('Bölüm sırası başka bir oturumda değişti. Akışı yenile.');
          return;
        }
        layout = saved;
        renderLayout();
        const controls = sections.children[target].querySelectorAll('button');
        const sameDirection = controls[direction < 0 ? 0 : 1];
        (sameDirection.disabled ? controls[direction < 0 ? 1 : 0] : sameDirection).focus();
        message('Ana sayfa sırası kaydedildi.');
      }, 'Bölüm sırası kaydedilemedi. Tekrar dene.'));
      move.disabled = target < 0 || target >= layout.sections.length;
      move.setAttribute('aria-label', name + ' bölümünü ' + label.toLocaleLowerCase('tr-TR'));
      row.append(move);
    }
    sections.append(row);
  });
}

function renderTeam() {
  const list = byId('invitations');
  list.replaceChildren();
  for (const member of members) {
    const item = document.createElement('li');
    item.textContent = member.email + ' · ' + roleLabels[member.role];
    if (member.role !== 'admin') {
      item.append(button('Erişimi kaldır', event => runAction(event.currentTarget, async active => {
        const removed = unwrap(await client.from('fa_panel_members').delete()
          .eq('user_id', member.user_id).eq('role', member.role).select('user_id').maybeSingle());
        if (!active()) return;
        if (!removed) {
          message('Ekip erişimi değişti. Akışı yenile.');
          return;
        }
        members = members.filter(entry => entry.user_id !== removed.user_id);
        renderTeam();
        byId('invite').elements.email.focus();
        message('Ekip üyesinin panel erişimi kaldırıldı.');
      }, 'Erişim kaldırılamadı. Tekrar dene.')));
    }
    list.append(item);
  }
}

function render() {
  for (const item of document.querySelectorAll('nav [data-page]')) {
    const name = item.dataset.page;
    item.hidden = (name === 'team' && role !== 'admin') || (name === 'layout' && !canReview());
    item.setAttribute('aria-pressed', String(name === page));
    byId(name).hidden = name !== page;
  }
  renderStories();
  renderLayout();
  renderTeam();
}

document.querySelectorAll('nav [data-page]').forEach(item => item.addEventListener('click', () => {
  if (busy || item.hidden) return;
  page = item.dataset.page;
  render();
}));
byId('reload').addEventListener('click', event => refresh(event.currentTarget));
byId('reset-button').addEventListener('click', () => {
  if (busy) return;
  openStory();
  storyForm.elements.title.focus();
});
byId('save-button').addEventListener('click', event => saveStory(event.currentTarget, 'draft'));
storyForm.addEventListener('submit', event => {
  event.preventDefault();
  saveStory(byId('submit-button'), 'review');
});

byId('preview-button').addEventListener('click', () => {
  const data = formData(storyForm);
  const article = preview.querySelector('article');
  article.replaceChildren();
  for (const [tag, text] of [['h3', data.title || 'Başlıksız haber'], ['p', data.topic], ['p', data.summary], ['p', data.body]]) {
    if (!text) continue;
    const element = document.createElement(tag);
    element.textContent = text;
    article.append(element);
  }
  if (validSource(data.image) && data.alt) {
    const image = document.createElement('img');
    image.src = data.image;
    image.alt = data.alt;
    image.referrerPolicy = 'no-referrer';
    article.append(image);
  }
  if (validSource(data.url)) {
    const link = document.createElement('a');
    link.href = data.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = data.source || 'Birincil kaynağı aç';
    article.append(link);
  }
  preview.showModal();
});

byId('invite').addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  const { email, permission } = formData(form);
  return runAction(event.submitter || form.querySelector('button'), async active => {
    const result = unwrap(await client.functions.invoke('fa-panel-invite', {
      body: { email, role: permission },
    }));
    if (!active()) return;
    const note = result.invited ? 'Davet e-postası gönderildi.' : 'Panel yetkisi kaydedildi.';
    message(note);
    form.reset();
    const { data, error } = await client.from('fa_panel_members').select('user_id,email,role').order('email');
    if (!active()) return;
    if (error) {
      message(note + ' Ekip listesini yenile.');
      return;
    }
    members = data;
    renderTeam();
  }, 'Davet veya yetki kaydı tamamlanamadı. Ekibi yenile ve gerekirse tekrar dene.');
});

byId('sign-in').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const control = form.querySelector('button');
  if (control.disabled) return;
  control.disabled = true;
  message('Giriş bağlantısı isteniyor.');
  try {
    unwrap(await client.auth.signInWithOtp({
      email: formData(form).email.toLowerCase(),
      options: { shouldCreateUser: false, emailRedirectTo: panelUrl },
    }));
    message('Giriş bağlantısı gönderildi. Gelen kutunu kontrol et.');
  } catch {
    message('Giriş bağlantısı gönderilemedi. E-posta adresini ve ekip davetini kontrol et.');
  } finally {
    control.disabled = false;
  }
});

byId('sign-out').addEventListener('click', async event => {
  const control = event.currentTarget;
  control.disabled = true;
  try {
    unwrap(await client.auth.signOut({ scope: 'local' }));
    await syncSession(null);
    message('Oturum kapatıldı.');
    byId('sign-in').elements.email.focus();
  } catch {
    message('Oturum kapatılamadı. Tekrar dene.');
  } finally {
    control.disabled = false;
  }
});

const { supabaseUrl, publishableKey } = window.faPanelConfig ?? {};
if (!/^https:\/\/[a-z0-9]+\.supabase\.co$/.test(supabaseUrl ?? '') || !/^sb_publishable_[\w-]+$/.test(publishableKey ?? '')) {
  message('Panelin Supabase bağlantısı henüz yapılandırılmadı.');
} else if (!window.supabase) {
  message('Giriş hizmeti yüklenemedi. Sayfayı yenileyip tekrar dene.');
} else {
  const callback = new URLSearchParams(window.location.hash.slice(1));
  if (callback.has('error_code')) message('Giriş bağlantısının süresi dolmuş olabilir. Yeni bağlantı iste.');
  client = window.supabase.createClient(supabaseUrl, publishableKey, {
    auth: { flowType: 'implicit', storageKey: 'fa-turkiye-editor-session' },
  });
  client.auth.onAuthStateChange((_event, session) => {
    setTimeout(() => syncSession(session), 0);
  });
}
