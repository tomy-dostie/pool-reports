// Generates the VAPID key pair for push notifications. Run once: node scripts/vapid.mjs
// - the PUBLIC key goes in wrangler.toml (VAPID_PUBLIC) and in the GitHub repo variable VAPID_PUBLIC_KEY;
// - the PRIVATE key is written to vapid-private.local.json (git-ignored): pipe it into
//   `npx wrangler secret put VAPID_PRIVATE_JWK`, then delete the file.
import { writeFileSync } from 'node:fs';

const keys = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
const raw = new Uint8Array(await crypto.subtle.exportKey('raw', keys.publicKey));
const pub = Buffer.from(raw).toString('base64url');
const jwk = await crypto.subtle.exportKey('jwk', keys.privateKey);
writeFileSync('vapid-private.local.json', JSON.stringify(jwk));
console.log('Public key (VAPID_PUBLIC / VAPID_PUBLIC_KEY):');
console.log(pub);
console.log('Private key written to vapid-private.local.json (never commit it).');
