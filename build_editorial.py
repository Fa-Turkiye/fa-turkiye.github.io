"""Build accessible, static Turkish research dossiers from editorial JSON."""
import json, re, html, math
from pathlib import Path
from study_centers import StudyCenters

ROOT = Path(__file__).resolve().parent
study_centers = StudyCenters(ROOT)
profiles = json.loads((ROOT / 'editorial-content.json').read_text())
news = json.loads((ROOT / 'editorial-news.json').read_text())
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
names = {'skyclarys':'Omaveloxolone · Skyclarys','vatiquinone':'Vatiquinone · PROVE-FA','nomlabofusp':'Nomlabofusp · FORWARD-FA','dt216p2':'DT-216P2 · RESTORE-FA','lx2006':'LX2006 · SUNRISE-FA 2','sgt212':'SGT-212 · FALCON','gv101':'GV101 · ROCK2 inhibitörü','ppl001':'PPL-001 · gen düzenlenmiş hücre tedavisi','nbib223':'NBIB-223 · FACET','brave':'Omaveloxolone · BRAVE','jive':'Nomlabofusp · JIVE/OLE'}
sponsors = {'skyclarys':'Biogen','vatiquinone':'PTC Therapeutics','nomlabofusp':'Larimar Therapeutics','dt216p2':'Design Therapeutics','lx2006':'Lexeo Therapeutics','sgt212':'Solid Biosciences','gv101':'Graviton BioScience','ppl001':'Papillon Therapeutics','nbib223':'Neurocrine Biosciences / Voyager Therapeutics','brave':'Biogen','jive':'Larimar Therapeutics'}

def page(title, body, filename, description, active='ilaclar.html'):
    nav = header.replace(f'href="{active}"', f'href="{active}" aria-current="page"')
    return f'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · FA Türkiye</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="https://fa-turkiye.github.io/{filename}">
<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="articles.css">
<link rel="icon" type="image/svg+xml" href="fa-logo.svg"><script src="script.js" defer></script><meta name="theme-color" content="#f7f7ef"></head><body><a class="skip-link" href="#main-content">İçeriğe geç</a>{nav}
<main class="wrap editorial-main" id="main-content" tabindex="-1">{body}</main><footer><div class="wrap">FA Türkiye · Haber Merkezi. Kaynaklara dayalı bağımsız bilgilendirme. Tedavi ve katılım kararları hekim ve çalışma ekibiyle değerlendirilir.</div></footer></body></html>'''

def article_body(title, status, sections, sources, category, back, sponsor=None, extra='', lead=None, studies=''):
    count = sum(len(p.split()) for _, p in sections)
    lead_text = lead or '. '.join(sections[0][1].split('. ')[:2]).rstrip('.') + '.'
    toc = ''.join(f'<li><a href="#bolum-{i}">{esc(t)}</a></li>' for i,(t,_) in enumerate(sections,1))
    if studies:
        toc += '<li><a href="#arastirma-merkezleri">Araştırma merkezleri</a></li>'
    paragraphs = ''.join(f'<section id="bolum-{i}" class="article-section"><h2>{esc(t)}</h2><p>{esc(p)}</p></section>' for i,(t,p) in enumerate(sections,1))
    src = ''.join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a></li>' for t,u in sources)
    return f'''<p class="breadcrumb"><a href="{back}">← {category}</a></p><article class="long-article">
<div class="article-heading"><span class="badge">{esc(status)}</span><h1>{esc(title)}</h1>
<p class="article-meta">Son kaynak kontrolü: <time datetime="2026-11-01">1 Kasım 2026</time> · Yaklaşık {max(2,math.ceil(count/160))} dakika okuma</p>
{f'<p class="article-meta">Geliştirici: {esc(sponsor)}</p>' if sponsor else ''}<p class="article-lead">{esc(lead_text)}</p></div>
<nav class="article-toc" aria-label="Yazı içindekiler"><h2>Bu yazıda</h2><ol>{toc}</ol></nav>
<div class="article-prose">{paragraphs}{studies}{extra}<section id="kaynaklar" class="article-section article-sources"><h2>Kaynaklar ve doğrulama</h2><ol>{src}</ol><p class="article-meta">Özgün Türkçe açıklama ve değerlendirme. Şirket hedefleri, açıklanmış bulgular ve henüz doğrulanmayan noktalar metinde ayrılmıştır. Kaynak tarihleri ve merkezlerin alım durumları farklı olabilir.</p></section></div>
<p class="article-end"><a href="{back}">← {category} sayfasına dön</a></p></article>'''

for key, item in profiles.items():
    filename = f'ilac-{key}.html'
    related = [n for n in news if n['drug']==key]
    more = '<aside class="article-related"><h2>İlgili ayrıntılı haberler</h2><ul>'+''.join(f'<li><a href="haber-{n["id"]}.html">{esc(n["title"])}</a></li>' for n in related)+'</ul></aside>' if related else ''
    if key=='skyclarys': more += '<p><a href="ilac-brave.html#arastirma-merkezleri">BRAVE çocuk çalışması ve merkezleri →</a></p>'
    if key=='brave': more += '<p><a href="ilac-skyclarys.html">Omaveloxolone’un ana ilaç dosyasını da okuyun →</a></p>'
    if key=='jive': more += '<p><a href="ilac-nomlabofusp.html">Nomlabofusp ana ilaç dosyasını da okuyun →</a></p>'
    more += '<p><a href="katilim-rehberi.html#program-'+key+'">Bu programın katılım rehberini aç →</a></p>'
    body = article_body(item['title'],item['status'],item['sections'],item['sources'],'İlaç kütüphanesi','ilaclar.html',sponsors[key],more,studies=study_centers.dossier(key))
    (ROOT / filename).write_text(page(item['title'],body,filename,item['sections'][0][1]))

cards = ''.join(f'''<a class="card dossier-card" href="ilac-{k}.html"><span class="badge">{esc(v['status'])}</span><h2>{esc(names[k])}</h2><p>{esc(v['sections'][0][1].split('. ')[0])}.</p><b>Kapsamlı dosyayı oku →</b></a>''' for k,v in profiles.items())
intro = '<div class="editorial-intro"><span class="badge">İLAÇ KÜTÜPHANESİ</span><h1>Bir özetten fazlası: FA tedavi dosyaları</h1><p>Hedef, mekanizma, geliştirme geçmişi, açıklanan sonuçlar, güvenlilik ve Türkiye’den katılım bilgileri. Her dosyada resmî kaynaklar ve kontrol tarihi bulunur.</p><p>Çalışma dosyalarındaki <strong>Araştırma merkezleri</strong> bölümünden kurum listesine ulaşabilirsiniz. <a href="merkezler.html">FA Merkezleri rehberi</a></p><p class="article-meta">9 tedavi/program dosyası ve aynı tedavilere ait 2 ayrı çalışma dosyası · 1 Kasım 2026</p></div>'
body = intro + '<div class="dossier-grid">'+cards+'</div><p><a href="https://www.curefa.org/drug-development/">FARA’nın tam geliştirme hattı ve geçmiş programları ↗</a></p>'
aliases = json.dumps({k:f'ilac-{k}.html' for k in profiles})
redirect = '<script>const dossierRoutes='+aliases+';const requested=new URLSearchParams(location.search).get("ilac");if(Object.hasOwn(dossierRoutes,requested)){location.replace(dossierRoutes[requested]+location.hash);}</script>'
(ROOT / 'ilaclar.html').write_text(page('İlaç kütüphanesi',body,'ilaclar.html','FA için kaynaklı ve kapsamlı 11 ilaç ve çalışma profili.').replace('</body>',redirect+'</body>'))

for n in news:
    sources = profiles[n['drug']]['sources']
    extra = f'<aside class="article-related"><h2>Programın tamamını inceleyin</h2><p><a href="ilac-{n["drug"]}.html">{esc(names[n["drug"]])}: mekanizma, kanıt, güvenlilik ve katılım →</a></p></aside>'
    sections = [('Haber tarihi ve kapsamı', f'Gelişmenin tarihi: {n["date"]}. Bu haber 1 Kasım 2026 kaynak kontrolüyle hazırlanmıştır; sonraki açıklamalar için ilgili ilaç dosyasına bakın.')] + n['sections']
    body = article_body(n['title'],n['date'],sections,sources,'Son haberler','haberler.html',extra=extra,lead=n['summary'])
    fn = f'haber-{n["id"]}.html'
    (ROOT / fn).write_text(page(n['title'],body,fn,n['summary'],'haberler.html'))

# Preserve the existing GV101 news URL and expand its contents.
g = profiles['gv101']
gvbody = article_body('GV101 için klinik araştırma izni: ne değişti, ne henüz bilinmiyor?','11 Ağustos 2026 · Geliştirme duyurusu',g['sections'],g['sources'],'Son haberler','haberler.html',extra='<p><a href="ilac-gv101.html">GV101 ana ilaç dosyası →</a></p>')
(ROOT / 'haber-gv101.html').write_text(page('GV101 için klinik araştırma izni',gvbody,'haber-gv101.html','GV101 IND izni, FA araştırmasının amacı ve kanıt sınırları.','haberler.html'))

newscards = ''.join(f'<article class="card dossier-card"><time class="badge" datetime="{n["iso"]}">{n["date"]}</time><h2><a href="haber-{n["id"]}.html">{esc(n["title"])}</a></h2><p>{esc(n["summary"])}</p><a class="textlink" href="haber-{n["id"]}.html">Haberin tamamını oku →</a></article>' for n in sorted(news,key=lambda n:n['iso'],reverse=True))
# Put August GV101 news in chronological order, rather than at the end.
gvcard = '<article class="card dossier-card"><time class="badge" datetime="2026-08-11">11 Ağustos 2026</time><h2><a href="haber-gv101.html">GV101 için FA klinik araştırma izni</a></h2><p>ROCK2 hedefi, planlanan araştırma ve henüz doğrulanmayan katılım bilgileri.</p><a class="textlink" href="haber-gv101.html">Haberin tamamını oku →</a></article>'
marker = '<article class="card dossier-card"><time class="badge" datetime="2026-08-03">'
newscards = newscards.replace(marker,gvcard+marker,1)
body = '<div class="editorial-intro"><span class="badge">SON HABERLER</span><h1>Gelişmenin arkasındaki bilim</h1><p>Ne açıklandı, hangi veriye dayanıyor, hastalar için ne ifade ediyor? Kısa kartlardan kaynaklı tam haberlere geçin.</p><p class="article-meta">Haber tarihleri olayın tarihidir. Son editoryal kontrol: 1 Kasım 2026.</p></div><div class="dossier-grid">'+newscards+'</div>'
(ROOT / 'haberler.html').write_text(page('Son haberler',body,'haberler.html','FA araştırmalarını ayrıntılı ve kaynaklı Türkçe haberlerle takip edin.','haberler.html'))

# Existing dedicated GV101 address remains useful and consistent.
(ROOT / 'gv101.html').write_text(page(g['title'],article_body(g['title'],g['status'],g['sections'],g['sources'],'İlaç kütüphanesi','ilaclar.html',sponsors['gv101'],studies=study_centers.dossier('gv101')),'gv101.html',g['sections'][0][1]))

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

