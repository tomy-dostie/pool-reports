// Pool LNH Worker: the reliable clock GitHub doesn't give us, plus push notifications.
//
// Runs every minute (one cron, all times computed in Toronto time, so daylight saving is handled):
//   04:05-09:00  morning report: if version.json isn't today's (or a game is missing), start daily.yml (official),
//                at most every 30 min, 4 tries a day.
//   07:00-12:00  once the morning report is out and there were games last night: morning notifications.
//   11:00-01:59  live: read the NHL scoreboard; when its signature differs from the live.json online, start live.yml
//                (at most every 3 min). Same signature as pool/live.py signature(): keep both in sync.
// HTTP (called by the page): POST /abonner, POST /desabonner.
//
// Secrets (wrangler secret put): GH_TOKEN (fine-grained, Actions read/write on this repo only), VAPID_PRIVATE_JWK.
// Nothing personal is stored: a subscription = the browser's push address + pooler id + chosen types.

import { sendPush, b64uDecode } from './push.js';
import { morningMessage, WELCOME } from './messages.js';

const TYPES = ['matin', 'depasse'];
const MAX_SUBS = 100;
const PUSH_HOSTS = [/^fcm\.googleapis\.com$/, /(^|\.)push\.apple\.com$/, /^updates\.push\.services\.mozilla\.com$/,
  /^[a-z0-9-]+\.notify\.windows\.com$/];
const UA = { 'User-Agent': 'pool-lnh-worker' };

// ------------------------------------------------------------------ time helpers
export function toronto(date) {
  const o = {};
  new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Toronto', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date).forEach((x) => { o[x.type] = x.value; });
  return { day: `${o.year}-${o.month}-${o.day}`, hour: +o.hour, minute: +o.minute };
}
export function addDays(day, n) {
  const d = new Date(`${day}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
/** NHL date of the game night in progress: until 6 h it's still the previous date (pool/live.py live_day). */
export const liveNight = (date) => toronto(new Date(date.getTime() - 6 * 3600e3)).day;

// ------------------------------------------------------------------ scoreboard signature (= pool/live.py)
const STARTED = new Set(['LIVE', 'CRIT', 'OFF', 'FINAL']);
export function nightGames(js, day) {
  return (js.games || []).filter((g) => g.gameDate === day && (g.gameType ?? 2) === 2);
}
export async function signature(games) {
  const key = games.filter((g) => STARTED.has(g.gameState || '')).map((g) => [g.id, g.gameState,
    (g.awayTeam || {}).score || 0, (g.homeTeam || {}).score || 0, g.period || 0,
    (g.clock || {}).inIntermission ? 1 : 0].join(':')).sort();
  if (!key.length) return null;
  const h = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key.join('|'))));
  return [...h].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
}

// ------------------------------------------------------------------ outside calls
async function getJson(url) {
  try {
    const r = await fetch(`${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`, { headers: UA });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}
async function dispatch(env, workflow, inputs) {
  const r = await fetch(`https://api.github.com/repos/${env.REPO}/actions/workflows/${workflow}/dispatches`, {
    method: 'POST',
    headers: { ...UA, Authorization: `Bearer ${env.GH_TOKEN}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
    body: JSON.stringify(inputs ? { ref: 'main', inputs } : { ref: 'main' }),
  });
  if (r.status !== 204) throw new Error(`dispatch ${workflow}: ${r.status}`);
  console.log(`dispatched ${workflow}`);
}

// ------------------------------------------------------------------ the three jobs
async function morningReport(env, t) {
  const v = await getJson(`${env.SITE}version.json`);
  if (v && v.day === t.day && !v.missing) return;
  let st = (await env.KV.get('morning', 'json')) || {};
  if (st.day !== t.day) st = { day: t.day, n: 0, at: 0 };
  if (st.n >= 4 || Date.now() - st.at < 30 * 60e3) return;
  await dispatch(env, 'daily.yml', { official: 'true' });
  await env.KV.put('morning', JSON.stringify({ day: t.day, n: st.n + 1, at: Date.now() }));
}

async function morningPush(env, t) {
  let st = (await env.KV.get('pushed', 'json')) || {};
  if (st.day === t.day && st.done) return;
  const v = await getJson(`${env.SITE}version.json`);
  if (!v || v.day !== t.day) return;                                   // morning report not out yet
  const data = await getJson(`${env.SITE}data.json`);
  if (!data || !data.meta) return;
  if (st.day !== t.day) st = { day: t.day, sent: [] };
  const todo = data.meta.lastDay === addDays(t.day, -1)               // no games last night: nothing to say
    ? (await listSubs(env)).filter((s) => !st.sent.includes(s.key)) : [];
  for (const s of todo.slice(0, 5)) {                                  // a few per minute keeps each run short
    const msg = morningMessage(data, s.pooler, s.types);
    if (msg) await deliver(env, s, msg);
    st.sent.push(s.key);
  }
  st.done = todo.length <= 5;
  await env.KV.put('pushed', JSON.stringify(st), { expirationTtl: 3 * 86400 });
}

async function live(env, now) {
  const night = liveNight(now);
  const js = await getJson(`https://api-web.nhle.com/v1/score/${night}`);
  if (!js) return;
  const sig = await signature(nightGames(js, night));
  if (!sig) return;                                                    // no game started yet
  // GitHub Pages ignores ?t= and serves live.json from its cache for up to 10 min, so the online copy can be
  // old right after a deploy. The Worker remembers the scoreboard it last asked a build for (KV liveRun) and only
  // re-asks for the same scoreboard when the online copy still differs once that cache has surely expired
  // (a box score missing at build time, "-incomplet"), at most twice.
  const online = await getJson(`${env.SITE}live.json`);
  if (online && (online.morning || '') > night) return;                // that night is already official
  if (online && online.sig === sig && online.day === night) return;    // page already up to date
  const run = (await env.KV.get('liveRun', 'json')) || {};
  if (!shouldRun(run, sig, night, Date.now())) return;
  await dispatch(env, 'live.yml');
  const again = run.sig === sig && run.night === night;
  await env.KV.put('liveRun', JSON.stringify({ sig, night, at: Date.now(), n: again ? (run.n || 1) + 1 : 1 }),
    { expirationTtl: 2 * 86400 });
}

/** Live build needed? run = last dispatch {sig, night, at, n}. New scoreboard: yes (3 min apart); same: retry later. */
export function shouldRun(run, sig, night, now) {
  if (now - (run.at || 0) < 3 * 60e3) return false;                    // a run is probably still going
  if (run.sig !== sig || run.night !== night) return true;             // something happened since the last build
  return now - run.at >= 12 * 60e3 && (run.n || 1) < 3;                // online copy still old after the cache: retry
}

// ------------------------------------------------------------------ subscriptions
async function listSubs(env) {
  const out = [];
  let cursor;
  do {
    const page = await env.KV.list({ prefix: 'sub:', cursor });
    for (const k of page.keys) {
      const s = await env.KV.get(k.name, 'json');
      if (s) out.push({ ...s, key: k.name });
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
  return out;
}
async function deliver(env, s, msg) {
  try {
    const status = await sendPush(s, msg, env);
    if (status === 404 || status === 410) await env.KV.delete(s.key);  // phone unsubscribed or app removed
    else if (status >= 300) console.log(`push ${status} for ${s.key}`);
  } catch (e) { console.log(`push error ${s.key}: ${e.message}`); }
}
async function subKey(endpoint) {
  const h = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(endpoint)));
  return 'sub:' + [...h].slice(0, 16).map((b) => b.toString(16).padStart(2, '0')).join('');
}
export function validSub(body, poolers) {
  try {
    const { sub, pooler, types } = body;
    const u = new URL(sub.endpoint);
    if (u.protocol !== 'https:' || !PUSH_HOSTS.some((re) => re.test(u.hostname)) || sub.endpoint.length > 1000) return null;
    const p256 = b64uDecode(sub.keys.p256dh), auth = b64uDecode(sub.keys.auth);
    if (p256.length !== 65 || p256[0] !== 4 || auth.length !== 16) return null;
    if (!poolers.includes(pooler) || !Array.isArray(types) || !types.length || types.some((t) => !TYPES.includes(t))) return null;
    return { endpoint: sub.endpoint, keys: { p256dh: sub.keys.p256dh, auth: sub.keys.auth }, pooler, types: [...new Set(types)] };
  } catch { return null; }
}

async function handle(request, env, ctx) {
  const cors = { 'Access-Control-Allow-Origin': env.ORIGIN, 'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400', Vary: 'Origin' };
  const reply = (status, text = '') => new Response(text, { status, headers: { ...cors, 'Content-Type': 'text/plain; charset=utf-8' } });
  const path = new URL(request.url).pathname;
  if (request.method === 'OPTIONS') return reply(204);
  if (request.method === 'GET' && path === '/') return reply(200, 'Pool LNH');
  if (request.method !== 'POST' || !['/abonner', '/desabonner'].includes(path)) return reply(404);
  if (request.headers.get('Origin') !== env.ORIGIN) return reply(403);
  const raw = await request.text();
  if (raw.length > 4096) return reply(413);
  let body;
  try { body = JSON.parse(raw); } catch { return reply(400); }

  if (path === '/desabonner') {
    if (typeof body.endpoint !== 'string') return reply(400);
    await env.KV.delete(await subKey(body.endpoint));
    return reply(200, 'ok');
  }
  const s = validSub(body, env.POOLERS.split(','));
  if (!s) return reply(400);
  const key = await subKey(s.endpoint);
  const existed = (await env.KV.get(key)) !== null;
  if (!existed && (await env.KV.list({ prefix: 'sub:' })).keys.length >= MAX_SUBS) return reply(429);
  await env.KV.put(key, JSON.stringify({ ...s, at: new Date().toISOString() }));
  if (!existed) ctx.waitUntil(deliver(env, { ...s, key }, WELCOME));  // first time: a test notification
  return reply(200, 'ok');
}

export default {
  fetch: (request, env, ctx) => handle(request, env, ctx),
  async scheduled(event, env, ctx) {
    const now = new Date(event.scheduledTime);
    const t = toronto(now), m = t.hour * 60 + t.minute;
    const jobs = [];
    if (m >= 4 * 60 + 5 && m < 9 * 60) jobs.push(morningReport(env, t));
    if (m >= 7 * 60 && m < 12 * 60) jobs.push(morningPush(env, t));
    if (t.hour >= 11 || t.hour < 2) jobs.push(live(env, now));
    const res = await Promise.allSettled(jobs);
    res.filter((r) => r.status === 'rejected').forEach((r) => console.log(`job failed: ${r.reason && r.reason.message}`));
  },
};
