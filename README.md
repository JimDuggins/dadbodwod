# Dad Bod WOD (dadbodwod.org)

A static site with no JS, no trackers and no external fonts. It's meant to be hosted on GitHub Pages under the custom domain in `CNAME`.

## Layout
- `index.html`, `home.html`, `gym.html` are generated from `content/*.md`.
- `today.html` is the newest day; `days/YYYY-MM-DD.html` is one file per day; `days/index.html` is the archive.
- `style.css` is mobile-first and supports dark mode.
- `sitelib.py` holds the shared page layout and a tiny Markdown converter (standard library only).
- `publish_day.py` is the daily publisher.
- `drafts/` and `preview/` are local only and listed in `.gitignore`.

## Publish a day
Write the day's Home and Gym sessions as Markdown (or HTML), then run:

    python3 publish_day.py --date 2026-11-04 --title "Upper" \
        --week "Week 1, about 85% volume" \
        --home drafts/2026-11-04-home.md --gym drafts/2026-11-04-gym.md

- It writes `days/2026-11-04.html`, rewrites `today.html` (only if this is the newest date, so backfills don't move "today" backwards), and rebuilds `days/index.html`.
- Inputs ending in `.html` are inserted as-is; anything else is treated as Markdown (headings, `-`/`1.` lists with one nested level, tables, **bold**, links).
- `-` reads that version from stdin.
- `--note "..."` adds a one-line intro above both versions.
- `--rebuild-pages` also regenerates index/home/gym from `content/`.

Re-running for the same date overwrites that day.

## Daily routine (once the repo exists)
1. Write today's Home and Gym sessions from the plan templates. Include no loads, no personal or health notes, and no names.
2. Run `publish_day.py`.
3. `git add -A && git commit -m "Day YYYY-MM-DD" && git push`. Pages deploys in about 1 minute.

## Privacy rule
Publish only generic outlines. Never include anyone's loads, logs, health details, names or locations.
