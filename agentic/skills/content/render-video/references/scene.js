// Shared by every scene template, after CUES (the scene's cue timeline from render.py) and before the
// template's build(). Every animation is a Web Animation: seek(t) pauses them all at t seconds, so a
// frame depends only on t. Lessons from the prototype: multi-keyframe animations use linear timing
// easing (per-iteration easing breaks holds), and an animation that undoes an earlier one on the same
// property uses fill 'forwards' so it does not override the earlier one before it starts.
const S = 1000, EASE = 'cubic-bezier(.2,.8,.2,1)', SVG = 'http://www.w3.org/2000/svg';
const $ = id => document.getElementById(id);

function make(tag, cls, text, parent) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  if (parent) parent.appendChild(node);
  return node;
}

function at(node, frames, start, duration, extra = {}) {
  return node.animate(frames, { delay: start * S, duration: duration * S, fill: 'both', easing: EASE, ...extra });
}

// A drawn stroke: an SVG path that draws itself from start over duration.
function stroke(svg, d, colour, width, start, duration = 0.4) {
  const path = document.createElementNS(SVG, 'path');
  path.setAttribute('d', d);
  path.setAttribute('class', 'draw');
  path.setAttribute('pathLength', '1');
  Object.assign(path.style, { stroke: colour, strokeWidth: width, strokeDasharray: 1, strokeDashoffset: 1 });
  svg.appendChild(path);
  at(path, [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], start, duration);
  return path;
}

function svgIn(parent, cls) {
  const svg = document.createElementNS(SVG, 'svg');
  if (cls) svg.setAttribute('class', cls);
  parent.appendChild(svg);
  return svg;
}

// Python-like colouring, built with textContent only: keywords, strings, numbers, comments.
const KEYWORDS = new Set(['def', 'return', 'import', 'from', 'with', 'as', 'assert', 'if', 'else', 'elif', 'not',
  'raise', 'is', 'in', 'for', 'while', 'class', 'try', 'except', 'None', 'True', 'False', 'and', 'or', 'lambda']);
function colour(text, parent) {
  const tokens = text.match(/#.*$|"[^"]*"?|'[^']*'?|\b\d+(?:\.\d+)?\b|[A-Za-z_]\w*|\s+|./g) || [];
  tokens.forEach(t => {
    const cls = t[0] === '#' ? 'c' : t[0] === '"' || t[0] === "'" ? 's' : /^\d/.test(t) ? 'n' : KEYWORDS.has(t) ? 'k' : '';
    make('span', cls, t, parent);
  });
}

// Theme, frame size, the common layers, the fades, and the slow camera drift.
function frame() {
  const root = document.documentElement.style, p = CUES.palette, u = Math.min(CUES.width, CUES.height) / 1080;
  root.setProperty('--bg', p.background);
  root.setProperty('--fg', p.text);
  root.setProperty('--accent', p.accent);
  root.setProperty('--u', u + 'px');
  root.setProperty('--pad', (CUES.width > CUES.height ? 80 : 60) * u + 'px');
  document.body.dataset.shape = CUES.width > CUES.height ? 'wide' : 'tall';
  Object.assign(document.body.style, { width: CUES.width + 'px', height: CUES.height + 'px' });
  $('brand').textContent = CUES.brand;
  $('heading').textContent = CUES.heading;
  at($('heading'), [{ opacity: 0, transform: 'translateY(30px)' }, { opacity: 1, transform: 'none' }], 0.1, 0.5);
  at($('camera'), [{ transform: 'scale(1)' }, { transform: 'scale(1.04)' }], 0, CUES.seconds, { easing: 'linear' });
  at($('stage'), [{ opacity: 0 }, { opacity: 1 }], 0, CUES.fade);
  at($('stage'), [{ opacity: 1 }, { opacity: 0 }], CUES.seconds - CUES.fade, CUES.fade, { fill: 'forwards' });
}

window.seek = sec => document.getAnimations().forEach(a => { a.pause(); a.currentTime = sec * S; });

// render.py waits for ready: true once both fonts loaded and the scene is built at t = 0.
window.ready = Promise.all(['700 16px "Space Grotesk"', '400 16px "Fira Code"'].map(f => document.fonts.load(f)))
  .then(sets => {
    if (!sets.every(set => set.length)) return false;
    frame();
    build();
    seek(0);
    return true;
  });
