"""Render verified study locations in both the treatment and center directories."""

from collections import defaultdict
from datetime import date
from html import escape
from urllib.parse import urlsplit
import json
import re
import unicodedata


def slug(value):
    folded = unicodedata.normalize("NFKD", value.casefold().replace("ı", "i"))
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def center_id(center):
    return slug(f'merkez-{center["country"]}-{center["city"]}-{center["name"]}')


def source_link(url, label):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username is not None:
        raise ValueError(f"Geçersiz çalışma kaynağı: {url}")
    return f'<a href="{escape(url)}">{escape(label)}</a>'


class StudyCenters:
    def __init__(self, root, directory=None):
        data = json.loads((root / "study-centers.json").read_text(encoding="utf-8"))
        if directory is None:
            directory = json.loads((root / "centers.json").read_text(encoding="utf-8"))
        self.programs = data["programs"]
        self.program_sources = data.get("programSources", {})
        self.countries = {**directory["countries"], **data.get("countries", {})}
        self.checked_on = date.fromisoformat(data["checked_on"])
        self.by_program = defaultdict(list)
        self.by_center = defaultdict(list)
        self.unpublished = {item["program"]: item for item in data["unpublished"]}
        ids = [center_id(center) for center in directory["centers"]]
        if len(set(ids)) != len(ids):
            raise ValueError("Merkez bağlantıları benzersiz olmalı")
        known_centers = set(ids)
        seen = set()
        for trial in data["trials"]:
            key = slug(trial["id"])
            if not key or key in seen:
                raise ValueError(f'Tekrarlanan veya eksik çalışma kimliği: {trial["id"]}')
            if trial["program"] not in self.programs:
                raise ValueError(f'Program adı eksik: {trial["program"]}')
            seen.add(key)
            self.by_program[trial["program"]].append(trial)
            paired = set()
            for location in trial["locations"]:
                if location["country"] not in self.countries:
                    raise ValueError(f'Ülke adı eksik: {location["country"]}')
                center = location.get("center")
                if center:
                    if center not in known_centers or center in paired:
                        raise ValueError(f'Geçersiz merkez eşleşmesi: {trial["id"]}, {center}')
                    paired.add(center)
                    self.by_center[center].append((trial, location))

    def dossier(self, program):
        trials = self.by_program.get(program, [])
        unpublished = self.unpublished.get(program)
        program_sources = self.program_sources.get(program, [])
        if not trials and not unpublished and not program_sources:
            return ""
        checked = self.checked_on.strftime("%d.%m.%Y")
        content = [
            '<section id="arastirma-merkezleri" class="article-section study-centers" aria-labelledby="study-centers-title">',
            '<h2 id="study-centers-title">Resmî kaynaklar ve iletişim</h2>',
            f'<p class="article-meta">Merkez kaynakları <time datetime="{self.checked_on}">{checked}</time> tarihinde kontrol edildi.</p>',
        ]
        if program_sources:
            content.append('<h3>Firma ve program kaynakları</h3><ul>')
            for source in program_sources:
                content.append(f'<li>{source_link(source["url"], source["label"])}</li>')
            content.append('</ul>')
        if trials:
            content.append(
                '<p>Resmî kaydın “Contacts and Locations” bölümünde, yayımlandığı ölçüde araştırma ekibi, '
                'merkezler ve iletişim bilgileri yer alır. Güncel durum için çalışma kaydını kontrol edin.</p>'
            )
        for trial in trials:
            content.append(self.trial_locations(trial, program_sources))
        if unpublished:
            if not trials:
                content.append('<h3>Klinik çalışma ve merkez durumu</h3>')
            source = unpublished["source"]
            content.append(f'<p>{escape(unpublished["text"])}</p>')
            content.append(f'<p>{source_link(source["url"], source["label"])}</p>')
        content.append('<p><a href="merkezler.html">FA Merkezleri rehberini aç</a></p></section>')
        return "".join(content)

    def trial_locations(self, trial, program_sources):
        locations = trial["locations"]
        heading = f'<h3 id="calisma-{slug(trial["id"])}">{escape(trial["title"])}</h3>'
        note = f'<p>{escape(trial["note"])}</p>' if trial.get("note") else ""
        sources = trial.get("extraSources", [])
        published_sources = {source["url"].split("#", 1)[0] for source in [*program_sources, *sources]}
        published_sources.add(trial["url"])
        rows = []
        for location in locations:
            city = escape(location["city"])
            country = escape(self.countries[location["country"]])
            name = escape(location["name"])
            if location.get("center"):
                name = f'<a href="merkezler.html#{escape(location["center"])}">{name}</a>'
            description = f'<small>{escape(location["note"])}</small>' if location.get("note") else ""
            url = location.get("sourceUrl")
            reference = ""
            if url and url.split("#", 1)[0] not in published_sources:
                reference = f'<small>{source_link(url, "Merkez kaynağı")}</small>'
            investigator = location.get("investigator")
            if investigator:
                profile = source_link(investigator["url"], investigator["name"])
                description += f'<small>Sorumlu araştırmacı · {profile}</small>'
            contact = location.get("contact")
            if contact:
                email = escape(contact["email"])
                description += (
                    f'<small>Araştırma iletişimi · {escape(contact["name"])} · '
                    f'<a href="mailto:{email}">{email}</a></small>'
                )
            rows.append(f'<li><strong>{name}</strong><small>{city}, {country}</small>{description}{reference}</li>')
        listing = ""
        if rows:
            open_attr = " open" if len(rows) <= 8 else ""
            listing = (
                f'<details class="study-location-list"{open_attr}><summary>{len(rows)} merkez</summary>'
                f'<ul>{"".join(rows)}</ul></details>'
            )
        registry = source_link(
            trial["url"], f'{trial["sourceLabel"]} · {trial["id"]} çalışma kaydı ve iletişim'
        )
        program_urls = {source["url"] for source in program_sources}
        other_links = [
            source_link(source["url"], source["label"]) for source in sources
            if source["url"] not in program_urls
        ]
        links = " · ".join(other_links)
        related = f'<p class="study-source-links">{links}</p>' if links else ""
        return f'<div class="study-location-group">{heading}{note}<p>{registry}</p>{listing}{related}</div>'

    def card(self, identifier):
        links = self.by_center.get(identifier, [])
        if not links:
            return ""
        programs = dict.fromkeys(trial["program"] for trial, _ in links)
        aliases = escape(" ".join(f"{key} {self.programs[key]}" for key in programs))
        rows = []
        for trial, location in links:
            program = trial["program"]
            label = escape(trial["title"])
            dossier = f'ilac-{escape(program)}.html#calisma-{slug(trial["id"])}'
            url = location.get("sourceUrl") or trial["url"]
            source = source_link(trial["url"], trial["sourceLabel"])
            if url.split("#", 1)[0] != trial["url"]:
                source += " · " + source_link(url, "Merkez kaynağı")
            note = f'<small>{escape(location["note"])}</small>' if location.get("note") else ""
            rows.append(f'<li><a href="{dossier}">{label}</a>{note}<small>{source}</small></li>')
        return (
            f'<div class="center-studies" data-search-aliases="{aliases}"><h3>FA tedavi çalışmaları</h3>'
            f'<ul class="directory-items">{"".join(rows)}</ul></div>'
        )
