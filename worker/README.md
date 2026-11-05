# Pool LNH Worker (Cloudflare, free plan)

GitHub's scheduler is throttled on this repo: the morning report and the live updates were late or never ran.
This small Worker is the reliable clock, and it also sends push notifications. GitHub Actions still builds and
GitHub Pages still hosts.

**What it does** (every minute, Toronto time):

| When | What |
|---|---|
| 4 h 05 to 9 h | If `version.json` isn't today's or a game is missing, it starts `daily.yml` (official). At most every 30 min, 4 tries a day. |
| 7 h to midi | Once the morning report is out, and only if there were games last night, it sends the morning notifications. |
| 11 h to 1 h 59 | It reads the NHL scoreboard. When the scores differ from `live.json`, it starts `live.yml` (at most every 3 min). |

## One-time setup (about 15 min)

Run these from the `worker/` folder.

1. **Log in.** Create a free Cloudflare account, then run `npx wrangler login`.
2. **Storage.** Run `npx wrangler kv namespace create pool-lnh`, then copy the printed `id` into `wrangler.toml`.
3. **Push keys.** Run `node scripts/vapid.mjs`.
   - Copy the public key into `wrangler.toml` (`VAPID_PUBLIC`).
   - Store the private key, then delete the file:
     - **PowerShell:** `Get-Content vapid-private.local.json | npx wrangler secret put VAPID_PRIVATE_JWK`
     - **Bash:** `npx wrangler secret put VAPID_PRIVATE_JWK < vapid-private.local.json`
4. **GitHub token.** Create one at GitHub → Settings → Developer settings → Fine-grained tokens:
   - Repository access: only `pool-reports`.
   - Permissions: **Actions: Read and write**. Nothing else.
   - Expiration: 1 year. Put a reminder in your calendar.

   Then run `npx wrangler secret put GH_TOKEN` and paste the token.
5. **Deploy.** Run `npx wrangler deploy` and note the URL it prints (`https://pool-lnh.<account>.workers.dev`).
6. **GitHub variables** (repo → Settings → Secrets and variables → Actions → Variables). These are public values:
   - `PUSH_URL` = the Worker URL, without a trailing `/`.
   - `VAPID_PUBLIC_KEY` = the public key from step 3.

   The next build shows the "Notifications" panel in the Moi tab.
7. **Turn off the GitHub live timer.** Remove the `schedule:` lines from `.github/workflows/live.yml`. The Worker replaces them.

## Checking it

- Watch the logs live with `npx wrangler tail`. You'll see `dispatched daily.yml` and `dispatched live.yml`.
- On GitHub Actions, the runs started by the Worker show as "workflow_dispatch".
- Turning notifications on in the app sends a test notification right away.

## Security

- **Token scope:** the token can only start workflows on this one repo.
- **Subscriptions** contain only the browser's push address, the pooler id and the chosen types.
- **Endpoints:** `POST /abonner` and `/desabonner` accept only the site's origin, the browsers' push services, the 10 pooler ids and at most 100 subscriptions.
