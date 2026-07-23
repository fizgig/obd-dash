/* PiZero OBD -- Eel frontend.
 *
 * Data arrives from Python via eel.push_data(snapshot). Four design options are
 * built here: each BUILDERS[name](stage) constructs its DOM and returns an
 * update(data) function. Switching design swaps the <body> theme class and the
 * #stage layout class, then rebuilds. Header/footer are shared across designs.
 */
'use strict';

const GAUGES = [
  { key:'rpm',     label:'RPM',     min:0,  max:8000, unit:'rpm',   dp:0, warn:6000, danger:7000 },
  { key:'speed',   label:'SPEED',   min:0,  max:160,  unit:'mph',   dp:0, warn:null, danger:null },
  { key:'coolant', label:'COOLANT', min:40, max:130,  unit:'°C', dp:0, warn:105, danger:115 },
  { key:'voltage', label:'BATTERY', min:10, max:16,   unit:'V',     dp:1, warn:null, danger:null },
];
const DESIGN_LABELS = {
  cockpit:'Cockpit', cluster:'Cluster', cards:'Cards', retro:'Retro LCD',
  neon:'Neon', hud:'Heads-Up',
};
const SVG_NS = 'http://www.w3.org/2000/svg';

const spec = (key) => GAUGES.find(g => g.key === key);
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
const fmt = (v, dp) => Number(v).toFixed(dp);
const frac = (v, s) => clamp((v - s.min) / (s.max - s.min), 0, 1);

function colorFor(v, s) {
  if (s.danger != null && v >= s.danger) return 'var(--red)';
  if (s.warn   != null && v >= s.warn)   return 'var(--amber)';
  return 'var(--accent)';
}
function sevColor(sev) {
  return { critical:'var(--red)', warning:'var(--amber)',
           info:'var(--accent)', pending:'var(--purple)' }[sev] || 'var(--muted)';
}
function el(tag, cls, html) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html != null) n.innerHTML = html;
  return n;
}

/* ------------------------------- primitives ------------------------------ */
function makeArc(s, big) {
  const R = 50, C = 2 * Math.PI * R, ARC = 0.75 * C, W = big ? 9 : 8;
  const wrap = el('div', 'gauge' + (big ? ' big' : ''));
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 120 120');
  const ring = (styleStroke, dash) => {
    const c = document.createElementNS(SVG_NS, 'circle');
    c.setAttribute('cx', 60); c.setAttribute('cy', 60); c.setAttribute('r', R);
    c.setAttribute('fill', 'none'); c.setAttribute('stroke-width', W);
    c.setAttribute('stroke-linecap', 'round');
    c.setAttribute('transform', 'rotate(135 60 60)');
    c.setAttribute('stroke-dasharray', dash);
    c.style.stroke = styleStroke;
    return c;
  };
  const track = ring('var(--track)', ARC + ' ' + C);
  const val = ring('var(--accent)', '0 ' + C);
  svg.appendChild(track); svg.appendChild(val);
  const txt = el('div', 'g-text',
    `<div class="g-label">${s.label}</div><div class="g-val">--</div><div class="g-unit">${s.unit}</div>`);
  wrap.appendChild(svg); wrap.appendChild(txt);
  const valEl = txt.querySelector('.g-val');
  return {
    el: wrap,
    set(v) {
      val.setAttribute('stroke-dasharray', (frac(v, s) * ARC) + ' ' + C);
      val.style.stroke = colorFor(v, s);
      valEl.textContent = fmt(v, s.dp);
    },
  };
}

function makeMeter(s) {
  const card = el('div', 'card');
  card.appendChild(el('div', 'c-label', s.label));
  const row = el('div', 'c-row');
  const valEl = el('span', 'c-val', '--');
  row.appendChild(valEl); row.appendChild(el('span', 'c-unit', s.unit));
  const meter = el('div', 'meter');
  const fill = el('span'); meter.appendChild(fill);
  card.appendChild(row); card.appendChild(meter);
  return {
    el: card,
    set(v) {
      valEl.textContent = fmt(v, s.dp);
      fill.style.width = (frac(v, s) * 100) + '%';
      fill.style.background = colorFor(v, s);
    },
  };
}

function makeSeg(s, n) {
  n = n || 18;
  const box = el('div', 'seg');
  const top = el('div', 's-top');
  const valEl = el('span', 's-val', '--');
  top.appendChild(el('span', 's-label', s.label));
  const right = el('span'); right.appendChild(valEl);
  right.appendChild(el('span', 's-unit', ' ' + s.unit));
  top.appendChild(right);
  const bar = el('div', 'segbar');
  const cells = [];
  for (let i = 0; i < n; i++) { const c = el('i'); bar.appendChild(c); cells.push(c); }
  box.appendChild(top); box.appendChild(bar);
  return {
    el: box,
    set(v) {
      valEl.textContent = fmt(v, s.dp);
      const lit = Math.round(frac(v, s) * n);
      let cls = 'on';
      if (s.danger != null && v >= s.danger) cls = 'danger';
      else if (s.warn != null && v >= s.warn) cls = 'warn';
      cells.forEach((c, i) => { c.className = i < lit ? cls : ''; });
    },
  };
}

/* DTC list with signature caching so it only rebuilds when the codes change. */
function makeDtcList(container, horiz) {
  container.className = 'dtc-list' + (horiz ? ' horiz' : '');
  let sig = null;
  return function (dtcs) {
    const s = dtcs.map(d => d.code + d.severity).join('|');
    if (s === sig) return;
    sig = s;
    container.innerHTML = '';
    if (!dtcs.length) { container.appendChild(el('div', 'dtc-empty', 'No faults stored')); return; }
    dtcs.forEach(d => {
      const col = sevColor(d.severity);
      const row = el('div', 'dtc-row');
      row.style.borderLeftColor = col;
      const top = el('div', 'r-top');
      top.appendChild(el('span', 'dtc-code', d.code));
      const sev = el('span', 'dtc-sev', d.severity.toUpperCase());
      sev.style.color = col; top.appendChild(sev);
      row.appendChild(top);
      row.appendChild(el('div', 'dtc-desc', d.desc));
      container.appendChild(row);
    });
  };
}

function makeTicker(container) {
  container.className = 'ticker panel';
  let sig = null;
  return function (dtcs) {
    const s = dtcs.map(d => d.code + d.severity).join('|');
    if (s === sig) return;
    sig = s;
    container.innerHTML = '';
    container.appendChild(el('span', 't-count', dtcs.length + ' DTC'));
    if (!dtcs.length) { container.appendChild(el('span', 'dtc-empty', 'No faults stored')); return; }
    dtcs.forEach(d => {
      const item = el('div', 't-item');
      const code = el('span', 't-code', d.code); code.style.color = sevColor(d.severity);
      item.appendChild(code);
      item.appendChild(el('span', null, d.desc));
      container.appendChild(item);
    });
  };
}

function dtcHead(title) {
  const head = el('div', 'dtc-head');
  head.appendChild(el('div', 'dtc-title', title));
  const badge = el('span', 'badge', '0');
  head.appendChild(badge);
  return { head, badge };
}
function setBadge(badge, dtcs) {
  badge.textContent = String(dtcs.length);
  badge.classList.toggle('alert', dtcs.length > 0);
}

/* ------------------------------- builders -------------------------------- */
const BUILDERS = {
  cockpit(stage) {
    const grid = el('div', 'gauge-grid');
    const arcs = GAUGES.map(s => { const g = makeArc(s); grid.appendChild(g.el); return g; });
    const panel = el('div', 'panel');
    const { head, badge } = dtcHead('TROUBLE CODES');
    const list = el('div'); panel.appendChild(head); panel.appendChild(list);
    const updateDtc = makeDtcList(list, false);
    stage.appendChild(grid); stage.appendChild(panel);
    return (d) => {
      arcs.forEach((g, i) => g.set(d[GAUGES[i].key]));
      setBadge(badge, d.dtcs); updateDtc(d.dtcs);
    };
  },

  cluster(stage) {
    const bigRow = el('div', 'big-row');
    const tach = makeArc(spec('rpm'), true), speedo = makeArc(spec('speed'), true);
    bigRow.appendChild(tach.el); bigRow.appendChild(speedo.el);
    const smallRow = el('div', 'small-row');
    const cool = makeArc(spec('coolant')), batt = makeArc(spec('voltage'));
    smallRow.appendChild(cool.el); smallRow.appendChild(batt.el);
    const ticker = el('div'); const updateTicker = makeTicker(ticker);
    stage.appendChild(bigRow); stage.appendChild(smallRow); stage.appendChild(ticker);
    return (d) => {
      tach.set(d.rpm); speedo.set(d.speed); cool.set(d.coolant); batt.set(d.voltage);
      updateTicker(d.dtcs);
    };
  },

  cards(stage) {
    const grid = el('div', 'card-grid');
    const meters = GAUGES.map(s => { const m = makeMeter(s); grid.appendChild(m.el); return m; });
    const panel = el('div', 'panel');
    const { head, badge } = dtcHead('TROUBLE CODES');
    const list = el('div'); panel.appendChild(head); panel.appendChild(list);
    const updateDtc = makeDtcList(list, true);
    stage.appendChild(grid); stage.appendChild(panel);
    return (d) => {
      meters.forEach((m, i) => m.set(d[GAUGES[i].key]));
      setBadge(badge, d.dtcs); updateDtc(d.dtcs);
    };
  },

  retro(stage) {
    const left = el('div', 'panel');
    const cols = el('div', 'retro-cols'); left.appendChild(cols);
    const segs = GAUGES.map(s => { const g = makeSeg(s); cols.appendChild(g.el); return g; });
    const panel = el('div', 'panel');
    const { head, badge } = dtcHead('FAULTS');
    const list = el('div'); panel.appendChild(head); panel.appendChild(list);
    const updateDtc = makeDtcList(list, false);
    stage.appendChild(left); stage.appendChild(panel);
    return (d) => {
      segs.forEach((g, i) => g.set(d[GAUGES[i].key]));
      setBadge(badge, d.dtcs); updateDtc(d.dtcs);
    };
  },

  neon(stage) {
    const row = el('div', 'neon-row');
    const arcs = GAUGES.map(s => { const g = makeArc(s); row.appendChild(g.el); return g; });
    const ticker = el('div'); const updateTicker = makeTicker(ticker);
    stage.appendChild(row); stage.appendChild(ticker);
    return (d) => {
      arcs.forEach((g, i) => g.set(d[GAUGES[i].key]));
      updateTicker(d.dtcs);
    };
  },

  hud(stage) {
    const top = el('div', 'hud-top');
    const tl = el('div', 'hud-rpm-top');
    tl.appendChild(el('span', null, 'RPM'));
    const rpmVal = el('span', 'hud-rpm-val', '--'); tl.appendChild(rpmVal);
    top.appendChild(tl);
    const bar = el('div', 'meter'); const rpmFill = el('span'); bar.appendChild(rpmFill);
    top.appendChild(bar);

    const center = el('div', 'hud-center');
    const speedEl = el('div', 'hud-speed', '--');
    center.appendChild(speedEl); center.appendChild(el('div', 'hud-speed-unit', 'MPH'));

    const bottom = el('div', 'hud-bottom');
    const read = (k) => {
      const box = el('div', 'hud-read'); box.appendChild(el('span', 'hud-k', k));
      const v = el('span', 'hud-v', '--'); box.appendChild(v); bottom.appendChild(box); return v;
    };
    const coolEl = read('COOLANT'), battEl = read('BATTERY'), fltEl = read('FAULTS');

    const holder = el('div', 'hud');
    holder.appendChild(top); holder.appendChild(center); holder.appendChild(bottom);
    stage.appendChild(holder);

    const sRpm = spec('rpm'), sSpeed = spec('speed'), sCool = spec('coolant'), sBatt = spec('voltage');
    return (d) => {
      rpmVal.textContent = fmt(d.rpm, 0);
      rpmFill.style.width = (frac(d.rpm, sRpm) * 100) + '%';
      rpmFill.style.background = colorFor(d.rpm, sRpm);
      speedEl.textContent = fmt(d.speed, 0);
      speedEl.style.color = colorFor(d.speed, sSpeed);
      coolEl.textContent = fmt(d.coolant, 0) + '°';
      coolEl.style.color = colorFor(d.coolant, sCool);
      battEl.textContent = fmt(d.voltage, 1) + 'V';
      battEl.style.color = colorFor(d.voltage, sBatt);
      fltEl.textContent = String(d.dtcs.length);
      fltEl.style.color = d.dtcs.length ? 'var(--red)' : 'var(--green)';
    };
  },
};

/* ------------------------------- runtime --------------------------------- */
let latest = null, updater = null;
const $ = (id) => document.getElementById(id);

function applyChrome(d) {
  $('clock').textContent = d.clock;
  const link = $('link');
  link.textContent = d.connected ? 'BT LINK' : 'NO LINK';
  link.classList.toggle('off', !d.connected);
  $('vehicle').textContent = d.vehicle;
  $('vin').textContent = 'VIN ' + d.vin;
}

function setDesign(name) {
  if (!BUILDERS[name]) name = 'cockpit';
  document.body.className = 'theme-' + name;
  const stage = $('stage');
  stage.className = 'layout-' + name;
  stage.innerHTML = '';
  updater = BUILDERS[name](stage);
  $('designSelect').value = name;
  if (latest) { applyChrome(latest); updater(latest); }
}

function onData(d) {
  latest = d;
  applyChrome(d);
  if (updater) updater(d);
}

// Receive pushed frames from Python.
eel.expose(onData, 'push_data');

window.addEventListener('DOMContentLoaded', () => {
  const sel = $('designSelect');
  Object.keys(DESIGN_LABELS).forEach(name => {
    const o = document.createElement('option');
    o.value = name; o.textContent = DESIGN_LABELS[name];
    sel.appendChild(o);
  });
  sel.addEventListener('change', (e) => setDesign(e.target.value));

  // Ask the backend for the initial design; fall back to cockpit.
  try {
    eel.get_config()((cfg) => setDesign((cfg && cfg.design) || 'cockpit'));
  } catch (_) {
    setDesign('cockpit');
  }
  setDesign('cockpit'); // render immediately; get_config may override

  // Safety net: if no push arrives shortly, poll once.
  setTimeout(() => {
    if (!latest) { try { eel.get_snapshot()(onData); } catch (_) {} }
  }, 800);
});
