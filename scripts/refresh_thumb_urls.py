"""Refresh Instagram thumbnail CDN URLs in `_data/thumbnails.json`.

Designed to be run periodically by GitHub Actions (or manually). Picks the
oldest stale entries, hits the public Instagram post page via yt-dlp (no
login, no cookies), and stores the resulting CDN thumbnail URL.

Polite-scraper behavior:
  * Random per-request delay (3-8s)
  * Random inter-batch pause (30-90s)
  * Rotating User-Agent
  * Early abort on repeated rate-limit responses
  * Caps total work per run

Usage:
    python scripts/refresh_thumb_urls.py [--max 30] [--batch 5]
                                         [--min-age-days 6] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
DATA_FILE = ROOT / "_data" / "thumbnails.json"

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

PLATFORM_RE = re.compile(r"^platform:\s*[\"']?([a-zA-Z0-9_-]+)", re.M)
VIDEO_RE = re.compile(r"^video_id:\s*[\"']?([A-Za-z0-9_-]+)", re.M)


def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {}


def save_data(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def scan_posts() -> set[str]:
    """Return set of Instagram video_ids referenced in _posts."""
    ids: set[str] = set()
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Only look at front matter (between the first two `---`).
        if not text.startswith("---"):
            continue
        end = text.find("---", 3)
        if end < 0:
            continue
        head = text[:end]
        plat = PLATFORM_RE.search(head)
        vid = VIDEO_RE.search(head)
        if plat and vid and plat.group(1).lower() == "instagram":
            ids.add(vid.group(1))
    return ids


def pick_work(data: dict, valid_ids: set[str], min_age_days: int, cap: int) -> list[str]:
    cutoff = date.today() - timedelta(days=min_age_days)
    pool: list[tuple[str, str]] = []  # (sort-key, video_id)
    for vid in valid_ids:
        entry = data.get(vid, {})
        status = entry.get("status", "pending")
        if status == "not_found":
            continue
        url = entry.get("url")
        fetched = entry.get("fetched")
        if not url or status in ("stale", "pending", "rate_limit", "error"):
            sort_key = "0000-00-00"
        else:
            try:
                f_date = datetime.strptime(fetched, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                f_date = date(2000, 1, 1)
            if f_date >= cutoff:
                continue
            sort_key = fetched
        pool.append((sort_key, vid))

    # Oldest first, then random within same date for fairness.
    pool.sort(key=lambda p: (p[0], random.random()))
    return [vid for _, vid in pool[:cap]]


def fetch_one(video_id: str) -> tuple[str, dict | None, str]:
    """Return (status, info-or-None, error-message)."""
    url = f"https://www.instagram.com/p/{video_id}/"
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--no-warnings",
        "--dump-json",
        "--user-agent",
        random.choice(UA_POOL),
        url,
    ]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, check=True, timeout=45, capture_output=True, text=True
        )
    except subprocess.TimeoutExpired:
        return ("error", None, f"timeout after {time.monotonic()-t0:.1f}s")
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or "").strip().splitlines()[-1].lower() if exc.stderr else ""
        if "rate-limit" in err or "rate limit" in err or "login required" in err:
            return ("rate_limit", None, err)
        if "not available" in err or "not found" in err or "404" in err:
            return ("not_found", None, err)
        return ("error", None, err or "yt-dlp failed")
    try:
        info = json.loads(proc.stdout.splitlines()[0])
    except (ValueError, IndexError):
        return ("error", None, "no json from yt-dlp")
    return ("ok", info, "")


def write_step_summary(lines: list[str]) -> None:
    """Append a Markdown summary to GitHub Actions step summary, if available."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError:
        pass


def summarize_state(data: dict) -> Counter:
    counts: Counter = Counter()
    for entry in data.values():
        counts[entry.get("status", "unknown")] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=30, help="Max IDs per run")
    parser.add_argument("--batch", type=int, default=5, help="IDs per batch")
    parser.add_argument(
        "--min-age-days",
        type=int,
        default=6,
        help="Skip entries fresher than this many days",
    )
    parser.add_argument("--dry-run", action="store_true", help="Don't call yt-dlp")
    args = parser.parse_args()

    data = load_data()
    valid_ids = scan_posts()

    # Drop stray entries no longer referenced by any post.
    orphans = [k for k in data if k not in valid_ids]
    for orphan in orphans:
        data.pop(orphan, None)

    pre_state = summarize_state(data)
    print(f"Scan: {len(valid_ids)} IG posts found, {len(data)} cache entries.")
    print(f"      orphans dropped: {len(orphans)}")
    print(f"      cache state: " + ", ".join(f"{k}={v}" for k, v in sorted(pre_state.items())))

    work = pick_work(data, valid_ids, args.min_age_days, args.max)
    if not work:
        print("Nothing to refresh (all entries fresher than min-age-days).")
        save_data(data)
        write_step_summary([
            "## Refresh thumbnails (no work)",
            f"- Posts scanned: **{len(valid_ids)}**",
            f"- Cache entries: **{len(data)}**",
            f"- Stale entries: **0**",
        ])
        return 0

    print(f"Picked {len(work)} entries to refresh "
          f"(batch={args.batch}, dry-run={args.dry_run}, min-age-days={args.min_age_days}).")

    if args.dry_run:
        for vid in work:
            entry = data.get(vid, {})
            print(f"  would fetch {vid} (status={entry.get('status', 'pending')}, fetched={entry.get('fetched', 'never')})")
        write_step_summary([
            "## Refresh thumbnails (dry run)",
            f"- Would refresh **{len(work)}** of {len(valid_ids)} posts.",
        ])
        return 0

    today = date.today().isoformat()
    consecutive_rl = 0
    run_counts: Counter = Counter()
    aborted = False
    sample_errors: list[str] = []
    t_start = time.monotonic()

    for i in range(0, len(work), args.batch):
        batch = work[i : i + args.batch]
        batch_no = i // args.batch + 1
        total_batches = (len(work) + args.batch - 1) // args.batch
        print(f"\n-- batch {batch_no}/{total_batches} ({len(batch)} ids) --")
        for vid in batch:
            t0 = time.monotonic()
            status, info, err = fetch_one(vid)
            dt = time.monotonic() - t0
            entry = data.setdefault(
                vid,
                {"url": None, "fetched": None, "status": "pending", "attempts": 0},
            )
            entry["attempts"] = int(entry.get("attempts", 0)) + 1
            run_counts[status] += 1
            if status == "ok":
                entry["url"] = (info or {}).get("thumbnail")
                entry["status"] = "ok" if entry["url"] else "error"
                entry["fetched"] = today
                consecutive_rl = 0
                print(f"  ok   {vid} ({dt:.1f}s)")
            elif status == "not_found":
                entry["status"] = "not_found"
                entry["fetched"] = today
                consecutive_rl = 0
                print(f"  404  {vid} ({dt:.1f}s)")
            elif status == "rate_limit":
                entry["status"] = "rate_limit"
                consecutive_rl += 1
                print(f"  rl   {vid} ({dt:.1f}s) :: {err[:120]}")
                if len(sample_errors) < 3:
                    sample_errors.append(f"`{vid}`: {err[:200]}")
                if consecutive_rl >= 3:
                    print("Aborting early: 3 consecutive rate-limits.")
                    aborted = True
                    break
            else:
                entry["status"] = "error"
                consecutive_rl = 0
                print(f"  err  {vid} ({dt:.1f}s) :: {err[:120]}")
                if len(sample_errors) < 3:
                    sample_errors.append(f"`{vid}`: {err[:200]}")
            time.sleep(random.uniform(3, 8))
        if aborted:
            break
        if i + args.batch < len(work):
            pause = random.uniform(30, 90)
            print(f"  -- inter-batch pause {pause:.1f}s --")
            time.sleep(pause)

    save_data(data)
    elapsed = time.monotonic() - t_start
    post_state = summarize_state(data)

    print(f"\nDone in {elapsed:.0f}s.")
    print("Run results: " + ", ".join(f"{k}={v}" for k, v in sorted(run_counts.items())))
    print("Cache state now: " + ", ".join(f"{k}={v}" for k, v in sorted(post_state.items())))

    summary = [
        "## Refresh thumbnails",
        f"- Posts scanned: **{len(valid_ids)}**",
        f"- Picked for refresh: **{len(work)}**",
        f"- Aborted early: **{'yes (3 consecutive rate-limits)' if aborted else 'no'}**",
        f"- Elapsed: **{elapsed:.0f}s**",
        "",
        "### This run",
        "| status | count |",
        "|---|---|",
    ]
    for k in sorted(run_counts):
        summary.append(f"| {k} | {run_counts[k]} |")
    summary += [
        "",
        "### Cache state",
        "| status | count |",
        "|---|---|",
    ]
    for k in sorted(post_state):
        summary.append(f"| {k} | {post_state[k]} |")
    if sample_errors:
        summary += ["", "### Sample errors"] + [f"- {e}" for e in sample_errors]
    write_step_summary(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
