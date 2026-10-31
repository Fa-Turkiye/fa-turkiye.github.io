"""Build accessible, static Turkish research dossiers from editorial JSON."""
import json, re, html, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
profiles = json.loads((ROOT / 'editorial-content.json').read_text())
news = json.loads((ROOT / 'editorial-news.json').read_text())
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
<script src="script.js" defer></script></head><body>{nav}
<main class="wrap editorial-main">{body}</main><footer><div class="wrap">FA Türkiye · Haber Merkezi. Kaynaklara dayalı bağımsız bilgilendirme. Tedavi ve katılım kararları hekim ve çalışma ekibiyle değerlendirilir.</div></footer></body></html>'''

def article_body(title, status, sections, sources, category, back, sponsor=None, extra=''):
    count = sum(len(p.split()) for _, p in sections)
    toc = ''.join(f'<li><a href="#bolum-{i}">{esc(t)}</a></li>' for i,(t,_) in enumerate(sections,1))
    paragraphs = ''.join(f'<section id="bolum-{i}" class="article-section"><h2>{esc(t)}</h2><p>{esc(p)}</p></section>' for i,(t,p) in enumerate(sections,1))
    src = ''.join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a></li>' for t,u in sources)
    return f'''<p class="breadcrumb"><a href="{back}">← {category}</a></p><article class="long-article">
<div class="article-heading"><span class="badge">{esc(status)}</span><h1>{esc(title)}</h1>
<p class="article-meta">Son kaynak kontrolü: <time datetime="2026-11-01">1 Kasım 2026</time> · Yaklaşık {max(2,math.ceil(count/160))} dakika okuma</p>
{f'<p class="article-meta">Geliştirici: {esc(sponsor)}</p>' if sponsor else ''}</div>
<nav class="article-toc" aria-label="Yazı içindekiler"><h2>Bu yazıda</h2><ol>{toc}</ol></nav>
<div class="article-prose">{paragraphs}{extra}<section id="kaynaklar" class="article-section article-sources"><h2>Kaynaklar ve doğrulama</h2><ol>{src}</ol><p class="article-meta">Özgün Türkçe açıklama ve değerlendirme. Şirket hedefleri, açıklanmış bulgular ve henüz doğrulanmayan noktalar metinde ayrılmıştır. Kaynak tarihleri ve merkezlerin alım durumları farklı olabilir.</p></section></div>
<p class="article-end"><a href="{back}">← {category} sayfasına dön</a></p></article>'''

for key, item in profiles.items():
    filename = f'ilac-{key}.html'
    related = [n for n in news if n['drug']==key]
    more = '<aside class="article-related"><h2>İlgili ayrıntılı haberler</h2><ul>'+''.join(f'<li><a href="haber-{n["id"]}.html">{esc(n["title"])}</a></li>' for n in related)+'</ul></aside>' if related else ''
    if key=='brave': more += '<p><a href="ilac-skyclarys.html">Omaveloxolone’un ana ilaç dosyasını da okuyun →</a></p>'
    if key=='jive': more += '<p><a href="ilac-nomlabofusp.html">Nomlabofusp ana ilaç dosyasını da okuyun →</a></p>'
    body = article_body(item['title'],item['status'],item['sections'],item['sources'],'İlaç kütüphanesi','ilaclar.html',sponsors[key],more)
    (ROOT / filename).write_text(page(item['title'],body,filename,item['sections'][0][1]))

cards = ''.join(f'''<a class="card dossier-card" href="ilac-{k}.html"><span class="badge">{esc(v['status'])}</span><h2>{esc(names[k])}</h2><p>{esc(v['sections'][0][1].split('. ')[0])}.</p><b>Kapsamlı dosyayı oku →</b></a>''' for k,v in profiles.items())
intro = '<div class="editorial-intro"><span class="badge">İLAÇ KÜTÜPHANESİ</span><h1>Bir özetten fazlası: FA tedavi dosyaları</h1><p>Hedef, mekanizma, geliştirme geçmişi, açıklanan sonuçlar, güvenlilik ve Türkiye’den katılım bilgileri. Her dosyada resmî kaynaklar ve kontrol tarihi bulunur.</p><p class="article-meta">9 tedavi/program dosyası ve aynı tedavilere ait 2 ayrı çalışma dosyası · 1 Kasım 2026</p></div>'
body = intro + '<div class="dossier-grid">'+cards+'</div><p><a href="https://www.curefa.org/drug-development/">FARA’nın tam geliştirme hattı ve geçmiş programları ↗</a></p>'
aliases = json.dumps({k:f'ilac-{k}.html' for k in profiles})
redirect = '<script>const dossierRoutes='+aliases+';const requested=new URLSearchParams(location.search).get("ilac");if(Object.hasOwn(dossierRoutes,requested)){location.replace(dossierRoutes[requested]+location.hash);}</script>'
(ROOT / 'ilaclar.html').write_text(page('İlaç kütüphanesi',body,'ilaclar.html','FA için kaynaklı ve kapsamlı 11 ilaç ve çalışma profili.').replace('</body>',redirect+'</body>'))

for n in news:
    sources = profiles[n['drug']]['sources']
    extra = f'<aside class="article-related"><h2>Programın tamamını inceleyin</h2><p><a href="ilac-{n["drug"]}.html">{esc(names[n["drug"]])}: mekanizma, kanıt, güvenlilik ve katılım →</a></p></aside>'
    sections = [('Haber tarihi ve kapsamı', f'Gelişmenin tarihi: {n["date"]}. Bu haber 1 Kasım 2026 kaynak kontrolüyle hazırlanmıştır; sonraki açıklamalar için ilgili ilaç dosyasına bakın.')] + n['sections']
    body = article_body(n['title'],n['date'],sections,sources,'Son haberler','haberler.html',extra=extra)
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
(ROOT / 'gv101.html').write_text(page(g['title'],article_body(g['title'],g['status'],g['sections'],g['sources'],'İlaç kütüphanesi','ilaclar.html',sponsors['gv101']),'gv101.html',g['sections'][0][1]))

# Replace old query links throughout retained pages; old shared URLs still resolve.
newslinks = {'lx2006':'lx2006-mds','dt216p2':'dt216p2-ilk-veri','brave':'brave-alim'}
for path in ROOT.glob('*.html'):
    text=path.read_text()
    if path.name=='index.html':
        for k,v in newslinks.items():
            text=text.replace('href="ilaclar.html?ilac='+k+'"','href="haber-'+v+'.html"')
    for k in profiles:
        text=text.replace('href="ilaclar.html?ilac='+k+'"','href="ilac-'+k+'.html"')
    if path.name=='tedaviler.html':
        text=text.replace('EMA ürün bilgisi ↗</a>', 'EMA ürün bilgisi ↗</a><p><a href="ilac-skyclarys.html">Skyclarys kapsamlı dosyasını oku →</a></p>')
    path.write_text(text)

print(json.dumps({'profiles':len(profiles),'news':len(news)+1,'profile_words':{k:sum(len(p.split()) for _,p in v['sections']) for k,v in profiles.items()}},ensure_ascii=False))
