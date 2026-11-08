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
