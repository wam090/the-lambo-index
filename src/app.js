(() => {
'use strict';

/* ================= data ================= */
const RAW = JSON.parse(document.getElementById('li-data').textContent);
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const norm = (s) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const fmt = (n) => Number(n).toLocaleString('en-US');
const icon = (id) => `<svg class="icon" aria-hidden="true"><use href="#i-${id}"/></svg>`;
const store = {
  get(k, d) { try { const v = localStorage.getItem('li:' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('li:' + k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ } },
};

/* Every #/ link stays inside the app, even when a host injects a <base> tag or rewrites static links
   into full URLs (htmlpreview does both): only the #/ part counts. No outside link contains "#/". */
const pageURL = () => location.href.split('#')[0];
document.addEventListener('click', (e) => {
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const a = e.target.closest('a[href*="#/"]');
  if (!a || a.target) return;
  e.preventDefault();
  const href = a.getAttribute('href');
  const h = href.slice(href.indexOf('#/'));
  if (location.hash !== h) location.hash = h;
});

/* Wikimedia serves thumbnails only at standard widths */
const STD = [330, 500, 960, 1280, 1920, 3840];
const THUMB = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/';
const ORIG = 'https://upload.wikimedia.org/wikipedia/commons/';
function imgUrl(im, want, original = false) {
  if (!im) return '';
  if (im.sz) {   // Flickr photo: fixed sizes up to 1024 px, smallest first
    const s = original ? null : im.sz.find(([w]) => w >= want);
    return (s || im.sz[im.sz.length - 1])[1];
  }
  const fits = STD.filter((s) => s < im.w);   // thumbnails must be narrower than the original
  let w = fits.find((s) => s >= want);
  if (!w && !original) w = fits[fits.length - 1];   // small photo: largest standard thumbnail
  return w ? `${THUMB}${im.h}/${im.n}/${w}px-${im.n}` : `${ORIG}${im.h}/${im.n}`;
}
const filePage = (im) => im.p || `https://commons.wikimedia.org/wiki/File:${im.n}`;
const photoSource = (im) => (im.src === 'flickr' || im.src === 'press' ? 'Flickr' : 'Wikimedia Commons');
const extLink = (url, html) => (/^https:\/\//i.test(url || '') ? `<a href="${esc(url)}" target="_blank" rel="noopener">${html}</a>` : html);   // https only
const REPORT = 'https://github.com/wam090/the-lambo-index/issues/new';
const reportHTML = (c, im) => (im ? ` · ${extLink(`${REPORT}?title=${encodeURIComponent(`Photo report: ${c.name}`)}&body=${encodeURIComponent(
  `Car: ${c.name}\nPage: https://wam090.github.io/the-lambo-index/#/m/${c.id}\nPhoto: ${filePage(im)}\n\nWhat is wrong with this photo (wrong car, wrong credit, should be removed)?`)}`, 'Report a photo')}` : '');
const creditHTML = (im) => im ? `${im.src === 'press' ? 'Press photo' : 'Photo'}: ${extLink(filePage(im), esc(im.a || `${photoSource(im)} contributor`))}${im.l ? ` · ${extLink(im.lu, esc(im.l))}` : ''} · ${photoSource(im)}` : '';
const photoSearches = (q) => `<a href="https://www.flickr.com/search/?text=${encodeURIComponent(q)}" target="_blank" rel="noopener">Flickr</a> · <a href="https://www.google.com/search?tbm=isch&amp;q=${encodeURIComponent(q)}" target="_blank" rel="noopener">Google Images</a>`;

const FAMILY_NAME = { Murcielago: 'Murciélago', Huracan: 'Huracán', Reventon: 'Reventón', Sian: 'Sián', Autentica: 'Auténtica', Cala: 'Calà', '350': '350 GT', '400': '400 GT', '291': 'Lambo 291' };
const famName = (f) => FAMILY_NAME[f] || f;
const KIND_ORDER = ['Production', 'Limited series', 'One-off', 'Concept', 'Prototype', 'Race car'];
const KIND_COLOUR = { Production: '#ff8100', 'Limited series': '#ffb46b', 'One-off': '#d8c3a5', Concept: '#8c7a66', Prototype: '#5e544a', 'Race car': '#c2410c' };
const ENG_ORDER = ['V12', 'Hybrid V12', 'V10', 'Hybrid V10', 'V8', 'Hybrid V8', 'Inline-6', 'Electric', 'Other'];
function bodyGroup(b) {
  const s = (b || '').toLowerCase();
  if (/suv|off-road/.test(s)) return 'SUV and off-road';
  if (/single-seater|group c|lmdh/.test(s)) return 'Race prototype';
  if (/roadster|targa|speedster|barchetta|spyder/.test(s)) return 'Open top';
  if (/2\+2|4-seat/.test(s)) return '2+2 and GT';
  if (/4-door|people carrier/.test(s)) return 'Four-door';
  if (/shooting/.test(s)) return 'Shooting brake';
  return 'Coupé';
}
const yearsLong = (c) => (c.end === 0 ? `${c.year}–present` : c.end && c.end !== c.year ? `${c.year}–${c.end}` : `${c.year}`);
const yearsShort = (c) => (c.end === 0 ? `${c.year}–now` : c.end && c.end !== c.year ? `${c.year}–${String(c.end).slice(2)}` : `${c.year}`);
const kw = (cv) => Math.round(cv * 0.7355);
const hp = (cv) => Math.round(cv * 0.98632);   // data is in CV, as Lamborghini quotes it; the site shows hp

const cars = RAW.cars.map((r, i) => {
  const c = { ...r, idx: i, imgs: r.imgs || [] };
  c.famName = famName(r.family);
  c.decade = `${Math.floor(r.year / 10) * 10}s`;
  c.bodyGroup = bodyGroup(r.body);
  c.designer = r.designer || 'Not credited';
  c.img = c.imgs[0] || null;
  let rest = '';
  for (const f of [c.famName, r.family]) {
    if (norm(r.name).startsWith(norm(f) + ' ')) { rest = r.name.slice(f.length + 1); c.head = r.name.slice(0, f.length); break; }
  }
  c.rest = rest;
  if (!rest) c.head = r.name;
  c.title = `Lamborghini ${r.name}`;
  c.hay = norm([r.name, c.famName, r.family, r.kind, r.body, c.bodyGroup, r.engine, r.eng, c.designer, r.note, r.year, r.end || '', c.decade, r.cv ? `${hp(r.cv)} hp ${r.cv} cv` : ''].join(' | '));
  return c;
});
const byId = new Map(cars.map((c) => [c.id, c]));
const totalPhotos = cars.reduce((a, c) => a + c.imgs.length, 0);
const countBy = (list, fn) => { const m = new Map(); for (const x of list) { const k = fn(x); m.set(k, (m.get(k) || 0) + 1); } return m; };
function phHTML(im, want, cls = '', overlay = '', label = 'No free photo found yet') {
  return im
    ? `<div class="ph ${cls}" data-empty="Photo unavailable"><img src="${esc(imgUrl(im, want))}" alt="" loading="lazy" decoding="async">${overlay}</div>`
    : `<div class="ph empty ${cls}" data-empty="${esc(label)}">${overlay}</div>`;
}
document.addEventListener('error', (e) => {   // photo hosts rate-limit bursts: retry once after a pause, then give up
  const t = e.target;
  if (!t || t.tagName !== 'IMG' || !t.parentElement || !t.parentElement.matches('.ph, .hero')) return;
  if (!t.dataset.retried) {
    t.dataset.retried = '1'; t.style.visibility = 'hidden';   // no broken-image icon while waiting
    t.addEventListener('load', () => { t.style.visibility = ''; }, { once: true });
    const src = t.src; setTimeout(() => { t.src = src; }, 1500 + Math.random() * 2500); return;
  }
  t.parentElement.classList.add('missing');
}, true);
{ // phones: a placeholder that fits the narrow search box
  const mq = matchMedia('(max-width:820px)');
  const ph = () => { document.getElementById('q').placeholder = mq.matches ? `Search ${cars.length} cars` : 'Search model, year, engine or designer'; };
  ph(); mq.addEventListener('change', ph);
}
function famRep(list) {
  const withImg = list.filter((c) => c.img);
  return withImg.find((c) => c.kind === 'Production') || withImg[0] || null;
}

/* ================= facets & state ================= */
const FACETS = [
  { key: 'fam', param: 'family', label: 'Family', get: (c) => c.family, name: famName, style: 'list', find: 'Find a family', top: 10 },
  { key: 'kind', param: 'type', label: 'Type', get: (c) => c.kind, style: 'chips', order: KIND_ORDER },
  { key: 'decade', param: 'decade', label: 'Decade', get: (c) => c.decade, style: 'chips', order: 'asc' },
  { key: 'eng', param: 'engine', label: 'Engine', get: (c) => c.eng, style: 'chips', order: ENG_ORDER },
  { key: 'body', param: 'body', label: 'Body', get: (c) => c.bodyGroup, style: 'chips' },
  { key: 'designer', param: 'designer', label: 'Designer', get: (c) => c.designer, style: 'list', find: 'Find a designer', top: 8 },
];
const FK = Object.fromEntries(FACETS.map((f) => [f.key, f]));
const POWER_STEPS = [0, 400, 600, 800, 1000];
const state = { q: '', sel: Object.fromEntries(FACETS.map((f) => [f.key, new Set()])), minHp: 0, sort: 'new', view: store.get('view', 'grid') };
const ui = { expanded: {}, find: {} };
let qTokens = [];
let results = [];
let currentQS = null;
const tokens = (q) => norm(q).split(/\s+/).filter(Boolean);
const matchTokens = (c, toks) => toks.every((t) => c.hay.includes(t));
function passes(c, except) {
  for (const f of FACETS) {
    if (f.key === except) continue;
    const s = state.sel[f.key];
    if (s.size && !s.has(f.get(c))) return false;
  }
  if (state.minHp && !(c.cv && hp(c.cv) >= state.minHp)) return false;
  if (qTokens.length && !matchTokens(c, qTokens)) return false;
  return true;
}
const SORTS = [['new', 'Newest first'], ['old', 'Oldest first'], ['power', 'Most powerful'], ['rare', 'Rarest first'], ['photos', 'Most photos'], ['name', 'Name, A to Z']];
const SORTERS = {
  new: (a, b) => b.year - a.year || a.idx - b.idx,
  old: (a, b) => a.year - b.year || a.idx - b.idx,
  power: (a, b) => (b.cv ?? -1) - (a.cv ?? -1) || b.year - a.year,
  rare: (a, b) => (a.units ?? 1e9) - (b.units ?? 1e9) || a.year - b.year,
  photos: (a, b) => b.imgs.length - a.imgs.length || b.year - a.year,
  name: (a, b) => a.name.localeCompare(b.name),
};
function stateToQS() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  for (const f of FACETS) for (const v of state.sel[f.key]) p.append(f.param, v);
  if (state.minHp) p.set('power', state.minHp);
  if (state.sort !== 'new') p.set('sort', state.sort);
  return p.toString();
}
function applyQS(p) {
  state.q = p.get('q') || '';
  for (const f of FACETS) state.sel[f.key] = new Set(p.getAll(f.param));
  state.minHp = +p.get('power') || 0;
  state.sort = SORTERS[p.get('sort')] ? p.get('sort') : 'new';
  qTokens = tokens(state.q);
}
const browseHash = () => { const qs = stateToQS(); return qs ? `#/?${qs}` : '#/'; };
function hashFor(sel) {
  const p = new URLSearchParams();
  for (const [k, vals] of Object.entries(sel)) for (const v of vals) p.append(FK[k].param, v);
  return `#/?${p}`;
}

/* ================= browse ================= */
const gridEl = $('#grid');
const BATCH = 36;
let shown = 0;
function update() {
  qTokens = tokens(state.q);
  results = cars.filter((c) => passes(c));
  results.sort(SORTERS[state.sort] || SORTERS.new);
  currentQS = stateToQS();
  if (activeView === 'browse' && !detailId && !location.hash.startsWith('#/m/')) {
    const h = browseHash();
    if (location.hash !== h && !(h === '#/' && (location.hash === '' || location.hash === '#'))) history.replaceState(null, '', pageURL() + h);
  }
  renderCount(); renderActive(); renderFacets(); renderStrip(); renderGrid(true); syncControls();
}
function renderCount() {
  const filtered = results.length !== cars.length;
  $('#masthead').classList.toggle('slim', filtered || !!state.q);
  $('#count').innerHTML = `${fmt(results.length)} ${results.length === 1 ? 'car' : 'cars'}${filtered ? ` <small>of ${fmt(cars.length)}</small>` : ''}`;
  $('#f-show').textContent = results.length ? `Show ${fmt(results.length)} ${results.length === 1 ? 'car' : 'cars'}` : 'No matches';
  const n = FACETS.reduce((a, f) => a + state.sel[f.key].size, 0) + (state.minHp ? 1 : 0);
  $('#f-n').textContent = n || '';
}
function renderActive() {
  const chips = [];
  if (state.q) chips.push(`<span class="achip"><span class="k">Search</span> “${esc(state.q)}”<button type="button" data-rm="q" aria-label="Remove search">${icon('x')}</button></span>`);
  for (const f of FACETS) for (const v of state.sel[f.key]) {
    const nm = f.name ? f.name(v) : v;
    chips.push(`<span class="achip"><span class="k">${f.label}</span> ${esc(nm)}<button type="button" data-rm="${f.key}" data-v="${esc(v)}" aria-label="Remove ${esc(f.label)} ${esc(nm)}">${icon('x')}</button></span>`);
  }
  if (state.minHp) chips.push(`<span class="achip"><span class="k">Power</span> ${fmt(state.minHp)}+ hp<button type="button" data-rm="power" aria-label="Remove power filter">${icon('x')}</button></span>`);
  if (chips.length > 1) chips.push('<button class="clear-all" type="button" data-clear-all>Clear all</button>');
  $('#active').innerHTML = chips.join('');
  $('#active').hidden = !chips.length;
}
function buildFacetShells() {
  $('#facets').innerHTML = FACETS.map((f) => `
    <section class="facet" data-facet="${f.key}">
      <div class="facet-h"><h3>${f.label}</h3><button type="button" data-clear-facet="${f.key}" hidden>Clear</button></div>
      ${f.find ? `<input class="facet-find" type="search" data-find="${f.key}" placeholder="${f.find}" aria-label="${f.find}">` : ''}
      <div class="${f.style === 'chips' ? 'chips' : 'opts'}" data-opts="${f.key}"></div>
      ${f.top ? `<button class="more-opts" type="button" data-more="${f.key}" hidden></button>` : ''}
    </section>`).join('') + `
    <section class="facet" data-facet="power">
      <div class="facet-h"><h3>Power</h3></div>
      <div class="chips" id="power-chips">${POWER_STEPS.map((p) => `<button class="chip" type="button" data-power="${p}" aria-pressed="false">${p ? `${fmt(p)}+ hp` : 'Any'}</button>`).join('')}</div>
    </section>`;
}
function renderFacets() {
  for (const f of FACETS) {
    const counts = countBy(cars.filter((c) => passes(c, f.key)), f.get);
    const sel = state.sel[f.key];
    for (const v of sel) if (!counts.has(v)) counts.set(v, 0);
    let entries = [...counts.entries()];
    if (Array.isArray(f.order)) entries.sort((a, b) => f.order.indexOf(a[0]) - f.order.indexOf(b[0]));
    else if (f.order === 'asc') entries.sort((a, b) => a[0].localeCompare(b[0]));
    else entries.sort((a, b) => (sel.has(b[0]) - sel.has(a[0])) || b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
    entries = entries.filter(([v, c]) => c > 0 || sel.has(v));
    const find = norm(ui.find[f.key] || '');
    if (find) entries = entries.filter(([v]) => norm(f.name ? f.name(v) : v).includes(find));
    let hidden = 0;
    if (f.top && !ui.expanded[f.key] && !find && entries.length > f.top + 2) { hidden = entries.length - f.top; entries = entries.slice(0, Math.max(f.top, sel.size)); }
    const host = $(`[data-opts="${f.key}"]`);
    if (f.style === 'chips') {
      host.innerHTML = entries.map(([v, c]) => `<button class="chip${c ? '' : ' is-zero'}" type="button" data-f="${f.key}" data-v="${esc(v)}" aria-pressed="${sel.has(v)}">${f.key === 'kind' ? `<span class="sw" style="--sw:${KIND_COLOUR[v]}"></span>` : ''}${esc(f.name ? f.name(v) : v)} <span class="ct">${fmt(c)}</span></button>`).join('');
    } else {
      host.innerHTML = entries.length ? entries.map(([v, c]) => `<label class="opt${c ? '' : ' is-zero'}"><input type="checkbox" data-f="${f.key}" value="${esc(v)}"${sel.has(v) ? ' checked' : ''}><span class="nm">${esc(f.name ? f.name(v) : v)}</span><span class="ct">${fmt(c)}</span></label>`).join('') : '<p class="opt" style="color:var(--faint);grid-template-columns:1fr">Nothing matches</p>';
    }
    const more = $(`[data-more="${f.key}"]`);
    if (more) { more.hidden = !(hidden || ui.expanded[f.key]) || !!find; more.textContent = ui.expanded[f.key] ? 'Show fewer' : `Show all ${fmt(hidden + f.top)}`; }
    $(`[data-clear-facet="${f.key}"]`).hidden = !sel.size;
  }
  $$('#power-chips .chip').forEach((b) => b.setAttribute('aria-pressed', String(+b.dataset.power === state.minHp)));
}
function renderStrip() {
  const famSel = [...state.sel.fam];
  let tiles = [];
  if (famSel.length === 1) {
    const fam = famSel[0];
    const list = cars.filter((c) => c.family === fam && passes(c, 'fam')).sort((a, b) => a.year - b.year);
    $('#strip-title').textContent = `The ${famName(fam)} family`;
    tiles.push(`<button class="tile back" type="button" data-strip-back>${icon('back')}All families</button>`);
    tiles = tiles.concat(list.map((c) => `<a class="tile" href="#/m/${c.id}" data-open="${c.id}">${phHTML(c.img, 500)}<span class="t"><b>${esc(c.rest || c.name)}</b><span>${c.year}</span></span></a>`));
  } else {
    const groups = new Map();
    for (const c of cars.filter((x) => passes(x, 'fam'))) { if (!groups.has(c.family)) groups.set(c.family, []); groups.get(c.family).push(c); }
    $('#strip-title').textContent = 'Browse by family';
    tiles = [...groups.entries()].sort((a, b) => b[1].length - a[1].length || famRep(b[1]) - famRep(a[1])).slice(0, 40).map(([f, list]) => {
      const rep = famRep(list);
      return `<button class="tile" type="button" data-strip-fam="${esc(f)}" aria-pressed="${state.sel.fam.has(f)}">${phHTML(rep && rep.img, 500)}<span class="t"><b>${esc(famName(f))}</b><span>${fmt(list.length)}</span></span></button>`;
    });
  }
  $('#strip').innerHTML = tiles.join('');
}
function powerLabel(c) { return c.cv ? `${fmt(hp(c.cv))} hp` : ''; }
function cardHTML(c) {
  const cmp = compare.includes(c.id);
  const overlay = `<span class="c-scale">${yearsShort(c)}</span>${c.kind !== 'Production' ? `<span class="c-kind" style="--k:${KIND_COLOUR[c.kind]}">${esc(c.kind)}</span>` : ''}${c.imgs.length > 1 ? `<span class="c-ph">${c.imgs.length} photos</span>` : ''}`;
  return `<article class="card" data-id="${c.id}">
  <a href="#/m/${c.id}" data-open="${c.id}">
    ${phHTML(c.img, 960, 'c-img', overlay)}
    <div class="c-body">
      <h3 class="c-title">${esc(c.head)}${c.rest ? ` <span class="v">${esc(c.rest)}</span>` : ''}</h3>
      <div class="c-maker"><span>${esc(c.engine)}</span></div>
      <span class="c-l-scale">${yearsShort(c)}</span>
      <div class="c-row"><span class="col">${esc(c.kind)}</span><span class="date">${c.units ? `${fmt(c.units)} built` : ''}</span><span class="score">${powerLabel(c)}</span></div>
    </div>
  </a>
  <button class="c-cmp" type="button" data-cmp="${c.id}" aria-pressed="${cmp}" aria-label="${cmp ? 'Remove from' : 'Add to'} compare: ${esc(c.name)}">${icon(cmp ? 'check' : 'plus')}</button>
</article>`;
}
function renderGrid(reset) {
  if (reset) { gridEl.innerHTML = ''; shown = 0; }
  gridEl.classList.toggle('list', state.view === 'list');
  const next = results.slice(shown, shown + BATCH);
  gridEl.insertAdjacentHTML('beforeend', next.map(cardHTML).join(''));
  shown += next.length;
  const left = results.length - shown;
  $('#load').hidden = left <= 0;
  $('#more').textContent = `Show ${fmt(Math.min(BATCH, left))} more (${fmt(left)} left)`;
  $('#empty').hidden = results.length > 0;
}
function syncControls() {
  const qi = $('#q');
  if (document.activeElement !== qi && qi.value !== state.q) qi.value = state.q;
  $('#q-clear').hidden = !qi.value;
  $('#sort').value = state.sort;
  $$('[data-layout]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.layout === state.view)));
}
function setHero(on) {   // the car of the day takes the family strip's place
  $('#masthead').hidden = !on; $('#strip-h').hidden = on; $('#strip').hidden = on;
  if (!on || $('#hero').childElementCount) return;
  // a wide, sharp Commons lead photo, the same for everyone on a given date
  const wide = cars.filter((c) => c.img && !c.img.sz && c.img.w >= 1600 && c.img.ht && c.img.w / c.img.ht >= 1.3 && c.img.w / c.img.ht <= 2.2);
  if (!wide.length) return;
  const day = Math.floor(Date.now() / 864e5);
  const pick = wide[(day * 2654435761 >>> 0) % wide.length];
  const yrs = pick.end === 0 ? `${pick.year}–now` : pick.end ? `${pick.year}–${pick.end}` : `${pick.year}`;
  $('#hero').innerHTML = `<img src="${esc(imgUrl(pick.img, 1920))}" alt="${esc(pick.title)}" fetchpriority="high" decoding="async">
    <a class="hero-tag" href="#/m/${esc(pick.id)}"><span class="mono">Car of the day</span><b>${esc(pick.name)}</b><span class="mono">${yrs}</span>${icon('right')}</a>
    <span class="hero-credit">${creditHTML(pick.img)}</span>`;
}
function introText() {
  $('#foot-l').textContent = `Index compiled ${RAW.generated} · ${fmt(cars.length)} cars · ${fmt(totalPhotos)} photos`;
}

/* ================= browse interactions ================= */
function toggleSel(key, v, on) {
  const s = state.sel[key];
  if (on === undefined) on = !s.has(v);
  if (on) s.add(v); else s.delete(v);
  update();
}
$('#facets').addEventListener('change', (e) => { const t = e.target; if (t.dataset.f) toggleSel(t.dataset.f, t.value, t.checked); });
$('#facets').addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  if (b.dataset.f) toggleSel(b.dataset.f, b.dataset.v);
  else if (b.dataset.more) { ui.expanded[b.dataset.more] = !ui.expanded[b.dataset.more]; renderFacets(); }
  else if (b.dataset.clearFacet) { state.sel[b.dataset.clearFacet].clear(); update(); }
  else if (b.dataset.power !== undefined) { state.minHp = +b.dataset.power; update(); }
});
$('#facets').addEventListener('input', (e) => { const t = e.target; if (t.dataset.find) { ui.find[t.dataset.find] = t.value; renderFacets(); } });
$('#active').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-rm]');
  if (!b) return;
  const k = b.dataset.rm;
  if (k === 'q') { state.q = ''; $('#q').value = ''; } else if (k === 'power') state.minHp = 0; else state.sel[k].delete(b.dataset.v);
  update();
});
function clearAll() { state.q = ''; $('#q').value = ''; for (const f of FACETS) state.sel[f.key].clear(); state.minHp = 0; update(); }
document.addEventListener('click', (e) => { if (e.target.closest('[data-clear-all]')) clearAll(); });
$('#strip').addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  if (b.dataset.stripBack !== undefined) state.sel.fam.clear();
  else if (b.dataset.stripFam !== undefined) { const f = b.dataset.stripFam; const only = state.sel.fam.size === 1 && state.sel.fam.has(f); state.sel.fam = new Set(only ? [] : [f]); }
  update();
  $('#strip').scrollLeft = 0;
});
$('#sort').innerHTML = SORTS.map(([k, l]) => `<option value="${k}">${l}</option>`).join('');
$('#sort').addEventListener('change', () => { state.sort = $('#sort').value; update(); });
$$('[data-layout]').forEach((b) => b.addEventListener('click', () => { state.view = b.dataset.layout; store.set('view', state.view); renderGrid(true); syncControls(); }));
$('#more').addEventListener('click', () => renderGrid(false));
new IntersectionObserver((ents) => {
  if (ents.some((x) => x.isIntersecting) && activeView === 'browse' && shown < results.length && shown > 0) renderGrid(false);
}, { rootMargin: '900px 0px' }).observe($('#sentinel'));
$('#random').addEventListener('click', () => { const pool = results.length ? results : cars; openModel(pool[Math.floor(Math.random() * pool.length)].id); });
$('#open-filters').addEventListener('click', () => document.body.classList.add('filters-open'));
$$('[data-close-filters]').forEach((b) => b.addEventListener('click', () => document.body.classList.remove('filters-open')));

/* ================= search + suggestions ================= */
const qi = $('#q');
const sgEl = $('#suggest');
let sgItems = [];
let sgIdx = -1;
let qTimer = 0;
qi.addEventListener('input', () => {
  $('#q-clear').hidden = !qi.value;
  renderSuggest();
  clearTimeout(qTimer);
  qTimer = setTimeout(() => { state.q = qi.value.trim(); if (activeView !== 'browse') { location.hash = browseHash(); return; } update(); }, 140);
});
qi.addEventListener('focus', renderSuggest);
qi.addEventListener('blur', () => setTimeout(hideSuggest, 150));
qi.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    if (!sgItems.length) return;
    e.preventDefault();
    sgIdx = (sgIdx + (e.key === 'ArrowDown' ? 1 : -1) + sgItems.length) % sgItems.length;
    $$('.sg', sgEl).forEach((el, i) => el.setAttribute('aria-selected', String(i === sgIdx)));
  } else if (e.key === 'Enter') {
    if (sgIdx >= 0 && sgItems[sgIdx]) { e.preventDefault(); pickSuggest(sgItems[sgIdx]); return; }
    clearTimeout(qTimer); state.q = qi.value.trim(); hideSuggest();
    if (activeView !== 'browse') location.hash = browseHash(); else update();
    qi.blur();
  } else if (e.key === 'Escape') { hideSuggest(); qi.blur(); }
});
$('#q-clear').addEventListener('click', () => { qi.value = ''; state.q = ''; $('#q-clear').hidden = true; hideSuggest(); update(); qi.focus(); });
sgEl.addEventListener('mousedown', (e) => e.preventDefault());
sgEl.addEventListener('click', (e) => { const b = e.target.closest('.sg'); if (b) pickSuggest(sgItems[+b.dataset.i]); });
function hideSuggest() { sgEl.hidden = true; qi.setAttribute('aria-expanded', 'false'); sgIdx = -1; }
function renderSuggest() {
  const raw = qi.value.trim();
  const t = norm(raw);
  if (t.length < 2) { hideSuggest(); sgItems = []; return; }
  const hits = [];
  for (const key of ['fam', 'kind', 'eng', 'designer', 'decade', 'body']) {
    const f = FK[key];
    for (const [v, n] of countBy(cars, f.get)) {
      const nm = f.name ? f.name(v) : v;
      const at = norm(nm).indexOf(t);
      if (at >= 0) hits.push({ type: 'facet', key, v, nm, n, score: at === 0 ? 0 : 1 });
    }
  }
  hits.sort((a, b) => a.score - b.score || b.n - a.n);
  const toks = tokens(raw);
  const carHits = cars.filter((c) => matchTokens(c, toks)).sort((a, b) => (norm(a.name).includes(t) ? 0 : 1) - (norm(b.name).includes(t) ? 0 : 1) || b.year - a.year).slice(0, 6).map((c) => ({ type: 'car', c }));
  sgItems = hits.slice(0, 5).concat(carHits);
  sgIdx = -1;
  if (!sgItems.length) { sgEl.innerHTML = `<div class="sg-h">No matches for “${esc(raw)}”</div>`; sgEl.hidden = false; return; }
  let html = '';
  sgItems.forEach((it, i) => {
    if (i === 0 && it.type === 'facet') html += '<div class="sg-h">Filter by</div>';
    if (it.type === 'car' && (i === 0 || sgItems[i - 1].type !== 'car')) html += '<div class="sg-h">Cars</div>';
    if (it.type === 'facet') html += `<button class="sg" type="button" role="option" data-i="${i}" aria-selected="false"><span class="k">${FK[it.key].label}</span><span class="n">${esc(it.nm)}</span><span class="c">${fmt(it.n)}</span></button>`;
    else html += `<button class="sg" type="button" role="option" data-i="${i}" aria-selected="false"><span class="th">${phHTML(it.c.img, 330)}</span><span class="n">${esc(it.c.name)} <span class="sub">${yearsShort(it.c)} · ${esc(it.c.kind)}</span></span><span class="c">${powerLabel(it.c)}</span></button>`;
  });
  sgEl.innerHTML = html;
  sgEl.hidden = false;
  qi.setAttribute('aria-expanded', 'true');
}
function pickSuggest(it) {
  hideSuggest(); clearTimeout(qTimer);
  if (it.type === 'car') { openModel(it.c.id); return; }
  qi.value = ''; state.q = '';
  state.sel[it.key].add(it.v);
  if (activeView !== 'browse') location.hash = browseHash(); else update();
  qi.blur();
}
document.addEventListener('keydown', (e) => {
  const tag = (document.activeElement && document.activeElement.tagName) || '';
  if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(tag) && !lb.open && !detailId) { e.preventDefault(); qi.focus(); qi.select(); }
});

/* ================= compare ================= */
let compare = (store.get('compare', []) || []).filter((id) => byId.has(id)).slice(0, 4);
function saveCompare() { store.set('compare', compare); renderTray(); }
function toggleCompare(id) {
  const i = compare.indexOf(id);
  if (i >= 0) compare.splice(i, 1);
  else if (compare.length >= 4) { toast('Compare holds four cars. Remove one first.'); return; }
  else compare.push(id);
  saveCompare();
  $$(`[data-cmp="${CSS.escape(id)}"]`).forEach((b) => {
    const on = compare.includes(id);
    b.setAttribute('aria-pressed', String(on));
    if (b.classList.contains('c-cmp')) { b.innerHTML = icon(on ? 'check' : 'plus'); b.setAttribute('aria-label', b.getAttribute('aria-label').replace(/^(Add to|Remove from)/, on ? 'Remove from' : 'Add to')); }
    else b.innerHTML = `${icon(on ? 'check' : 'plus')}${on ? 'In compare' : 'Add to compare'}`;
  });
  if (activeView === 'compare') renderCompare();
}
function renderTray() {
  $$('[data-cmp-count]').forEach((n) => { n.textContent = compare.length; n.hidden = !compare.length; });
  $('#tray').hidden = !compare.length || activeView === 'compare' || !!detailId;
  $('#tray-ths').innerHTML = compare.map((id) => { const c = byId.get(id); return `<span class="t" title="${esc(c.name)}">${phHTML(c.img, 330)}<button type="button" data-tray-rm="${c.id}" aria-label="Remove ${esc(c.name)} from compare">${icon('x')}</button></span>`; }).join('');
  $('#tray-go').textContent = compare.length > 1 ? `Compare ${compare.length}` : 'Add another';
  $('#tray-go').setAttribute('href', compare.length > 1 ? '#/compare' : browseHash());
}
$('#tray-ths').addEventListener('click', (e) => { const b = e.target.closest('[data-tray-rm]'); if (b) toggleCompare(b.dataset.trayRm); });
$('#tray-clear').addEventListener('click', () => { compare.slice().forEach((id) => toggleCompare(id)); });
document.addEventListener('click', (e) => { const b = e.target.closest('[data-cmp]'); if (b) { e.preventDefault(); toggleCompare(b.dataset.cmp); } });
const EXAMPLE = ['miura-p400', 'countach-lp400', 'diablo', 'aventador-lp700'];
function renderCompare() {
  const list = compare.map((id) => byId.get(id)).filter(Boolean);
  const host = $('#compare');
  $('#cmp-tools').innerHTML = list.length ? '<button class="btn ghost" type="button" id="cmp-clear">Clear all</button>' : '';
  if (list.length < 2) {
    host.innerHTML = `<div class="empty-state"><b>${list.length ? 'Add at least one more car.' : 'Nothing to compare yet.'}</b>Use the <b>+</b> on any card, or try four generations of V12 flagship: Miura, Countach, Diablo and Aventador.<div style="margin-top:14px"><button class="btn primary" type="button" id="cmp-example">Load this example</button></div></div>`;
    $('#cmp-example').addEventListener('click', () => { compare = EXAMPLE.filter((id) => byId.has(id)); saveCompare(); renderCompare(); });
  } else {
    const best = (vals, low) => { const nums = vals.filter((v) => v != null); if (nums.length < 2) return null; const b = low ? Math.min(...nums) : Math.max(...nums); return nums.every((v) => v === b) ? null : b; };
    const bestCv = best(list.map((c) => c.cv));
    const rarest = best(list.map((c) => c.units), true);
    const rows = [
      ['Years', (c) => yearsLong(c)], ['Type', (c) => esc(c.kind)], ['Body', (c) => esc(c.body)], ['Engine', (c) => esc(c.engine)],
      ['Power', (c) => (c.cv ? `<span class="mono">${fmt(hp(c.cv))} hp</span> <span style="color:var(--faint)">${fmt(kw(c.cv))} kW</span>` : '—'), (c) => c.cv != null && c.cv === bestCv],
      ['Built', (c) => (c.units ? `<span class="mono">${fmt(c.units)}</span>` : '—'), (c) => c.units != null && c.units === rarest],
      ['Designer', (c) => esc(c.designer)], ['Photos', (c) => `<span class="mono">${c.imgs.length}</span>`],
    ];
    host.innerHTML = `<div class="cmp-wrap"><table class="cmp"><thead><tr><th scope="row"></th>${list.map((c) => `<td>${phHTML(c.img, 960)}<a class="cname" href="#/m/${c.id}" data-open="${c.id}" style="text-decoration:none">${esc(c.head)} <span class="v">${esc(c.rest)}</span></a><div style="color:var(--muted);font-size:13px">${yearsLong(c)}</div><button class="rm" type="button" data-cmp-rm="${c.id}">Remove</button></td>`).join('')}</tr></thead><tbody>
      ${rows.map(([label, fn, hi]) => `<tr><th scope="row">${label}</th>${list.map((c) => `<td class="${hi && hi(c) ? 'best' : ''}">${fn(c)}</td>`).join('')}</tr>`).join('')}
      <tr><th scope="row">More</th>${list.map((c) => `<td>${c.wiki ? `<a href="https://en.wikipedia.org/wiki/${encodeURIComponent(c.wiki.replace(/ /g, '_'))}" target="_blank" rel="noopener" style="color:var(--accent-2)">Wikipedia</a>` : '—'}</td>`).join('')}</tr>
    </tbody></table></div><p class="note" style="color:var(--faint);font-size:12.5px;margin:-60px 0 80px">Highlighted: most powerful, and fewest built.</p>`;
  }
  const cc = $('#cmp-clear');
  if (cc) cc.addEventListener('click', () => { compare = []; saveCompare(); renderCompare(); });
}
$('#compare').addEventListener('click', (e) => { const b = e.target.closest('[data-cmp-rm]'); if (b) toggleCompare(b.dataset.cmpRm); });

/* ================= detail sheet ================= */
const sheet = $('#sheet');
const panel = $('#sheet-panel');
let detailId = null;
let detailFromApp = false;
let detailList = null;
let lastFocus = null;
let lastViewHash = '#/';
function openModel(id) { detailFromApp = true; lastFocus = document.activeElement; location.hash = `#/m/${id}`; }
function closeModel() {
  if (detailFromApp) { detailFromApp = false; history.back(); }
  else location.hash = activeView === 'browse' ? browseHash() : lastViewHash;
}
function showDetail(c) {
  detailId = c.id;
  const src = activeView === 'compare' ? compare.map((id) => byId.get(id)) : results;
  detailList = src.includes(c) ? src : null;
  renderDetail(c);
  if (sheet.hidden) {
    sheet.hidden = false;
    document.documentElement.classList.add('locked');
    sheet.scrollTop = 0;
    setTimeout(() => $('#d-close') && $('#d-close').focus({ preventScroll: true }), 30);
  }
  renderTray();
}
function hideDetail() {
  if (sheet.hidden) return;
  sheet.hidden = true;
  detailId = null;
  document.documentElement.classList.remove('locked');
  closeLB();
  renderTray();
  if (lastFocus && document.contains(lastFocus)) lastFocus.focus({ preventScroll: true });
}
function relatedRow(title, list, more) {
  if (!list.length) return '';
  return `<section><h3>${esc(title)} <span class="mono" style="color:var(--faint);letter-spacing:0">${fmt(list.length)}</span>${more ? ` · <a href="${more}" style="color:var(--accent-2);text-transform:none;letter-spacing:0;font-weight:500">browse all</a>` : ''}</h3><div class="rel-row">${list.slice(0, 14).map(cardHTML).join('')}</div></section>`;
}
function renderDetail(c) {
  const idx = detailList ? detailList.indexOf(c) : -1;
  const photos = c.imgs;
  const sameFam = cars.filter((x) => x !== c && x.family === c.family).sort((a, b) => a.year - b.year);
  const sameDecade = cars.filter((x) => x !== c && x.decade === c.decade && x.family !== c.family).sort((a, b) => a.year - b.year);
  const q = `Lamborghini ${c.name.replace(/[“”]/g, '')}`;
  const stage = photos.length
    ? `<div class="ph stage" id="stage" role="button" tabindex="0" aria-label="Open photo viewer" data-empty="Photo unavailable"><img id="stage-img" src="${esc(imgUrl(photos[0], 1920))}" alt="${esc(c.title)}"><span class="zoom">1 / ${photos.length} · full resolution</span></div>
       <p class="credit" id="stage-credit">${creditHTML(photos[0])}${reportHTML(c, photos[0])}</p>
       ${photos.length > 1 ? `<div class="thumbs" id="thumbs">${photos.map((im, i) => `<button type="button" data-ph="${i}" aria-label="Photo ${i + 1}" aria-current="${i === 0}"><img src="${esc(imgUrl(im, 330))}" alt="" loading="lazy"></button>`).join('')}</div>` : ''}`
    : `<div class="ph stage empty" data-empty="No freely licensed photo yet"></div>
       <p class="credit">Every photo of this car we could find is copyrighted, so it can't be shown here. See it on ${photoSearches(q)}.</p>`;
  panel.innerHTML = `
  <div class="sheet-bar">
    <div class="grp">
      <button class="iconbtn" type="button" id="d-prev" aria-label="Previous car" ${idx > 0 ? '' : 'disabled'}>${icon('left')}</button>
      <button class="iconbtn" type="button" id="d-next" aria-label="Next car" ${detailList && idx < detailList.length - 1 ? '' : 'disabled'}>${icon('right')}</button>
      <span class="pos">${idx >= 0 ? `${fmt(idx + 1)} of ${fmt(detailList.length)}` : esc(c.famName)}</span>
    </div>
    <button class="iconbtn" type="button" id="d-close" aria-label="Close">${icon('x')}</button>
  </div>
  <div class="d-grid">
    <div>${stage}</div>
    <div>
      <div class="d-eyebrow">${yearsLong(c)} · ${esc(c.kind)}</div>
      <h2 class="d-title" id="d-title">${esc(c.head)}${c.rest ? ` <span class="v">${esc(c.rest)}</span>` : ''}</h2>
      <p class="d-sub">${esc(c.note)}</p>
      <dl class="facts">
        <dt>Years</dt><dd>${yearsLong(c)}</dd>
        <dt>Type</dt><dd><a href="${hashFor({ kind: [c.kind] })}" style="color:var(--text)">${esc(c.kind)}</a></dd>
        <dt>Body</dt><dd>${esc(c.body)}</dd>
        <dt>Engine</dt><dd>${esc(c.engine)}</dd>
        ${c.cv ? `<dt>Power</dt><dd><span class="mono">${fmt(hp(c.cv))} hp</span> <span class="hint">${fmt(kw(c.cv))} kW</span></dd>` : ''}
        <dt>Built</dt><dd>${c.units ? `<span class="mono">${fmt(c.units)}</span>${c.units === 1 ? ' <span class="hint">one of one</span>' : ''}` : '<span class="hint">not reliably known</span>'}</dd>
        <dt>Designer</dt><dd><a href="${hashFor({ designer: [c.designer] })}" style="color:var(--text)">${esc(c.designer)}</a></dd>
        <dt>Family</dt><dd><a href="${hashFor({ fam: [c.family] })}" style="color:var(--text)">${esc(c.famName)}</a> <span class="hint">${fmt(sameFam.length + 1)} in the index</span></dd>
      </dl>
      <div class="d-actions">
        ${c.wiki ? `<a class="btn primary" href="https://en.wikipedia.org/wiki/${encodeURIComponent(c.wiki.replace(/ /g, '_'))}" target="_blank" rel="noopener">Read on Wikipedia ${icon('ext')}</a>` : ''}
        <button class="btn" type="button" data-cmp="${c.id}" aria-pressed="${compare.includes(c.id)}">${icon(compare.includes(c.id) ? 'check' : 'plus')}${compare.includes(c.id) ? 'In compare' : 'Add to compare'}</button>
        ${c.cats && c.cats[0] ? `<a class="btn" href="https://commons.wikimedia.org/wiki/Category:${encodeURIComponent(c.cats[0].replace(/ /g, '_'))}" target="_blank" rel="noopener">All photos ${icon('ext')}</a>` : ''}
      </div>
      <div class="forsale"><h3>Go further</h3>
        <div class="links">
          <a class="btn" href="https://www.google.com/search?q=${encodeURIComponent(`${q} for sale`)}" target="_blank" rel="noopener">For sale ${icon('ext')}</a>
          <a class="btn" href="https://bringatrailer.com/search/?s=${encodeURIComponent(q)}" target="_blank" rel="noopener">Auction results ${icon('ext')}</a>
          <a class="btn" href="https://www.flickr.com/search/?text=${encodeURIComponent(q)}" target="_blank" rel="noopener">More photos ${icon('ext')}</a>
          <a class="btn" href="https://www.lambodiecast.com/list.php?t=${encodeURIComponent(c.family)}" target="_blank" rel="noopener">Scale models ${icon('ext')}</a>
        </div>
        <p>Scale models open the ${esc(c.famName)} list on lambodiecast.com.</p>
      </div>
    </div>
  </div>
  <div class="related">
    ${relatedRow(`The ${c.famName} family`, sameFam, hashFor({ fam: [c.family] }))}
    ${relatedRow(`Also from the ${c.decade}`, sameDecade, hashFor({ decade: [c.decade] }))}
  </div>`;
  $('#d-close').addEventListener('click', closeModel);
  $('#d-prev').addEventListener('click', () => stepDetail(-1));
  $('#d-next').addEventListener('click', () => stepDetail(1));
  const st = $('#stage');
  if (st && photos.length) {
    let cur = 0;
    const setPhoto = (i) => {
      cur = i;
      $('#stage-img').src = imgUrl(photos[i], 1920);
      st.classList.remove('missing');
      st.querySelector('.zoom').textContent = `${i + 1} / ${photos.length} · full resolution`;
      $('#stage-credit').innerHTML = creditHTML(photos[i]) + reportHTML(c, photos[i]);
      $$('#thumbs button').forEach((b, j) => b.setAttribute('aria-current', String(j === i)));
    };
    st.addEventListener('click', () => openLB(c, cur));
    st.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openLB(c, cur); } });
    const th = $('#thumbs');
    if (th) th.addEventListener('click', (e) => { const b = e.target.closest('[data-ph]'); if (b) setPhoto(+b.dataset.ph); });
  }
  document.title = `${c.name} (${yearsLong(c)}) · The Lambo Index`;
}
function stepDetail(d) {
  if (!detailList) return;
  const i = detailList.findIndex((x) => x.id === detailId) + d;
  if (i < 0 || i >= detailList.length) return;
  const c = detailList[i];
  history.replaceState(null, '', `#/m/${c.id}`);
  detailId = c.id;
  renderDetail(c);
  sheet.scrollTop = 0;
}
sheet.addEventListener('click', (e) => {
  if (e.target === sheet) { closeModel(); return; }
  const a = e.target.closest('a[data-open]');
  if (a) {
    e.preventDefault();
    const c = byId.get(a.dataset.open);
    if (!c) return;
    history.replaceState(null, '', `#/m/${c.id}`);
    detailId = c.id; detailList = null;
    renderDetail(c); sheet.scrollTop = 0;
    return;
  }
  const b = e.target.closest('a[href^="#/?"]');
  if (b) { e.preventDefault(); const h = b.getAttribute('href'); detailFromApp = false; hideDetail(); location.hash = h; }
});
document.addEventListener('click', (e) => { const a = e.target.closest('a[data-open]'); if (a && !sheet.contains(a)) { detailFromApp = true; lastFocus = a; } });

/* ================= lightbox ================= */
const lb = { open: false, c: null, i: 0 };
function openLB(c, i) { lb.open = true; lb.c = c; lb.i = i; $('#lightbox').hidden = false; renderLB(); $('#lb-close').focus({ preventScroll: true }); }
function closeLB() { if (!lb.open) return; lb.open = false; $('#lightbox').hidden = true; const st = $('#stage'); if (st) st.focus({ preventScroll: true }); }
function renderLB() {
  const { c, i } = lb;
  const im = c.imgs[i];
  $('#lb-img').src = imgUrl(im, 3840, true);
  $('#lb-img').alt = `${c.title}, photo ${i + 1}`;
  $('#lb-count').textContent = `${i + 1} / ${c.imgs.length}`;
  $('#lb-title').textContent = `${c.name} · ${yearsLong(c)}`;
  $('#lb-credit').innerHTML = `${creditHTML(im)} · ${fmt(im.w)} × ${fmt(im.ht)} px${reportHTML(c, im)}`;
  [i - 1, i + 1].forEach((j) => { if (j >= 0 && j < c.imgs.length) { const pre = new Image(); pre.src = imgUrl(c.imgs[j], 3840, true); } });
}
function stepLB(d) { const n = lb.c.imgs.length; lb.i = (lb.i + d + n) % n; renderLB(); }
$('#lb-close').addEventListener('click', closeLB);
$('#lb-prev').addEventListener('click', () => stepLB(-1));
$('#lb-next').addEventListener('click', () => stepLB(1));
$('#lb-stage').addEventListener('click', (e) => { if (e.target.id === 'lb-stage') closeLB(); });
let touchX = null;
$('#lb-stage').addEventListener('touchstart', (e) => { touchX = e.touches[0].clientX; }, { passive: true });
$('#lb-stage').addEventListener('touchend', (e) => { if (touchX == null) return; const dx = e.changedTouches[0].clientX - touchX; if (Math.abs(dx) > 40) stepLB(dx < 0 ? 1 : -1); touchX = null; });
document.addEventListener('keydown', (e) => {
  if (lb.open) { if (e.key === 'Escape') { e.preventDefault(); closeLB(); } else if (e.key === 'ArrowLeft') stepLB(-1); else if (e.key === 'ArrowRight') stepLB(1); return; }
  if (detailId) {
    const typing = /INPUT|SELECT/.test(document.activeElement.tagName);
    if (e.key === 'Escape') { e.preventDefault(); closeModel(); } else if (e.key === 'ArrowLeft' && !typing) stepDetail(-1); else if (e.key === 'ArrowRight' && !typing) stepDetail(1);
    return;
  }
  if (e.key === 'Escape' && document.body.classList.contains('filters-open')) document.body.classList.remove('filters-open');
});

/* ================= timeline ================= */
let tlBuilt = false;
let fastBuilt = false;
/* Timeline legend chips filter the timeline and combine as AND: a car shows only when it has every
   chosen badge. Debut goes with any kind; the kinds exclude each other, since a car has one kind.
   #/timeline?only=debut,race */
const TL_ONLY = { debut: ['debut', 'debut', 'debuts'], race: ['race', 'race car', 'race cars'], lim: ['lim', 'limited', 'limited'], one: ['one', 'one-off', 'one-offs'] };
const TL_KINDS = ['race', 'lim', 'one'];
const tlSelected = () => ($('#timeline').dataset.only || '').split(' ').filter(Boolean);
function applyTlOnly(raw) {
  const asked = String(raw || '').split(',');
  const kind = TL_KINDS.find((k) => asked.includes(k));
  const sel = [...(asked.includes('debut') ? ['debut'] : []), ...(kind ? [kind] : [])];
  const tl = $('#timeline');
  if (sel.length) tl.dataset.only = sel.join(' '); else tl.removeAttribute('data-only');
  $('.tl-legend').classList.toggle('on', sel.length > 0);
  $$('.tl-legend [data-tlf]').forEach((b) => b.setAttribute('aria-pressed', String(sel.includes(b.dataset.tlf))));
  $$('#timeline .tl-item').forEach((it) => it.classList.toggle('hit', sel.length > 0 && sel.every((f) => it.classList.contains(TL_ONLY[f][0]))));
  $$('#timeline .decade').forEach((sec) => {
    const small = sec.querySelector('h2 small');
    const n = sel.length ? sec.querySelectorAll('.tl-item.hit').length : -1;
    sec.classList.toggle('none', n === 0);
    small.textContent = !sel.length ? small.dataset.all
      : sel.length === 1 ? `${n} ${n === 1 ? TL_ONLY[sel[0]][1] : TL_ONLY[sel[0]][2]}`
      : `${n} debut ${n === 1 ? TL_ONLY[sel[1]][1] : TL_ONLY[sel[1]][2]}`;
  });
}
document.addEventListener('click', (e) => {
  const clear = e.target.closest('.tl-legend [data-tlf-clear]');
  const b = e.target.closest('.tl-legend [data-tlf]');
  if (!clear && !b) return;
  const cur = new Set(clear ? [] : tlSelected());
  if (b) {
    const f = b.dataset.tlf;
    if (cur.has(f)) cur.delete(f);
    else { if (TL_KINDS.includes(f)) TL_KINDS.forEach((k) => cur.delete(k)); cur.add(f); }
  }
  const sel = Object.keys(TL_ONLY).filter((k) => cur.has(k));
  location.hash = sel.length ? `#/timeline?only=${sel.join(',')}` : '#/timeline';
  window.scrollTo(0, 0);
});
/* Fast 10: horsepower first, then claimed top speed ("350+" ranks above 350). Road cars with an
   official top speed only; open versions count with their coupé, so a Roadster never takes a second place. */
function buildFast() {
  if (fastBuilt) return;
  fastBuilt = true;
  const speed = (c) => c.vmax + (c.vplus ? 0.5 : 0);
  const top = cars.filter((c) => c.vmax && !/Roadster$/.test(c.name))
    .sort((a, b) => (b.cv || 0) - (a.cv || 0) || speed(b) - speed(a)).slice(0, 10);
  $('#fast').innerHTML = top.map((c, i) => `<a class="f10" href="#/m/${c.id}" data-open="${c.id}"><span class="rk">${i + 1}</span>${phHTML(c.img, 960)}<span class="b"><span class="nm">${esc(c.name)}</span><span class="yr">${yearsLong(c)}</span><span class="st">${c.acc ? `<span><b>${c.acc}</b> s 0–100</span>` : ''}</span></span><span class="sp"><span><b>${fmt(hp(c.cv))}</b>hp</span><span><b>${c.vmax}${c.vplus ? '+' : ''}</b>km/h</span></span></a>`).join('');
}
function buildTimeline() {
  if (tlBuilt) return;
  tlBuilt = true;
  const decades = new Map();
  const sorted = cars.slice().sort((a, b) => a.year - b.year || a.idx - b.idx);
  // debuts are flagged in the catalogue: the original form of each distinct car
  const debut = new Set(cars.filter((c) => c.debut).map((c) => c.id));
  const SPARKLES = `<span class="gems" aria-hidden="true">${'<i></i>'.repeat(7)}</span>`;   // crystal glints on one-offs
  for (const c of sorted) { if (!decades.has(c.decade)) decades.set(c.decade, []); decades.get(c.decade).push(c); }
  let html = '';
  for (const [d, list] of decades) {
    const nDebut = list.filter((c) => debut.has(c.id)).length;
    html += `<section class="decade"><h2>${d}<small data-all="${list.length} cars · ${nDebut} debut${nDebut === 1 ? '' : 's'}">${list.length} cars · ${nDebut} debut${nDebut === 1 ? '' : 's'}</small></h2><div class="tl">${list.map((c) => {
      const isDebut = debut.has(c.id);
      // one frame per car, the highest it qualifies for: one-off diamond > limited platinum >
      // race red > debut orange. Every badge stays.
      const kc = { 'Limited series': 'lim', 'One-off': 'one', 'Race car': 'race' }[c.kind] || '';
      const tags = `${isDebut ? ' <span class="tl-tag debut">Debut</span>' : ''}${kc === 'lim' ? ' <span class="tl-tag lim">Limited</span>' : ''}${kc === 'one' ? ' <span class="tl-tag one">One-off</span>' : ''}${kc === 'race' ? ' <span class="tl-tag race">Race car</span>' : ''}`;
      return `<a class="tl-item${isDebut ? ' debut' : ''}${kc ? ` ${kc}` : ''}" href="#/m/${c.id}" data-open="${c.id}">${phHTML(c.img, 960, '', isDebut && !kc ? '<span class="frame" aria-hidden="true"></span>' : '')}<span class="b"><span class="yr">${yearsLong(c)}${tags}</span><span class="nm">${esc(c.name)}</span><span class="meta"><span>${esc(c.kind)}</span><span>${c.cv ? `<span class="mono">${fmt(hp(c.cv))}</span> hp` : esc(c.eng)}</span></span></span>${kc === 'one' ? SPARKLES : ''}</a>`;
    }).join('')}</div></section>`;
  }
  html += '<p class="tl-foot">Years mark when a car was first shown or first built. Click any car for photos and specifications.</p>';
  $('#timeline').innerHTML = html;
}

/* ================= views & routing ================= */
let activeView = null;
const TITLES = { browse: 'The Lambo Index', timeline: 'Timeline · The Lambo Index', fast: 'Fast 10 · The Lambo Index', compare: 'Compare · The Lambo Index' };
function showView(v) {
  if (activeView !== v) {
    activeView = v;
    $$('.view').forEach((s) => { s.hidden = s.dataset.view !== v; });
    $$('a[data-view]').forEach((a) => a.setAttribute('aria-current', a.dataset.view === v ? 'page' : 'false'));
    if (v === 'timeline') buildTimeline();
    if (v === 'fast') buildFast();
    window.scrollTo(0, 0);
  }
  if (v === 'compare') renderCompare();
  if (!detailId) document.title = TITLES[v];
  renderTray();
}
function parseHash() {
  const h = location.hash.replace(/^#/, '') || '/';
  const i = h.indexOf('?');
  return { path: i >= 0 ? h.slice(0, i) : h, params: new URLSearchParams(i >= 0 ? h.slice(i + 1) : '') };
}
function route() {
  const { path, params } = parseHash();
  if (path.startsWith('/m/')) {
    const c = byId.get(decodeURIComponent(path.slice(3)));
    if (c) { if (!activeView) { applyQS(new URLSearchParams()); showView('browse'); update(); } showDetail(c); return; }
  }
  hideDetail();
  lastViewHash = location.hash || '#/';
  if (path === '/timeline') { showView('timeline'); applyTlOnly(params.get('only') || ''); }
  else if (path === '/fast10') showView('fast');
  else if (path === '/compare') {
    const ids = (params.get('ids') || '').split(',').filter((id) => byId.has(id)).slice(0, 4);
    if (ids.length) { compare = ids; saveCompare(); }
    showView('compare');
  } else {
    const was = activeView === 'browse';
    setHero(true);
    showView('browse');
    if (params.toString() !== currentQS || !was) { if (params.toString() !== currentQS) applyQS(params); update(); }
    document.title = TITLES.browse;
  }
}
window.addEventListener('hashchange', route);
let toastTimer = 0;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 2600); }

buildFacetShells();
introText();
route();
})();
