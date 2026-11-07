(() => {
  "use strict";

  const filters = document.querySelector(".directory-filters");
  const query = document.querySelector("#center-query");
  const country = document.querySelector("#center-country");
  const kind = document.querySelector("#center-kind");
  const result = document.querySelector("#center-result");
  const empty = document.querySelector("#center-empty");

  function searchWords(text) {
    return text.toLocaleLowerCase("tr").normalize("NFD").replace(/\p{M}/gu, "").replace(/ı/g, "i")
      .split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  }

  const groups = [...document.querySelectorAll(".center-country")].map(group => {
    const countryName = group.querySelector("h2").firstChild.textContent;
    const records = [...group.querySelectorAll(".center-record")].map(record => {
      const fields = record.querySelectorAll(".center-name, .center-city, .center-person, .center-service-info");
      return {
        element: record,
        types: record.dataset.types.split(" "),
        words: searchWords([countryName, ...[...fields].map(field => field.textContent)].join(" "))
      };
    });
    return { element: group, count: group.querySelector("[data-country-count]"), records };
  });

  function filterCenters() {
    const words = searchWords(query.value);
    let total = 0;
    for (const group of groups) {
      const matchingCountry = !country.value || country.value === group.element.dataset.country;
      let count = 0;
      for (const record of group.records) {
        const matchingKind = !kind.value || record.types.includes(kind.value);
        const matchingQuery = words.every(word => record.words.some(keyword => keyword.startsWith(word)));
        const visible = matchingCountry && matchingKind && matchingQuery;
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

  filters.addEventListener("submit", event => event.preventDefault());
  query.addEventListener("input", filterCenters);
  country.addEventListener("change", filterCenters);
  kind.addEventListener("change", filterCenters);
  filterCenters();
  filters.hidden = false;
  result.hidden = false;
})();
