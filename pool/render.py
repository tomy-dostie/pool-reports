"""Turns the report data into one self-contained mobile web page (swipeable cards, French)."""
import json
import os
import shutil

TEMPLATE = r"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0B1020">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<title>Pool de la LNH : rapport du jour</title>
<style>
__FONTS__
:root{--bg:#0B1020;--surface:#141B2E;--line:#232C45;--text:#F2F6FF;--muted:#98A4C2;--accent:#D6F0FF;--warm:#FF8A6B;--ink:#0B1020}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:'Barlow',system-ui,sans-serif;-webkit-text-size-adjust:100%}
button{font:inherit;color:inherit;border:0;background:transparent;padding:0;cursor:pointer;text-align:center}
button:focus-visible{outline:2px solid var(--text);outline-offset:2px}
.app{height:100vh;height:100dvh;max-width:480px;margin:0 auto;padding:20px 16px calc(20px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:16px}
.progress{display:flex;gap:6px}.progress span{flex:1;height:4px;border-radius:2px;background:var(--line)}.progress span.on{background:var(--accent)}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.kicker{font:700 14px 'Barlow Condensed',sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.badge{font:700 12px 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--warm);border:1px solid var(--warm);border-radius:999px;padding:3px 10px;white-space:nowrap}
.card{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain;outline:none}
.card.enter-next{animation:inr .22s ease-out}.card.enter-prev{animation:inl .22s ease-out}
@keyframes inr{from{opacity:0;transform:translateX(28px)}to{opacity:1;transform:none}}
@keyframes inl{from{opacity:0;transform:translateX(-28px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.card.enter-next,.card.enter-prev{animation:none}}
.stack{display:flex;flex-direction:column;gap:14px;min-height:100%}
.h1{margin:0;font:800 48px/.92 'Barlow Condensed',sans-serif;text-transform:uppercase}.h1.sm{font-size:36px}
.demo{background:var(--warm);color:var(--ink);font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase;text-align:center;border-radius:10px;padding:6px 10px}
.alert{font-size:13px;line-height:1.4;color:var(--warm);margin:0}
.sub{font-size:15px;line-height:1.4;color:var(--muted);margin:0}
.label{font:700 14px 'Barlow Condensed',sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.big{font:800 150px/.8 'Barlow Condensed',sans-serif}
.month{font:800 54px/.9 'Barlow Condensed',sans-serif;text-transform:uppercase;color:var(--accent)}
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.tile{background:var(--surface);border-radius:16px;padding:14px 12px;display:flex;flex-direction:column;gap:4px}
.tile b{font:800 40px/1 'Barlow Condensed',sans-serif}.tile span{font-size:13px;color:var(--muted)}
.hero{background:var(--accent);color:var(--ink);border-radius:22px;padding:20px;display:flex;flex-direction:column;gap:8px}
.hero .t{font:800 46px/.95 'Barlow Condensed',sans-serif;text-transform:uppercase}.hero p{margin:0;font-size:16px;line-height:1.4;font-weight:500}
.spacer{flex:1}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{flex:none;min-height:44px;padding:0 14px;border-radius:12px;background:var(--surface);font-size:16px;font-weight:600}
.chip[aria-pressed=true]{color:var(--ink)}
.row{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.hr{border-top:1px solid var(--line);padding-top:12px}
.val{font:800 40px/1 'Barlow Condensed',sans-serif}
.small{font-size:13px;color:var(--muted)}
.pts{font:700 20px 'Barlow Condensed',sans-serif;min-width:18px;text-align:right}
.name{font-size:16px;font-weight:600}
.pill{background:var(--surface);border-radius:14px;padding:10px 14px;display:grid;grid-template-columns:1fr auto;align-items:center;gap:12px}
.pill .time{font:700 20px 'Barlow Condensed',sans-serif}
.list{background:var(--surface);border-radius:18px;overflow:hidden}
.list>*{border-top:1px solid var(--line)}.list>*:first-child{border-top:0}
.race{display:grid;grid-template-columns:26px 36px minmax(0,1fr) 76px 62px;align-items:center;gap:10px;padding:6px 12px}.race .ini{width:36px;height:36px;font-size:16px}
.rk{display:flex;flex-direction:column;align-items:center;font:800 24px/1 'Barlow Condensed',sans-serif}
.rk i{font:600 11px 'Barlow',sans-serif;font-style:normal}
.up{color:var(--accent)}.down{color:var(--warm)}.flat{color:var(--muted)}
.ini{width:40px;height:40px;border-radius:12px;color:var(--ink);display:flex;align-items:center;justify-content:center;font:800 18px 'Barlow Condensed',sans-serif}
.tot{display:flex;flex-direction:column;align-items:flex-end;font:700 28px/1 'Barlow Condensed',sans-serif}.tot span{font:400 11px 'Barlow',sans-serif;color:var(--muted)}
.deal{display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:12px;padding:10px 14px}
.deal .n{font:700 18px 'Barlow Condensed',sans-serif;color:var(--muted)}.deal .p{font:800 30px/1 'Barlow Condensed',sans-serif;color:var(--accent)}
.cold{display:grid;grid-template-columns:8px 1fr auto;align-items:center;gap:12px;background:var(--surface);border-radius:14px;padding:10px 14px}
.cold .bar{width:8px;height:32px;border-radius:4px}.cold b{font-size:13px;color:var(--warm);font-weight:600;text-align:right}
.award{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px}
.award .w{font:800 28px/1 'Barlow Condensed',sans-serif;text-transform:uppercase}.award .d{font-size:15px;font-weight:600;text-align:right;color:var(--accent)}
.talk{display:grid;grid-template-columns:40px 1fr;gap:12px;align-items:start}
.talk .tag{font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.14em;text-transform:uppercase}.talk p{margin:3px 0 0;font-size:16px;line-height:1.35}
.pl{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:12px;padding:9px 14px}
.pl .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pl .p{display:flex;flex-direction:column;align-items:flex-end;font:800 28px/1 'Barlow Condensed',sans-serif}.pl .p span{font:600 12px 'Barlow',sans-serif;color:var(--muted)}
.mv{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;align-items:baseline;padding:10px 14px}
.mv b{font:700 16px 'Barlow Condensed',sans-serif;color:var(--muted);text-transform:uppercase}
.race{width:100%;text-align:left}
.link{text-align:left;font-size:15px;color:var(--accent);text-decoration:underline;text-underline-offset:3px;min-height:44px}
.copy{height:48px;border-radius:14px;background:var(--surface);font:700 16px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase}
.nav{display:grid;grid-template-columns:1fr 2fr;gap:10px}
.nav button{height:52px;border-radius:16px;font:700 18px 'Barlow Condensed',sans-serif;letter-spacing:.1em;text-transform:uppercase}
#prev{background:var(--surface)}#prev:disabled{color:#4A5A85}#next{background:var(--accent);color:var(--ink);font-weight:800;font-size:20px}
</style>
</head>
<body>
<div class="app">
  <div class="progress" id="progress" aria-hidden="true"></div>
  <div class="demo" id="demo" hidden>Aperçu : chiffres inventés, ce ne sont pas les vrais résultats</div>
  <div class="top"><span class="kicker" id="kicker"></span><span class="badge" id="badge" hidden>Données fictives</span></div>
  <main class="card" id="card" tabindex="-1"></main>
  <nav class="nav"><button id="prev" aria-label="Page précédente">Retour</button><button id="next" aria-label="Page suivante">Suivant</button></nav>
</div>
<script>
window.DATA = __DATA__;
(function () {
  var D = window.DATA, M = D.meta;
  var KICKERS = ['Hier en bref', 'Ma soirée', 'Classement', 'Agents libres', 'Les prix du jour'];
  var RACE = 2, detail = null;   // detail = id of the pooler whose team is open over the standings
  var idx = 0, me = null;

  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function add(parent) { for (var i = 1; i < arguments.length; i++) if (arguments[i]) parent.appendChild(arguments[i]); return parent; }
  function plural(n, one, many) { return Math.abs(n) <= 1 ? one : many; }

  function pickMe() {
    var ids = D.poolers.map(function (p) { return p.id; }), want = null;
    try { want = new URLSearchParams(location.search).get('p'); } catch (e) {}
    if (ids.indexOf(want) < 0) { try { want = localStorage.getItem('pool.me'); } catch (e) { want = null; } }
    me = ids.indexOf(want) >= 0 ? want : ids[0];
  }

  function spark(values, color) {
    var ns = 'http://www.w3.org/2000/svg', w = 76, h = 32, svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('width', w); svg.setAttribute('height', h); svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    svg.setAttribute('role', 'img');
    if (values.length > 1) {
      var lo = Math.min.apply(null, values), hi = Math.max.apply(null, values), span = Math.max(1, hi - lo);
      var d = values.map(function (v, i) { return (i ? 'L' : 'M') + (2 + i / (values.length - 1) * (w - 4)).toFixed(1) + ' ' + (h - 3 - (v - lo) / span * (h - 6)).toFixed(1); }).join(' ');
      var path = document.createElementNS(ns, 'path');
      path.setAttribute('d', d); path.setAttribute('fill', 'none'); path.setAttribute('stroke', color);
      path.setAttribute('stroke-width', '2.5'); path.setAttribute('stroke-linecap', 'round'); path.setAttribute('stroke-linejoin', 'round');
      svg.appendChild(path);
    }
    svg.setAttribute('aria-label', 'Progression sur les derniers matchs, de ' + values[0] + ' à ' + values[values.length - 1] + ' points');
    return svg;
  }

  function cover() {
    var s = el('div', 'stack');
    add(s, add(el('div'), el('div', 'big', String(M.dayNumber)), el('div', 'month', M.month)),
      el('p', 'sub', M.weekday.charAt(0).toUpperCase() + M.weekday.slice(1) + '. ' + 'Résultats du ' + M.lastDayLabel + '.'));
    var tiles = el('div', 'tiles');
    D.tiles.forEach(function (t) { add(tiles, add(el('div', 'tile'), el('b', null, t.value), el('span', null, t.label))); });
    var hero = add(el('div', 'hero'), el('div', 'label', 'La une'), el('div', 't', D.headline.title), el('p', null, D.headline.text));
    hero.querySelector('.label').style.color = 'inherit';
    add(s, el('div', 'spacer'), tiles, hero, el('p', 'small', 'Mis à jour le ' + M.updated + '.'));
    if (M.missingGames) add(s, el('p', 'alert', 'Attention : ' + M.missingGames + ' match(s) n\u2019ont pas pu être chargés. Les points sont possiblement incomplets, réessaie plus tard.'));
    if (M.unresolved && M.unresolved.length) add(s, el('p', 'alert', 'Attention : joueur non reconnu, points possiblement incomplets : ' + M.unresolved.join(', ') + '.'));
    var rm = D.recentMoves || [];
    if (rm.length) {
      var names = [];
      rm.forEach(function (m) { if (names.indexOf(m.name) < 0) names.push(m.name); });
      var b = el('button', 'link', 'Mouvements récents : ' + names.join(', '));
      b.onclick = function () { openTeam(rm[0].id); };
      add(s, b);
    }
    return s;
  }

  function setMe(id) { me = id; try { localStorage.setItem('pool.me', me); } catch (e) {} }
  function openTeam(id) { var d = RACE >= idx ? 1 : -1; detail = id; idx = RACE; show(d); }
  function closeTeam() { detail = null; show(-1); }
  function byId(id) { return D.poolers.filter(function (x) { return x.id === id; })[0]; }
  function current() { return byId(me); }
  function poolerChips() {
    var chips = el('div', 'chips');
    D.poolers.forEach(function (p) {
      var b = el('button', 'chip', p.name);
      var on = p.id === me;
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      if (on) b.style.background = p.color;
      b.onclick = function () { setMe(p.id); show(0, true); };
      chips.appendChild(b);
    });
    return chips;
  }
  function ordinal(n) { return n === 1 ? '1er' : n + 'e'; }
  function pts(n) { return n + ' ' + plural(n, 'pt', 'pts'); }

  function team() {
    var s = el('div', 'stack'), p = byId(detail);
    var back = el('button', 'link', '← Classement');
    back.onclick = closeTeam;
    var ini = el('div', 'ini', p.initials); ini.style.background = p.color;
    var head = add(el('div', 'race'), add(el('div', 'rk'), document.createTextNode(String(p.rank))), ini,
      add(el('div'), el('div', 'name', p.name), el('div', 'small', p.rank === 1 ? 'Au sommet' : 'à ' + p.gap + ' du 1er')), el('span'),
      add(el('div', 'tot', String(p.total)), el('span', null, p.proj + ' prévus')));
    add(s, back, el('h1', 'h1 sm', 'L’alignement'), head);
    var list = el('div', 'list');
    (p.team || []).forEach(function (r) {
      var stats = r.team + ' · ' + r.pos + ' · ' + r.gp + ' PJ · ' + r.g + ' B · ' + r.a + ' A';
      var right = add(el('span', 'p', String(r.pts)), el('span', null, r.last7 > 0 ? '+' + r.last7 + ' en 7 j' : ' '));
      if (r.last7 > 0) right.lastChild.style.color = p.color;
      add(list, add(el('div', 'pl'), add(el('span'), el('div', 'name', r.player), el('div', 'small', stats)), right));
    });
    add(s, el('div', 'label', 'Actifs'), list);
    if (p.former && p.former.length) {
      var fl = el('div', 'list');
      p.former.forEach(function (r) {
        add(fl, add(el('div', 'pl'), add(el('span'), el('div', 'name', r.player), el('div', 'small', r.team + ' · ' + r.gp + ' PJ · jusqu’au ' + r.until)),
          add(el('span', 'p', String(r.pts)), el('span', null, plural(r.pts, 'gardé', 'gardés')))));
      });
      add(s, el('div', 'label', 'Partis'), el('p', 'small', 'Les points amassés avant leur départ restent au pooler.'), fl);
    }
    var ml = el('div', 'list');
    if (p.moves && p.moves.length) p.moves.forEach(function (m) {
      var what = m.out && m.in ? m.out + ' ➜ ' + m.in : (m.out ? m.out + ' retiré' : m.in + ' ajouté');
      var detail = [];
      if (m.out) detail.push(pts(m.outPts) + ' ' + plural(m.outPts, 'gardé', 'gardés'));
      if (m.in) detail.push(pts(m.inPts) + ' depuis');
      add(ml, add(el('div', 'mv'), el('b', null, m.dateLabel), add(el('span'), el('div', 'name', what), el('div', 'small', detail.join(' · ')))));
    });
    else add(ml, add(el('div', 'mv'), el('b', null, '–'), el('span', 'small', 'Aucun mouvement depuis le début de la saison.')));
    add(s, el('div', 'label', 'Mouvements'), ml);
    return s;
  }

  function mine() {
    var s = el('div', 'stack');
    var p = current();
    add(s, el('h1', 'h1', 'Ma soirée'), poolerChips());
    var y = add(el('div', 'row hr'), el('span', 'label', 'Hier soir'), el('span', 'val', '+' + p.yday));
    y.lastChild.style.color = p.color;
    add(s, y);
    if (p.scorers.length) {
      var more = p.scorers.slice(5), shown = p.scorers.slice(0, 5);
      shown.forEach(function (sc) { add(s, add(el('div', 'row'), el('span', 'name', sc.player), add(el('span', 'row'), el('span', 'small', sc.line), el('span', 'pts', String(sc.pts))))); });
      if (more.length) { var extra = more.reduce(function (n, x) { return n + x.pts; }, 0); add(s, el('p', 'small', '+ ' + more.length + ' ' + plural(more.length, 'autre joueur', 'autres joueurs') + ' (' + extra + ' ' + plural(extra, 'pt', 'pts') + ')')); }
    } else add(s, el('p', 'sub', 'Personne n’a pointé. Soirée difficile.'));
    add(s, add(el('div', 'row hr'), el('span', 'label', 'Ce soir'), el('span', 'small', p.tonight.length ? p.tonight.length + ' ' + plural(p.tonight.length, 'joueur', 'joueurs') + ' en action' : 'Aucun joueur en action')));
    p.tonight.forEach(function (t) {
      var time = el('span', 'time', t.time); time.style.color = p.color;
      add(s, add(el('div', 'pill'), add(el('span'), el('div', 'name', t.player), el('div', 'small', t.game)), time));
    });
    return s;
  }

  function race() {
    var s = el('div', 'stack'), list = el('div', 'list');
    add(s, el('h1', 'h1 sm', 'La course au titre'));
    D.poolers.forEach(function (p) {
      var r = el('button', 'race');
      r.setAttribute('aria-label', p.name + ', ' + ordinal(p.rank) + ', ' + pts(p.total) + '. Voir l’alignement');
      r.onclick = function () { openTeam(p.id); };
      var rk = add(el('div', 'rk', null), document.createTextNode(String(p.rank)));
      var mv = el('i', p.move > 0 ? 'up' : (p.move < 0 ? 'down' : 'flat'), p.move > 0 ? '▲' + p.move : (p.move < 0 ? '▼' + Math.abs(p.move) : '–'));
      rk.appendChild(mv);
      var ini = el('div', 'ini', p.initials); ini.style.background = p.color;
      var nm = add(el('div'), el('div', 'name', p.name), el('div', 'small', p.rank === 1 ? 'Au sommet' : 'à ' + p.gap + ' du 1er'));
      var tot = add(el('div', 'tot', String(p.total)), el('span', null, p.proj + ' prévus'));
      add(r, rk, ini, nm, spark(p.spark, p.color), tot);
      list.appendChild(r);
    });
    add(s, list, el('p', 'small', 'Touche un pooler pour voir son alignement, ses joueurs partis et ses mouvements.'), el('p', 'small', 'Courbes :derniers jours de match. Prévisions : total actuel projeté sur ' + M.seasonGames + ' matchs, donc approximatives en début de saison.'));
    return s;
  }

  function deals() {
    var s = el('div', 'stack');
    add(s, el('h1', 'h1', 'Chasse aux aubaines'), el('p', 'sub', 'Les meilleurs joueurs de la semaine que personne n’a dans le pool.'));
    var list = el('div', 'list');
    if (D.deals.length) D.deals.forEach(function (d, i) {
      add(list, add(el('div', 'deal'), el('span', 'n', String(i + 1)),
        add(el('span'), el('div', 'name', d.player), el('div', 'small', d.meta)), el('span', 'p', String(d.pts))));
    });
    else add(list, add(el('div', 'deal'), el('span'), el('span', 'small', 'Pas encore assez de matchs.'), el('span')));
    add(s, list);
    if (D.cold.length) {
      add(s, el('div', 'label', 'Sur la glace mince'));
      D.cold.forEach(function (c) {
        var owner = D.poolers.filter(function (p) { return p.name === c.owner; })[0];
        var bar = el('span', 'bar'); bar.style.background = owner ? owner.color : 'var(--muted)';
        add(s, add(el('div', 'cold'), bar, add(el('span'), el('div', 'name', c.player), el('div', 'small', c.owner)), el('b', null, c.line)));
      });
    }
    return s;
  }

  function prizes() {
    var s = el('div', 'stack');
    add(s, el('h1', 'h1', 'Les prix du jour'));
    if (D.awards.length) {
      var list = el('div', 'list');
      D.awards.forEach(function (a) { add(list, add(el('div', 'award'), add(el('span'), el('div', 'label', a.label), el('div', 'w', a.winner)), el('span', 'd', a.detail))); });
      add(s, list);
    }
    if (D.chatter.length) {
      add(s, el('div', 'label', 'La jasette'));
      D.chatter.forEach(function (c) {
        var ini = el('div', 'ini', c.name.slice(0, 2).toUpperCase()); ini.style.background = c.color;
        var tag = el('div', 'tag', c.tag); tag.className += c.good ? ' up' : ' down';
        add(s, add(el('div', 'talk'), ini, add(el('div'), tag, el('p', null, c.text))));
      });
    }
    var b = el('button', 'copy', 'Copier le résumé');
    b.onclick = function () {
      function done(ok) { b.textContent = ok ? 'Copié' : 'Copie impossible'; }
      function fallback() { var t = document.createElement('textarea'); t.value = D.summary; document.body.appendChild(t); t.select(); var ok = false; try { ok = document.execCommand('copy'); } catch (e) {} t.remove(); done(ok); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(D.summary).then(function () { done(true); }, fallback); else fallback();
    };
    add(s, el('div', 'spacer'), b);
    return s;
  }

  var BUILD = [cover, mine, race, deals, prizes];

  function show(dir, keep) {
    var card = document.getElementById('card');
    card.className = 'card' + (dir && !keep ? ' enter-' + (dir > 0 ? 'next' : 'prev') : '');
    var scroll = keep ? card.scrollTop : 0;
    card.textContent = '';
    card.appendChild(detail && idx === RACE ? team() : BUILD[idx]());
    card.scrollTop = scroll;
    document.getElementById('kicker').textContent = KICKERS[idx];
    var pr = document.getElementById('progress'); pr.textContent = '';
    BUILD.forEach(function (_, i) { var sp = el('span', i <= idx ? 'on' : ''); pr.appendChild(sp); });
    document.getElementById('prev').disabled = idx === 0;
    document.getElementById('next').textContent = idx === BUILD.length - 1 ? 'Recommencer' : 'Suivant';
  }
  function go(step) {
    if (detail) { if (step < 0) return closeTeam(); detail = null; }
    var n = idx + step; if (n >= BUILD.length) n = 0; if (n < 0) return; var d = n > idx ? 1 : -1; idx = n; show(n === 0 && step > 0 ? -1 : d); }

  pickMe();
  document.getElementById('badge').hidden = !M.demo;
  document.getElementById('demo').hidden = !M.demo;
  document.getElementById('prev').onclick = function () { go(-1); };
  document.getElementById('next').onclick = function () { go(1); };
  document.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') go(1); else if (e.key === 'ArrowLeft') go(-1); else if (e.key === 'Escape' && detail) closeTeam(); });
  var sx = 0, sy = 0, skip = false;
  document.addEventListener('touchstart', function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; skip = !!(e.target.closest && e.target.closest('.chips')); }, { passive: true });
  document.addEventListener('touchend', function (e) {
    if (skip) return; var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) go(dx < 0 ? 1 : -1);
  }, { passive: true });
  if (location.hash === '#equipe') { idx = RACE; detail = me; }
  show(0);
})();
</script>
</body>
</html>
"""


FONT_DIR = os.path.join(os.path.dirname(__file__), "static", "fonts")
# Fonts are served from the site itself (no Google Fonts request, so visitors are not tracked). SIL OFL, see OFL.txt.
FONTS = [("Barlow", 400, "barlow-400"), ("Barlow", 500, "barlow-500"), ("Barlow", 600, "barlow-600"),
         ("Barlow Condensed", 600, "barlow-condensed-600"), ("Barlow Condensed", 700, "barlow-condensed-700"),
         ("Barlow Condensed", 800, "barlow-condensed-800")]
FONT_CSS = "\n".join(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;src:url(fonts/{f}.woff2) format('woff2')}}"
                     for fam, w, f in FONTS)


def copy_static(out):
    """Copy the font files next to index.html."""
    dest = os.path.join(out, "fonts")
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(FONT_DIR):
        shutil.copyfile(os.path.join(FONT_DIR, name), os.path.join(dest, name))


def _embed(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render(data):
    return TEMPLATE.replace("__FONTS__", FONT_CSS).replace("__DATA__", _embed(data))
