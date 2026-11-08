(() => {
  "use strict";
  const form = document.getElementById("site-search");
  const field = document.getElementById("site-query");
  const status = document.getElementById("search-status");
  const output = document.getElementById("search-results");
  const normalize = text => text.toLocaleLowerCase("tr").normalize("NFD")
    .replace(/\p{M}/gu, "").replace(/ı/g, "i");
  const words = text => normalize(text).split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  let records;
  let latestSearch = 0;

  async function search() {
    const request = ++latestSearch;
    const query = words(field.value);
    output.replaceChildren();
    if (!query.length) {
      status.textContent = "Aramak için bir ilaç, şehir, terim veya hekim adı yazın.";
      return;
    }
    status.textContent = "Aranıyor…";
    try {
      if (!records) {
        const response = await fetch("arama-verileri.json");
        if (!response.ok) throw Error(response.status);
        records = await response.json();
      }
      if (request !== latestSearch) return;
      let count = 0;
      for (const [group, entries] of Object.entries(records)) {
        const matches = entries.filter(([title, , detail, tags]) => {
          const haystack = words([title, detail, tags].join(" "));
          return query.every(word => haystack.some(term => term.startsWith(word)));
        });
        if (!matches.length) continue;
        const section = document.createElement("section");
        section.className = "search-group";
        const heading = document.createElement("h2");
        heading.textContent = group + " (" + matches.length + ")";
        const list = document.createElement("ul");
        for (const [title, href, detail] of matches) {
          const item = document.createElement("li");
          const link = document.createElement("a");
          link.href = href;
          link.textContent = title;
          const description = document.createElement("small");
          description.textContent = detail;
          item.append(link, description);
          list.append(item);
        }
        section.append(heading, list);
        output.append(section);
        count += matches.length;
      }
      status.textContent = count ? count + " sonuç bulundu." : "Eşleşen sonuç bulunamadı.";
    } catch {
      if (request === latestSearch) status.textContent = "Arama dizini yüklenemedi. Tekrar deneyin.";
    }
  }

  function restoreQuery() {
    field.value = new URLSearchParams(location.search).get("q") || "";
    search();
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    const url = new URL(location.href);
    url.searchParams.set("q", field.value.trim());
    if (url.href !== location.href) history.pushState(null, "", url);
    search();
  });
  window.addEventListener("popstate", restoreQuery);
  restoreQuery();
})();
