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
function stroke(svg, d, colour, width, start, duration = M.wipe) {
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

// Motion rule (render-video SKILL.md): purposeful, medium motion timed to the narration's cues, never
// decoration. Elements enter with one short eased-out move, focus bands and links wipe in, earlier elements dim,
// and render.py staggers entrances so one element starts moving at a time; the camera drift stays subtle. No
// bounce, overshoot, spin, particles, or loop. Intensity is tuned only in render.py MOTION, read here as M.
const M = CUES.motion;

// An element's entrance: it fades in while sliding (left, up) or scaling from M.offset of its size off its place.
function enter(node, start, from = 'up') {
  const o = M.offset * 100;
  const move = { left: `translateX(-${o}%)`, up: `translateY(${o}%)`, scale: `scale(${1 - M.offset})` }[from];
  return at(node, [{ opacity: 0, transform: move }, { opacity: 1, transform: 'none' }], start, M.enter);
}

// A palette colour, #rrggbb, at alpha a.
function rgba(hex, a) {
  return `rgba(${[1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)).join(',')},${a})`;
}

// A wipe: the element is revealed left to right.
function wipe(node, start, duration = M.wipe) {
  return at(node, [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], start, duration);
}

// An earlier element dims to opacity to once a newer one takes the focus.
function dim(node, start, to = 0.45) {
  return at(node, [{ opacity: 1 }, { opacity: to }], start, M.dim, { fill: 'forwards' });
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

// A code editor view in panel (a .panel holding a .bar and a .code): view has file, lines, typing (0 shows
// it whole), rows in view, and focus cues {line, at, top, note?}. At each cue the line's band wipes in, the rest
// dims, and the view scrolls to cue.top. A cue with a note (a mark) gets a callout chip in free space (no code,
// earlier chip, or connector under it), on its row or the nearest row above or below, joined by one straight
// horizontal or vertical connector to an arrowhead on the marked row after its last character; with no free
// space the chip goes at the view's right and window.layout.problems names the line. Earlier marks stay, dimmed.
// A cue without a note gets an arrow pointing at the line's end. The font is fitted to
// the longest line, the arrow, and view.rows lines, at most maxSize design pixels.
function codeView(panel, view, start, maxSize = 30) {
  const box = panel.querySelector('.code'), bar = panel.querySelector('.bar'), lines = view.lines;
  make('span', '', ' ' + view.file, bar);
  const u = Math.min(CUES.width, CUES.height) / 1080, inset = 16 * u, notes = view.focus.some(c => c.note);
  const arrow = notes ? 60 * u : view.focus.length || CUES.kind === 'code' ? 150 * u : 0;
  // Fit the longest line, the arrow, and view.rows lines inside the panel; Fira Code advances 0.6 em.
  const wide = Math.max(...lines.map(l => l.length), 20) + 4, shown = Math.min(Math.max(lines.length, 1), view.rows);
  const room = panel.clientWidth - 56 * u - inset - arrow, high = panel.clientHeight - bar.offsetHeight - 30 * u;
  const size = Math.min(maxSize * u, room / (wide * 0.6), high / (shown * 1.6)), lh = size * 1.6, ch = size * 0.6;
  box.style.fontSize = size + 'px';
  const frame = make('div', 'view', undefined, box), scroll = make('div', 'scroll', undefined, frame);
  frame.style.height = shown * lh + 'px';
  // Every line, blank or not, gets the same box at i * lh, so the band, arrow, and chip sit exactly on it.
  const total = Math.max(lines.reduce((n, l) => n + l.length + 1, 0), 1);
  let t = start;
  const rows = lines.map((text, i) => {
    const row = make('span', 'line', undefined, scroll);
    Object.assign(row.style, { left: inset + 'px', top: i * lh + 'px', height: lh + 'px', lineHeight: lh + 'px' });
    make('span', 'ln', String(i + 1), row);
    colour(text, row);
    const share = view.typing * (text.length + 1) / total;
    if (!view.typing) row.style.width = (text.length + 5) + 'ch';
    else at(row, [{ width: '0ch' }, { width: (text.length + 5) + 'ch' }], t, Math.max(share, 0.001),
      { easing: `steps(${Math.max(text.length, 1)})` });
    t += share;
    return row;
  });
  const end = i => inset + (lines[i].length + 5) * ch, svg = svgIn(scroll, 'pointer'), taken = [];
  let last = null, top = 0, marks = [];
  // Mark placement (scroll pixels): a spot is free when no code character, earlier chip, or earlier connector lies
  // under the chip or its connector (a 1 px graze aside). A box is {l, t, r, b}; a line's code ends at inset + (length + 4) ch.
  const gap = 12 * u, wing = 12 * u, chars = i => i < lines.length ? inset + (lines[i].length + 4) * ch : 0;
  const hits = (p, q) => p.l < q.r && q.l < p.r && p.t < q.b && q.t < p.b;
  const clear = p => {
    for (let i = Math.max(Math.floor((p.t + 1) / lh), 0); i * lh < p.b - 1; i++) if (chars(i) + gap > p.l) return false;
    return !taken.some(q => hits(p, q));
  };
  // The chip's top on row r, kept inside the view.
  const place = (r, cue, h) => Math.min(Math.max(r * lh + (lh - h) / 2, cue.top * lh), (cue.top + shown) * lh - h);
  // Spots in order: on the marked row after its end, joined by a horizontal connector; else on the nearest row above
  // or below, its left edge past the line's end where it fits (else shifted left over shorter rows), joined by a
  // vertical connector landing on the marked row after its end. null when none is free.
  function markSpot(cue, w, h, far) {
    const line = cue.line, y = line * lh + lh / 2, x = chars(line) + gap, spots = [];
    const side = { l: x + 48 * u, t: place(line, cue, h) };
    if (side.l <= far) spots.push({ from: 'side', box: { ...side, r: side.l + w, b: side.t + h }, tip: { x, y },
      link: { l: x, t: y - wing, r: side.l, b: y + wing } });
    for (let d = 1; d < shown; d++) [line - d, line + d].forEach(r => {
      if (r < cue.top || r >= cue.top + shown) return;
      const t = place(r, cue, h), l = Math.min(x, far), tx = Math.max(l + 16 * u, x + wing);
      const from = t + h <= y ? 'above' : 'below', edge = from === 'above' ? t + h : t;
      if (l < 0 || tx > l + w - 16 * u || Math.abs(edge - y) < 24 * u || (t < (line + 1) * lh && t + h > line * lh)) return;
      spots.push({ from, box: { l, t, r: l + w, b: t + h }, tip: { x: tx, y },
        link: { l: tx - wing, t: Math.min(edge, y - wing), r: tx + wing, b: Math.max(edge, y + wing) } });
    });
    return spots.find(s => clear(s.box) && clear(s.link)) ?? null;
  }
  // No free spot: the chip at the view's right on its row, reported as a layout problem render.py refuses.
  function fallback(cue, w, h, far) {
    const y = cue.line * lh + lh / 2, x = chars(cue.line) + gap, t = place(cue.line, cue, h);
    window.layout.problems.push(`mark on line ${cue.line + 1}: no free space for its note; shorten the line or the note (write-video-script)`);
    return { from: 'side', box: { l: far, t, r: far + w, b: t + h }, tip: { x, y }, link: { l: x, t: y - wing, r: far, b: y + wing } };
  }
  view.focus.forEach((cue, k) => {
    rows.forEach((row, i) => {
      const was = last === null || i === last ? 1 : 0.28;
      at(row, [{ opacity: was }, { opacity: i === cue.line ? 1 : 0.28 }], cue.at, M.dim, { fill: 'forwards' });
    });
    at(scroll, [{ transform: `translateY(${-top * lh}px)` }, { transform: `translateY(${-cue.top * lh}px)` }],
      cue.at, M.dim, { fill: 'forwards' });
    const band = make('div', 'glow', undefined, scroll), y = cue.line * lh + lh / 2, next = view.focus[k + 1];
    Object.assign(band.style, { top: cue.line * lh + 'px', height: lh + 'px' });
    wipe(band, cue.at);
    if (next) at(band, [{ opacity: 1 }, { opacity: 0 }], next.at, 0.2, { fill: 'forwards' });
    const x = end(cue.line);
    if (!cue.note) {
      const path = stroke(svg, `M${x + 130 * u} ${y} H${x} M${x + 22 * u} ${y - 18 * u} L${x} ${y} L${x + 22 * u} ${y + 18 * u}`,
        CUES.palette.accent, 6 * u, cue.at + 0.1);
      if (next) at(path, [{ opacity: 1 }, { opacity: 0 }], next.at, 0.2, { fill: 'forwards' });
    } else {
      const chip = make('div', 'note', cue.note, scroll);
      // One row high (line-height 1.15, 3u padding, 2 px borders) where at least 14u allows.
      chip.style.fontSize = Math.max(Math.min(24 * u, size * 0.95, (lh - 6 * u - 4) / 1.15), 14 * u) + 'px';
      const w = chip.offsetWidth, h = chip.offsetHeight, far = frame.clientWidth - w - 14 * u;
      const spot = markSpot(cue, w, h, far) ?? fallback(cue, w, h, far), { box: c, tip: { x: tx, y: ty }, from } = spot;
      Object.assign(chip.style, { left: c.l + 'px', top: c.t + 'px' });
      taken.push(c, spot.link);
      // One straight connector from the chip to its arrowhead, on the marked row after the line's last character.
      const a = 12 * u, b = from === 'above' ? -18 * u : 18 * u;
      const [d, head] = from === 'side'
        ? [`M${c.l - 8 * u} ${ty} H${tx}`, `M${tx + 18 * u} ${ty - a} L${tx} ${ty} L${tx + 18 * u} ${ty + a}`]
        : [`M${tx} ${from === 'above' ? c.b : c.t} V${ty}`, `M${tx - a} ${ty + b} L${tx} ${ty} L${tx + a} ${ty + b}`];
      const link = stroke(svg, d, CUES.palette.accent, 4 * u, cue.at + 0.1);
      const arrowhead = stroke(svg, head, CUES.palette.accent, 4 * u, cue.at + 0.1);
      link.classList.add('link');
      arrowhead.classList.add('head');
      enter(chip, cue.at + 0.15, 'left');
      marks.forEach(m => dim(m, cue.at, 0.4));
      marks = [chip, link, arrowhead];
    }
    last = cue.line;
    top = cue.top;
  });
  return { size, rows };
}

// Flat glyphs drawn as strokes on a 24-unit box: a repository book, a folder, a file, and a chain link.
const ICONS = {
  repo: 'M5 4 H16 A2 2 0 0 1 18 6 V20 H7 A2 2 0 0 1 5 18 Z M5 18 A2 2 0 0 1 7 16 H18 M9 4 V11 L10.5 9.8 L12 11 V4',
  dir: 'M3 7 A2 2 0 0 1 5 5 H9 L11 7 H19 A2 2 0 0 1 21 9 V17 A2 2 0 0 1 19 19 H5 A2 2 0 0 1 3 17 Z',
  file: 'M6 3 H14 L18 7 V21 H6 Z M14 3 V7 H18',
  link: 'M10 14 A4 4 0 0 1 10 8 L13 5 A4 4 0 0 1 19 11 L17.5 12.5 M14 10 A4 4 0 0 1 14 16 L11 19 A4 4 0 0 1 5 13 L6.5 11.5',
};
function icon(parent, name, colour) {
  const svg = svgIn(parent, 'icon'), path = document.createElementNS(SVG, 'path');
  svg.setAttribute('viewBox', '0 0 24 24');
  path.setAttribute('d', ICONS[name]);
  path.setAttribute('class', 'draw');
  Object.assign(path.style, { stroke: colour, strokeWidth: 2 });
  svg.appendChild(path);
}

// A GitHub-style repository card in the channel palette, in the .panel.card holding #head, #crumbs, #tree, and
// #url (repo and kit scenes): a drawn book glyph, owner/repo, a neutral "github.com" label (no third-party logo),
// the path as a breadcrumb, the files as a tree (a folder row whenever a file's folder differs from the one
// before), and the link wiping in at CUES.link.at, broken after a slash over at most lines lines. The template
// animates the rows and then the card's entrance (enterCard), after measuring: returns each file's rows.
function githubCard(lines, treeSize = 32) {
  const u = Math.min(CUES.width, CUES.height) / 1080, p = CUES.palette, muted = 'var(--muted)';
  const [owner, name] = CUES.repo.split('/'), head = $('head');
  icon(head, 'repo', p.text);
  make('span', '', owner, head);
  make('span', 'sep', '/', head);
  make('b', '', name, head);
  make('span', 'site', 'github.com', head);
  icon($('crumbs'), 'dir', muted);
  const parts = [name, ...CUES.path.split('/')];
  parts.forEach((part, i) => make(i === parts.length - 1 ? 'b' : 'span', '', part + (i < parts.length - 1 ? ' /' : ''), $('crumbs')));
  let folder = null;
  const rows = CUES.files.map(file => {
    const cut = file.text.lastIndexOf('/'), dir = cut < 0 ? null : file.text.slice(0, cut), own = [];
    if (dir && dir !== folder) {
      const row = make('div', 'row dir', undefined, $('tree'));
      icon(row, 'dir', p.accent);
      make('span', '', dir, row);
      own.push(row);
    }
    folder = dir;
    const row = make('div', dir ? 'row in' : 'row', undefined, $('tree'));
    icon(row, 'file', muted);
    make('span', '', file.text.slice(cut + 1), row);
    own.push(row);
    return own;
  });
  // The link large; Fira Code advances 0.6 em.
  const url = $('url'), text = CUES.link.text;
  icon(url, 'link', p.accent);
  const span = make('span', '', undefined, url);
  const room = url.clientWidth - 40 * u - 60 * u;
  url.style.fontSize = Math.min(44 * u, room * lines / (text.length * 0.6) * 0.95) + 'px';
  text.split(/(?<=\/)/).forEach(part => { make('span', '', part, span); span.appendChild(document.createElement('wbr')); });
  wipe(url, CUES.link.at);
  // Fit: a long file list shrinks until every row shows.
  const tree = $('tree');
  tree.style.fontSize = treeSize * u + 'px';
  for (let size = treeSize; tree.scrollHeight > tree.clientHeight && size > 18; size -= 1) tree.style.fontSize = size * u + 'px';
  return rows;
}

// The card's entrance, scaling in at CUES.card.at; called last, so the template measures it unscaled.
function enterCard() {
  enter($('card'), CUES.card.at, 'scale');
}

// Theme, frame size, the common layers, the fades, and the slow camera drift.
function frame() {
  const root = document.documentElement.style, p = CUES.palette, u = Math.min(CUES.width, CUES.height) / 1080;
  root.setProperty('--bg', p.background);
  root.setProperty('--fg', p.text);
  root.setProperty('--accent', p.accent);
  root.setProperty('--u', u + 'px');
  root.setProperty('--pad', (CUES.width > CUES.height ? 80 : 60) * u + 'px');
  root.setProperty('--floor', CUES.floor + 'px');  // content ends this far above the bottom: a Short's caption band
  document.body.dataset.shape = CUES.width > CUES.height ? 'wide' : 'tall';
  Object.assign(document.body.style, { width: CUES.width + 'px', height: CUES.height + 'px' });
  $('brand').textContent = CUES.brand;
  // The channel's background image behind everything, outside the drifting camera so it stays still: centred and
  // faint ("contain"), or filling the frame ("cover") under a scrim, a vertical gradient of the palette background
  // whose alpha is render.py's scrim.middle in the middle and scrim.edge at the top and bottom.
  const back = CUES.backdrop;
  if (back) {
    if (back.fit === 'cover') {
      const veil = make('div', 'scrim'), edge = rgba(p.background, back.scrim.edge), middle = rgba(p.background, back.scrim.middle);
      veil.style.background = `linear-gradient(${edge}, ${middle} 30%, ${middle} 70%, ${edge})`;
      $('stage').prepend(veil);
    }
    const image = make('img', back.fit === 'cover' ? 'backdrop cover' : 'backdrop');
    image.src = back.image;
    image.style.opacity = back.opacity;
    $('stage').prepend(image);
  }
  $('heading').textContent = CUES.heading.text;
  enter($('heading'), CUES.heading.at, 'up');
  at($('camera'), [{ transform: 'scale(1)' }, { transform: 'scale(1.04)' }], 0, CUES.seconds, { easing: 'linear' });
  at($('stage'), [{ opacity: 0 }, { opacity: 1 }], 0, CUES.fade);
  at($('stage'), [{ opacity: 1 }, { opacity: 0 }], CUES.seconds - CUES.fade, CUES.fade, { fill: 'forwards' });
}

// Layout problems found while building the scene, each a line render.py reports.
window.layout = { problems: [] };

window.seek = sec => document.getAnimations().forEach(a => { a.pause(); a.currentTime = sec * S; });

// render.py waits for ready: true once both fonts loaded, the brand image decoded, and the scene is built at t = 0.
window.ready = Promise.all(['700 16px "Space Grotesk"', '400 16px "Fira Code"'].map(f => document.fonts.load(f)))
  .then(sets => {
    if (!sets.every(set => set.length)) return false;
    frame();
    build();
    seek(0);
    const image = document.querySelector('.backdrop');
    return image ? image.decode().then(() => true) : true;
  });
