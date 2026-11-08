(() => {
  "use strict";
  const article = document.querySelector(".long-article");
  if (!article || !window.HTMLDialogElement) return;

  const fxn = "https://medlineplus.gov/genetics/gene/fxn/";
  const terms = new Map([
    ["mfars", ["mFARS", "Friedreich ataksisinde konuşma ve yutma, uzuv koordinasyonu ve dik duruş gibi işlevleri değerlendiren klinik bir ölçek.", "https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-first-treatment-friedreichs-ataxia"]],
    ["frataxin", ["Frataxin", "FXN geninin yapım talimatını taşıdığı protein. Hücrenin enerji üretiminde görev alan mitokondrilerde işlev görür.", fxn]],
    ["fxn", ["FXN", "Frataxin proteininin yapım talimatını taşıyan gen.", fxn]],
    ["yetim ilaç statüsü", ["Yetim ilaç statüsü", "Nadir hastalıklar için geliştirilen adaylara araştırma ve geliştirme desteği sağlayabilen bir düzenleyici statü. Pazarlama ruhsatı ayrı bir değerlendirmedir.", "https://www.ema.europa.eu/en/documents/other/rare-diseases-orphan-medicines-getting-facts-straight_en.pdf"]],
    ["biyobelirteç", ["Biyobelirteç", "Vücuttaki bir süreci ya da tedaviye verilen biyolojik yanıtı izlemek için ölçülebilen özellik.", "https://www.nih.gov/nih-style-guide/appendix-biomedical-definitions"]],
    ["aav", ["AAV", "Adeno ilişkili virüs. Gen tedavilerinde, genetik materyali hücrelere taşımak üzere tasarlanan vektörlerin yapımında kullanılabilir.", "https://www.fda.gov/vaccines-blood-biologics/cellular-gene-therapy-products/what-gene-therapy"]]
  ]);
  const pattern = /\b(mFARS|frataxin|FXN|yetim ilaç statüsü|biyobelirteç|AAV)(?!\p{L})/giu;
  const dialog = document.createElement("dialog");
  dialog.className = "glossary-dialog";
  dialog.id = "term-dialog";
  dialog.setAttribute("aria-labelledby", "term-title");
  const title = document.createElement("h2");
  title.id = "term-title";
  const description = document.createElement("p");
  const source = document.createElement("a");
  source.textContent = "Kaynağı aç";
  const close = document.createElement("form");
  close.method = "dialog";
  const closeButton = document.createElement("button");
  closeButton.type = "submit";
  closeButton.autofocus = true;
  closeButton.textContent = "Kapat";
  close.append(closeButton);
  dialog.append(title, description, source, close);

  const seen = new Set();
  for (const paragraph of article.querySelectorAll(".article-lead, .milestone-event > p, .article-prose .article-section > p")) {
    const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) {
      if (!walker.currentNode.parentElement.closest("a, button, time")) nodes.push(walker.currentNode);
    }
    for (const node of nodes) {
      const fragment = document.createDocumentFragment();
      let end = 0;
      for (const match of node.textContent.matchAll(pattern)) {
        const key = match[0].toLowerCase();
        if (seen.has(key) || !terms.has(key)) continue;
        seen.add(key);
        const button = document.createElement("button");
        button.type = "button";
        button.className = "term-trigger";
        button.textContent = match[0];
        button.setAttribute("aria-haspopup", "dialog");
        button.setAttribute("aria-controls", dialog.id);
        button.setAttribute("aria-label", match[0] + " teriminin açıklaması");
        button.addEventListener("click", () => {
          const [name, definition, url] = terms.get(key);
          title.textContent = name;
          description.textContent = definition;
          source.href = url;
          dialog.showModal();
        });
        fragment.append(node.textContent.slice(end, match.index), button);
        end = match.index + match[0].length;
      }
      if (end) {
        fragment.append(node.textContent.slice(end));
        node.replaceWith(fragment);
      }
    }
  }
  if (seen.size) document.body.append(dialog);
})();
