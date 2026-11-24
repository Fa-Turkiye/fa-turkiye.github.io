"""Build a sourced, filterable study list from the existing trial directory."""

import json
import re
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlsplit


MONTHS = ('Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
          'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık')
STATUS_ORDER = {'open': 0, 'planned': 1, 'closed': 2, 'check': 3}


def label_date(value):
    day = date.fromisoformat(value)
    return f'{day.day} {MONTHS[day.month - 1]} {day.year}'


def build(root: Path):
    trials = json.loads((root / 'study-centers.json').read_text(encoding='utf-8'))
    directory = json.loads((root / 'centers.json').read_text(encoding='utf-8'))
    entries = json.loads((root / 'trial-finder.json').read_text(encoding='utf-8'))
    known = {item['id']: item for item in trials['trials']}
    countries = {**directory['countries'], **trials.get('countries', {})}
    seen = set()
    cards = []
    for item in sorted(entries, key=lambda row: (STATUS_ORDER[row['status']], row['id'])):
        identifier = item['id']
        if identifier in seen or identifier not in known:
            raise ValueError(f'Tekrarlanan veya kaydı bulunmayan çalışma: {identifier}')
        seen.add(identifier)
        if item['status'] not in STATUS_ORDER:
            raise ValueError(f'Geçersiz çalışma durumu: {identifier}')
        source = urlsplit(item['status_source'])
        if source.scheme != 'https' or not source.hostname or source.username:
            raise ValueError(f'Geçersiz durum kaynağı: {identifier}')
        checked = label_date(item['checked_on'])
        low, high = item['age_min'], item['age_max']
        if (low is None and high is not None) or (
            low is not None and (not isinstance(low, int) or low < 0 or
                                 high is not None and (not isinstance(high, int) or high < low))
        ):
            raise ValueError(f'Geçersiz yaş aralığı: {identifier}')
        trial = known[identifier]
        program = item.get('program', trial['program'])
        places = sorted({place['country'] for place in trial['locations']},
                        key=lambda code: countries[code])
        place_labels = ', '.join(countries[code] for code in places) or 'Kayıtta merkez bulunamadı'
        dossier = item.get('dossier', 'nomlabofusp' if program == 'jive' else 'skyclarys' if program == 'brave' else program)
        dossier_link = f'<a href="ilac-{escape(dossier)}.html">Tedavi dosyası</a>' if dossier else ''
        country_note = f'<p class="trial-meta">{escape(item["country_note"])}</p>' if item.get('country_note') else ''
        minimum = '' if low is None else str(low)
        maximum = '' if high is None else str(high)
        cards.append(f'''<article class="trial-card" data-program="{escape(program)}" data-status="{escape(item['status'])}" data-countries=" {' '.join(places)} " data-min-age="{minimum}" data-max-age="{maximum}">
<div class="trial-card-top"><span class="trial-status trial-status-{escape(item['status'])}">{escape(item['status_label'])}</span><span>{escape(item['phase'])}</span></div>
<h3>{escape(trial['title'])}</h3><p class="trial-meta"><strong>Yaş:</strong> {escape(item['age_label'])}</p>
<p class="trial-meta"><strong>Kayıtta listelenen ülkeler:</strong> {escape(place_labels)}</p>{country_note}
<p class="trial-check">Durum kaynağı <time datetime="{escape(item['checked_on'])}">{checked}</time> tarihinde kontrol edildi.</p>
<div class="trial-links"><a href="{escape(trial['url'])}">Resmî çalışma kaydı · {escape(identifier)}</a><a href="{escape(item['status_source'])}">Alım durumu kaynağı</a>{dossier_link}</div></article>''')

    program_names = {}
    for row in entries:
        program = row.get('program', known[row['id']]['program'])
        label = row.get('program_label', trials['programs'][known[row['id']]['program']])
        program_names.setdefault(program, label)
    options = ''.join(f'<option value="{escape(key)}">{escape(value)}</option>'
                      for key, value in program_names.items())
    country_codes = sorted({loc['country'] for id in seen for loc in known[id]['locations']},
                           key=lambda code: countries[code])
    country_options = ''.join(f'<option value="{code}">{escape(countries[code])}</option>'
                              for code in country_codes)
    section = f'''<section class="wrap trial-finder" id="calisma-bul" aria-labelledby="trial-finder-title">
<div class="trial-intro"><div><h2 id="trial-finder-title">Çalışmaları karşılaştırın</h2><p>İlaç, ülke, yaş ve katılımcı alım durumuna göre {len(entries)} kayıtlı çalışmayı tarayın.</p></div><a href="katilim-rehberi.html">Katılım rehberini oku</a></div>
<form id="trial-filters" class="trial-filters" aria-label="Klinik araştırmaları filtrele" hidden>
<label>İlaç veya program<select id="trial-program"><option value="">Tüm programlar</option>{options}</select></label>
<label>Ülke<select id="trial-country"><option value="">Tüm ülkeler</option>{country_options}</select></label>
<label>Yaş<input id="trial-age" type="number" inputmode="numeric" min="0" max="100" placeholder="Örn. 24"></label>
<label>Katılımcı alımı<select id="trial-status"><option value="">Tüm durumlar</option><option value="open">Alım açık</option><option value="planned">Henüz alım başlamadı</option><option value="closed">Alım kapalı</option><option value="check">Durumu doğrulayın</option></select></label>
<button type="reset" class="trial-reset">Filtreleri temizle</button></form>
<p id="trial-result" class="trial-result" role="status" aria-atomic="true" hidden></p>
<div class="trial-grid">{''.join(cards)}</div>
<p id="trial-empty" class="note" hidden>Bu filtrelerle kayıt bulunamadı. Yaşı veya ülkeyi temizleyip yeniden arayın.</p>
<p class="trial-caution">Yaş aralığı ve listelenen ülke tek başına katılım hakkı göstermez. Merkezlerin alımı değişebilir; başvurmadan önce resmî kaydı ve çalışma ekibini kontrol edin. Bu sayfa sağlık bilgisi toplamaz.</p>
</section>'''
    page = root / 'klinik-arastirmalar.html'
    html = page.read_text(encoding='utf-8')
    pattern = r'<!-- trial-finder:start -->.*?<!-- trial-finder:end -->'
    if len(re.findall(pattern, html, flags=re.S)) != 1:
        raise ValueError('Klinik araştırmalar sayfasında çalışma bulucu işaretleri eksik')
    html = re.sub(pattern, lambda _: f'<!-- trial-finder:start -->{section}<!-- trial-finder:end -->', html, count=1, flags=re.S)
    page.write_text(html, encoding='utf-8')

