// Shared by every thumbnail layout: load the embedded fonts, shrink each .fit box's font from its data-size until
// every line fits the box (in data-cols columns), never below --min-text, then set window.ready (false when a font
// did not load) and window.overflow (true when a box's text does not fit even at --min-text).
const least = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--min-text')) || 24;
function fit(box) {
  let size = parseFloat(box.dataset.size);
  const column = box.clientWidth / (parseFloat(box.dataset.cols) || 1);
  const over = () => box.scrollHeight > box.clientHeight || [...box.children].some((line) => line.offsetWidth > column);
  box.style.fontSize = size + 'px';
  while (size > least && over()) {
    size = Math.max(least, size - 2);
    box.style.fontSize = size + 'px';
  }
  return over();
}
Promise.all([document.fonts.load("700 100px 'Space Grotesk'"), document.fonts.load("600 100px 'Fira Code'")])
  .then((loaded) => {
    window.overflow = [...document.querySelectorAll('.fit')].map(fit).some(Boolean);
    window.ready = loaded.every((faces) => faces.length > 0);
  })
  .catch(() => { window.ready = false; });
