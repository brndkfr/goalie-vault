"""Collect GitHub Pages traffic stats and merge into `_data/traffic/`.

GitHub's Traffic API only exposes the last 14 days. Running this daily
(with a 14-day overlap) means every day is captured even if a couple of
runs fail. Older data is preserved by appending to repo-tracked files.

Outputs (under `_data/traffic/`):
  views.csv      - date,views,uniques        (one row per day, dedup on date)
  clones.csv     - date,clones,uniques
  paths.json     - {"YYYY-MM-DD": [{"path":..,"title":..,"count":..,"uniques":..}, ...]}
  referrers.json - {"YYYY-MM-DD": [{"referrer":..,"count":..,"uniques":..}, ...]}
  meta.json      - {"last_run":..,"repo":..,"rows_added":{...}}

Usage:
    python scripts/collect_traffic.py [--repo owner/name] [--dry-run]

Auth: reads GITHUB_TOKEN from env. In a workflow, the default token works
when the job has `permissions: contents: write` and the repo is the same
one being queried.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "_data" / "traffic"

API_BASE = "https://api.github.com"


def gh_get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "goalie-vault-traffic-collector",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _date_only(ts: str) -> str:
    """Convert API timestamp (`2024-01-02T00:00:00Z`) to ISO date."""
    return ts[:10]


def merge_timeseries(csv_path: Path, header: list[str], rows: list[dict]) -> int:
    """Merge `rows` (list of dicts with keys matching `header`) into a CSV.

    Dedup by the first column (date). Newer values for an existing date
    overwrite older ones (the API may revise yesterday's count slightly
    once data is finalized). Returns number of *new* dates added.
    """
    existing: dict[str, list[str]] = {}
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            file_header = next(reader, None)
            if file_header != header:
                # Header drift: rewrite from scratch using on-disk rows where
                # we can (assume column order matches new header).
                pass
            for row in reader:
                if row:
                    existing[row[0]] = row

    added = 0
    for r in rows:
        key = r[header[0]]
        new_row = [str(r[h]) for h in header]
        if key not in existing:
            added += 1
        existing[key] = new_row

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    buf = StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for key in sorted(existing):
        writer.writerow(existing[key])
    csv_path.write_text(buf.getvalue(), encoding="utf-8")
    return added


def merge_snapshot(json_path: Path, today: str, items: list[dict]) -> bool:
    """Append today's snapshot to a date-keyed JSON dict.

    Overwrites today's entry if one exists (idempotent same-day reruns).
    Returns True if today's entry was new.
    """
    data: dict = {}
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
    is_new = today not in data
    data[today] = items
    json_path.parent.mkdir(parents=True, exist_ok=True)
    # Sort keys so diffs stay reviewable.
    json_path.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return is_new


def collect(repo: str, token: str, dry_run: bool) -> dict:
    views_resp = gh_get(f"/repos/{repo}/traffic/views", token)
    clones_resp = gh_get(f"/repos/{repo}/traffic/clones", token)
    paths_resp = gh_get(f"/repos/{repo}/traffic/popular/paths", token)
    refs_resp = gh_get(f"/repos/{repo}/traffic/popular/referrers", token)

    views_rows = [
        {"date": _date_only(d["timestamp"]), "views": d["count"], "uniques": d["uniques"]}
        for d in views_resp.get("views", [])
    ]
    clones_rows = [
        {"date": _date_only(d["timestamp"]), "clones": d["count"], "uniques": d["uniques"]}
        for d in clones_resp.get("clones", [])
    ]
    paths_items = [
        {"path": p["path"], "title": p.get("title", ""), "count": p["count"], "uniques": p["uniques"]}
        for p in paths_resp
    ]
    refs_items = [
        {"referrer": r["referrer"], "count": r["count"], "uniques": r["uniques"]}
        for r in refs_resp
    ]

    today = datetime.now(timezone.utc).date().isoformat()

    summary = {
        "views_fetched": len(views_rows),
        "clones_fetched": len(clones_rows),
        "paths_fetched": len(paths_items),
        "referrers_fetched": len(refs_items),
    }

    if dry_run:
        print(json.dumps({"dry_run": True, "today": today, **summary}, indent=2))
        return summary

    summary["views_added"] = merge_timeseries(
        DATA_DIR / "views.csv", ["date", "views", "uniques"], views_rows
    )
    summary["clones_added"] = merge_timeseries(
        DATA_DIR / "clones.csv", ["date", "clones", "uniques"], clones_rows
    )
    summary["paths_snapshot_new"] = merge_snapshot(
        DATA_DIR / "paths.json", today, paths_items
    )
    summary["referrers_snapshot_new"] = merge_snapshot(
        DATA_DIR / "referrers.json", today, refs_items
    )

    meta = {
        "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": repo,
        "rows_added": {
            "views": summary["views_added"],
            "clones": summary["clones_added"],
        },
    }
    (DATA_DIR / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({"today": today, **summary}, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", "brndkfr/goalie-vault"),
        help="owner/name (default: $GITHUB_REPOSITORY or brndkfr/goalie-vault)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN (or GH_TOKEN) must be set in env", file=sys.stderr)
        return 2

    try:
        collect(args.repo, token, args.dry_run)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: HTTP {e.code} from {e.url}\n{body}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
