"""Validate published FA Türkiye pages and editorial source references."""
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
SITE = "fa-turkiye.github.io"
LEGACY_WITHOUT_PRIMARY = {
    "nbib223-facet", "dt216p2-takvim", "brave-alim",
    "ppl001-uretim", "nomlabofusp-bla", "dt216p2-ilk-veri",
}
LEGACY_WITHOUT_REVIEW = LEGACY_WITHOUT_PRIMARY | {"vatiquinone-prove", "sgt212-avrupa", "lx2006-mds"}
LINK_ATTRIBUTES = {"href", "src", "action"}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.anchors = set()
        self.links = []
        self.source_links = set()
        self.in_sources = False
        self.feed(path.read_text(encoding="utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and attrs.get("id") == "kaynaklar":
            self.in_sources = True
        if attrs.get("id"):
            self.anchors.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.anchors.add(attrs["name"])
        for key in LINK_ATTRIBUTES:
            url = attrs.get(key)
            if url:
                self.links.append(url)
                if self.in_sources and tag == "a" and key == "href" and is_https(url):
                    self.source_links.add(url)

    def handle_endtag(self, tag):
        if tag == "section":
            self.in_sources = False


def is_https(url):
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username


def local_target(page, href):
    url = urlsplit(href)
    if url.scheme not in ("", "http", "https") or url.netloc not in ("", SITE):
        return None
    path = unquote(url.path)
    if not path:
        path = "index.html" if url.netloc else page
    elif path.endswith("/"):
        path += "index.html"
    elif not path.startswith("/"):
        path = posixpath.join(posixpath.dirname(page), path)
    return posixpath.normpath(path.lstrip("/")), unquote(url.fragment)


def check_links(pages):
    for name, page in pages.items():
        for href in page.links:
            target = local_target(name, href)
            if target is None:
                continue
            path, anchor = target
            if path == ".." or path.startswith("../") or not (ROOT / path).is_file():
                yield f"{name}: eksik iç bağlantı: {href}"
            elif anchor and path in pages and anchor not in pages[path].anchors:
                yield f"{name}: eksik bölüm bağlantısı: {href}"


def check_news(pages):
    items = json.loads((ROOT / "editorial-news.json").read_text(encoding="utf-8"))
    seen = set()
    for item in items:
        identifier = item["id"]
        filename = f"haber-{identifier}.html"
        if identifier in seen:
            yield f"{filename}: tekrarlanan haber kimliği"
        seen.add(identifier)
        page = pages.get(filename)
        if page is None:
            yield f"{filename}: haber sayfası eksik"
        elif not page.source_links:
            yield f"{filename}: kaynak bölümünde HTTPS bağlantısı eksik"
        primary = item.get("primary_source")
        if primary is None and identifier in LEGACY_WITHOUT_PRIMARY:
            continue
        if (not isinstance(primary, list) or len(primary) != 2
                or not isinstance(primary[0], str) or not primary[0].strip()
                or not is_https(primary[1])):
            yield f"{filename}: geçerli primary_source alanı eksik"
        elif page and identifier not in LEGACY_WITHOUT_REVIEW and primary[1] not in page.source_links:
            yield f"{filename}: birincil kaynak yayımlanan kaynaklar arasında bulunamadı"
        if identifier not in LEGACY_WITHOUT_REVIEW:
            review = item.get("source_review") or {}
            try:
                date.fromisoformat(review.get("checked_on", ""))
                if not review.get("checked_label", "").strip():
                    raise ValueError
            except (AttributeError, TypeError, ValueError):
                yield f"{filename}: geçerli kaynak kontrol tarihi eksik"
    if "haber-gv101.html" not in pages or not pages["haber-gv101.html"].source_links:
        yield "haber-gv101.html: arşiv haberi veya HTTPS kaynağı eksik"


def main():
    pages = {path.name: Page(path) for path in sorted(ROOT.glob("*.html"))}
    errors = [*check_links(pages), *check_news(pages)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"{len(pages)} sayfa: iç bağlantılar ve haber kaynak alanları doğrulandı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
