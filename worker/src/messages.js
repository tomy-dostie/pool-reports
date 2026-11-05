// Notification texts (Quebec French, "like the guys talk"), built from the site's data.json.

const ord = (n) => (n === 1 ? '1er' : `${n}e`);
const names = (a) => (a.length < 2 ? a.join('') : `${a.slice(0, -1).join(', ')} pis ${a[a.length - 1]}`);

/** Morning notification for one pooler, or null when there's nothing to say for the chosen types. */
export function morningMessage(data, id, types) {
  const P = data.poolers || [];
  const p = P.find((x) => x.id === id);
  if (!p) return null;
  const parts = [];

  if (types.includes('matin')) {
    let s = `T’es ${ord(p.rank)} avec ${p.total} pts, +${p.yday} hier.`;
    if (p.rank === 1) {
      const second = P.filter((q) => q.id !== p.id).sort((a, b) => b.total - a.total)[0];
      if (second) s += p.total > second.total ? ` ${p.total - second.total} d’avance sur ${second.name}.` : ` À égalité avec ${second.name}.`;
    } else {
      s += ` À ${p.gap} du 1er.`;
    }
    parts.push(s);
  }

  if (types.includes('depasse')) {
    const ok = (q) => Array.isArray(q.ranks) && q.ranks.length >= 2;
    const prev = (q) => q.ranks[q.ranks.length - 2];
    const cur = (q) => q.ranks[q.ranks.length - 1];
    if (ok(p)) {
      const others = P.filter((q) => q.id !== p.id && ok(q));
      const passedMe = others.filter((q) => prev(q) > prev(p) && cur(q) < cur(p)).map((q) => q.name);
      const iPassed = others.filter((q) => prev(q) < prev(p) && cur(q) > cur(p)).map((q) => q.name);
      if (passedMe.length) parts.push(`${names(passedMe)} ${passedMe.length > 1 ? 't’ont' : 't’a'} dépassé.`);
      if (iPassed.length) parts.push(`T’as dépassé ${names(iPassed)} !`);
    }
  }

  if (!parts.length) return null;
  return { title: `Pool LNH · ${data.meta.lastDayLabel}`, body: parts.join(' '), url: './#moi', tag: 'matin' };
}

export const WELCOME = { title: 'Pool LNH', body: 'C’est beau, les notifs sont activées. À demain matin !', url: './#moi', tag: 'bienvenue' };
