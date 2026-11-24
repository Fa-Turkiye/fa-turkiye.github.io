(() => {
  'use strict';
  const filters = document.querySelector('#trial-filters');
  if (!filters) return;

  const program = document.querySelector('#trial-program');
  const country = document.querySelector('#trial-country');
  const age = document.querySelector('#trial-age');
  const status = document.querySelector('#trial-status');
  const result = document.querySelector('#trial-result');
  const empty = document.querySelector('#trial-empty');
  const cards = [...document.querySelectorAll('.trial-card')];

  function update() {
    const years = age.value === '' ? null : Number(age.value);
    let visible = 0;
    for (const card of cards) {
      const minimum = card.dataset.minAge === '' ? null : Number(card.dataset.minAge);
      const maximum = card.dataset.maxAge === '' ? null : Number(card.dataset.maxAge);
      const matched = (!program.value || program.value === card.dataset.program)
        && (!country.value || card.dataset.countries.includes(` ${country.value} `))
        && (!status.value || status.value === card.dataset.status)
        && (years === null || (minimum !== null && years >= minimum && (maximum === null || years <= maximum)));
      card.hidden = !matched;
      if (matched) visible += 1;
    }
    result.textContent = `${visible} çalışma gösteriliyor${years !== null ? ' · Yaş filtresi yalnızca kayıtlı aralıkları gösterir' : ''}`;
    empty.hidden = visible !== 0;
  }

  filters.addEventListener('input', update);
  filters.addEventListener('change', update);
  filters.addEventListener('reset', () => requestAnimationFrame(update));
  filters.hidden = false;
  result.hidden = false;
  update();
})();
