(() => {
  "use strict";

  const filters = document.querySelector(".directory-filters");
  const query = document.querySelector("#center-query");
  const country = document.querySelector("#center-country");
  const kind = document.querySelector("#center-kind");
  const result = document.querySelector("#center-result");
  const empty = document.querySelector("#center-empty");

  const city = document.createElement("select");
  city.id = "center-city";
  const cityField = document.createElement("div");
  cityField.className = "directory-field";
  const cityLabel = document.createElement("label");
  cityLabel.htmlFor = city.id;
  cityLabel.textContent = "Şehir";
  cityField.append(cityLabel, city);
  country.closest(".directory-field").after(cityField);
  kind.labels[0].textContent = "Hizmet veya çalışma türü";
  kind.options[0].textContent = "Tüm hizmet ve çalışma türleri";
  const reset = document.createElement("button");
  reset.type = "button";
  reset.className = "directory-reset";
  reset.textContent = "Filtreleri temizle";
  filters.append(reset);

  function searchWords(text) {
    return text.toLocaleLowerCase("tr").normalize("NFD").replace(/\p{M}/gu, "").replace(/ı/g, "i")
      .split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  }

  const groups = [...document.querySelectorAll(".center-country")].map(group => {
    const countryName = group.querySelector("h2").firstChild.textContent;
    const records = [...group.querySelectorAll(".center-record")].map(record => {
      const fields = record.querySelectorAll(".center-name, .center-city, .center-person, .center-service-info, .center-studies");
      const searchable = [...fields].map(field => field.textContent + " " + (field.dataset.searchAliases || ""));
      return {
        element: record,
        types: record.dataset.types.split(" "),
        city: record.querySelector(".center-city").textContent.trim(),
        words: searchWords([countryName, ...searchable].join(" "))
      };
    });
    return { element: group, count: group.querySelector("[data-country-count]"), records };
  });

  function updateCities(selected = "") {
    const cities = new Set();
    for (const group of groups) {
      if (country.value && country.value !== group.element.dataset.country) continue;
      for (const record of group.records) cities.add(record.city);
    }
    const sorted = [...cities].sort(new Intl.Collator("tr").compare);
    city.replaceChildren(new Option("Tüm şehirler", ""), ...sorted.map(name => new Option(name, name)));
    if (cities.has(selected)) city.value = selected;
  }

  function clearFilters() {
    filters.reset();
    updateCities();
    filterCenters();
  }

  function filterCenters() {
    const words = searchWords(query.value);
    let total = 0;
    for (const group of groups) {
      const matchingCountry = !country.value || country.value === group.element.dataset.country;
      let count = 0;
      for (const record of group.records) {
        const matchingKind = !kind.value || record.types.includes(kind.value);
        const matchingQuery = words.every(word => record.words.some(keyword => keyword.startsWith(word)));
        const matchingCity = !city.value || city.value === record.city;
        const visible = matchingCountry && matchingCity && matchingKind && matchingQuery;
        record.element.hidden = !visible;
        if (visible) count += 1;
      }
      group.count.textContent = count + " merkez";
      group.element.hidden = count === 0;
      total += count;
    }
    result.textContent = total ? total + " merkez gösteriliyor" : "Eşleşen merkez bulunamadı";
    empty.hidden = total !== 0;
  }

  function openLinkedCenter() {
    const center = document.getElementById(location.hash.slice(1));
    if (!center?.classList.contains("center-record")) return;
    if (center.hidden) {
      clearFilters();
    }
    center.open = true;
    center.scrollIntoView({ block: "start" });
  }

  filters.addEventListener("submit", event => event.preventDefault());
  query.addEventListener("input", filterCenters);
  country.addEventListener("change", () => {
    updateCities(city.value);
    filterCenters();
  });
  city.addEventListener("change", filterCenters);
  reset.addEventListener("click", clearFilters);
  kind.addEventListener("change", filterCenters);
  updateCities();
  filterCenters();
  filters.hidden = false;
  result.hidden = false;
  openLinkedCenter();
  window.addEventListener("hashchange", openLinkedCenter);
})();
