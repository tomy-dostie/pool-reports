"""The report page (main design since 2026-11-03): data-dense "advanced stats" look. The previous design (render.py)
is still built at /classique/ as a fallback.

Inspired by stats-hub layouts (stat tiles with pool rank and average, percentile bars, sortable leaderboards,
trend chart, head-to-head). Own colours and wording; no league logos, marks or images.
"""
from .render import FONT_CSS, _embed

TEMPLATE = r"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<meta name="theme-color" content="#0A0D12">
<title>Pool LNH : analyse</title>
<style>
__FONTS__
:root{--bg:#0A0D12;--panel:#131820;--panel2:#1B222C;--line:#262E3A;--text:#EEF2F7;--muted:#8C97A8;--accent:#2BE3A6;--accent2:#7FE0C1;--mid:#55657B;--warm:#FF7A59;--ink:#0A0D12}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:'Barlow',system-ui,sans-serif;-webkit-text-size-adjust:100%}
button{font:inherit;color:inherit;border:0;background:transparent;padding:0;cursor:pointer;text-align:left}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.app{height:100vh;height:100dvh;max-width:520px;margin:0 auto;padding:14px 16px calc(14px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:12px}
.bar-top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.brand{font:800 18px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase}.brand b{color:var(--accent)}
.kick{font:700 12px 'Barlow Condensed',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}
.prog{display:flex;gap:4px}.prog span{flex:1;height:3px;border-radius:2px;background:var(--line)}.prog span.on{background:var(--accent)}
.demo{background:var(--warm);color:var(--ink);font:700 12px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;text-align:center;border-radius:8px;padding:5px 8px}
.card{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain}
.card.in{animation:in .2s ease-out}@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.card.in{animation:none}}
.stack{display:flex;flex-direction:column;gap:12px;padding-bottom:6px}
h1{margin:0;font:800 34px/.95 'Barlow Condensed',sans-serif;text-transform:uppercase;letter-spacing:.01em}
h2{margin:6px 0 0;font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}
.sub{margin:0;font-size:14px;line-height:1.4;color:var(--muted)}
.small{font-size:12px;color:var(--muted)}
.alert{margin:0;font-size:13px;color:var(--warm)}
.num{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-variant-numeric:tabular-nums}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px}
.rows>*{display:block;width:100%;border-top:1px solid var(--line)}.rows>*:first-child{border-top:0}
.date{display:flex;align-items:flex-end;gap:12px}.date .d{font-size:88px;line-height:.8}.date .m{font:800 28px/.9 'Barlow Condensed',sans-serif;text-transform:uppercase;color:var(--accent)}
.lead{padding:14px 16px;display:flex;flex-direction:column;gap:6px;border-left:3px solid var(--accent)}
.lead .t{font:800 26px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}.lead p{margin:0;font-size:15px;line-height:1.4}
.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.tiles.three{grid-template-columns:repeat(3,minmax(0,1fr))}
.tile{padding:12px;display:flex;flex-direction:column;gap:6px;min-width:0}
.tile .l{font:700 11px 'Barlow Condensed',sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.tile .v{font-size:36px;line-height:1}.tile .r{font-size:12px;color:var(--muted)}.tile .r b{color:var(--text);font-weight:600}
.track{position:relative;height:6px;border-radius:3px;background:var(--panel2);overflow:visible}
.fill{position:absolute;left:0;top:0;bottom:0;border-radius:3px}
.tick{position:absolute;top:-3px;width:2px;height:12px;background:var(--text);opacity:.7;border-radius:1px}
.chips{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}.chips::-webkit-scrollbar{display:none}
.chip{flex:none;min-height:40px;padding:0 12px;border-radius:10px;background:var(--panel);border:1px solid var(--line);font-size:15px;font-weight:600}
.chip[aria-pressed=true]{color:var(--ink);border-color:transparent}
.seg{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:3px;gap:3px}
.seg button{min-height:36px;border-radius:7px;text-align:center;font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.seg button[aria-pressed=true]{background:var(--panel2);color:var(--text)}
.lb{display:grid;grid-template-columns:26px minmax(0,1fr) 96px 48px;align-items:center;gap:10px;padding:10px 12px}
.lb .rk{font-size:22px;color:var(--muted)}.lb .nm{font-size:16px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lb .vv{font-size:26px;text-align:right}.dot{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:7px;vertical-align:1px}
.mv-up{color:var(--accent)}.mv-down{color:var(--warm)}
.pl{padding:10px 12px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;align-items:center}
.pl .nm{font-size:15px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pl .pp{grid-row:span 2;display:flex;flex-direction:column;align-items:flex-end}.pl .pp .num{font-size:28px;line-height:1}
.pct{grid-column:1/-1;display:grid;grid-template-columns:86px minmax(0,1fr) 34px;gap:8px;align-items:center;font-size:11px;color:var(--muted)}
.pct b{font:700 14px 'Barlow Condensed',sans-serif;text-align:right}
.hero{display:grid;grid-template-columns:54px minmax(0,1fr) auto;gap:12px;align-items:center;padding:14px}
.ini{width:54px;height:54px;border-radius:12px;color:var(--ink);display:flex;align-items:center;justify-content:center;font:800 24px 'Barlow Condensed',sans-serif}
.hero .nm{font:800 28px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}.hero .tot{font-size:44px;line-height:1;text-align:right}
.link{min-height:40px;font-size:14px;color:var(--accent);font-weight:600}
.btn{min-height:44px;border-radius:12px;background:var(--panel2);border:1px solid var(--line);text-align:center;font:700 15px 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase}
.chart{padding:10px 8px 6px}.chart svg{display:block;width:100%;height:auto}
.duel{display:grid;grid-template-columns:minmax(0,1fr) 92px minmax(0,1fr);gap:8px;align-items:center;padding:10px 12px}
.duel .a{text-align:right}.duel .mid{text-align:center;font:700 11px 'Barlow Condensed',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.duel .num{font-size:26px}.duel .win{color:var(--accent)}
.mvr{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;padding:10px 12px;align-items:baseline}.mvr b{font:700 14px 'Barlow Condensed',sans-serif;text-transform:uppercase;color:var(--muted)}
.award{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 14px}.award .w{font:800 22px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}.award .d{font-weight:600;color:var(--accent);text-align:right}
.since{padding:14px 16px;display:flex;flex-direction:column;gap:10px;border-color:var(--accent);background:linear-gradient(160deg,rgba(43,227,166,.12),var(--panel) 60%)}
.since .row{display:flex;align-items:flex-end;justify-content:space-between;gap:12px}
.since .big{font-size:52px;line-height:.85}.since .rk{font-size:30px;line-height:1;text-align:right}
.since ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:6px;font-size:15px;line-height:1.35}
.since li{display:flex;gap:8px}.since li i{font-style:normal;width:16px;flex:none;text-align:center}
.who{padding:14px 16px;display:flex;flex-direction:column;gap:10px}.who .t{font:800 26px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}
.me-line{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:14px;color:var(--muted)}.me-line b{color:var(--text)}
.tag{display:inline-block;padding:2px 7px;border-radius:6px;font:700 11px 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase;background:var(--panel2);color:var(--muted)}
.tag.good{background:rgba(43,227,166,.16);color:var(--accent)}.tag.bad{background:rgba(255,122,89,.16);color:var(--warm)}
.trade{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;align-items:center;padding:10px 12px}
.trade .num{font-size:26px;text-align:right}.trade>.small{grid-column:1/-1}
.pop{display:inline-block;animation:pop .6s ease-out .5s both}@keyframes pop{0%{transform:scale(.4);opacity:0}70%{transform:scale(1.25)}100%{transform:none;opacity:1}}
@media (prefers-reduced-motion:reduce){.pop{animation:none}}
.nav{display:grid;grid-template-columns:1fr 2fr;gap:8px}
.nav button{height:48px;border-radius:12px;text-align:center;font:700 16px 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase}
#prev{background:var(--panel);border:1px solid var(--line)}#prev:disabled{color:#46536A}#next{background:var(--accent);color:var(--ink);font-weight:800}
</style>
</head>
<body>
<div class="app">
  <div class="bar-top"><span class="brand">Pool <b>LNH</b> · Analyse</span><span class="kick" id="kick"></span></div>
  <div class="prog" id="prog" aria-hidden="true"></div>
  <div class="demo" id="demo" hidden>Aperçu : chiffres inventés</div>
  <main class="card" id="card" tabindex="-1"></main>
  <nav class="nav"><button id="prev">Retour</button><button id="next">Suivant</button></nav>
</div>
<script>
window.DATA = __DATA__;
(function () {
  var D = window.DATA, M = D.meta, P = D.poolers;
  var KICK = ['Aperçu', 'Ma soirée', 'Classement', 'Agents libres', 'Les prix'];
  var KPI = [['total', 'Total'], ['yday', 'Hier'], ['last7', '7 jours'], ['proj', 'Projection']];
  var idx = 0, me = null, known = false, asking = false, detail = null, rival = null, picking = false, raceKey = 'total', sortKey = 'pts';
  var chartMode = 'pts', h2hOpen = false;

  function el(t, c, x) { var n = document.createElement(t); if (c) n.className = c; if (x != null) n.textContent = x; return n; }
  function add(p) { for (var i = 1; i < arguments.length; i++) if (arguments[i]) p.appendChild(arguments[i]); return p; }
  function plural(n, a, b) { return Math.abs(n) <= 1 ? a : b; }
  function ord(n) { return n === 1 ? '1er' : n + 'e'; }
  function byId(id) { return P.filter(function (p) { return p.id === id; })[0]; }
  function maxOf(k) { return Math.max.apply(null, P.map(function (p) { return p.kpi[k].v; }).concat([1])); }
  function tier(p) { return p >= 90 ? 'var(--accent)' : p >= 75 ? 'var(--accent2)' : p >= 50 ? 'var(--mid)' : 'var(--warm)'; }
  function verdict(x) {                                 // a move judged by what each player did afterwards
    if (!x.out || !x.in || x.outAfter == null) return null;
    var d = x.inPts - x.outAfter;
    return el('span', 'tag ' + (d > 0 ? 'good' : d < 0 ? 'bad' : ''), d > 0 ? 'Bon coup +' + d : d < 0 ? 'Regret ' + d : 'Égal');
  }
  function last(name) { return String(name).split(' ').slice(-1)[0]; }
  function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var still = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

  // ---- "since your last visit": the browser keeps a small snapshot of the standings (nothing leaves the phone) ----
  // base = what you saw before the latest results; it stays the same all day so the panel does not vanish on reload.
  function snapshot() {
    var s = { day: M.lastDay, label: M.lastDayLabel, t: {}, r: {}, pl: {} };
    P.forEach(function (p) { s.t[p.id] = p.total; s.r[p.id] = p.rank; s.pl[p.id] = {}; p.team.concat(p.former).forEach(function (x) { s.pl[p.id][x.player] = (s.pl[p.id][x.player] || 0) + x.pts; }); });
    return s;
  }
  var base = null, animate = false, mem = M.demo ? null : (load('pool.seen') || {});
  if (mem && !(mem.cur && mem.cur.day > M.lastDay)) {               // (an older cached page never overwrites newer memory)
    if (!mem.cur || mem.cur.day !== M.lastDay) mem = { base: mem.cur || null, cur: snapshot(), shown: null };
    base = mem.base;
    animate = !!base && mem.shown !== M.lastDay && !still;           // the count-up plays once per new day, not on every visit
    mem.shown = M.lastDay; save('pool.seen', mem);
  }

  function countUp(node, to, prefix) {
    if (!animate || !to) { node.textContent = prefix + to; return; }
    var t0 = null;
    node.textContent = prefix + 0;
    function step(t) { if (t0 == null) t0 = t; var k = Math.min(1, (t - t0) / 1100); node.textContent = prefix + Math.round(to * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(step); }
    setTimeout(function () { requestAnimationFrame(step); }, 250);
  }
  function sincePanel(p) {
    if (!base || base.t[p.id] == null) return null;
    var was = base.t[p.id], wasRk = base.r[p.id], gained = p.total - was, dRk = wasRk - p.rank;
    var box = el('div', 'panel since'), head = el('div', 'row');
    var big = el('div', 'big num'), rk = el('div', 'rk num');
    countUp(big, gained, '+');
    rk.textContent = ord(p.rank);
    if (dRk) { var arrow = el('span', (dRk > 0 ? 'mv-up' : 'mv-down') + (animate ? ' pop' : ''), dRk > 0 ? ' ▲' + dRk : ' ▼' + (-dRk)); rk.appendChild(arrow); }
    add(head, add(el('div'), el('div', 'kick', 'Depuis ta dernière visite'), big, el('div', 'small', plural(gained, 'point', 'points') + ' · total ' + p.total)), add(el('div'), rk, el('div', 'small', dRk ? 'était ' + ord(wasRk) : 'même rang')));
    add(box, head);
    var ul = el('ul');
    function li(icon, text, cls) { var x = add(el('li', cls || null), el('i', null, icon), el('span', null, text)); ul.appendChild(x); }
    var passed = [], passedBy = [];
    P.forEach(function (q) {
      if (q.id === p.id || base.t[q.id] == null) return;
      if (was < base.t[q.id] && p.total > q.total) passed.push(q.name);
      if (was > base.t[q.id] && p.total < q.total) passedBy.push(q.name);
    });
    if (p.rank === 1 && wasRk > 1) li('👑', 'Tu prends le 1er rang.', 'mv-up');
    if (passed.length) li('▲', 'Tu as dépassé ' + passed.join(', ') + '.', 'mv-up');
    if (passedBy.length) li('▼', passedBy.join(', ') + ' ' + (passedBy.length > 1 ? 't’ont' : 't’a') + ' dépassé.', 'mv-down');
    var leaderWas = Math.max.apply(null, P.map(function (q) { return base.t[q.id] || 0; })), gapWas = leaderWas - was;
    if (p.rank > 1 && gapWas !== p.gap) li('↔', 'Écart avec le 1er : ' + gapWas + ' → ' + p.gap + (p.gap < gapWas ? '. Ça se rapproche.' : '.'));
    var mine = base.pl[p.id] || {}, deltas = [];
    p.team.concat(p.former).forEach(function (x) { var d = x.pts - (mine[x.player] || 0); if (d > 0) deltas.push([d, x.player]); });
    deltas.sort(function (a, b) { return b[0] - a[0]; });
    if (deltas.length) li('★', deltas.slice(0, 3).map(function (d) { return last(d[1]) + ' +' + d[0]; }).join(' · '));
    else if (gained === 0) li('·', 'Aucun point depuis. On se reprend ce soir.');
    if (ul.childNodes.length) add(box, ul);
    add(box, el('div', 'small', 'Résultats du ' + base.label + ' au ' + M.lastDayLabel + '.'));
    animate = false;                                                  // coming back to this card later: no replay
    return box;
  }
  function setMe(id) { me = id; asking = false; known = true; try { localStorage.setItem('pool.me', id); } catch (e) {} }
  function whoPanel() {
    return add(el('div', 'panel who'), el('div', 't', 'T’es qui ?'),
      el('p', 'sub', 'Choisis ton nom une fois : la page s’ouvrira sur ton équipe et te dira ce qui a changé depuis ta dernière visite. Rien n’est envoyé, c’est gardé sur ton téléphone.'),
      chips(asking && known ? me : null, setMe));
  }

  function track(frac, color, tickFrac) {
    var t = el('div', 'track'), f = el('div', 'fill');
    f.style.width = Math.max(2, Math.min(100, frac * 100)) + '%'; f.style.background = color; t.appendChild(f);
    if (tickFrac != null) { var k = el('div', 'tick'); k.style.left = 'calc(' + Math.min(100, tickFrac * 100) + '% - 1px)'; k.title = 'Moyenne du pool'; t.appendChild(k); }
    return t;
  }
  function tile(label, k, p) {
    var mx = maxOf(k), x = p.kpi[k];
    var r = el('div', 'r'); add(r, el('b', null, ord(x.rank)), document.createTextNode(' sur ' + P.length + ' · moy. ' + String(x.avg).replace('.', ',')));
    return add(el('div', 'panel tile'), el('div', 'l', label), el('div', 'v num', (k === 'yday' || k === 'last7' ? '+' : '') + x.v), track(x.v / mx, p.color, x.avg / mx), r);
  }
  function pctRow(pct, ppg) {
    var r = el('div', 'pct');
    if (pct == null) { add(r, el('span', null, 'Rang LNH'), el('span', null, 'moins de 5 matchs'), el('b')); return r; }
    var b = el('b', null, ord(pct)); b.style.color = tier(pct);
    add(r, el('span', null, ppg == null ? 'Rang LNH' : String(ppg).replace('.', ',') + ' pt/match'), track(pct / 100, tier(pct)), b);
    r.title = 'Centile parmi les joueurs de la LNH à la même position (points par match, saison)';
    return r;
  }
  function seg(opts, cur, pick) {
    var s = el('div', 'seg');
    opts.forEach(function (o) { var b = el('button', null, o[1]); b.setAttribute('aria-pressed', o[0] === cur ? 'true' : 'false'); b.onclick = function () { pick(o[0]); show(true); }; s.appendChild(b); });
    return s;
  }
  function chips(cur, pick, skip) {
    var c = el('div', 'chips');
    P.forEach(function (p) {
      if (p.id === skip) return;
      var b = el('button', 'chip', p.name), on = p.id === cur;
      b.setAttribute('aria-pressed', on ? 'true' : 'false'); if (on) b.style.background = p.color;
      b.onclick = function () { pick(p.id); show(true); }; c.appendChild(b);
    });
    return c;
  }
  function chart(ids) {
    var ns = 'http://www.w3.org/2000/svg', W = 340, H = 150, L = 30, R = 8, T = 8, B = 20, n = D.trendDays.length;
    var svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('role', 'img');
    var byRank = chartMode === 'rank' && P[0].ranks, key = byRank ? 'ranks' : 'trend', N = P.length;
    var top = Math.max.apply(null, P.map(function (p) { return p.trend.length ? p.trend[p.trend.length - 1] : 0; }).concat([1]));
    var X = function (i) { return L + (n > 1 ? i / (n - 1) : 0) * (W - L - R); };
    var Y = byRank ? function (v) { return T + (N > 1 ? (v - 1) / (N - 1) : 0) * (H - T - B); } : function (v) { return T + (1 - v / top) * (H - T - B); };
    function line(x1, y1, x2, y2, c, w, o) { var l = document.createElementNS(ns, 'line'); l.setAttribute('x1', x1); l.setAttribute('y1', y1); l.setAttribute('x2', x2); l.setAttribute('y2', y2); l.setAttribute('stroke', c); l.setAttribute('stroke-width', w); if (o) l.setAttribute('opacity', o); svg.appendChild(l); }
    function text(x, y, s, anchor, c) { var t = document.createElementNS(ns, 'text'); t.setAttribute('x', x); t.setAttribute('y', y); t.setAttribute('fill', c || '#8C97A8'); t.setAttribute('font-size', '10'); t.setAttribute('font-family', 'Barlow, sans-serif'); t.setAttribute('text-anchor', anchor || 'start'); t.textContent = s; svg.appendChild(t); }
    if (byRank) [1, Math.ceil(N / 2), N].forEach(function (v) { line(L, Y(v), W - R, Y(v), '#262E3A', 1); text(L - 6, Y(v) + 3, ord(v), 'end'); });
    else [0, .5, 1].forEach(function (f) { var v = Math.round(top * f); line(L, Y(v), W - R, Y(v), '#262E3A', 1); text(L - 6, Y(v) + 3, String(v), 'end'); });
    if (n) { text(X(0), H - 5, D.trendDays[0]); text(X(n - 1), H - 5, D.trendDays[n - 1], 'end'); }
    var order = P.filter(function (p) { return ids.indexOf(p.id) < 0; }).concat(ids.map(byId));
    order.forEach(function (p) {
      if (p[key].length < 2) return;
      var on = ids.indexOf(p.id) >= 0, path = document.createElementNS(ns, 'path');
      path.setAttribute('d', p[key].map(function (v, i) { return (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); }).join(' '));
      path.setAttribute('fill', 'none'); path.setAttribute('stroke', on ? p.color : '#55657B'); path.setAttribute('stroke-width', on ? 2.5 : 1);
      path.setAttribute('opacity', on ? 1 : .45); path.setAttribute('stroke-linejoin', 'round'); svg.appendChild(path);
    });
    svg.setAttribute('aria-label', (byRank ? 'Rang au classement, soir après soir' : 'Points cumulés de la saison') + ids.map(function (id) { var p = byId(id); return ', ' + p.name + ' ' + (byRank ? ord(p.rank) : p.total); }).join(''));
    return add(el('div', 'panel chart'), svg);
  }

  function chartToggle() { return P[0].ranks ? seg([['pts', 'Points'], ['rank', 'Rang']], chartMode, function (k) { chartMode = k; }) : null; }
  function wlt(r) { return r[0] + '-' + r[1] + (r[2] ? '-' + r[2] : ''); }
  // "Nuits gagnées": each night, more pool points than another pooler = a night won against them
  function nights(p) {
    if (!p.h2h) return null;
    var box = el('div', 'stack'), opp = Object.keys(p.h2h).map(function (id) { return { q: byId(id), r: p.h2h[id], s: p.h2hStreak[id] }; }).filter(function (o) { return o.q; });
    if (!opp.length) return null;
    var tot = opp.reduce(function (a, o) { return [a[0] + o.r[0], a[1] + o.r[1], a[2] + o.r[2]]; }, [0, 0, 0]);
    opp.sort(function (a, b) { return (b.r[0] - b.r[1]) - (a.r[0] - a.r[1]) || (a.q.name < b.q.name ? -1 : 1); });
    var vic = opp[0], bete = opp[opp.length - 1];
    var t = el('div', 'tiles');
    function who(label, o, good) {
      var v = el('div', 'v num', o.q.name); v.style.fontSize = '28px';
      return add(el('div', 'panel tile'), el('div', 'l', label), v, el('div', 'r ' + (good ? 'mv-up' : 'mv-down'), wlt(o.r) + ' contre lui'));
    }
    if (vic.r[0] > vic.r[1]) t.appendChild(who('Ta victime', vic, true));
    if (bete !== vic && bete.r[1] > bete.r[0]) t.appendChild(who('Ta bête noire', bete, false));
    add(box, el('h2', null, 'Nuits gagnées · ' + wlt(tot)));
    if (t.childNodes.length) add(box, t);
    var tog = el('button', 'link', h2hOpen ? 'Cacher les duels ‹' : 'Voir les ' + opp.length + ' duels ›');
    tog.onclick = function () { h2hOpen = !h2hOpen; show(true); };
    add(box, tog);
    if (h2hOpen) {
      var l = el('div', 'panel rows');
      opp.forEach(function (o) {
        var st = Math.abs(o.s) >= 2 ? el('div', 'small ' + (o.s > 0 ? 'mv-up' : 'mv-down'), (o.s > 0 ? 'Gagne ' : 'Perd ') + Math.abs(o.s) + ' soirs de suite') : el('div', 'small', o.s > 0 ? 'A gagné hier' : o.s < 0 ? 'A perdu hier' : 'Égalité hier');
        var r = add(el('button', 'pl'), add(el('span'), el('div', 'nm', 'Contre ' + o.q.name), st), add(el('span', 'pp'), el('span', 'num', wlt(o.r))));
        r.onclick = function () { rival = o.q.id; picking = false; show(); };
        l.appendChild(r);
      });
      add(box, l, el('p', 'small', 'Une nuit gagnée = plus de points que l’autre ce soir-là. Touche un duel pour comparer.'));
    }
    return box;
  }

  function dec(x) { return String(x).replace('.', ','); }
  // "À ce rythme": recent form projected forward (the report never gives a date more than 60 days away)
  function pacePanel(p, mine) {
    var x = p.pace; if (!x) return null;
    var ul = el('ul'); ul.style.cssText = 'margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:6px;font-size:15px;line-height:1.35';
    function li(text, cls) { ul.appendChild(el('li', cls || null, text)); }
    var c = x.chase;
    if (c && c.kind === 'catch') li((mine ? 'Tu passes ' : p.name + ' passe ') + c.name + ' vers le ' + c.date + ' (+' + dec(c.gain) + ' pt par jour sur ' + c.name + ').', 'mv-up');
    if (c && c.kind === 'threat') li(c.name + (mine ? ' te rattrape' : ' rattrape ' + p.name) + ' vers le ' + c.date + ' s’il garde ce rythme (+' + dec(c.gain) + ' pt par jour).', 'mv-down');
    if (!c && p.rank > 1) li((mine ? 'Tu ne rattrapes' : p.name + ' ne rattrape') + ' personne à ce rythme. Il faut accélérer.');
    if (!c && p.rank === 1) li(mine ? 'Personne ne te rattrape à ce rythme.' : 'Personne ne rattrape ' + p.name + ' à ce rythme.', 'mv-up');
    if (x.milestone) li('Cap des ' + x.milestone.value + ' pts vers le ' + x.milestone.date + (/\.$/.test(x.milestone.date) ? '' : '.'));
    return add(el('div', 'panel lead'), el('div', 'kick', 'À ce rythme · ' + dec(x.rate) + ' pts par jour (14 j)'), ul);
  }
  // "Qui porte l'équipe": each player's share of the pooler's points (players gone included)
  function shares(p) {
    var m = {}; p.team.concat(p.former).forEach(function (r) { m[r.player] = (m[r.player] || 0) + r.pts; });
    return Object.keys(m).map(function (k) { return { player: k, pts: m[k], pct: p.total ? Math.round(100 * m[k] / p.total) : 0 }; })
      .filter(function (x) { return x.pts > 0; }).sort(function (a, b) { return b.pts - a.pts; });
  }
  function carry(p) {
    var sh = shares(p); if (!sh.length || !p.total) return null;
    var top = sh.slice(0, 4), rest = p.total - top.reduce(function (a, x) { return a + x.pts; }, 0);
    var bar = el('div'); bar.style.cssText = 'display:flex;height:14px;border-radius:5px;overflow:hidden;background:var(--panel2);gap:2px';
    var leg = el('div'); leg.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px 12px;font-size:13px';
    top.forEach(function (x, i) {
      var seg = el('div'); seg.style.flex = String(x.pts); seg.style.background = p.color; seg.style.opacity = String(1 - i * .2); bar.appendChild(seg);
      var k = el('span'); var d = el('span', 'dot'); d.style.background = p.color; d.style.opacity = String(1 - i * .2);
      add(leg, add(k, d, document.createTextNode(last(x.player) + ' '), el('b', null, x.pct + ' %')));
    });
    if (rest > 0) { var o = el('div'); o.style.flex = String(rest); o.style.background = 'var(--mid)'; o.style.opacity = '.5'; bar.appendChild(o); add(leg, el('span', 'small', 'Autres ' + Math.round(100 * rest / p.total) + ' %')); }
    var lead = top[0], say = lead.pct >= 20 ? 'Sans ' + last(lead.player) + ', ça irait mal.' : lead.pct <= 12 ? 'Une équipe balancée : personne ne porte tout.' : last(lead.player) + ' mène la charge.';
    return add(el('div', 'stack'), el('h2', null, 'Qui porte l’équipe'), add(el('div', 'panel lead'), bar, leg, el('p', 'small', say)));
  }
  // tonight: the game with the most pool players, and how many players each pooler has in action
  function tonightPanel() {
    var c = D.tonightClash, load = P.map(function (p) { return { p: p, n: p.tonight.length }; }).filter(function (x) { return x.n; }).sort(function (a, b) { return b.n - a.n || (a.p.name < b.p.name ? -1 : 1); });
    if (!c && !load.length) return null;
    var box = el('div', 'panel lead');
    add(box, el('div', 'kick', 'Ce soir · ' + M.gamesTonight + ' ' + plural(M.gamesTonight, 'match', 'matchs')));
    if (c) {
      add(box, el('div', 't', 'Le choc : ' + c.game), el('p', 'small', c.time + ' · ' + c.players + ' joueurs du pool : ' + c.poolers.map(function (x) { return x.name + ' ' + x.n; }).join(', ')));
    }
    if (load.length) {
      var w = el('div'); w.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px';
      load.forEach(function (x) { var t = el('span', 'tag', x.p.name + ' ' + x.n); if (x.p.id === me && !asking) { t.style.background = x.p.color; t.style.color = 'var(--ink)'; } w.appendChild(t); });
      add(box, el('div', 'small', 'Joueurs en action'), w);
    }
    return box;
  }

  // ---- cards ----
  function cover() {
    var s = el('div', 'stack');
    add(s, add(el('div', 'date'), el('div', 'd num', String(M.dayNumber)), add(el('div'), el('div', 'm', M.month), el('div', 'small', M.weekday + ' · résultats du ' + M.lastDayLabel))));
    if (asking) add(s, whoPanel());
    else {
      var p = byId(me), ch = el('button', 'link', 'Changer');
      ch.onclick = function () { asking = true; show(true); };
      add(s, add(el('div', 'me-line'), add(el('span'), document.createTextNode('Toi : '), el('b', null, p.name + ' · ' + ord(p.rank)), document.createTextNode(p.rank === 1 ? ' · au sommet' : ' · à ' + p.gap + ' du 1er')), ch));
      add(s, sincePanel(p));
    }
    add(s, add(el('div', 'panel lead'), el('div', 't', D.headline.title), el('p', null, D.headline.text)));
    var t = el('div', 'tiles three');
    D.tiles.forEach(function (x) { add(t, add(el('div', 'panel tile'), el('div', 'l', x.label), el('div', 'v num', x.value))); });
    add(s, t, tonightPanel(), el('h2', null, 'Le podium'));
    var lb = el('div', 'panel rows');
    P.slice(0, 3).forEach(function (p) { lb.appendChild(lbRow(p, 'total', maxOf('total'))); });
    add(s, lb);
    var rm = D.recentMoves || [];
    if (rm.length) { var names = []; rm.forEach(function (m) { if (names.indexOf(m.name) < 0) names.push(m.name); }); var b = el('button', 'link', 'Mouvements récents : ' + names.join(', ') + ' ›'); b.onclick = function () { open(rm[0].id); }; add(s, b); }
    if (M.missingGames) add(s, el('p', 'alert', M.missingGames + ' match(s) non chargé(s) : points possiblement incomplets.'));
    if (M.unresolved && M.unresolved.length) add(s, el('p', 'alert', 'Joueur non reconnu, points possiblement incomplets : ' + M.unresolved.join(', ') + '.'));
    add(s, el('p', 'small', 'Mis à jour le ' + M.updated + '.'));
    return s;
  }
  function mine() {
    var s = el('div', 'stack'), p = byId(me);
    add(s, el('h1', null, 'Ma soirée'), chips(me, setMe));
    var t = el('div', 'tiles'); KPI.forEach(function (k) { t.appendChild(tile(k[1], k[0], p)); }); add(s, t, pacePanel(p, true));
    add(s, el('h2', null, 'Hier soir · +' + p.yday));
    var l = el('div', 'panel rows');
    if (p.scorers.length) p.scorers.forEach(function (x) { add(l, add(el('div', 'pl'), add(el('span'), el('div', 'nm', x.player), el('div', 'small', x.line)), add(el('span', 'pp'), el('span', 'num', String(x.pts))))); });
    else add(l, add(el('div', 'pl'), el('span', 'small', 'Personne n’a pointé. Soirée difficile.')));
    add(s, l, el('h2', null, 'Ce soir · ' + (p.tonight.length ? p.tonight.length + ' ' + plural(p.tonight.length, 'joueur', 'joueurs') : 'aucun joueur')));
    if (p.tonight.length) {
      var more = 1 + P.filter(function (q) { return q.tonight.length > p.tonight.length; }).length;
      add(s, el('p', 'small', more === 1 ? 'Le plus gros alignement en action ce soir. À toi de jouer.' : ord(more) + ' plus gros alignement en action ce soir.'));
    }
    if (D.tonightClash && D.tonightClash.poolers.some(function (x) { return x.id === p.id; })) {
      var c = D.tonightClash, foes = c.poolers.filter(function (x) { return x.id !== p.id; }).map(function (x) { return x.name; });
      if (foes.length) add(s, el('p', 'small', 'Le choc de la soirée (' + c.game + ') : tu y affrontes ' + foes.join(', ') + '.'));
    }
    if (p.tonight.length) { var g = el('div', 'panel rows'); p.tonight.forEach(function (x) { add(g, add(el('div', 'pl'), add(el('span'), el('div', 'nm', x.player), el('div', 'small', x.game)), add(el('span', 'pp'), el('span', 'num', x.time)))); }); add(s, g); }
    var b = el('button', 'btn', 'Voir mon alignement'); b.onclick = function () { open(me); }; add(s, b);
    return s;
  }
  function lbRow(p, k, mx) {
    var r = el('button', 'lb'), v = p.kpi[k].v;
    var mv = p.move > 0 ? el('span', 'mv-up', ' ▲' + p.move) : p.move < 0 ? el('span', 'mv-down', ' ▼' + Math.abs(p.move)) : null;
    var nm = add(el('div'), add(el('div', 'nm'), el('span', 'dot'), document.createTextNode(p.name), k === 'total' ? mv : null), el('div', 'small', k === 'total' ? (p.rank === 1 ? 'Au sommet' : 'à ' + p.gap + ' du 1er') : p.total + ' pts au total'));
    nm.querySelector('.dot').style.background = p.color;
    add(r, el('span', 'rk num', String(p.kpi[k].rank)), nm, track(v / mx, p.color, p.kpi[k].avg / mx), el('span', 'vv num', (k === 'yday' || k === 'last7' ? '+' : '') + v));
    r.setAttribute('aria-label', p.name + ', ' + ord(p.kpi[k].rank) + ', ' + v + '. Voir l’alignement');
    r.onclick = function () { open(p.id); };
    return r;
  }
  function race() {
    if (detail) return rival ? duel() : profile();
    var s = el('div', 'stack');
    add(s, el('h1', null, 'Classement'), seg(KPI, raceKey, function (k) { raceKey = k; }));
    var mx = maxOf(raceKey), rows = P.slice().sort(function (a, b) { return a.kpi[raceKey].rank - b.kpi[raceKey].rank || (a.name < b.name ? -1 : 1); });
    var lb = el('div', 'panel rows'); rows.forEach(function (p) { lb.appendChild(lbRow(p, raceKey, mx)); });
    add(s, lb, el('p', 'small', 'Touche un pooler pour son alignement. Trait blanc : moyenne du pool. Projection sur ' + M.seasonGames + ' matchs.'));
    return s;
  }
  function profile() {
    var s = el('div', 'stack'), p = byId(detail);
    var back = el('button', 'link', '‹ Classement'); back.onclick = function () { detail = null; picking = false; show(); };
    var ini = el('div', 'ini', p.initials); ini.style.background = p.color;
    add(s, back, add(el('div', 'panel hero'), ini, add(el('div'), el('div', 'nm', p.name), el('div', 'small', ord(p.rank) + ' sur ' + P.length + (p.rank === 1 ? ' · au sommet' : ' · à ' + p.gap + ' du 1er'))), el('div', 'tot num', String(p.total))));
    var t = el('div', 'tiles'); KPI.forEach(function (k) { t.appendChild(tile(k[1], k[0], p)); }); add(s, t, pacePanel(p, p.id === me && known));
    add(s, el('h2', null, 'Progression de la saison'), chartToggle(), chart([p.id]));
    add(s, nights(p), carry(p));
    var duelBtn = el('button', 'btn', picking ? 'Choisis un adversaire' : 'Duel contre un pooler'); duelBtn.onclick = function () { picking = !picking; show(true); };
    add(s, duelBtn);
    if (picking) add(s, chips(null, function (id) { rival = id; picking = false; }, p.id));
    add(s, el('h2', null, 'Actifs'), seg([['pts', 'Points'], ['ppg', 'Pts/match'], ['last7', '7 jours']], sortKey, function (k) { sortKey = k; }));
    var rows = p.team.slice().sort(function (a, b) { return (b[sortKey] || 0) - (a[sortKey] || 0) || b.pts - a.pts; });
    var l = el('div', 'panel rows');
    rows.forEach(function (r) {
      var right = add(el('span', 'pp'), el('span', 'num', String(r.pts)), el('span', 'small', r.last7 > 0 ? '+' + r.last7 + ' en 7 j' : ' '));
      if (r.last7 > 0) right.lastChild.style.color = p.color;
      add(l, add(el('div', 'pl'), el('div', 'nm', r.player), right, el('div', 'small', r.team + ' · ' + r.pos + ' · ' + r.gp + ' PJ · ' + r.g + ' B · ' + r.a + ' A'), pctRow(r.pct, r.ppg)));
    });
    add(s, l, el('p', 'small', 'Barre : rang LNH en points par match cette saison, parmi les joueurs à la même position (100 = le meilleur). Points du pool : seulement pendant qu’il appartient à ' + p.name + '.'));
    if (p.former.length) {
      var f = el('div', 'panel rows');
      p.former.forEach(function (r) {
        var after = r.after ? el('div', 'small mv-down', '+' + r.after + ' ' + plural(r.after, 'pt', 'pts') + ' depuis son départ' + (r.after >= 3 ? ' 😬' : '')) : null;
        add(f, add(el('div', 'pl'), el('div', 'nm', r.player), add(el('span', 'pp'), el('span', 'num', String(r.pts)), el('span', 'small', plural(r.pts, 'gardé', 'gardés'))), el('div', 'small', r.team + ' · ' + r.gp + ' PJ · jusqu’au ' + r.until), after));
      });
      add(s, el('h2', null, 'Partis'), f);
    }
    var m = el('div', 'panel rows');
    if (p.moves.length) p.moves.forEach(function (x) {
      var what = x.out && x.in ? x.out + ' ➜ ' + x.in : (x.out ? x.out + ' retiré' : x.in + ' ajouté'), det = [];
      if (x.in) det.push(last(x.in) + ' ' + x.inPts + ' ' + plural(x.inPts, 'pt', 'pts') + ' ici');
      if (x.out && x.outAfter != null) det.push(last(x.out) + ' ' + x.outAfter + ' ailleurs');
      if (x.out) det.push(x.outPts + ' ' + plural(x.outPts, 'pt gardé', 'pts gardés'));
      add(m, add(el('div', 'mvr'), el('b', null, x.dateLabel), add(el('span'), add(el('div', 'nm'), document.createTextNode(what + ' '), verdict(x)), el('div', 'small', det.join(' · ')))));
    });
    else add(m, add(el('div', 'mvr'), el('b', null, '–'), el('span', 'small', 'Aucun mouvement cette saison.')));
    add(s, el('h2', null, 'Mouvements'), m);
    return s;
  }
  function duel() {
    var s = el('div', 'stack'), a = byId(detail), b = byId(rival);
    var back = el('button', 'link', '‹ ' + a.name); back.onclick = function () { rival = null; show(); };
    var head = el('div', 'panel duel');
    function side(p, cls) { var n = el('div', 'nm ' + cls); var d = el('span', 'dot'); d.style.background = p.color; add(n, d, document.createTextNode(p.name)); n.style.fontWeight = 700; return n; }
    add(head, side(a, 'a'), el('div', 'mid', 'Duel'), side(b, ''));
    add(s, back, el('h1', null, 'Duel'), head);
    var rows = el('div', 'panel rows');
    function cmp(label, va, vb, plus) {
      var x = el('span', 'num' + (va > vb ? ' win' : '')), y = el('span', 'num' + (vb > va ? ' win' : ''));
      x.textContent = (plus ? '+' : '') + va; y.textContent = (plus ? '+' : '') + vb;
      add(rows, add(el('div', 'duel'), add(el('div', 'a'), x), el('div', 'mid', label), add(el('div'), y)));
    }
    KPI.forEach(function (k) { cmp(k[1], a.kpi[k[0]].v, b.kpi[k[0]].v, k[0] === 'yday' || k[0] === 'last7'); });
    if (a.h2h && a.h2h[b.id]) cmp('Nuits gagnées', a.h2h[b.id][0], a.h2h[b.id][1]);
    function by(p, pos) { return p.team.concat(p.former).filter(function (r) { return r.pos === pos; }).reduce(function (n, r) { return n + r.pts; }, 0); }
    cmp('Attaquants', by(a, 'Att'), by(b, 'Att')); cmp('Défenseurs', by(a, 'Déf'), by(b, 'Déf'));
    function best(p) { return p.team.length ? p.team[0].player.split(' ').slice(-1)[0] + ' (' + p.team[0].pts + ')' : '–'; }
    add(rows, add(el('div', 'duel'), el('div', 'a small', best(a)), el('div', 'mid', 'Meilleur'), el('div', 'small', best(b))));
    var st = a.h2hStreak && a.h2hStreak[b.id];
    if (st && Math.abs(st) >= 2) add(rows, add(el('div', 'duel'), el('div', 'a small', ''), el('div', 'mid', 'Série'), el('div', 'small', (st > 0 ? a.name : b.name) + ' gagne ' + Math.abs(st) + ' soirs de suite')));
    add(s, rows, el('h2', null, 'Progression'), chartToggle(), chart([a.id, b.id]));
    return s;
  }
  function deals() {
    var s = el('div', 'stack');
    add(s, el('h1', null, 'Agents libres'), el('p', 'sub', 'Les meilleurs joueurs de la semaine que personne n’a.'));
    var l = el('div', 'panel rows');
    if (D.deals.length) D.deals.forEach(function (d) { add(l, add(el('div', 'pl'), el('div', 'nm', d.player), add(el('span', 'pp'), el('span', 'num', '+' + d.pts), el('span', 'small', '7 derniers jours')), el('div', 'small', d.meta), pctRow(d.pct, null))); });
    else add(l, add(el('div', 'pl'), el('span', 'small', 'Pas encore assez de matchs.')));
    add(s, l);
    if (D.cold.length) {
      var c = el('div', 'panel rows');
      D.cold.forEach(function (x) { add(c, add(el('div', 'pl'), el('div', 'nm', x.player), add(el('span', 'pp'), el('span', 'small', x.line)), el('div', 'small', x.owner))); });
      add(s, el('h2', null, 'Sur la glace mince'), c);
    }
    return s;
  }
  function prizes() {
    var s = el('div', 'stack');
    add(s, el('h1', null, 'Les prix du jour'));
    if (D.awards.length) { var l = el('div', 'panel rows'); D.awards.forEach(function (a) { add(l, add(el('div', 'award'), add(el('span'), el('div', 'small', a.label), el('div', 'w', a.winner)), el('span', 'd', a.detail))); }); add(s, l); }
    if (D.chatter.length) { var c = el('div', 'panel rows'); D.chatter.forEach(function (x) { add(c, add(el('div', 'pl'), add(el('div'), el('div', 'small ' + (x.good ? 'mv-up' : 'mv-down'), x.tag), el('div', null, x.text)))); }); add(s, el('h2', null, 'La jasette'), c); }
    var R = D.records || [];
    if (R.length) {
      var rl = el('div', 'panel rows');
      R.forEach(function (x) {
        var r = el('button', 'trade'), lab = add(el('div', 'small'), document.createTextNode(x.label + ' '), x.new ? el('span', 'tag good', 'Nouveau record') : null);
        var txt = el('div', null, x.text); txt.style.fontWeight = 600; txt.style.lineHeight = 1.3;
        add(r, add(el('div'), lab, txt), el('span', 'num', String(x.value)));
        r.onclick = function () { open(x.who); };
        rl.appendChild(r);
      });
      add(s, el('h2', null, 'Records de la saison'), rl);
    }
    var dep = P.map(function (p) { var x = shares(p)[0]; return x && { p: p, x: x }; }).filter(Boolean).sort(function (a, b) { return b.x.pct - a.x.pct; })[0];
    if (dep) {
      var dr = el('button', 'trade'); dr.onclick = function () { open(dep.p.id); };
      add(dr, add(el('div'), el('div', 'small', 'Le plus dépendant'), el('div', null, dep.p.name + ' : ' + last(dep.x.player) + ' fait ' + dep.x.pct + ' % de ses points')), el('span', 'num', dep.x.pct + ' %'));
      dr.firstChild.lastChild.style.fontWeight = 600;
      add(s, add(el('div', 'panel rows'), dr));
    }
    var T = D.trades || [];
    if (T.length) {
      // best moves first, then the worst regrets (each move shown once)
      var good = T.filter(function (t) { return t.diff > 0; }).slice(0, 2), bad = T.filter(function (t) { return t.diff < 0; }).slice(-2).reverse();
      var list = good.concat(bad);
      if (!list.length) list = T.slice(0, 2);
      var tl = el('div', 'panel rows');
      list.forEach(function (t) {
        var r = el('button', 'trade'), n = el('span', 'num ' + (t.diff > 0 ? 'mv-up' : t.diff < 0 ? 'mv-down' : ''), (t.diff > 0 ? '+' : '') + t.diff);
        var tag = el('span', 'tag ' + (t.diff > 0 ? 'good' : t.diff < 0 ? 'bad' : ''), t.tag);
        var who = add(el('div'), add(el('div', 'small'), tag, document.createTextNode(' ' + t.name + ' · ' + t.dateLabel)), el('div', 'nm', last(t.out) + ' ➜ ' + last(t.in)));
        add(r, who, n, el('div', 'small', last(t.in) + ' ' + t.inPts + ' ' + plural(t.inPts, 'pt', 'pts') + ' depuis · ' + last(t.out) + ' ' + t.outAfter + ' ailleurs'));
        r.onclick = function () { open(t.id); };
        tl.appendChild(r);
      });
      add(s, el('h2', null, 'Bons coups et regrets'), tl);
    }
    var b = el('button', 'btn', 'Copier le résumé');
    b.onclick = function () {
      function done(ok) { b.textContent = ok ? 'Copié' : 'Copie impossible'; }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(D.summary).then(function () { done(true); }, function () { done(false); }); else done(false);
    };
    add(s, b);
    return s;
  }

  var BUILD = [cover, mine, race, deals, prizes], RACE = 2;
  function open(id) { detail = id; rival = null; picking = false; idx = RACE; show(); }
  function show(keep) {
    var card = document.getElementById('card'), sc = keep ? card.scrollTop : 0;
    card.className = 'card' + (keep ? '' : ' in'); card.textContent = ''; card.appendChild(BUILD[idx]()); card.scrollTop = sc;
    document.getElementById('kick').textContent = KICK[idx];
    var pr = document.getElementById('prog'); pr.textContent = ''; BUILD.forEach(function (_, i) { pr.appendChild(el('span', i <= idx ? 'on' : '')); });
    document.getElementById('prev').disabled = idx === 0 && !detail;
    document.getElementById('next').textContent = idx === BUILD.length - 1 ? 'Recommencer' : 'Suivant';
  }
  function go(step) {
    if (detail && step < 0) { if (rival) rival = null; else { detail = null; picking = false; } return show(); }
    detail = null; rival = null; picking = false;
    var n = idx + step; if (n >= BUILD.length) n = 0; if (n < 0) return; idx = n; show();
  }
  var ids = P.map(function (p) { return p.id; }), want = null;
  try { want = new URLSearchParams(location.search).get('p'); } catch (e) {}
  if (ids.indexOf(want) < 0) { try { want = localStorage.getItem('pool.me'); } catch (e) { want = null; } }
  known = ids.indexOf(want) >= 0;
  me = known ? want : ids[0];
  asking = !known;                                     // first visit: ask "T'es qui ?" on the first card (no login)
  if (location.hash === '#equipe') { idx = RACE; detail = me; }
  document.getElementById('demo').hidden = !M.demo;
  document.getElementById('prev').onclick = function () { go(-1); };
  document.getElementById('next').onclick = function () { go(1); };
  document.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') go(1); else if (e.key === 'ArrowLeft' || e.key === 'Escape') go(-1); });
  var sx = 0, sy = 0, skip = false;
  document.addEventListener('touchstart', function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; skip = !!(e.target.closest && e.target.closest('.chips,.chart')); }, { passive: true });
  document.addEventListener('touchend', function (e) { if (skip) return; var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy; if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.6) go(dx < 0 ? 1 : -1); }, { passive: true });
  show();
})();
</script>
</body>
</html>
"""


def render_edge(data):
    return TEMPLATE.replace("__FONTS__", FONT_CSS).replace("__DATA__", _embed(data))
