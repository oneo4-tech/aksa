// Shared by every thumbnail layout: load the embedded fonts, shrink each .fit box's font from its
// data-size until every line fits the box, then set window.ready (false when a font did not load).
function fit(box) {
  let size = parseFloat(box.dataset.size);
  const over = () => box.scrollHeight > box.clientHeight || [...box.children].some((line) => line.offsetWidth > box.clientWidth);
  box.style.fontSize = size + 'px';
  while (size > 24 && over()) {
    size -= 2;
    box.style.fontSize = size + 'px';
  }
}
Promise.all([document.fonts.load("700 100px 'Space Grotesk'"), document.fonts.load("600 100px 'Fira Code'")])
  .then((loaded) => {
    document.querySelectorAll('.fit').forEach(fit);
    window.ready = loaded.every((faces) => faces.length > 0);
  })
  .catch(() => { window.ready = false; });
