(() => {
  'use strict';
  const filters = document.querySelector('#news-filters');
  if (!filters) return;

  const query = document.querySelector('#news-query');
  const category = document.querySelector('#news-category');
  const drug = document.querySelector('#news-drug');
  const result = document.querySelector('#news-result');
  const empty = document.querySelector('#news-empty');
  const cards = [...document.querySelectorAll('.news-archive > article')];
  const normalize = text => text.toLocaleLowerCase('tr').normalize('NFD')
    .replace(/\p{M}/gu, '').replace(/ı/g, 'i');
  const entries = cards.map(card => ({ card, text: normalize(card.textContent) }));

  function update() {
    const words = normalize(query.value).split(/[^\p{L}\p{N}]+/u).filter(Boolean);
    let count = 0;
    for (const { card, text } of entries) {
      const matched = (!category.value || card.dataset.newsCategory === category.value)
        && (!drug.value || card.dataset.newsDrug === drug.value)
        && words.every(word => text.includes(word));
      card.hidden = !matched;
      if (matched) count += 1;
    }
    result.textContent = `${count} haber gösteriliyor`;
    empty.hidden = count !== 0;
  }

  filters.addEventListener('input', update);
  filters.addEventListener('change', update);
  filters.addEventListener('reset', () => requestAnimationFrame(update));
  filters.hidden = false;
  result.hidden = false;
  update();
})();
