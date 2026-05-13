# TODO

## Stats / GitHub Traffic archive — one-time setup

The daily traffic collector (`.github/workflows/collect-traffic.yml`) and
the `/stats/` dashboard are wired up, but the workflow needs a personal
access token because the default `GITHUB_TOKEN` cannot read the
`/repos/{repo}/traffic/*` endpoints (no `Administration` scope is
exposed to the auto-token).

Steps (~2 min):

1. Create a fine-grained PAT: <https://github.com/settings/personal-access-tokens/new>
   - **Resource owner:** `brndkfr`
   - **Repository access:** *Only select repositories* → `goalie-vault`
   - **Repository permissions:**
     - Administration: **Read-only**  *(required for traffic API)*
     - Contents: **Read-only**
     - Metadata: **Read-only**  *(auto)*
   - **Expiration:** 1 year (or your preference)
2. Add the token as a repo secret:
   `Settings → Secrets and variables → Actions → New repository secret`
   - **Name:** `TRAFFIC_TOKEN`
   - **Value:** *(paste the PAT)*
3. Trigger the first collection manually:
   `Actions → Collect GitHub traffic stats → Run workflow`
4. Once the run finishes, verify the dashboard at
   <https://brndkfr.github.io/goalie-vault/stats/>.

After this, the workflow runs daily at 06:17 UTC and commits any new
data to `_data/traffic/` automatically.

### Renewal

Fine-grained PATs expire. When `TRAFFIC_TOKEN` expires the workflow
will start failing with HTTP 401 — repeat steps 1–2 with a fresh token.
