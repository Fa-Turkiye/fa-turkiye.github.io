"""Generate merkezler.html from the sourced records in centers.json."""

from collections import defaultdict
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import unicodedata
from study_centers import StudyCenters, center_id

ROOT = Path(__file__).resolve().parent
KINDS = {
    "clinic": "Klinik bakım",
    "genetics": "Tanı ve genetik birimi",
    "fa-test": "FA’ya özgü genetik test",
    "research": "Araştırma",
}
MONTHS = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")


def text_key(value):
    value = unicodedata.normalize("NFKD", value.casefold().replace("ı", "i"))
    return "".join(char for char in value if not unicodedata.combining(char))


def external_link(url, label):
    parts = urlsplit(url)
    if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username:
        raise ValueError(f"Geçersiz kurum veya kaynak bağlantısı: {url}")
    return f'<a href="{escape(url)}">{escape(label)}</a>'


def contact_link(contact):
    label = contact["label"]
    value = contact["value"]
    if contact["kind"] == "url":
        return external_link(value, label)
    if contact["kind"] == "email":
        if not re.fullmatch(r"[A-Za-z0-9.!+_-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value):
            raise ValueError(f"Geçersiz e-posta: {value}")
        href = f"mailto:{value}"
    elif contact["kind"] == "phone":
        number, *extension = re.split(r"\s*(?:;ext=|\b(?:dahili|ext\.?|x)\s*)", value, maxsplit=1, flags=re.I)
        dial = re.sub(r"[^+0-9]", "", number.replace("(0)", ""))
        if not re.fullmatch(r"\+?[0-9]{5,15}", dial) or any(not part.isdigit() for part in extension):
            return f"{escape(label)} <span>{escape(value)}</span>"
        href = f"tel:{dial}"
        if extension:
            href += f";ext={extension[0]}"
    else:
        raise ValueError(f'Geçersiz iletişim türü: {contact["kind"]}')
    return f'{escape(label)} <a href="{escape(href)}">{escape(value)}</a>'


def record_html(center, study_centers):
    types = center["types"]
    tags = [kind for kind in types if kind != "genetics" or "fa-test" not in types]
    kinds = "".join(f'<span class="tag">{KINDS[kind]}</span>' for kind in tags)
    if not center["contacts"] or not center["sources"]:
        raise ValueError(f'{center["name"]} için iletişim veya kaynak eksik')

    contacts = "".join(f"<li>{contact_link(contact)}</li>" for contact in center["contacts"])
    sources = "".join(f'<li>{external_link(source["url"], source["label"])}</li>' for source in center["sources"])
    people = []
    for person in center["people"]:
        name = external_link(person["url"], person["name"]) if person.get("url") else escape(person["name"])
        people.append(f'<li><span class="center-person">{name}</span> <small>{escape(person["role"])}</small></li>')
    staff = f'<ul class="directory-items">{"".join(people)}</ul>' if people else '<p>İlgili hekim için kurumla iletişime geçin.</p>'
    address = f'<address>{escape(center["address"])}</address>' if center.get("address") else ""
    note = f'<p class="center-note">{escape(center["note"])}</p>' if center.get("note") else ""
    service_items = []
    for service in center.get("services", []):
        name = escape(service["name"])
        description = escape(service["description"])
        source = external_link(service["url"], f'{service["name"]} kaynağı')
        service_items.append(f'<li><strong>{name}</strong><p>{description}</p>{source}</li>')
    services = ""
    if service_items or note:
        service_list = f'<ul class="directory-items center-services">{"".join(service_items)}</ul>' if service_items else ""
        services = f'<div class="center-service-info"><h3>Birimler ve hizmetler</h3>{service_list}{note}</div>'
    identifier = center_id(center)
    return f"""
        <details class="center-record" id="{identifier}" data-types="{' '.join(types)}">
          <summary>
            <span class="center-name">{escape(center["name"])}</span>
            <span class="center-city">{escape(center["city"])}</span>
            <span class="center-kinds">{kinds}</span>
          </summary>
          <div class="center-info">
            {address}
            {services}
            {study_centers.card(identifier)}
            <h3>Hekimler ve araştırma ekibi</h3>
            {staff}
            <h3>İletişim</h3>
            <ul class="directory-items">{contacts}</ul>
            <h3>Kaynaklar</h3>
            <ul class="directory-items center-sources">{sources}</ul>
          </div>
        </details>"""


def build():
    data = json.loads((ROOT / "centers.json").read_text(encoding="utf-8"))
    study_centers = StudyCenters(ROOT, data)
    checked_on = date.fromisoformat(data["checked_on"])
    checked_label = f"{checked_on.day} {MONTHS[checked_on.month - 1]} {checked_on.year}"
    countries = data["countries"]
    groups = defaultdict(list)
    seen = set()
    for center in data["centers"]:
        country = center["country"]
        key = (country, text_key(center["city"]), text_key(center["name"]))
        if key in seen or country not in countries or not center["types"]:
            raise ValueError(f"Tekrarlanan veya eksik merkez kaydı: {key}")
        seen.add(key)
        groups[country].append(center)

    codes = sorted(groups, key=lambda code: (code != "TR", text_key(countries[code])))
    sections = []
    for code in codes:
        records = sorted(groups[code], key=lambda center: (text_key(center["city"]), text_key(center["name"])))
        cards = "".join(record_html(center, study_centers) for center in records)
        sections.append(f"""
      <section class="center-country" data-country="{code}" id="ulke-{code.lower()}" aria-labelledby="baslik-{code.lower()}">
        <h2 id="baslik-{code.lower()}">{escape(countries[code])} <span data-country-count>{len(records)} merkez</span></h2>
        <div class="center-grid">{cards}
        </div>
      </section>""")

    options = "".join(f'<option value="{code}">{escape(countries[code])}</option>' for code in codes)
    kind_options = "".join(f'<option value="{kind}">{label}</option>' for kind, label in KINDS.items())
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    header = re.search(r"<header>.*?</header>", home, re.S).group()
    header = header.replace(' aria-current="page"', "").replace(
        'href="merkezler.html"', 'href="merkezler.html" aria-current="page"'
    )
    turkey = '<a href="#ulke-tr">Türkiye’deki merkezler</a>' if "TR" in groups else ""
    count = len(data["centers"])
    (ROOT / "merkezler.html").write_text(f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#f7f7ef">
  <title>Dünyada Friedreich ataksisi merkezleri · FA Türkiye</title>
  <meta name="description" content="Friedreich ataksisi kliniklerini, tanı ve araştırma merkezlerini ülkeye, şehre veya hekime göre bulun. Kurum adresleri, iletişim bilgileri ve kaynaklar.">
  <link rel="canonical" href="https://fa-turkiye.github.io/merkezler.html">
  <link rel="icon" href="fa-logo.svg" type="image/svg+xml">
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="merkezler.css">
  <script src="script.js" defer></script>
  <script src="merkezler.js" defer></script>
</head>
<body class="directory-page">
  <a class="skip-link" href="#main-content">İçeriğe geç</a>
  {header}
  <main class="wrap" id="main-content" tabindex="-1">
    <section class="directory-intro" aria-labelledby="directory-title">
      <h1 id="directory-title">FA Merkezleri</h1>
      <p>Dünya genelinde Friedreich ataksisiyle ilgili klinik bakım, genetik tanı ve araştırma merkezleri. Birimlere, hekimlere ve kurumsal iletişim bilgilerine ulaşın.</p>
      <div class="directory-facts">
        <strong>{len(codes)} ülke, {count} merkez</strong>
        <span>Kaynak kontrolü <time datetime="{checked_on}">{checked_label}</time></span>
        {turkey}
        <a href="ilaclar.html">Tedavi ve çalışma dosyaları</a>
      </div>
    </section>
    <form class="directory-filters" role="search" aria-label="Merkezleri filtrele" hidden>
      <div class="directory-field">
        <label for="center-query">Merkezlerde ara</label>
        <input id="center-query" type="search" autocomplete="off" placeholder="Örn. İzmir, FXN, LX2006" aria-describedby="center-query-help">
        <small id="center-query-help">Şehir, hekim, hizmet veya çalışma adı</small>
      </div>
      <div class="directory-field">
        <label for="center-country">Ülke</label>
        <select id="center-country"><option value="">Tüm ülkeler</option>{options}</select>
      </div>
      <div class="directory-field">
        <label for="center-kind">Merkez türü</label>
        <select id="center-kind"><option value="">Tüm türler</option>{kind_options}</select>
      </div>
    </form>
    <p class="directory-result" id="center-result" role="status" aria-atomic="true" hidden></p>
    <p class="note" id="center-empty" hidden>Arama sözcüğünü kısaltın veya ülke ve merkez türü filtrelerini genişletin.</p>
    {"".join(sections)}
    <section class="directory-method" aria-labelledby="directory-sources">
      <h2 id="directory-sources">Rehberin kapsamı</h2>
      <p>Rehber, resmî kurum sayfalarında, ulusal nadir hastalık ağlarında veya FA çalışma kayıtlarında bağlantısı doğrulanabilen merkezleri kapsar. Hekim ve ekip bilgileri ilgili kurumun veya çalışmanın yayımladığı kapsamla sınırlıdır. Güncel görev, randevu koşulları ve ziyaret adresi için doğrudan kuruma başvurun.</p>
      <p>Tanı ve genetik birimlerinde, kaynağında yer alan FA testini veya danışmanlık hizmetini ayrı ayrı belirttik. Araştırma iletişimini çalışma hakkında bilgi almak için, randevu hatlarını klinik değerlendirme için kullanın. Ulusal listeler ve çalışma kayıtları ek merkezlere ulaşmanıza yardımcı olabilir.</p>
      <p>Tedavi çalışması bağlantıları kurum adı doğrulanabilen kayıtları kapsar. Çalışmanın güncel katılım durumunu resmî kayıttan ve çalışma ekibinden öğrenebilirsiniz.</p>
      <ul class="directory-items">
        <li><a href="https://www.curefa.org/research/initiatives/fa-global-clinical-consortium/">FARA · Küresel FA Klinik Konsorsiyumu</a></li>
        <li><a href="https://www.orpha.net/en/expert-centres/centres/95?age=all&amp;consulting=medical&amp;diseaseName=Friedreich+ataxia&amp;official=0">Orphanet · Friedreich ataksisi uzman merkezleri</a></li>
        <li><a href="https://www.malattierare.gov.it/centri_cura/elenco_per_malattia/75">İtalya Sağlık Bakanlığı · FA tanı ve bakım merkezleri</a></li>
        <li><a href="https://www.afaf.asso.fr/la-maladie/prise-en-charge-medicale/">AFAF · Fransa FA klinik ağı</a></li>
        <li><a href="avrupa-merkezleri.html">Avrupa’daki FA araştırma merkezleri ve çalışma kayıtları</a></li>
      </ul>
    </section>
  </main>
  <footer><div class="wrap">FA Türkiye · Friedreich ataksisi bilgi merkezi.</div></footer>
</body>
</html>
""", encoding="utf-8")
    print(f"{count} merkez, {len(codes)} ülke")


if __name__ == "__main__":
    build()
