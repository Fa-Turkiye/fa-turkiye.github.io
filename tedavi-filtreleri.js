(() => {
  "use strict";

  const form = document.getElementById("treatment-filters");
  const group = document.getElementById("treatment-group");
  const scope = document.getElementById("treatment-scope");
  const result = document.getElementById("treatment-result");
  const cards = [...document.querySelectorAll(".treatment-card")];
  const requestedScope = new URLSearchParams(location.search).get("durum");

  if (requestedScope === "arastirma") scope.value = requestedScope;

  function filterTreatments() {
    let count = 0;
    for (const card of cards) {
      const matchesGroup = !group.value || card.dataset.treatmentGroup === group.value;
      const matchesScope = !scope.value || (card.dataset.research === "true") === (scope.value === "arastirma");
      card.hidden = !matchesGroup || !matchesScope;
      if (!card.hidden) count += 1;
    }
    result.textContent = count ? count + " dosya gösteriliyor" : "Bu filtrelere uyan dosya bulunamadı.";
  }

  form.addEventListener("submit", event => event.preventDefault());
  form.addEventListener("change", filterTreatments);
  filterTreatments();
  form.hidden = false;
  result.hidden = false;
})();

(() => {
  "use strict";
  const toolbar = document.getElementById("compare-toolbar");
  const dialog = document.getElementById("compare-dialog");
  if (!toolbar || !dialog?.showModal) return;

  const show = document.getElementById("compare-show");
  const clear = document.getElementById("compare-clear");
  const status = document.getElementById("compare-status");
  const output = document.getElementById("compare-content");
  const choices = [...document.querySelectorAll(".compare-choice input")];
  const selected = () => choices.filter(choice => choice.checked);

  function updateSelection() {
    const count = selected().length;
    for (const choice of choices) choice.disabled = count >= 3 && !choice.checked;
    show.disabled = count < 2;
    clear.disabled = !count;
    status.textContent = count + " / 3 dosya seçildi.";
  }

  function createCell(tag, value, scope) {
    const cell = document.createElement(tag);
    if (scope) cell.scope = scope;
    if (typeof value === "string") cell.textContent = value;
    else cell.append(value);
    return cell;
  }

  function addRow(tablePart, label, values, isHeading = false) {
    const row = tablePart.insertRow();
    row.append(createCell("th", label, isHeading ? "col" : "row"));
    for (const value of values) row.append(createCell(isHeading ? "th" : "td", value, isHeading ? "col" : ""));
  }

  show.addEventListener("click", () => {
    const cards = selected().map(choice => choice.closest(".treatment-card"));
    const table = document.createElement("table");
    const titles = cards.map(card => card.querySelector("h2 a").cloneNode(true));
    addRow(table.createTHead(), "Başlık", titles, true);
    const rows = table.createTBody();
    addRow(rows, "Araştırma aşaması", cards.map(card => card.dataset.phase));
    addRow(rows, "Hedef", cards.map(card => card.dataset.target));
    addRow(rows, "Açıklanan bilgiler", cards.map(card => card.dataset.results));
    addRow(rows, "Kaynak", cards.map(card => {
      const link = document.createElement("a");
      link.href = card.dataset.source;
      link.textContent = "Kaynağı aç";
      return link;
    }));
    output.replaceChildren(table);
    dialog.showModal();
  });

  clear.addEventListener("click", () => {
    for (const choice of choices) choice.checked = false;
    updateSelection();
    choices.find(choice => !choice.closest(".treatment-card").hidden)?.focus();
  });
  for (const choice of choices) {
    choice.closest("label").hidden = false;
    choice.addEventListener("change", updateSelection);
  }
  toolbar.hidden = false;
  updateSelection();
})();
