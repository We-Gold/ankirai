// Replace {{c1::term}} with <mark>term</mark> in card-front elements
// Uses a text-node walker so MathJax-rendered elements are not disturbed
function highlightCloze(el) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) textNodes.push(node);
  for (const textNode of textNodes) {
    if (!/\{\{c\d+::/.test(textNode.textContent)) continue;
    const span = document.createElement('span');
    span.innerHTML = textNode.textContent.replace(/\{\{c\d+::(.+?)\}\}/g, '<mark>$1</mark>');
    textNode.parentNode.replaceChild(span, textNode);
  }
}
function applyHighlights() {
  document.querySelectorAll('.card-front').forEach(highlightCloze);
}

// Wire export confirmation for buttons with data-pending > 0
function wireExportConfirm() {
  document.querySelectorAll('[data-pending]').forEach(btn => {
    const pending = parseInt(btn.dataset.pending, 10);
    if (pending > 0) {
      const form = btn.closest('form');
      if (form && !form.dataset.confirmWired) {
        form.dataset.confirmWired = '1';
        form.addEventListener('submit', e => {
          if (!confirm(`${pending} card(s) still pending. Export anyway?`)) e.preventDefault();
        });
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  applyHighlights();
  wireExportConfirm();
});

document.addEventListener('htmx:afterSwap', () => {
  applyHighlights();
  wireExportConfirm();
});
