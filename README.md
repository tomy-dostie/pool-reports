# Pool de la LNH : rapport quotidien

Every morning a free GitHub server downloads last night's NHL games, applies your rosters and scoring
(1 point per goal, 1 per assist, only active players), and publishes a swipeable mobile page in French.

## Setup (about 15 minutes, all in the browser)

1. Create a free account at github.com, then **New repository**: name it `pool-lnh`, choose **Public**, leave "Add a README" unchecked.
2. Unzip this folder on your computer. In the new repository click **uploading an existing file** and drag in
   everything from the unzipped folder: `pool/`, `tests/`, `roster.json`, `expected.json`, `README.md`, `.gitignore`
   (do not worry about `workflow-daily.yml` yet). Click **Commit changes**.
3. Still in the repository: **Add file > Create new file**. In the name box type `.github/workflows/daily.yml`
   (typing the slashes creates the folders). Open `workflow-daily.yml` from the zip in a text editor, copy everything,
   paste it into the big box, then **Commit changes**.
4. **Settings > Pages > Build and deployment > Source: GitHub Actions.**
5. **Actions** tab > **Rapport quotidien** > **Run workflow**. After about 2 minutes the run turns green.
   Your page is at `https://YOUR-USERNAME.github.io/pool-lnh/`.
6. Open the run, then the **build** job, then the step **Compare with the PoolExpert numbers**. It lists every player of
   Gab, Vallée and Réj with `ok` or `DIFF`. Send a screenshot of that step to Claude if any line says DIFF.

From then on it runs by itself every morning around 5 h. You can also start it by hand from the Actions tab.
GitHub pauses scheduled runs after 60 days without any change to the repository; making any edit (for example a
roster change) restarts them.

## Personal links

Each friend can open their own page directly on their own name: add `?p=` and the pooler id to the address.
Ids: `tomy`, `vinny`, `gab`, `vallee`, `flo`, `yves`, `rej`, `charlene`, `denis`, `jeff`.
Example: `https://YOUR-USERNAME.github.io/pool-lnh/?p=gab`. The page remembers the last choice on that phone.

## Roster changes (waiver moves, reserve swaps)

Open `roster.json` on GitHub and click the pencil icon. A move has two parts, both with the SAME date:
the player leaving gets a `droppedOn`, and the player arriving is added as a new entry with `addedOn`.
The date is the first day the change applies (the dropped player's game that day does NOT count).

```json
{ "name": "Brock Boeser", "team": "VAN", "position": "F", "playerId": null, "addedOn": "2026-09-29", "droppedOn": "2026-11-03" },
{ "name": "Connor Bedard", "team": "CHI", "position": "F", "playerId": null, "addedOn": "2026-11-03", "droppedOn": null }
```

Leave `playerId` as `null`: the program finds the NHL id from the name. Positions are `F` or `D`. If a name is
misspelled the run prints a WARNING in the **Build the page** step.

## Posting to the group chat (optional)

- Discord: Server settings > Integrations > Webhooks > copy the URL. In the repository: Settings > Secrets and
  variables > Actions > New repository secret, name `DISCORD_WEBHOOK`.
- Telegram: secrets `TELEGRAM_TOKEN` (from @BotFather) and `TELEGRAM_CHAT` (the chat id).
- Messenger or WhatsApp cannot be posted to automatically. The last card of the page has a **Copier le résumé**
  button that copies a ready-to-paste text.

## Rules built into the engine

- Only active players score. Reserves do not. A player counts games with `addedOn <= date < droppedOn`.
- A game counts on the NHL's Eastern date. Regular season only.
- Ties share a rank. The season projection scales the current total to `seasonGames` (84 in `roster.json`).
- Everything comes from the NHL's public web data, which is unofficial and could change. If a run fails, the previous
  page stays online.
