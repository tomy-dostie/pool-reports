"""The report page (main design since 2026-11-03): data-dense "advanced stats" look. The previous design (render.py)
is still built at /classique/ as a fallback.

Navigation (2026-11-03 UX overhaul): bottom tab bar with icons (Accueil, Moi, Classement, Marché, Prix) and screens
opened on top of a tab (pooler profile with sub-tabs, duel, live view, "T'es qui ?"). Every screen is a hash route
kept in the browser history, so the phone's back gesture and the "‹ Retour" button both go back.

Inspired by stats-hub layouts (stat tiles with pool rank and average, percentile bars, sortable leaderboards,
trend chart, head-to-head). Own colours, icons and wording; no league logos, marks or images.
"""
from .render import FONT_CSS, _embed

TEMPLATE = r"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<meta name="theme-color" content="#0A0D12">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Pool LNH">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Pool LNH : analyse</title>
<style>
__FONTS__
:root{--bg:#0A0D12;--panel:#131820;--panel2:#1B222C;--line:#2A3340;--text:#F2F5F9;--muted:#A9B4C4;--faint:#7D899B;--accent:#2BE3A6;--accent2:#7FE0C1;--mid:#55657B;--warm:#FF8A6B;--live:#FF4D5E;--ink:#0A0D12}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:'Barlow',system-ui,sans-serif;font-size:16px;-webkit-text-size-adjust:100%}
button{font:inherit;color:inherit;border:0;background:transparent;padding:0;cursor:pointer;text-align:left;-webkit-tap-highlight-color:transparent}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
/* The app is pinned to the visible screen edges (position:fixed + inset 0) instead of 100vh/100dvh: on a home-screen
   install the phone reports a taller viewport than what is visible, which pushed the tab bar off the bottom. */
html,body{height:100%;overflow:hidden}
.app{position:fixed;top:0;right:0;bottom:0;left:0;max-width:520px;margin:0 auto;padding:calc(10px + env(safe-area-inset-top)) 16px 0;display:flex;flex-direction:column;gap:10px}
/* top bar: brand on tabs, "‹ Retour" + title on screens */
.top{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:10px;min-height:46px}
.brand{font:800 19px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase}.brand b{color:var(--accent)}
.top .when{font-size:14px;color:var(--muted);text-align:right;grid-column:3}
.back{min-height:44px;padding:0 14px 0 10px;border-radius:12px;background:var(--panel2);border:1px solid var(--line);font-weight:600;font-size:16px;white-space:nowrap}
.back:active{background:var(--line)}
.top .ttl{font:800 22px/1 'Barlow Condensed',sans-serif;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top .val{font-size:30px;line-height:1}
.demo{background:var(--warm);color:var(--ink);font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;text-align:center;border-radius:8px;padding:5px 8px}
.card{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}
.card.in{animation:in .18s ease-out}@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.card.in{animation:none}}
.stack{display:flex;flex-direction:column;gap:12px;padding-bottom:18px}
/* bottom tab bar */
.tabs{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin:0 -16px;border-top:1px solid var(--line);background:#0D1117;padding-bottom:env(safe-area-inset-bottom)}
.tabs button{position:relative;min-height:58px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;color:var(--faint);font-size:12px;font-weight:600;text-align:center}
.tabs button svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.tabs button[aria-current=page]{color:var(--accent)}
.tabs button[aria-current=page]::before{content:'';position:absolute;top:0;left:28%;right:28%;height:3px;border-radius:0 0 3px 3px;background:var(--accent)}
.tabs .badge{position:absolute;top:9px;left:calc(50% + 8px);width:9px;height:9px;border-radius:50%;background:var(--live);box-shadow:0 0 0 2px #0D1117;animation:blink 1.4s ease-in-out infinite}
h1{margin:0;font:800 34px/.95 'Barlow Condensed',sans-serif;text-transform:uppercase;letter-spacing:.01em}
h2{margin:8px 0 0;font:700 15px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.sub{margin:0;font-size:15px;line-height:1.45;color:var(--muted)}
.small{font-size:14px;line-height:1.35;color:var(--muted)}
.alert{margin:0;font-size:14px;color:var(--warm)}
.num{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-variant-numeric:tabular-nums}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px}
.rows>*{display:block;width:100%;border-top:1px solid var(--line)}.rows>*:first-child{border-top:0}
.rows>.tap:first-child{border-radius:14px 14px 0 0}.rows>.tap:last-child{border-radius:0 0 14px 14px}.rows>.tap:only-child{border-radius:14px}
/* anything tappable: arrow on the right + pressed state */
.tap{position:relative;padding-right:36px !important;min-height:48px}
.tap::after{content:'›';position:absolute;right:13px;top:50%;transform:translateY(-52%);font-size:26px;line-height:1;color:var(--faint)}
.tap:active{background:var(--panel2)}
@media (hover:hover){.tap:hover{background:var(--panel2)}}   /* iOS keeps :hover after a tap: only real mice get it */
.link{min-height:44px;font-size:16px;color:var(--accent);font-weight:600}
.btn{min-height:48px;border-radius:12px;background:transparent;border:1.5px solid var(--line);text-align:center;font:700 16px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase}
.btn:active{background:var(--panel2)}
.btn.main{background:var(--accent);border-color:transparent;color:var(--ink)}
.btn.hot{background:var(--live);border-color:transparent;color:var(--ink)}
.date{display:flex;align-items:flex-end;gap:12px}.date .d{font-size:84px;line-height:.8}.date .m{font:800 28px/.9 'Barlow Condensed',sans-serif;text-transform:uppercase;color:var(--accent)}
.lead{padding:14px 16px;display:flex;flex-direction:column;gap:8px;border-left:3px solid var(--accent)}
.lead .t{font:800 26px/1.05 'Barlow Condensed',sans-serif;text-transform:uppercase}.lead p{margin:0;font-size:16px;line-height:1.45}
.kick{font:700 14px 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.tile{padding:12px;display:flex;flex-direction:column;gap:6px;min-width:0}
.tile .l{font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.tile .v{font-size:38px;line-height:1}.tile .r{font-size:14px;color:var(--muted)}.tile .r b{color:var(--text);font-weight:600}
.track{position:relative;height:7px;border-radius:4px;background:var(--panel2);overflow:visible}
.fill{position:absolute;left:0;top:0;bottom:0;border-radius:4px}
.tick{position:absolute;top:-3px;width:2px;height:13px;background:var(--text);opacity:.75;border-radius:1px}
.chips{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}.chips::-webkit-scrollbar{display:none}
.chips.wrap{flex-wrap:wrap;overflow:visible}
.chip{flex:none;min-height:44px;padding:0 14px;border-radius:12px;background:var(--panel);border:1px solid var(--line);font-size:16px;font-weight:600}
.chip:active{background:var(--panel2)}
.chip[aria-pressed=true]{color:var(--ink);border-color:transparent}
.seg{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:3px;gap:3px}
.seg button{min-height:42px;border-radius:9px;text-align:center;font:700 14px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.seg button[aria-pressed=true]{background:var(--accent);color:var(--ink)}
.subtabs{position:sticky;top:0;z-index:3;background:var(--bg);padding:4px 0 6px}
.lb{display:grid;grid-template-columns:28px minmax(0,1fr) 72px 46px;align-items:center;gap:10px;padding:10px 12px}
.lb .rk{font-size:24px;color:var(--muted)}.nm{font-size:17px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lb .vv{font-size:28px;text-align:right}.dot{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:8px;vertical-align:1px}
.mv-up{color:var(--accent)}.mv-down{color:var(--warm)}
.pl{padding:11px 12px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;align-items:center}
.pl .pp{grid-row:span 2;display:flex;flex-direction:column;align-items:flex-end}.pl .pp .num{font-size:28px;line-height:1}
.pct{grid-column:1/-1;display:grid;grid-template-columns:98px minmax(0,1fr) 38px;gap:8px;align-items:center;font-size:13px;color:var(--muted)}
.pct b{font:700 16px 'Barlow Condensed',sans-serif;text-align:right}
.hero{display:grid;grid-template-columns:56px minmax(0,1fr);gap:12px;align-items:center;padding:12px 14px}
.ini{width:56px;height:56px;border-radius:13px;color:var(--ink);display:flex;align-items:center;justify-content:center;font:800 24px 'Barlow Condensed',sans-serif;flex:none}
.ini.sm{width:42px;height:42px;border-radius:10px;font-size:19px}
.hero .nm{font:800 28px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}
.chart{padding:10px 8px 6px}.chart svg{display:block;width:100%;height:auto}
.duel{display:grid;grid-template-columns:minmax(0,1fr) 104px minmax(0,1fr);gap:8px;align-items:center;padding:11px 12px}
.duel .a{text-align:right}.duel .mid{text-align:center;font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.duel .num{font-size:28px}.duel .win{color:var(--accent)}
.mvr{display:grid;grid-template-columns:56px minmax(0,1fr);gap:10px;padding:11px 12px;align-items:baseline}.mvr b{font:700 15px 'Barlow Condensed',sans-serif;text-transform:uppercase;color:var(--muted)}
.wrapt{white-space:normal;line-height:1.3}
.award{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 14px}.award .w{font:800 23px/1.05 'Barlow Condensed',sans-serif;text-transform:uppercase}.award .d{font-weight:700;color:var(--accent);text-align:right;font-size:16px}
.since{padding:14px 16px;display:flex;flex-direction:column;gap:10px;border-color:rgba(43,227,166,.5);background:linear-gradient(160deg,rgba(43,227,166,.12),var(--panel) 60%)}
.since .row{display:flex;align-items:flex-end;justify-content:space-between;gap:12px}
.since .big{font-size:54px;line-height:.85}.since .rk{font-size:32px;line-height:1;text-align:right}
.since ul,.plain{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:7px;font-size:16px;line-height:1.4}
.since li{display:flex;gap:8px}.since li i{font-style:normal;width:18px;flex:none;text-align:center}
.mecard{display:grid;grid-template-columns:42px minmax(0,1fr);gap:12px;align-items:center;padding:12px 14px}
.mecard .nm{font:800 22px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}
.tag{display:inline-block;padding:3px 8px;border-radius:7px;font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase;background:var(--panel2);color:var(--muted)}
.tag.good{background:rgba(43,227,166,.16);color:var(--accent)}.tag.bad{background:rgba(255,138,107,.16);color:var(--warm)}
.trade{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;align-items:center;padding:11px 12px}
.trade .num{font-size:28px;text-align:right}.trade>.small{grid-column:1/-1}
.pop{display:inline-block;animation:pop .6s ease-out .5s both}@keyframes pop{0%{transform:scale(.4);opacity:0}70%{transform:scale(1.25)}100%{transform:none;opacity:1}}
@media (prefers-reduced-motion:reduce){.pop{animation:none}.tabs .badge{animation:none}}
.livep{padding:14px 16px;display:flex;flex-direction:column;gap:10px;border-color:var(--live);background:linear-gradient(160deg,rgba(255,77,94,.16),var(--panel) 65%)}
.livehd{display:flex;justify-content:space-between;align-items:center;gap:10px}
.onair{display:inline-flex;align-items:center;gap:8px;font:800 17px 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--live)}
.onair i{width:10px;height:10px;border-radius:50%;background:var(--live);animation:blink 1.4s ease-in-out infinite}.onair.done{color:var(--muted)}.onair.done i{background:var(--muted);animation:none}
@keyframes blink{50%{opacity:.25}}@media (prefers-reduced-motion:reduce){.onair i{animation:none}}
.lv{display:grid;grid-template-columns:28px minmax(0,1fr) auto 36px;align-items:center;gap:10px;padding:10px 12px}
.lv .rk{font-size:24px;color:var(--muted)}.lv .vv{font-size:28px;text-align:right}.lv .mv{text-align:right;font:700 15px 'Barlow Condensed',sans-serif}
.lvs{padding:2px 12px 12px 50px;display:flex;flex-direction:column;gap:6px;font-size:15px;color:var(--muted)}
.gm{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 12px;padding:10px 12px;align-items:center}
.gm .sc{font:800 21px 'Barlow Condensed',sans-serif;font-variant-numeric:tabular-nums}.gm .st{font-size:14px;color:var(--muted);text-align:right}.gm.on .st{color:var(--live);font-weight:700}
/* "T'es qui ?" */
.welcome{display:flex;flex-direction:column;gap:14px;padding:6px 0 18px}
.welcome h1{font-size:42px}
.picks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.pick{display:flex;align-items:center;gap:12px;padding:10px 12px;min-height:66px;border-radius:14px;background:var(--panel);border:1.5px solid var(--line)}
.pick:active{background:var(--panel2)}@media (hover:hover){.pick:hover{background:var(--panel2)}}.pick[aria-pressed=true]{border-color:var(--accent)}
.pick .nm{font-size:18px}.pick .small{font-size:13px}
.toast{position:fixed;left:50%;bottom:calc(76px + env(safe-area-inset-bottom));transform:translateX(-50%);max-width:min(92vw,480px);background:var(--accent);color:var(--ink);font-weight:700;font-size:16px;padding:12px 16px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.4);z-index:10;text-align:center}
</style>
</head>
<body>
<div class="app">
  <header class="top" id="top"><span class="brand">Pool <b>LNH</b> · Analyse</span></header>
  <div class="demo" id="demo" hidden>Aperçu : chiffres inventés</div>
  <main class="card" id="card" tabindex="-1"></main>
  <nav class="tabs" id="tabs" aria-label="Sections"></nav>
</div>
<script>
window.DATA = __DATA__;
(function () {
  var D = window.DATA, M = D.meta, P = D.poolers;
  var KPI = [['total', 'Total'], ['yday', 'Hier'], ['last7', '7 jours'], ['proj', 'Projection']];
  var TABS = [
    ['accueil', 'Accueil', 'M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z'],
    ['moi', 'Moi', 'M16 8a4 4 0 1 1-8 0a4 4 0 1 1 8 0M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6'],
    ['classement', 'Classement', 'M3 21V13h5v8M9.5 21V5h5v16M16 21v-6h5v6M2 21h20'],
    ['marche', 'Waivers', 'M4 8h15l-4-4M20 16H5l4 4'],
    ['prix', 'Prix', 'M17 15a5 5 0 1 1-10 0a5 5 0 1 1 10 0M8.5 11 6 3h4l2 5 2-5h4l-2.5 8']
  ];
  var SUBS = [['resume', 'Résumé'], ['alignement', 'Alignement'], ['duels', 'Duels'], ['mouvements', 'Mouvements']];
  var me = null, known = false, spectator = false;
  var raceKey = 'total', sortKey = 'pts', chartMode = 'pts', liveSel = null, picking = false, lastSub = 'resume';
  var route = { tab: 'accueil', depth: 0 };

  function el(t, c, x) { var n = document.createElement(t); if (c) n.className = c; if (x != null) n.textContent = x; return n; }
  function add(p) { for (var i = 1; i < arguments.length; i++) if (arguments[i]) p.appendChild(arguments[i]); return p; }
  function txt(s) { return document.createTextNode(s); }
  function plural(n, a, b) { return Math.abs(n) <= 1 ? a : b; }
  function ord(n) { return n === 1 ? '1er' : n + 'e'; }
  function dec(x) { return String(x).replace('.', ','); }
  function byId(id) { return P.filter(function (p) { return p.id === id; })[0]; }
  function byName(n) { return P.filter(function (p) { return p.name === n; })[0]; }
  function maxOf(k) { return Math.max.apply(null, P.map(function (p) { return p.kpi[k].v; }).concat([1])); }
  function tier(p) { return p >= 90 ? 'var(--accent)' : p >= 75 ? 'var(--accent2)' : p >= 50 ? 'var(--mid)' : 'var(--warm)'; }
  function last(name) { return String(name).split(' ').slice(-1)[0]; }
  function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function getRaw(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function setRaw(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} }
  function tap(tag, cls) { return el(tag || 'button', (cls ? cls + ' ' : '') + 'tap'); }
  function gapText(p) { return p.rank === 1 ? 'au sommet' : 'à ' + p.gap + ' du 1er'; }
  function iniBox(p, small) { var b = el('div', 'ini' + (small ? ' sm' : ''), p.initials); b.style.background = p.color; return b; }
  var still = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

  // ---------------------------------------------------------------- navigation (hash routes + browser history)
  function hashOf(r) {
    if (r.screen === 'pooler') return '#pooler/' + r.a + (r.sub && r.sub !== 'resume' ? '/' + r.sub : '');
    if (r.screen === 'duel') return '#duel/' + r.a + '/' + r.b;
    if (r.screen) return '#' + r.screen;
    return '#' + r.tab;
  }
  function parse(h) {
    var parts = String(h || '').replace(/^#\/?/, '').split('/');
    var t = TABS.map(function (x) { return x[0]; });
    if (parts[0] === 'equipe') return { tab: 'classement', screen: 'pooler', a: me, sub: 'resume' };            // old personal links
    if (parts[0] === 'pooler' && byId(parts[1])) return { tab: 'classement', screen: 'pooler', a: parts[1], sub: SUBS.some(function (s) { return s[0] === parts[2]; }) ? parts[2] : 'resume' };
    if (parts[0] === 'duel' && byId(parts[1]) && byId(parts[2]) && parts[1] !== parts[2]) return { tab: 'classement', screen: 'duel', a: parts[1], b: parts[2] };
    if (parts[0] === 'direct' && D.live && D.live.poolers) return { tab: 'accueil', screen: 'direct' };
    if (parts[0] === 'qui') return { tab: 'accueil', screen: 'qui' };
    return { tab: t.indexOf(parts[0]) >= 0 ? parts[0] : 'accueil' };
  }
  function card() { return document.getElementById('card'); }
  // push = a new screen (one more step back); otherwise the current step is replaced (tabs, sub-tabs)
  function nav(r, push) {
    var cur = route;
    if (push) {
      try { history.replaceState(Object.assign({}, cur, { scroll: card().scrollTop }), '', hashOf(cur)); } catch (e) {}
      r.depth = (cur.depth || 0) + 1;
      try { history.pushState(r, '', hashOf(r)); } catch (e) {}
    } else {
      if (r.depth == null) r.depth = r.screen ? (cur.depth || 0) : 0;
      try { history.replaceState(r, '', hashOf(r)); } catch (e) {}
    }
    route = r; picking = false; render();
  }
  function goBack() {
    if (route.depth > 0 && window.history && history.length > 1) { try { history.back(); return; } catch (e) {} }
    nav({ tab: route.tab || 'accueil' }, false);                       // opened from a link: go to the parent tab
  }
  function openTab(t) { liveSel = null; nav({ tab: t }, false); }
  function openPooler(id, sub) { nav({ tab: route.tab, screen: 'pooler', a: id, sub: sub || lastSub || 'resume' }, true); }
  function openDuel(a, b) { nav({ tab: route.tab, screen: 'duel', a: a, b: b }, true); }
  function openLive() { nav({ tab: 'accueil', screen: 'direct' }, true); }
  function openWho() { nav({ tab: route.tab, screen: 'qui', from: route.tab }, true); }

  // ---------------------------------------------------------------- who are you (no login: kept on the phone)
  function setMe(id) { me = id; known = true; spectator = false; setRaw('pool.me', id); setRaw('pool.spectator', null); }
  function toast(s) {
    var t = el('div', 'toast', s); t.setAttribute('role', 'status'); document.body.appendChild(t);
    setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 3000);
  }
  function picker(onPick) {
    var g = el('div', 'picks');
    P.forEach(function (p) {
      var b = el('button', 'pick'); b.setAttribute('aria-pressed', known && p.id === me ? 'true' : 'false');
      add(b, iniBox(p, true), add(el('div'), el('div', 'nm', p.name), el('div', 'small', ord(p.rank) + ' · ' + p.total + ' pts')));
      b.onclick = function () { onPick(p.id); };
      g.appendChild(b);
    });
    return g;
  }
  function welcome() {
    var s = el('div', 'welcome');
    add(s, el('div', 'kick', 'Bienvenue dans le pool'), el('h1', null, 'T’es qui ?'),
      el('p', 'sub', 'Choisis ton nom une fois pis la page va s’ouvrir sur ton équipe, avec ce qui a changé depuis ta dernière visite. Pas de compte, rien est envoyé : c’est gardé dans ton téléphone.'),
      picker(function (id) {
        setMe(id); var from = route.from || 'accueil';
        toast('Salut ' + byId(id).name + ' ! La page va s’ouvrir sur ton équipe.');
        if (route.depth > 0) goBack(); else nav({ tab: from }, false);
      }));
    var spec = el('button', 'link', 'Je regarde juste ›');
    spec.onclick = function () { spectator = true; setRaw('pool.spectator', '1'); if (route.depth > 0) goBack(); else nav({ tab: 'accueil' }, false); };
    return add(s, spec);
  }

  // ---------------------------------------------------------------- "since your last visit" (snapshot kept on the phone)
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
    if (dRk) rk.appendChild(el('span', (dRk > 0 ? 'mv-up' : 'mv-down') + (animate ? ' pop' : ''), dRk > 0 ? ' ▲' + dRk : ' ▼' + (-dRk)));
    add(head, add(el('div'), el('div', 'kick', 'Depuis ta dernière visite'), big, el('div', 'small', plural(gained, 'point', 'points') + ' · total ' + p.total)), add(el('div'), rk, el('div', 'small', dRk ? 'était ' + ord(wasRk) : 'même rang')));
    add(box, head);
    var ul = el('ul');
    function li(icon, text, cls) { ul.appendChild(add(el('li', cls || null), el('i', null, icon), el('span', null, text))); }
    var passed = [], passedBy = [];
    P.forEach(function (q) {
      if (q.id === p.id || base.t[q.id] == null) return;
      if (was < base.t[q.id] && p.total > q.total) passed.push(q.name);
      if (was > base.t[q.id] && p.total < q.total) passedBy.push(q.name);
    });
    if (p.rank === 1 && wasRk > 1) li('👑', 'T’es rendu 1er !', 'mv-up');
    if (passed.length) li('▲', 'T’as dépassé ' + passed.join(', ') + '.', 'mv-up');
    if (passedBy.length) li('▼', passedBy.join(', ') + ' ' + (passedBy.length > 1 ? 't’ont' : 't’a') + ' dépassé.', 'mv-down');
    var leaderWas = Math.max.apply(null, P.map(function (q) { return base.t[q.id] || 0; })), gapWas = leaderWas - was;
    if (p.rank > 1 && gapWas !== p.gap) li('↔', 'Écart avec le 1er : ' + gapWas + ' → ' + p.gap + (p.gap < gapWas ? '. Ça se resserre.' : '.'));
    var mine = base.pl[p.id] || {}, deltas = [];
    p.team.concat(p.former).forEach(function (x) { var d = x.pts - (mine[x.player] || 0); if (d > 0) deltas.push([d, x.player]); });
    deltas.sort(function (a, b) { return b[0] - a[0]; });
    if (deltas.length) li('★', deltas.slice(0, 3).map(function (d) { return last(d[1]) + ' +' + d[0]; }).join(' · '));
    else if (gained === 0) li('·', 'Pas un point depuis. On se reprend à soir.');
    if (ul.childNodes.length) add(box, ul);
    add(box, el('div', 'small', 'Résultats du ' + base.label + ' au ' + M.lastDayLabel + '.'));
    animate = false;                                                  // coming back to this screen later: no replay
    return box;
  }

  // ---------------------------------------------------------------- "En direct" (evening builds; official numbers next morning)
  function liveOn() { return !!(D.live && D.live.poolers); }
  function liveAge() { var L = D.live; if (!L || !L.updatedAt) return null; var m = Math.round((Date.now() - Date.parse(L.updatedAt)) / 60000); return isNaN(m) ? null : Math.max(0, m); }
  function ago(m) { return m == null ? '' : m < 1 ? 'à l’instant' : m < 60 ? 'il y a ' + m + ' min' : 'il y a ' + Math.floor(m / 60) + ' h ' + String(m % 60).padStart(2, '0'); }
  function liveStatus(L) {
    var bits = [];
    if (L.inProgress) bits.push(L.inProgress + ' en cours');
    if (L.finals) bits.push(L.finals + ' ' + plural(L.finals, 'final', 'finals'));
    if (L.upcoming) bits.push(L.upcoming + ' à venir');
    return bits.join(' · ');
  }
  function onAir(L) { return add(el('span', 'onair' + (L.allDone ? ' done' : '')), el('i'), txt(L.allDone ? 'Soirée terminée' : 'En direct')); }
  function livePanel() {
    if (!liveOn()) return null;
    var L = D.live, box = el('div', 'panel livep');
    add(box, add(el('div', 'livehd'), onAir(L), el('span', 'small', 'màj ' + L.updated + ' · ' + ago(liveAge()))), el('div', 'small', liveStatus(L)));
    var mine = known ? L.poolers.filter(function (r) { return r.id === me; })[0] : null;
    if (mine) {
      var n = el('span', 'num', '+' + mine.tonight); n.style.fontSize = '42px'; n.style.color = mine.tonight ? 'var(--text)' : 'var(--muted)';
      var line = add(el('div'), n, txt('  à soir · ' + ord(mine.rank) + ' provisoire'));
      if (mine.move) add(line, el('span', mine.move > 0 ? 'mv-up' : 'mv-down', mine.move > 0 ? ' ▲' + mine.move : ' ▼' + (-mine.move)));
      add(box, line);
    }
    var top = L.poolers.slice().sort(function (a, b) { return b.tonight - a.tonight || (a.name < b.name ? -1 : 1); }).slice(0, 3).filter(function (r) { return r.tonight > 0; });
    if (top.length) add(box, el('div', null, 'À soir : ' + top.map(function (r) { return r.name + ' +' + r.tonight; }).join(' · ')));
    var b = el('button', 'btn hot', 'Voir le direct ›'); b.onclick = openLive;
    return add(box, b);
  }
  function liveView() {
    var s = el('div', 'stack'), L = D.live, m = liveAge();
    add(s, add(el('div', 'livehd'), onAir(L), el('span', 'small', 'màj ' + L.updated + ' · ' + ago(m))), el('h1', null, 'Soirée du ' + L.dayLabel), el('p', 'sub', liveStatus(L)));
    if (m != null && m > 35 && !L.allDone) add(s, el('p', 'alert', 'Le direct est en retard (ça se met à jour aux 15 min à peu près). Les points s’en viennent.'));
    if (L.failed) add(s, el('p', 'alert', L.failed + ' partie(s) pas encore rentrée(s) : y manque des points.'));
    add(s, el('h2', null, 'Classement provisoire'));
    var lb = el('div', 'panel rows');
    L.poolers.forEach(function (r) {
      var row = tap('button', 'lv'), dot = el('span', 'dot'); dot.style.background = r.color;
      var bits = ['+' + r.tonight + ' ce soir']; if (r.playing) bits.push(r.playing + ' en jeu'); if (r.toCome) bits.push(r.toCome + ' à venir');
      var nm = add(el('div'), add(el('div', 'nm'), dot, txt(r.name)), el('div', 'small', bits.join(' · ')));
      var mv = el('span', 'mv ' + (r.move > 0 ? 'mv-up' : r.move < 0 ? 'mv-down' : 'small'), r.move > 0 ? '▲' + r.move : r.move < 0 ? '▼' + (-r.move) : '–');
      add(row, el('span', 'rk num', String(r.rank)), nm, el('span', 'vv num', String(r.total)), mv);
      if (r.id === me && known) row.style.background = 'var(--panel2)';
      row.setAttribute('aria-expanded', liveSel === r.id ? 'true' : 'false');
      row.onclick = function () { liveSel = liveSel === r.id ? null : r.id; render(true); };
      lb.appendChild(row);
      if (liveSel === r.id) {
        var det = el('div', 'lvs');
        if (r.scorers.length) r.scorers.forEach(function (x) { add(det, el('div', null, x.player + ' (' + x.team + ') · ' + x.line + ' · +' + x.pts)); });
        else add(det, el('div', null, 'Pas de points pour l’instant.'));
        var go = el('button', 'link', 'Voir le profil de ' + r.name + ' ›'); go.onclick = function () { openPooler(r.id); };
        lb.appendChild(add(det, go));
      }
    });
    add(s, lb, el('p', 'small', 'Touche un pooler pour voir ses marqueurs. Rang provisoire = total de ce matin + points d’à soir.'));
    add(s, el('h2', null, 'Parties'));
    var gl = el('div', 'panel rows');
    L.games.forEach(function (g) {
      var started = g.live || g.final;
      add(gl, add(el('div', 'gm' + (g.live ? ' on' : '')), el('span', 'sc', started ? g.away + ' ' + g.as + ' – ' + g.hs + ' ' + g.home : g.away + ' à ' + g.home), el('span', 'st', g.status)));
    });
    add(s, gl, el('p', 'small', 'C’est provisoire : les vrais points rentrent demain matin. Mise à jour aux 15 minutes à peu près.'));
    return s;
  }
  function refreshLive() {
    if (!D.live || !window.fetch || document.visibilityState === 'hidden') return;
    fetch('live.json?t=' + Date.now(), { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (L) {
      if (!L || !L.poolers || L.day !== D.live.day || Date.parse(L.updatedAt) <= Date.parse(D.live.updatedAt)) return;
      D.live = L; if (route.tab === 'accueil' && (!route.screen || route.screen === 'direct')) render(true); else drawTabs();
    }, function () {});
  }

  // ---------------------------------------------------------------- "Install as an app"
  var installEvt = null, standalone = !!((window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone);
  var ios = /iPhone|iPad|iPod/.test(navigator.userAgent || '');
  window.addEventListener && window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); installEvt = e; if (route.tab === 'accueil' && !route.screen) render(true); });
  function installPanel() {
    if (standalone || getRaw('pool.install') === 'non' || M.demo || (!installEvt && !ios)) return null;
    var box = add(el('div', 'panel lead'), el('div', 'kick', 'Le pool sur ton écran d’accueil'));
    if (installEvt) {
      var b = el('button', 'btn main', 'Installer l’app');
      b.onclick = function () { installEvt.prompt(); installEvt = null; render(true); };
      add(box, el('p', 'sub', 'Une icône, plein écran, pis un tap le matin.'), b);
    } else add(box, el('p', 'sub', 'Sur iPhone : touche Partager (le carré avec la flèche), pis « Sur l’écran d’accueil ». Ça ouvre le pool en plein écran, comme une app.'));
    var no = el('button', 'link', 'Non merci'); no.onclick = function () { setRaw('pool.install', 'non'); render(true); };
    return add(box, no);
  }

  // ---------------------------------------------------------------- building blocks
  function track(frac, color, tickFrac) {
    var t = el('div', 'track'), f = el('div', 'fill');
    f.style.width = Math.max(2, Math.min(100, frac * 100)) + '%'; f.style.background = color; t.appendChild(f);
    if (tickFrac != null) { var k = el('div', 'tick'); k.style.left = 'calc(' + Math.min(100, tickFrac * 100) + '% - 1px)'; k.title = 'Moyenne du pool'; t.appendChild(k); }
    return t;
  }
  function tile(label, k, p) {
    var mx = maxOf(k), x = p.kpi[k];
    var r = add(el('div', 'r'), el('b', null, ord(x.rank)), txt(' sur ' + P.length + ' · moy. ' + dec(x.avg)));
    return add(el('div', 'panel tile'), el('div', 'l', label), el('div', 'v num', (k === 'yday' || k === 'last7' ? '+' : '') + x.v), track(x.v / mx, p.color, x.avg / mx), r);
  }
  function tiles(p) { var t = el('div', 'tiles'); KPI.forEach(function (k) { t.appendChild(tile(k[1], k[0], p)); }); return t; }
  function pctRow(pct, ppg) {
    var r = el('div', 'pct');
    if (pct == null) { add(r, el('span', null, 'Rang LNH'), el('span', null, 'moins de 5 parties'), el('b')); return r; }
    var b = el('b', null, ord(pct)); b.style.color = tier(pct);
    add(r, el('span', null, ppg == null ? 'Rang LNH' : dec(ppg) + ' pt/partie'), track(pct / 100, tier(pct)), b);
    r.title = 'Centile parmi les joueurs de la LNH à la même position (points par partie, saison)';
    return r;
  }
  function seg(opts, cur, pick, label) {
    var s = el('div', 'seg'); if (label) s.setAttribute('aria-label', label);
    opts.forEach(function (o) { var b = el('button', null, o[1]); b.setAttribute('aria-pressed', o[0] === cur ? 'true' : 'false'); b.onclick = function () { pick(o[0]); }; s.appendChild(b); });
    return s;
  }
  function chips(cur, pick, skip, wrap) {
    var c = el('div', 'chips' + (wrap ? ' wrap' : ''));
    P.forEach(function (p) {
      if (p.id === skip) return;
      var b = el('button', 'chip', p.name), on = p.id === cur;
      b.setAttribute('aria-pressed', on ? 'true' : 'false'); if (on) b.style.background = p.color;
      b.onclick = function () { pick(p.id); }; c.appendChild(b);
    });
    return c;
  }
  function verdict(x) {                                 // a move judged by what each player did afterwards
    if (!x.out || !x.in || x.outAfter == null) return null;
    var d = x.inPts - x.outAfter;
    return el('span', 'tag ' + (d > 0 ? 'good' : d < 0 ? 'bad' : ''), d > 0 ? 'Bon coup +' + d : d < 0 ? 'Regret ' + d : 'Égal');
  }
  function chart(ids) {
    var ns = 'http://www.w3.org/2000/svg', W = 340, H = 156, L = 32, R = 8, T = 8, B = 22, n = D.trendDays.length;
    var svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('role', 'img');
    var byRank = chartMode === 'rank' && P[0].ranks, key = byRank ? 'ranks' : 'trend', N = P.length;
    var top = Math.max.apply(null, P.map(function (p) { return p.trend.length ? p.trend[p.trend.length - 1] : 0; }).concat([1]));
    var X = function (i) { return L + (n > 1 ? i / (n - 1) : 0) * (W - L - R); };
    var Y = byRank ? function (v) { return T + (N > 1 ? (v - 1) / (N - 1) : 0) * (H - T - B); } : function (v) { return T + (1 - v / top) * (H - T - B); };
    function line(x1, y1, x2, y2, c, w) { var l = document.createElementNS(ns, 'line'); l.setAttribute('x1', x1); l.setAttribute('y1', y1); l.setAttribute('x2', x2); l.setAttribute('y2', y2); l.setAttribute('stroke', c); l.setAttribute('stroke-width', w); svg.appendChild(l); }
    function text(x, y, s, anchor) { var t = document.createElementNS(ns, 'text'); t.setAttribute('x', x); t.setAttribute('y', y); t.setAttribute('fill', '#A9B4C4'); t.setAttribute('font-size', '11'); t.setAttribute('font-family', 'Barlow, sans-serif'); t.setAttribute('text-anchor', anchor || 'start'); t.textContent = s; svg.appendChild(t); }
    if (byRank) [1, Math.ceil(N / 2), N].forEach(function (v) { line(L, Y(v), W - R, Y(v), '#2A3340', 1); text(L - 6, Y(v) + 4, ord(v), 'end'); });
    else [0, .5, 1].forEach(function (f) { var v = Math.round(top * f); line(L, Y(v), W - R, Y(v), '#2A3340', 1); text(L - 6, Y(v) + 4, String(v), 'end'); });
    if (n) { text(X(0), H - 5, D.trendDays[0]); text(X(n - 1), H - 5, D.trendDays[n - 1], 'end'); }
    var order = P.filter(function (p) { return ids.indexOf(p.id) < 0; }).concat(ids.map(byId));
    order.forEach(function (p) {
      if (p[key].length < 2) return;
      var on = ids.indexOf(p.id) >= 0, path = document.createElementNS(ns, 'path');
      path.setAttribute('d', p[key].map(function (v, i) { return (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); }).join(' '));
      path.setAttribute('fill', 'none'); path.setAttribute('stroke', on ? p.color : '#55657B'); path.setAttribute('stroke-width', on ? 2.8 : 1);
      path.setAttribute('opacity', on ? 1 : .4); path.setAttribute('stroke-linejoin', 'round'); svg.appendChild(path);
    });
    svg.setAttribute('aria-label', (byRank ? 'Rang au classement, soir après soir' : 'Points cumulés de la saison') + ids.map(function (id) { var p = byId(id); return ', ' + p.name + ' ' + (byRank ? ord(p.rank) : p.total); }).join(''));
    return add(el('div', 'panel chart'), svg);
  }
  function chartBlock(ids) {
    var t = P[0].ranks ? seg([['pts', 'Points'], ['rank', 'Rang']], chartMode, function (k) { chartMode = k; render(true); }, 'Type de courbe') : null;
    return add(el('div', 'stack'), t, chart(ids));
  }
  function wlt(r) { return r[0] + '-' + r[1] + (r[2] ? '-' + r[2] : ''); }
  // one row of a ranking (standings, podium): tap = that pooler's profile
  function lbRow(p, k, mx) {
    var r = tap('button', 'lb'), v = p.kpi[k].v;
    var mv = p.move > 0 ? el('span', 'mv-up', ' ▲' + p.move) : p.move < 0 ? el('span', 'mv-down', ' ▼' + Math.abs(p.move)) : null;
    var dot = el('span', 'dot'); dot.style.background = p.color;
    var nm = add(el('div'), add(el('div', 'nm'), dot, txt(p.name), k === 'total' ? mv : null), el('div', 'small', k === 'total' ? (p.rank === 1 ? 'Au sommet' : 'à ' + p.gap + ' du 1er') : p.total + ' pts au total'));
    add(r, el('span', 'rk num', String(p.kpi[k].rank)), nm, track(v / mx, p.color, p.kpi[k].avg / mx), el('span', 'vv num', (k === 'yday' || k === 'last7' ? '+' : '') + v));
    r.setAttribute('aria-label', p.name + ', ' + ord(p.kpi[k].rank) + ', ' + v + '. Voir son profil');
    r.onclick = function () { openPooler(p.id); };
    return r;
  }
  // "À ce rythme": recent form projected forward (the report never gives a date more than 60 days away)
  function pacePanel(p, mine) {
    var x = p.pace; if (!x) return null;
    var ul = el('ul', 'plain');
    function li(text, cls) { ul.appendChild(el('li', cls || null, text)); }
    var c = x.chase;
    if (c && c.kind === 'catch') li((mine ? 'Tu passes ' : p.name + ' passe ') + c.name + ' vers le ' + c.date + ' (+' + dec(c.gain) + ' pt par jour sur ' + c.name + ').', 'mv-up');
    if (c && c.kind === 'threat') li(c.name + (mine ? ' te rattrape' : ' rattrape ' + p.name) + ' vers le ' + c.date + ' s’il garde le rythme (+' + dec(c.gain) + ' pt par jour).', 'mv-down');
    if (!c && p.rank > 1) li((mine ? 'Tu rattrapes' : p.name + ' rattrape') + ' personne à ce rythme-là. Faut que ça débloque.');
    if (!c && p.rank === 1) li(mine ? 'Personne te rattrape à ce rythme-là.' : 'Personne rattrape ' + p.name + ' à ce rythme-là.', 'mv-up');
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
    var bar = el('div'); bar.style.cssText = 'display:flex;height:16px;border-radius:5px;overflow:hidden;background:var(--panel2);gap:2px';
    var leg = el('div'); leg.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px 14px;font-size:15px';
    top.forEach(function (x, i) {
      var sg = el('div'); sg.style.flex = String(x.pts); sg.style.background = p.color; sg.style.opacity = String(1 - i * .2); bar.appendChild(sg);
      var d = el('span', 'dot'); d.style.background = p.color; d.style.opacity = String(1 - i * .2);
      add(leg, add(el('span'), d, txt(last(x.player) + ' '), el('b', null, x.pct + ' %')));
    });
    if (rest > 0) { var o = el('div'); o.style.flex = String(rest); o.style.background = 'var(--mid)'; o.style.opacity = '.5'; bar.appendChild(o); add(leg, el('span', 'small', 'Autres ' + Math.round(100 * rest / p.total) + ' %')); }
    var lead = top[0], say = lead.pct >= 20 ? 'Sans ' + last(lead.player) + ', ça irait pas ben.' : lead.pct <= 12 ? 'Une équipe balancée : personne porte toute la charge.' : last(lead.player) + ' mène le bal.';
    return add(el('div', 'stack'), el('h2', null, 'Qui porte l’équipe'), add(el('div', 'panel lead'), bar, leg, el('p', 'small', say)));
  }
  // tonight: the game with the most pool players, and how many players each pooler has in action
  function tonightPanel() {
    var c = D.tonightClash, ld = P.map(function (p) { return { p: p, n: p.tonight.length }; }).filter(function (x) { return x.n; }).sort(function (a, b) { return b.n - a.n || (a.p.name < b.p.name ? -1 : 1); });
    if (!c && !ld.length) return null;
    var box = el('div', 'panel lead');
    add(box, el('div', 'kick', 'Ce soir · ' + M.gamesTonight + ' ' + plural(M.gamesTonight, 'partie', 'parties')));
    if (c) add(box, el('div', 't', 'La grosse partie : ' + c.game), el('p', 'small', c.time + ' · ' + c.players + ' joueurs du pool : ' + c.poolers.map(function (x) { return x.name + ' ' + x.n; }).join(', ')));
    if (ld.length) {
      var w = el('div'); w.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px';
      ld.forEach(function (x) { var t = el('span', 'tag', x.p.name + ' ' + x.n); if (known && x.p.id === me) { t.style.background = x.p.color; t.style.color = 'var(--ink)'; } w.appendChild(t); });
      add(box, el('div', 'small', 'Joueurs en action'), w);
    }
    return box;
  }

  // ---------------------------------------------------------------- tab: Accueil (sorted by priority)
  function home() {
    var s = el('div', 'stack');
    add(s, add(el('div', 'date'), el('div', 'd num', String(M.dayNumber)), add(el('div'), el('div', 'm', M.month), el('div', 'small', M.weekday + ' · résultats du ' + M.lastDayLabel))));
    add(s, livePanel());
    if (known) {
      var p = byId(me), mc = tap('button', 'panel mecard');
      add(mc, iniBox(p, true), add(el('div'), el('div', 'kick', 'Toi'), el('div', 'nm', p.name + ' · ' + ord(p.rank)), el('div', 'small', gapText(p) + ' · ' + p.total + ' pts · mon équipe')));
      mc.onclick = function () { openPooler(p.id); };
      add(s, mc, sincePanel(p));
    } else {
      var w = add(el('div', 'panel lead'), el('div', 't', 'T’es qui ?'), el('p', 'small', 'Choisis ton nom pour voir ta soirée pis ce qui a changé depuis ta dernière visite.'));
      var bw = el('button', 'btn main', 'Choisir mon nom ›'); bw.onclick = openWho; add(s, add(w, bw));
    }
    var hl = add(el('div', 'panel lead'), el('div', 't', D.headline.title), el('p', null, D.headline.text));
    if (D.tiles && D.tiles.length > 1) add(hl, el('div', 'small', D.tiles[0].value + ' ' + D.tiles[0].label + ' · ' + D.tiles[1].value + ' ' + D.tiles[1].label));
    add(s, hl, tonightPanel(), el('h2', null, 'Le podium'));
    var lb = el('div', 'panel rows'), mx = maxOf('total');
    P.slice(0, 3).forEach(function (p) { lb.appendChild(lbRow(p, 'total', mx)); });
    var all = el('button', 'link', 'Voir tout le classement ›'); all.onclick = function () { openTab('classement'); };
    add(s, lb, all);
    var rm = D.recentMoves || [];
    if (rm.length) {
      var seen = [], c = el('div', 'chips wrap');
      rm.forEach(function (m) { if (seen.indexOf(m.id) >= 0) return; seen.push(m.id); var b = el('button', 'chip', m.name + ' ›'); b.onclick = function () { openPooler(m.id, 'mouvements'); }; c.appendChild(b); });
      add(s, el('h2', null, 'Mouvements récents'), c);
    }
    add(s, installPanel());
    if (M.missingGames) add(s, el('p', 'alert', M.missingGames + ' partie(s) pas rentrée(s) : y manque peut-être des points.'));
    if (M.unresolved && M.unresolved.length) add(s, el('p', 'alert', 'Joueur non reconnu, points possiblement incomplets : ' + M.unresolved.join(', ') + '.'));
    add(s, el('p', 'small', 'Mis à jour le ' + M.updated + '.'));
    return s;
  }

  // ---------------------------------------------------------------- tab: Moi (Ma soirée)
  function mine() {
    var s = el('div', 'stack');
    if (!known) {
      add(s, el('h1', null, 'Ma soirée'), el('p', 'sub', 'Choisis ton nom pour voir ta soirée. C’est gardé dans ton téléphone, rien est envoyé.'),
        picker(function (id) { setMe(id); toast('Salut ' + byId(id).name + ' !'); render(); }));
      return s;
    }
    var p = byId(me), ch = el('button', 'link', 'Pas toi ? Changer ›'); ch.onclick = openWho;
    add(s, add(el('div', 'hero panel'), iniBox(p), add(el('div'), el('div', 'nm', p.name), el('div', 'small', ord(p.rank) + ' sur ' + P.length + ' · ' + gapText(p)))), ch);
    add(s, tiles(p), pacePanel(p, true));
    add(s, el('h2', null, 'Hier soir · +' + p.yday));
    var l = el('div', 'panel rows');
    if (p.scorers.length) p.scorers.forEach(function (x) { add(l, add(el('div', 'pl'), add(el('span'), el('div', 'nm', x.player), el('div', 'small', x.line)), add(el('span', 'pp'), el('span', 'num', String(x.pts))))); });
    else add(l, add(el('div', 'pl'), el('span', 'small', 'Personne a fait de points. Soirée ordinaire.')));
    add(s, l, el('h2', null, 'Ce soir · ' + (p.tonight.length ? p.tonight.length + ' ' + plural(p.tonight.length, 'joueur', 'joueurs') : 'aucun joueur')));
    if (p.tonight.length) {
      var more = 1 + P.filter(function (q) { return q.tonight.length > p.tonight.length; }).length;
      add(s, el('p', 'small', more === 1 ? 'Le plus gros alignement en action à soir. C’est ta soirée.' : ord(more) + ' plus gros alignement en action à soir.'));
    }
    if (D.tonightClash && D.tonightClash.poolers.some(function (x) { return x.id === p.id; })) {
      var c = D.tonightClash, foes = c.poolers.filter(function (x) { return x.id !== p.id; }).map(function (x) { return x.name; });
      if (foes.length) add(s, el('p', 'small', 'Grosse partie à soir (' + c.game + ') : t’affrontes ' + foes.join(', ') + '.'));
    }
    if (p.tonight.length) { var g = el('div', 'panel rows'); p.tonight.forEach(function (x) { add(g, add(el('div', 'pl'), add(el('span'), el('div', 'nm', x.player), el('div', 'small', x.game)), add(el('span', 'pp'), el('span', 'num', x.time)))); }); add(s, g); }
    var b = el('button', 'btn main', 'Mon équipe ›'); b.onclick = function () { openPooler(me); }; add(s, b);
    return s;
  }

  // ---------------------------------------------------------------- tab: Classement
  function race() {
    var s = el('div', 'stack');
    add(s, el('h1', null, 'Classement'), seg(KPI, raceKey, function (k) { raceKey = k; render(true); }, 'Trier le classement'));
    var mx = maxOf(raceKey), rows = P.slice().sort(function (a, b) { return a.kpi[raceKey].rank - b.kpi[raceKey].rank || (a.name < b.name ? -1 : 1); });
    var lb = el('div', 'panel rows'); rows.forEach(function (p) { lb.appendChild(lbRow(p, raceKey, mx)); });
    add(s, lb, el('p', 'small', 'Touche un pooler pour voir son équipe. Trait blanc : moyenne du pool. Projection sur ' + M.seasonGames + ' parties.'));
    return s;
  }

  // ---------------------------------------------------------------- screen: pooler profile with sub-tabs
  function profile() {
    var p = byId(route.a), sub = route.sub || 'resume', mineToo = known && p.id === me, s = el('div', 'stack');
    lastSub = sub;
    add(s, add(el('div', 'hero panel'), iniBox(p), add(el('div'), el('div', 'nm', p.name), el('div', 'small', ord(p.rank) + ' sur ' + P.length + ' · ' + gapText(p) + (mineToo ? ' · toi' : '')))));
    add(s, add(el('div', 'subtabs'), seg(SUBS, sub, function (k) { nav(Object.assign({}, route, { sub: k }), false); }, 'Sections du profil')));
    if (sub === 'resume') {
      add(s, tiles(p), pacePanel(p, mineToo), el('h2', null, 'Progression de la saison'), chartBlock([p.id]), carry(p));
    } else if (sub === 'alignement') {
      add(s, el('h2', null, 'Actifs · ' + p.team.length), seg([['pts', 'Points'], ['ppg', 'Pts/partie'], ['last7', '7 jours']], sortKey, function (k) { sortKey = k; render(true); }, 'Trier les joueurs'));
      var rows = p.team.slice().sort(function (a, b) { return (b[sortKey] || 0) - (a[sortKey] || 0) || b.pts - a.pts; });
      var l = el('div', 'panel rows');
      rows.forEach(function (r) {
        var right = add(el('span', 'pp'), el('span', 'num', String(r.pts)), el('span', 'small', r.last7 > 0 ? '+' + r.last7 + ' en 7 j' : ' '));
        if (r.last7 > 0) right.lastChild.style.color = 'var(--accent)';
        add(l, add(el('div', 'pl'), el('div', 'nm', r.player), right, el('div', 'small', r.team + ' · ' + r.pos + ' · ' + r.gp + ' PJ · ' + r.g + ' B · ' + r.a + ' A'), pctRow(r.pct, r.ppg)));
      });
      add(s, l, el('p', 'small', 'Barre : rang LNH en points par partie cette saison, parmi les joueurs à la même position (100 = le meilleur). Points du pool : seulement pendant qu’il appartient à ' + p.name + '.'));
      if (p.former.length) {
        var f = el('div', 'panel rows');
        p.former.forEach(function (r) {
          var after = r.after ? el('div', 'small mv-down', '+' + r.after + ' ' + plural(r.after, 'pt', 'pts') + ' depuis son départ' + (r.after >= 3 ? ' 😬' : '')) : null;
          add(f, add(el('div', 'pl'), el('div', 'nm', r.player), add(el('span', 'pp'), el('span', 'num', String(r.pts)), el('span', 'small', plural(r.pts, 'gardé', 'gardés'))), el('div', 'small', r.team + ' · ' + r.gp + ' PJ · jusqu’au ' + r.until), after));
        });
        add(s, el('h2', null, 'Partis'), f);
      }
    } else if (sub === 'duels') {
      add(s, nights(p, mineToo));
      var cmpBtn = el('button', 'btn', picking ? 'Choisis un pooler' : 'Comparer avec… ›'); cmpBtn.onclick = function () { picking = !picking; render(true); };
      add(s, cmpBtn);
      if (picking) add(s, chips(null, function (id) { openDuel(p.id, id); }, p.id, true));
    } else {
      var m = el('div', 'panel rows');
      if (p.moves.length) p.moves.forEach(function (x) {
        var what = x.out && x.in ? x.out + ' ➜ ' + x.in : (x.out ? x.out + ' retiré' : x.in + ' ajouté'), det = [];
        if (x.in) det.push(last(x.in) + ' ' + x.inPts + ' ' + plural(x.inPts, 'pt', 'pts') + ' ici');
        if (x.out && x.outAfter != null) det.push(last(x.out) + ' ' + x.outAfter + ' ailleurs');
        if (x.out) det.push(x.outPts + ' ' + plural(x.outPts, 'pt gardé', 'pts gardés'));
        add(m, add(el('div', 'mvr'), el('b', null, x.dateLabel), add(el('span'), add(el('div', 'nm wrapt'), txt(what + ' '), verdict(x)), el('div', 'small', det.join(' · ')))));
      });
      else add(m, add(el('div', 'mvr'), el('b', null, '–'), el('span', 'small', 'Pas de mouvement cette saison.')));
      add(s, el('h2', null, 'Mouvements'), m, el('p', 'small', 'Bon coup / Regret : points du nouveau joueur ici, contre les points de l’ancien depuis son départ.'));
    }
    return s;
  }
  // "Nuits gagnées": each night, more pool points than another pooler = a night won against them
  function nights(p, mineToo) {
    if (!p.h2h) return el('p', 'small', 'Pas encore de duels.');
    var box = el('div', 'stack'), opp = Object.keys(p.h2h).map(function (id) { return { q: byId(id), r: p.h2h[id], s: p.h2hStreak[id] }; }).filter(function (o) { return o.q; });
    if (!opp.length) return null;
    var tot = opp.reduce(function (a, o) { return [a[0] + o.r[0], a[1] + o.r[1], a[2] + o.r[2]]; }, [0, 0, 0]);
    opp.sort(function (a, b) { return (b.r[0] - b.r[1]) - (a.r[0] - a.r[1]) || (a.q.name < b.q.name ? -1 : 1); });
    var vic = opp[0], bete = opp[opp.length - 1], t = el('div', 'tiles');
    function who(label, o, good) {
      var b = tap('button', 'panel tile'), v = el('div', 'v num', o.q.name); v.style.fontSize = '30px';
      add(b, el('div', 'l', label), v, el('div', 'r ' + (good ? 'mv-up' : 'mv-down'), wlt(o.r) + ' contre lui'));
      b.onclick = function () { openDuel(p.id, o.q.id); }; return b;
    }
    if (vic.r[0] > vic.r[1]) t.appendChild(who(mineToo ? 'Ta victime' : 'Sa victime', vic, true));
    if (bete !== vic && bete.r[1] > bete.r[0]) t.appendChild(who(mineToo ? 'Ta bête noire' : 'Sa bête noire', bete, false));
    add(box, el('h2', null, 'Nuits gagnées · ' + wlt(tot)), el('p', 'small', 'Une nuit gagnée = plus de points que l’autre ce soir-là.'));
    if (t.childNodes.length) add(box, t);
    var l = el('div', 'panel rows');
    opp.forEach(function (o) {
      var st = Math.abs(o.s) >= 2 ? el('div', 'small ' + (o.s > 0 ? 'mv-up' : 'mv-down'), (o.s > 0 ? 'Gagne ' : 'Perd ') + Math.abs(o.s) + ' soirs de suite') : el('div', 'small', o.s > 0 ? 'A gagné hier' : o.s < 0 ? 'A perdu hier' : 'Égalité hier');
      var r = add(tap('button', 'pl'), add(el('span'), el('div', 'nm', 'Contre ' + o.q.name), st), add(el('span', 'pp'), el('span', 'num', wlt(o.r))));
      r.onclick = function () { openDuel(p.id, o.q.id); };
      l.appendChild(r);
    });
    return add(box, l);
  }

  // ---------------------------------------------------------------- screen: duel
  function duel() {
    var s = el('div', 'stack'), a = byId(route.a), b = byId(route.b);
    var head = el('div', 'panel duel');
    function side(p, cls) { var n = tap('button', 'nm ' + cls), d = el('span', 'dot'); d.style.background = p.color; add(n, d, txt(p.name)); n.style.fontWeight = 700; n.onclick = function () { openPooler(p.id); }; return n; }
    add(head, side(a, 'a'), el('div', 'mid', 'contre'), side(b, ''));
    add(s, head);
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
    function best(p) { return p.team.length ? last(p.team[0].player) + ' (' + p.team[0].pts + ')' : '–'; }
    add(rows, add(el('div', 'duel'), el('div', 'a small', best(a)), el('div', 'mid', 'Meilleur'), el('div', 'small', best(b))));
    var st = a.h2hStreak && a.h2hStreak[b.id];
    if (st && Math.abs(st) >= 2) add(rows, add(el('div', 'duel'), el('div', 'a small', ''), el('div', 'mid', 'Série'), el('div', 'small', (st > 0 ? a.name : b.name) + ' gagne ' + Math.abs(st) + ' soirs de suite')));
    add(s, rows, el('h2', null, 'Progression'), chartBlock([a.id, b.id]));
    add(s, el('h2', null, 'Changer d’adversaire'), chips(b.id, function (id) { nav(Object.assign({}, route, { b: id }), false); }, a.id, true));
    return s;
  }

  // ---------------------------------------------------------------- tab: Marché
  function market() {
    var s = el('div', 'stack');
    add(s, el('h1', null, 'Waivers'), el('h2', null, 'Agents libres'), el('p', 'sub', 'Les meilleurs joueurs de la semaine que personne a pris.'));
    var l = el('div', 'panel rows');
    if (D.deals.length) D.deals.forEach(function (d) { add(l, add(el('div', 'pl'), el('div', 'nm', d.player), add(el('span', 'pp'), el('span', 'num', '+' + d.pts), el('span', 'small', '7 derniers jours')), el('div', 'small', d.meta), pctRow(d.pct, null))); });
    else add(l, add(el('div', 'pl'), el('span', 'small', 'Pas encore assez de parties.')));
    add(s, l);
    if (D.cold.length) {
      var c = el('div', 'panel rows');
      D.cold.forEach(function (x) {
        var o = byName(x.owner), r = o ? tap('button', 'pl') : el('div', 'pl');
        add(r, el('div', 'nm', x.player), add(el('span', 'pp'), el('span', 'small', x.line)), el('div', 'small', 'chez ' + x.owner));
        if (o) r.onclick = function () { openPooler(o.id, 'alignement'); };
        c.appendChild(r);
      });
      add(s, el('h2', null, 'En panne sèche'), c);
    }
    var T = D.trades || [];
    if (T.length) {
      var tl = el('div', 'panel rows');
      T.forEach(function (t) {
        var r = tap('button', 'trade'), n = el('span', 'num ' + (t.diff > 0 ? 'mv-up' : t.diff < 0 ? 'mv-down' : ''), (t.diff > 0 ? '+' : '') + t.diff);
        var tag = el('span', 'tag ' + (t.diff > 0 ? 'good' : t.diff < 0 ? 'bad' : ''), t.tag);
        add(r, add(el('div'), add(el('div', 'small'), tag, txt(' ' + t.name + ' · ' + t.dateLabel)), el('div', 'nm', last(t.out) + ' ➜ ' + last(t.in))), n,
          el('div', 'small', last(t.in) + ' ' + t.inPts + ' ' + plural(t.inPts, 'pt', 'pts') + ' depuis · ' + last(t.out) + ' ' + t.outAfter + ' ailleurs'));
        r.onclick = function () { openPooler(t.id, 'mouvements'); };
        tl.appendChild(r);
      });
      add(s, el('h2', null, 'Bons coups et regrets'), tl, el('p', 'small', 'Chaque échange jugé sur ce que les deux joueurs ont fait depuis.'));
    }
    return s;
  }

  // ---------------------------------------------------------------- tab: Prix
  function prizes() {
    var s = el('div', 'stack');
    add(s, el('h1', null, 'Les prix'));
    if (D.awards.length) { var l = el('div', 'panel rows'); D.awards.forEach(function (a) { add(l, add(el('div', 'award'), add(el('span'), el('div', 'small', a.label), el('div', 'w', a.winner)), el('span', 'd', a.detail))); }); add(s, el('h2', null, 'Prix du jour'), l); }
    var R = D.records || [];
    if (R.length) {
      var rl = el('div', 'panel rows');
      R.forEach(function (x) {
        var r = tap('button', 'trade'), lab = add(el('div', 'small'), txt(x.label + ' '), x.new ? el('span', 'tag good', 'Nouveau record') : null);
        add(r, add(el('div'), lab, el('div', 'nm wrapt', x.text)), el('span', 'num', String(x.value)));
        r.onclick = function () { openPooler(x.who); };
        rl.appendChild(r);
      });
      add(s, el('h2', null, 'Records de la saison'), rl);
    }
    var dep = P.map(function (p) { var x = shares(p)[0]; return x && { p: p, x: x }; }).filter(Boolean).sort(function (a, b) { return b.x.pct - a.x.pct; })[0];
    if (dep) {
      var dr = tap('button', 'trade'); dr.onclick = function () { openPooler(dep.p.id); };
      add(dr, add(el('div'), el('div', 'small', 'Le plus dépendant'), el('div', 'nm wrapt', dep.p.name + ' : ' + last(dep.x.player) + ' fait ' + dep.x.pct + ' % de ses points')), el('span', 'num', dep.x.pct + ' %'));
      add(s, add(el('div', 'panel rows'), dr));
    }
    if (D.chatter.length) {
      var c = el('div', 'panel rows');
      D.chatter.forEach(function (x) {
        var o = x.name && byName(x.name), r = o ? tap('button', 'pl') : el('div', 'pl');
        add(r, add(el('div'), el('div', 'small ' + (x.good ? 'mv-up' : 'mv-down'), x.tag), el('div', 'wrapt', x.text)));
        if (o) r.onclick = function () { openPooler(o.id); };
        c.appendChild(r);
      });
      add(s, el('h2', null, 'La jasette'), c);
    }
    var b = el('button', 'btn', 'Copier le résumé');
    b.onclick = function () {
      function done(ok) { b.textContent = ok ? 'Copié' : 'Copie impossible'; }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(D.summary).then(function () { done(true); }, function () { done(false); }); else done(false);
    };
    add(s, b);
    return s;
  }

  // ---------------------------------------------------------------- frame: top bar, tab bar, render
  function drawTop() {
    var top = document.getElementById('top'); top.textContent = '';
    if (!route.screen || route.screen === 'qui' && !route.depth) {
      add(top, add(el('span', 'brand'), txt('Pool '), el('b', null, 'LNH'), txt(' · Analyse')), el('span', 'when', M.weekday + ' ' + M.dayNumber));
      return;
    }
    var back = el('button', 'back', '‹ Retour'); back.onclick = goBack; back.setAttribute('aria-label', 'Retour');
    var title = '', val = null;
    if (route.screen === 'pooler') { var p = byId(route.a); title = p.name; val = el('span', 'val num', String(p.total)); }
    else if (route.screen === 'duel') title = 'Duel';
    else if (route.screen === 'direct') title = 'En direct';
    else if (route.screen === 'qui') title = 'T’es qui ?';
    add(top, back, el('span', 'ttl', title), val);
  }
  function drawTabs() {
    var nav_ = document.getElementById('tabs'); nav_.textContent = '';
    nav_.hidden = route.screen === 'qui' && !route.depth;               // first visit: the welcome screen gets the whole page
    var ns = 'http://www.w3.org/2000/svg';
    TABS.forEach(function (t) {
      var b = el('button'), svg = document.createElementNS(ns, 'svg'), path = document.createElementNS(ns, 'path');
      svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true'); path.setAttribute('d', t[2]); svg.appendChild(path);
      add(b, svg, el('span', null, t[1]));
      if (route.tab === t[0]) b.setAttribute('aria-current', 'page');
      if (t[0] === 'accueil' && liveOn() && !D.live.allDone) { var bd = el('span', 'badge'); bd.title = 'En direct'; b.appendChild(bd); }
      b.onclick = function () { if (route.tab === t[0] && !route.screen) { card().scrollTop = 0; return; } openTab(t[0]); };
      nav_.appendChild(b);
    });
  }
  function view() {
    if (route.screen === 'qui') return welcome();
    if (route.screen === 'pooler' && byId(route.a)) return profile();
    if (route.screen === 'duel' && byId(route.a) && byId(route.b)) return duel();
    if (route.screen === 'direct' && liveOn()) return liveView();
    return { accueil: home, moi: mine, classement: race, marche: market, prix: prizes }[route.tab || 'accueil']();
  }
  // The tab bar and the top bar are drawn first and a failing section is caught: navigation can never disappear.
  function render(keep) {
    var c = card(), sc = keep ? c.scrollTop : (route.scroll || 0), content;
    try { drawTabs(); } catch (e) {}
    try { drawTop(); } catch (e) {}
    try { content = view(); } catch (e) {
      content = add(el('div', 'stack'), el('h1', null, 'Oups'), el('p', 'sub', 'Cette section a pas voulu s’afficher. Les autres onglets marchent.'), el('p', 'small', String(e && e.message || e)));
      var home_ = el('button', 'btn main', 'Retour à l’accueil'); home_.onclick = function () { openTab('accueil'); }; content.appendChild(home_);
    }
    c.className = 'card' + (keep ? '' : ' in'); c.textContent = ''; c.appendChild(content);
    c.scrollTop = sc; route.scroll = 0;
    try { document.title = 'Pool LNH : ' + (route.screen === 'pooler' ? byId(route.a).name : TABS.filter(function (t) { return t[0] === route.tab; })[0][1].toLowerCase()); } catch (e) {}
  }

  // ---------------------------------------------------------------- start
  var ids = P.map(function (p) { return p.id; }), want = null;
  try { want = new URLSearchParams(location.search).get('p'); } catch (e) {}
  if (ids.indexOf(want) < 0) want = getRaw('pool.me');               // a ?p= link shows that pooler but is never saved
  known = ids.indexOf(want) >= 0;
  me = known ? want : ids[0];
  spectator = getRaw('pool.spectator') === '1';
  route = parse(location.hash);
  if (!known && !spectator && !route.screen) route = { tab: route.tab, screen: 'qui', from: route.tab };
  route.depth = 0;
  try { history.replaceState(route, '', hashOf(route)); } catch (e) {}
  window.addEventListener && window.addEventListener('popstate', function (e) {
    route = (e.state && e.state.tab) ? e.state : parse(location.hash);
    if (route.depth == null) route.depth = 0;
    picking = false; render();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && route.screen) goBack(); });
  if (D.live) { refreshLive(); setInterval(refreshLive, 120000); document.addEventListener('visibilitychange', refreshLive); }

  // New report deployed? Phones keep the installed app in memory and never reload it by themselves:
  // check version.json when the app comes back on screen (reload right away) and every 2 min while it is open
  // (reload only when idle on Accueil / En direct, so nobody loses their spot mid-scroll).
  var lastTouch = 0;
  ['touchstart', 'scroll', 'keydown', 'click'].forEach(function (ev) {
    document.addEventListener(ev, function () { lastTouch = Date.now(); }, { passive: true, capture: true });
  });
  function checkVersion(resume) {
    if (!M.build || !window.fetch || document.visibilityState === 'hidden') return;
    fetch('version.json?t=' + Date.now(), { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (v) {
      if (!v || !v.build || String(v.build) <= String(M.build)) return;
      if (!resume && (Date.now() - lastTouch < 30000 || (route.screen && route.screen !== 'direct'))) return;
      try {
        var q = new URLSearchParams(location.search); q.set('v', v.build);   // new URL: skips the 10-min HTTP cache
        location.replace(location.pathname + '?' + q.toString() + location.hash);
      } catch (e) { location.reload(); }
    }, function () {});
  }
  document.addEventListener('visibilitychange', function () { checkVersion(true); });
  window.addEventListener && window.addEventListener('pageshow', function (e) { if (e.persisted) checkVersion(true); });
  window.addEventListener && window.addEventListener('focus', function () { checkVersion(true); });
  setInterval(function () { checkVersion(false); }, 120000);
  checkVersion(true);
  document.getElementById('demo').hidden = !M.demo;
  render();
})();
</script>
</body>
</html>
"""


def render_edge(data):
    return TEMPLATE.replace("__FONTS__", FONT_CSS).replace("__DATA__", _embed(data))
