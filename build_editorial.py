"""Build accessible, static Turkish research dossiers from editorial JSON."""
import json, re, html, math
from pathlib import Path
from datetime import date
from study_centers import StudyCenters, center_id

ROOT = Path(__file__).resolve().parent
study_centers = StudyCenters(ROOT)
profiles = json.loads((ROOT / 'editorial-content.json').read_text())
news = json.loads((ROOT / 'editorial-news.json').read_text())
milestones = json.loads((ROOT / 'editorial-milestones.json').read_text())
expansion = json.loads((ROOT / 'editorial-expansion.json').read_text())
for key, sections in expansion.items():
    profiles[key]['sections'].extend(sections)
profiles['skyclarys']['sources'].append(['FDA: kontrollü çalışma ve uzun dönem değerlendirmesi', 'https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-first-treatment-friedreichs-ataxia'])
profiles['nomlabofusp']['sources'].append(['Hakemli mekanizma araştırması, The AAPS Journal (2025)', 'https://link.springer.com/article/10.1208/s12248-025-01054-5'])
profiles['gv101']['sources'].append(['Hakemli ROCK1/ROCK2 araştırması: PubMed kaydı', 'https://pubmed.ncbi.nlm.nih.gov/40404357/'])
profiles['vatiquinone']['sources'].append(['PTC: 2026 üçüncü çeyrek geliştirme güncellemesi', 'https://ir.ptcbio.com/news-releases/news-release-details/ptc-therapeutics-provides-corporate-update-and-reports-third-4'])
news_extensions = {'vatiquinone-prove':[2,3], 'sgt212-avrupa':[3,4], 'lx2006-mds':[0,2], 'nbib223-facet':[0,2], 'dt216p2-takvim':[0,4], 'brave-alim':[0,2], 'ppl001-uretim':[0,3], 'nomlabofusp-bla':[0,3], 'dt216p2-ilk-veri':[1,2]}
for item in news:
    item['sections'].extend(expansion[item['drug']][i] for i in news_extensions.get(item['id'], []))
esc = html.escape
base = (ROOT / 'ilaclar.html').read_text()
header = re.search(r'<header>.*?</header>', base, re.S).group()
header = header.replace(' aria-current="page"', '')
names = {'skyclarys':'Omaveloxolone · Skyclarys','vatiquinone':'Vatiquinone · PROVE-FA','nomlabofusp':'Nomlabofusp · FORWARD-FA','dt216p2':'DT-216P2 · RESTORE-FA','lx2006':'LX2006 · SUNRISE-FA 2','sgt212':'SGT-212 · FALCON','gv101':'GV101 · ROCK2 inhibitörü','ppl001':'PPL-001 · gen düzenlenmiş hücre tedavisi','nbib223':'NBIB-223 · FACET','brave':'Omaveloxolone · BRAVE','jive':'Nomlabofusp · JIVE/OLE','ati105':'ATI-105'}
sponsors = {'skyclarys':'Biogen','vatiquinone':'PTC Therapeutics','nomlabofusp':'Larimar Therapeutics','dt216p2':'Design Therapeutics','lx2006':'Lexeo Therapeutics','sgt212':'Solid Biosciences','gv101':'Graviton BioScience','ppl001':'Papillon Therapeutics','nbib223':'Neurocrine Biosciences / Voyager Therapeutics','brave':'Biogen','jive':'Larimar Therapeutics','ati105':'Adjuvia Therapeutics'}

def page(title, body, filename, description, active='ilaclar.html'):
    nav = header.replace(f'href="{active}"', f'href="{active}" aria-current="page"')
    glossary = '<script src="terimler.js" defer></script>' if filename.startswith(('ilac-', 'haber-')) or filename == 'gv101.html' else ''
    return f'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · FA Türkiye</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="https://fa-turkiye.github.io/{filename}">
<link rel="stylesheet" href="style.css?v=aqua-jade-1"><link rel="stylesheet" href="articles.css?v=aqua-jade-1">
<link rel="icon" type="image/svg+xml" href="fa-logo.svg"><script src="script.js?v=aqua-jade-1" defer></script><meta name="theme-color" content="#0a1224">{glossary}</head><body><a class="skip-link" href="#main-content">İçeriğe geç</a>{nav}
<main class="wrap editorial-main" id="main-content" tabindex="-1">{body}</main><footer><div class="wrap">FA Türkiye · Haber Merkezi. Kaynaklara dayalı bağımsız bilgilendirme. Tedavi ve katılım kararları hekim ve çalışma ekibiyle değerlendirilir.</div></footer></body></html>'''

months = ('Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık')

def source_anchor(source):
    label, url = source
    return f'<a href="{esc(url)}">{esc(label)} ↗</a>'

def milestone_event(item, heading):
    day = date.fromisoformat(item['date'])
    stamp = f'{day.day} {months[day.month - 1]} {day.year}'
    article = f' <a href="haber-{esc(item["article"])}.html">Ayrıntılı haber</a>' if item.get('article') else ''
    return f'''<div class="milestone-event"><p class="milestone-meta"><time datetime="{day.isoformat()}">{stamp}</time> <span>{esc(item['kind'])}</span></p>
<{heading}>{esc(item['title'])}</{heading}><p>{esc(item['summary'])}</p>
<p class="milestone-links">{source_anchor(item['source'])}{article}</p></div>'''

def treatment_updates(key):
    item = milestones[key]
    events = sorted(item['events'], key=lambda event: event['date'], reverse=True)
    older = ''.join(f'<li>{milestone_event(event, "h4")}</li>' for event in events[1:])
    timeline = f'<details class="milestone-history"><summary>Önceki gelişmeler ({len(events) - 1})</summary><ol>{older}</ol></details>' if older else ''
    expected = ''.join(f'<li><strong>{esc(event["window"])}</strong><p>{esc(event["title"])}</p>{source_anchor(event["source"])}</li>' for event in item.get('expected', []))
    planned = f'<div class="milestone-planned"><h3>Beklenen duyurular ve sunumlar</h3><p>Kaynakların açıkladığı planlar ve tahminler.</p><ul>{expected}</ul></div>' if expected else ''
    return f'''<section class="milestone-panel" id="son-gelismeler" aria-labelledby="milestone-title">
<h2 id="milestone-title">Bu tedavide ne değişti?</h2><p class="milestone-label">Son açıklanan gelişme</p>
{milestone_event(events[0], 'h3')}{timeline}{planned}</section>'''

def article_body(title, status, sections, sources, category, back, sponsor=None, extra='', lead=None, studies='', checked_on='2026-11-01', checked_label='1 Kasım 2026', updates=''):
    count = sum(len(p.split()) for _, p in sections)
    lead_text = lead or '. '.join(sections[0][1].split('. ')[:2]).rstrip('.') + '.'
    toc = ''.join(f'<li><a href="#bolum-{i}">{esc(t)}</a></li>' for i,(t,_) in enumerate(sections,1))
    if studies:
        toc = '<li><a href="#arastirma-merkezleri">Resmî kaynaklar ve iletişim</a></li>' + toc
    paragraphs = ''.join(f'<section id="bolum-{i}" class="article-section"><h2>{esc(t)}</h2><p>{esc(p)}</p></section>' for i,(t,p) in enumerate(sections,1))
    src = ''.join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a></li>' for t,u in sources)
    return f'''<p class="breadcrumb"><a href="{back}">← {category}</a></p><article class="long-article">
<div class="article-heading"><span class="badge">{esc(status)}</span><h1>{esc(title)}</h1>
<p class="article-meta">Son kaynak kontrolü: <time datetime="{esc(checked_on)}">{esc(checked_label)}</time> · Yaklaşık {max(2,math.ceil(count/160))} dakika okuma</p>
{f'<p class="article-meta">Geliştirici: {esc(sponsor)}</p>' if sponsor else ''}<p class="article-lead">{esc(lead_text)}</p></div>
{updates}<nav class="article-toc" aria-label="Yazı içindekiler"><h2>Bu yazıda</h2><ol>{toc}</ol></nav>
<div class="article-prose">{paragraphs}{studies}{extra}<section id="kaynaklar" class="article-section article-sources"><h2>Kaynaklar ve doğrulama</h2><ol>{src}</ol><p class="article-meta">Özgün Türkçe açıklama ve değerlendirme. Şirket hedefleri, açıklanmış bulgular ve henüz doğrulanmayan noktalar metinde ayrılmıştır. Kaynak tarihleri ve merkezlerin alım durumları farklı olabilir.</p></section></div>
<p class="article-end"><a href="{back}">← {category} sayfasına dön</a></p></article>'''

for key, item in profiles.items():
    filename = f'ilac-{key}.html'
    related = [n for n in news if n['drug']==key]
    more = '<aside class="article-related"><h2>İlgili ayrıntılı haberler</h2><ul>'+''.join(f'<li><a href="haber-{n["id"]}.html">{esc(n["title"])}</a></li>' for n in related)+'</ul></aside>' if related else ''
    if key=='skyclarys': more += '<p><a href="ilac-brave.html#arastirma-merkezleri">BRAVE çocuk çalışması ve merkezleri →</a></p>'
    if key=='brave': more += '<p><a href="ilac-skyclarys.html">Omaveloxolone’un ana ilaç dosyasını da okuyun →</a></p>'
    if key=='jive': more += '<p><a href="ilac-nomlabofusp.html">Nomlabofusp ana ilaç dosyasını da okuyun →</a></p>'
    review = item.get('source_review', {})
    body = article_body(item['title'],item['status'],item['sections'],item['sources'],'İlaç kütüphanesi','ilaclar.html',sponsors[key],more,studies=study_centers.dossier(key), updates=treatment_updates(key), **review)
    (ROOT / filename).write_text(page(item['title'],body,filename,item['sections'][0][1]))

treatment_groups = {
    'gene': 'Gen temelli tedaviler',
    'frataxin': 'Frataxin düzeyini hedefleyen tedaviler',
    'other': 'Diğer yaklaşımlar',
}
card_details = {
    'skyclarys': ('other', 'Ruhsatlı tedavi'),
    'vatiquinone': ('other', 'Faz III · PROVE-FA'),
    'nomlabofusp': ('frataxin', 'Faz III · FORWARD-FA'),
    'dt216p2': ('frataxin', 'Faz I/II · RESTORE-FA'),
    'lx2006': ('gene', 'Faz II · SUNRISE-FA 2'),
    'sgt212': ('gene', 'Faz 1b · FALCON'),
    'gv101': ('other', 'Faz IIa'),
    'ppl001': ('gene', 'Klinik öncesi'),
    'nbib223': ('gene', 'Faz I · FACET duyurusu'),
    'brave': ('other', 'Faz III · BRAVE'),
    'jive': ('frataxin', 'Faz II · Açık etiketli takip'),
    'ati105': ('other', 'Faz I · Sağlıklı gönüllüler'),
}

def treatment_card(key, item):
    group, phase = card_details[key]
    review = item.get('source_review', {})
    checked_on = review.get('checked_on', '2026-11-01')
    checked_label = review.get('checked_label', '1 Kasım 2026')
    research = 'false' if key == 'skyclarys' else 'true'
    comparison = milestones[key]
    return f'''<article class="card dossier-card treatment-card" data-treatment-group="{group}" data-research="{research}" data-phase="{esc(phase)}" data-target="{esc(comparison["target"])}" data-results="{esc(comparison["results"])}" data-source="{esc(comparison["source"][1])}">
<span class="badge">{esc(treatment_groups[group])}</span>
<h2><a href="ilac-{key}.html">{esc(names[key])}</a></h2>
<dl><div><dt>Aşama</dt><dd>{esc(phase)}</dd></div><div><dt>Geliştirici</dt><dd>{esc(sponsors[key])}</dd></div>
<div><dt>Kaynak kontrolü</dt><dd><time datetime="{esc(checked_on)}">{esc(checked_label)}</time></dd></div></dl>
<p>{esc(item['sections'][0][1].split('. ')[0])}.</p>
<a class="textlink" href="ilac-{key}.html" aria-label="{esc(names[key])} dosyasını oku">Dosyayı oku <span aria-hidden="true">↗</span></a>
<label class="compare-choice" hidden><input type="checkbox" value="{key}"> {esc(names[key])} karşılaştırmaya ekle</label></article>'''

cards = ''.join(treatment_card(key, item) for key, item in profiles.items())
intro = '''<div class="editorial-intro treatment-intro"><span class="badge">FA Türkiye</span><h1>FA tedavi dosyaları</h1><p>Ruhsatlı tedaviyi ve araştırılan adayları inceleyin. Her dosyada tedavinin amacı, bilinen bulgular, resmî kaynaklar ve yayımlanan çalışma iletişimi bulunur.</p></div>'''
group_options = ''.join(f'<option value="{key}">{esc(label)}</option>' for key, label in treatment_groups.items())
filters = f'''<section class="treatment-browse" id="arastirilan" aria-labelledby="treatment-browse-title">
<h2 id="treatment-browse-title">Tedavileri incele</h2>
<form class="treatment-filters" id="treatment-filters" hidden>
<label for="treatment-group">Araştırma yaklaşımı<select id="treatment-group"><option value="">Tüm yaklaşımlar</option>{group_options}</select></label>
<label for="treatment-scope">Tedavi durumu<select id="treatment-scope"><option value="">Tüm dosyalar</option><option value="arastirma">Araştırılan tedaviler</option><option value="ruhsatli">Ruhsatlı tedavi</option></select></label>
</form><p class="article-meta" id="treatment-result" role="status" aria-atomic="true" hidden></p>
<aside class="compare-toolbar" id="compare-toolbar" aria-labelledby="compare-title" hidden>
<h3 id="compare-title">Tedavileri yan yana incele</h3><p>Kartlardan 2 veya 3 dosya seçin. Her çalışmanın sonuçları kendi araştırma tasarımı içinde değerlendirilir.</p>
<div><button class="btn" id="compare-show" type="button" disabled>Karşılaştırmayı göster</button> <button class="compare-clear" id="compare-clear" type="button">Seçimi temizle</button></div>
<p class="article-meta" id="compare-status" role="status" aria-atomic="true"></p>
</aside><div class="dossier-grid">{cards}</div>
<dialog class="compare-dialog" id="compare-dialog" aria-labelledby="compare-dialog-title">
<div class="compare-dialog-head"><h2 id="compare-dialog-title">Tedavi dosyaları karşılaştırması</h2><form method="dialog"><button type="submit" autofocus>Kapat</button></form></div>
<div id="compare-content" tabindex="0" role="region" aria-label="Karşılaştırma tablosu"></div>
</dialog>
<p><a href="https://www.curefa.org/drug-development/">FARA’nın geliştirme hattı ve geçmiş programları ↗</a></p></section>'''
aliases = json.dumps({k:f'ilac-{k}.html' for k in profiles})
redirect = '<script>const dossierRoutes='+aliases+';const requested=new URLSearchParams(location.search).get("ilac");if(Object.hasOwn(dossierRoutes,requested)){location.replace(dossierRoutes[requested]+location.hash);}</script>'
library = page('İlaç kütüphanesi',intro + filters,'ilaclar.html','FA için kaynaklı ilaç ve çalışma profilleri.')
library = library.replace('</head>', '<link rel="stylesheet" href="portal.css?v=aqua-jade-1"><script src="tedavi-filtreleri.js" defer></script></head>')
(ROOT / 'ilaclar.html').write_text(library.replace('</body>',redirect+'</body>'))

for n in news:
    primary = n.get('primary_source') if n.get('source_review') else None
    sources = ([primary] if primary else []) + [source for source in profiles[n['drug']]['sources'] if not primary or source[1] != primary[1]]
    extra = f'<aside class="article-related"><h2>Programın tamamını inceleyin</h2><p><a href="ilac-{n["drug"]}.html">{esc(names[n["drug"]])}: mekanizma, kanıt, güvenlilik ve katılım →</a></p></aside>'
    review = n.get('source_review', {})
    reviewed = review.get('checked_label', '1 Kasım 2026')
    if review:
        scope_text = f'Gelişmenin tarihi {n["date"]}. Kaynaklar {reviewed} tarihinde kontrol edildi. Sonraki açıklamalar için ilaç dosyasına bakabilirsiniz.'
    else:
        scope_text = f'Gelişmenin tarihi: {n["date"]}. Bu haber 1 Kasım 2026 kaynak kontrolüyle hazırlanmıştır; sonraki açıklamalar için ilgili ilaç dosyasına bakın.'
    sections = [('Haber tarihi ve kapsamı', scope_text)] + n['sections']
    body = article_body(n['title'],n['date'],sections,sources,'Son haberler','haberler.html',extra=extra,lead=n['summary'], **review)
    fn = f'haber-{n["id"]}.html'
    (ROOT / fn).write_text(page(n['title'],body,fn,n['summary'],'haberler.html'))

# Preserve the existing GV101 news URL and expand its contents.
g = profiles['gv101']
gvbody = article_body('GV101 için klinik araştırma izni: ne değişti, ne henüz bilinmiyor?','11 Ağustos 2026 · Geliştirme duyurusu',g['sections'],g['sources'],'Son haberler','haberler.html',extra='<p><a href="ilac-gv101.html">GV101 ana ilaç dosyası →</a></p>')
(ROOT / 'haber-gv101.html').write_text(page('GV101 için klinik araştırma izni',gvbody,'haber-gv101.html','GV101 IND izni, FA araştırmasının amacı ve kanıt sınırları.','haberler.html'))

ordered_news = sorted(news, key=lambda item: item['iso'], reverse=True)
newscards = ''.join(f'<article class="card dossier-card"><time class="badge" datetime="{n["iso"]}">{n["date"]}</time><h2><a href="haber-{n["id"]}.html">{esc(n["title"])}</a></h2><p>{esc(n["summary"])}</p><a class="textlink" href="haber-{n["id"]}.html">Haberin tamamını oku →</a></article>' for n in ordered_news)
def home_news_card(item):
    label, url = item.get('primary_source') or profiles[item['drug']]['sources'][0]
    key = item['drug']
    return f'''<article class="news-card">
      <time datetime="{esc(item['iso'])}">{esc(item['date'])}</time>
      <h3><a href="haber-{item['id']}.html">{esc(item['title'])}</a></h3>
      <p>{esc(item['summary'])}</p>
      <div class="dispatch-links"><a href="ilac-{key}.html">{esc(names[key])} dosyası</a><a href="{esc(url)}">{esc(label)} ↗</a></div>
    </article>'''

home_path = ROOT / 'index.html'
home = home_path.read_text(encoding='utf-8')
home_news = '\n    '.join(home_news_card(item) for item in ordered_news[:3])
home = re.sub(r'<!-- home-news:start -->.*?<!-- home-news:end -->',
              lambda _: f'<!-- home-news:start -->\n    {home_news}\n    <!-- home-news:end -->', home, count=1, flags=re.S)
home_path.write_text(home, encoding='utf-8')

center_data = json.loads((ROOT / 'centers.json').read_text(encoding='utf-8'))
directory_names = {'clinic': 'Klinik bakım', 'genetics': 'Tanı ve genetik', 'fa-test': 'FA genetik testi FXN', 'research': 'Klinik araştırma'}
search_centers = []
for center in center_data['centers']:
    country = center_data['countries'][center['country']]
    area = f'{center["city"]}, {country}'
    people = ', '.join(person['name'] for person in center.get('people', []))
    labels = [directory_names[kind] for kind in center['types']]
    services = [service['name'] for service in center.get('services', [])]
    search_centers.append([center['name'], f'merkezler.html#{center_id(center)}', area,
                           ' '.join([people, *labels, *services])])
search_data = {
    'Tedavi dosyaları': [[names[key], f'ilac-{key}.html', sponsors[key], milestones[key]['target'] + ' ' + card_details[key][1]]
                         for key in profiles],
    'FA Merkezleri': search_centers,
    'Haberler': [[item['title'], f'haber-{item["id"]}.html', item['date'], names[item['drug']]]
                 for item in ordered_news] + [
                     ['GV101 için FA klinik araştırma izni', 'haber-gv101.html', '11 Ağustos 2026', 'Graviton BioScience']
                 ],
    'Site sayfaları': [
        ['FA’yı tanı', 'fa-hakkinda.html', 'Belirtiler, tanı ve genetik temel', 'FXN frataxin Friedreich ataksisi'],
        ['Tedavi ve bakım', 'tedaviler.html', 'Ruhsatlı tedavi ve destekleyici bakım', 'Skyclarys'],
        ['Araştırma takvimi', 'arastirma-takvimi.html', 'Duyurular ve beklenen gelişmeler', 'klinik çalışma'],
        ['Klinik araştırmalar', 'klinik-arastirmalar.html', 'Çalışma kayıtları ve araştırma türleri', 'ClinicalTrials.gov'],
        ['Topluluk', 'topluluk.html', 'FA ile yaşayan kişiler ve yakınları', 'dayanışma'],
        ['Kaynaklar', 'kaynaklar.html', 'Kurumlar ve bilimsel kaynaklar', 'FARA'],
    ],
}
(ROOT / 'arama-verileri.json').write_text(json.dumps(search_data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

# Put August GV101 news in chronological order, rather than at the end.
gvcard = '<article class="card dossier-card"><time class="badge" datetime="2026-08-11">11 Ağustos 2026</time><h2><a href="haber-gv101.html">GV101 için FA klinik araştırma izni</a></h2><p>ROCK2 hedefi, planlanan araştırma ve henüz doğrulanmayan katılım bilgileri.</p><a class="textlink" href="haber-gv101.html">Haberin tamamını oku →</a></article>'
marker = '<article class="card dossier-card"><time class="badge" datetime="2026-08-03">'
newscards = newscards.replace(marker,gvcard+marker,1)
body = '<div class="editorial-intro"><span class="badge">SON HABERLER</span><h1>Gelişmenin arkasındaki bilim</h1><p>Ne açıklandı, hangi veriye dayanıyor, hastalar için ne ifade ediyor? Kısa kartlardan kaynaklı tam haberlere geçin.</p><p class="article-meta">Haber tarihleri gelişmenin tarihini gösterir. Her yazıda kaynak kontrol tarihini bulabilirsiniz.</p></div><div class="dossier-grid">'+newscards+'</div>'
(ROOT / 'haberler.html').write_text(page('Son haberler',body,'haberler.html','FA araştırmalarını ayrıntılı ve kaynaklı Türkçe haberlerle takip edin.','haberler.html'))

# Existing dedicated GV101 address remains useful and consistent.
(ROOT / 'gv101.html').write_text(page(g['title'],article_body(g['title'],g['status'],g['sections'],g['sources'],'İlaç kütüphanesi','ilaclar.html',sponsors['gv101'],studies=study_centers.dossier('gv101'), updates=treatment_updates('gv101')),'gv101.html',g['sections'][0][1]))

# Generate a participation guide for every listed program, including closed/preclinical ones.
guide = json.loads((ROOT / 'participation-guide.json').read_text())
guide_toc = '<nav class="article-toc" aria-label="Programa göre katılım"><h2>Program seçin</h2><ol>' + ''.join(f'<li><a href="#program-{k}">{esc(names[k])}</a></li>' for k in guide) + '</ol></nav>'
guide_sections = ''
for key, item in guide.items():
    contact = esc(item['contact'])
    contact = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', lambda m: f'<a href="mailto:{m.group()}">{m.group()}</a>', contact)
    guide_sections += f'''<section id="program-{key}" class="article-section guide-program"><span class="badge">{esc(item['label'])}</span><h2>{esc(names[key])}</h2><h3>Koşullar ve araştırma yükü</h3><p>{esc(item['criteria'])}</p><h3>Türkiye’den ve Avrupa’dan katılım</h3><p>{esc(item['action'])}</p><h3>İletişim ve sonraki adım</h3><p>{contact}</p><p><a href="{esc(item['source'])}" target="_blank" rel="noopener">Resmî bilgi / çalışma kaydı ↗</a> · <a href="ilac-{key}.html">Kapsamlı ilaç ve çalışma dosyası →</a></p></section>'''
guide_intro = '<p class="breadcrumb"><a href="index.html">← Ana Sayfa</a></p><article class="long-article"><div class="article-heading"><span class="badge">KLİNİK ARAŞTIRMAYA KATILIM</span><h1>Her program için ayrı bir yol haritası</h1><p class="article-lead">11 ilaç ve çalışma başlığı: kimler değerlendirilebilir, nerede yürütülüyor, Türkiye’den ne sorulmalı ve hangi iletişim kullanılmalı?</p><p class="article-meta">Kaynak kontrolü: 1 Kasım 2026. Merkezlerin durumu başvuru günü yeniden teyit edilmelidir.</p></div>'
steps = '<section class="article-section"><h2>İlk iletişimden önce</h2><ol><li>İlacın, araştırmanın ve sponsorun tam adını kontrol edin. Aynı ilacın farklı çalışmaları farklı koşullar taşıyabilir.</li><li>Yaş, genetik tanı ve ikamet koşullarını okuyun; kayıtlı merkezin fiilen tarama yaptığını sorun.</li><li>Türkiye’de yaşadığınızı belirtip seyahat, konaklama, bakım veren ve uzun dönem takip koşullarını öğrenin.</li><li>Mevcut ilaçlarınızı kendi başınıza değiştirmeyin. Uygunluk ve güvenlilik değerlendirmesini hekim ve çalışma ekibi yapar.</li><li>İlk aşamada bilgi isteyin; sağlık belgelerini yalnızca doğrulanmış kurumun istediği güvenli kanaldan iletin.</li></ol></section>'
questions = '<section class="article-section"><h2>Çalışma ekibine sorulabilecek sorular</h2><p>Türkiye’de ikamet edenleri kabul ediyor musunuz? Hangi kohort taramaya açık? Kaç ziyaret ve ne kadar bölgede kalış gerekiyor? Bakım veren gerekli mi? Seyahat desteği neleri kapsıyor? Kullanılan ilaçlar uygunluğu nasıl etkiliyor? Değerlendirme sonucunu kim ve hangi kanaldan bildiriyor?</p><p>Bu site başvuru toplamaz ve kişisel uygunluk kararı vermez. Açık alım kaydı bile kabul garantisi değildir. Ruhsatlı tedaviye erişim, webinar kaydı ve klinik araştırma başvurusu birbirinden farklı süreçlerdir.</p></section>'
guide_body = guide_intro + guide_toc + '<div class="article-prose">' + steps + guide_sections + questions + '</div></article>'
(ROOT / 'katilim-rehberi.html').write_text(page('Klinik araştırmalara katılım rehberi',guide_body,'katilim-rehberi.html','11 FA ilaç ve çalışma programı için katılım, merkez ve resmî iletişim rehberi.','katilim-rehberi.html'))

# Replace old query links throughout retained pages; old shared URLs still resolve.
newslinks = {'lx2006':'lx2006-mds','dt216p2':'dt216p2-ilk-veri','brave':'brave-alim'}
for path in ROOT.glob('*.html'):
    text=path.read_text()
    text=re.sub(r'<span class="mark"(?: aria-hidden="true")?>FA</span>', '<img class="brand-symbol" src="fa-logo.svg" width="52" height="52" alt="" aria-hidden="true">', text)
    text=text.replace('<a class="brand" href="index.html">FA Türkiye Haber Merkezi</a>', '<a class="brand" href="index.html"><img class="brand-symbol" src="fa-logo.svg" width="52" height="52" alt="" aria-hidden="true"><span>FA Türkiye<br><small>Haber Merkezi</small></span></a>')
    if '<link rel="icon"' not in text:
        text=text.replace('</head>', '<link rel="icon" type="image/svg+xml" href="fa-logo.svg"></head>')
    if path.name=='index.html':
        for k,v in newslinks.items():
            text=text.replace('href="ilaclar.html?ilac='+k+'"','href="haber-'+v+'.html"')
    for k in profiles:
        text=text.replace('href="ilaclar.html?ilac='+k+'"','href="ilac-'+k+'.html"')
    if path.name=='tedaviler.html':
        if 'Skyclarys kapsamlı dosyasını oku' not in text:
            text=text.replace('EMA ürün bilgisi ↗</a>', 'EMA ürün bilgisi ↗</a><p><a href="ilac-skyclarys.html">Skyclarys kapsamlı dosyasını oku →</a></p>')
    path.write_text(text)

print(json.dumps({'profiles':len(profiles),'news':len(news)+1,'profile_words':{k:sum(len(p.split()) for _,p in v['sections']) for k,v in profiles.items()}},ensure_ascii=False))

