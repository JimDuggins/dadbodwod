# Dad Bod WOD (dadbodwod.org)

A static site with no JS, no trackers and no external fonts. It's meant to be hosted on GitHub Pages under the custom domain in `CNAME`.

## Layout
- `index.html`, `home.html`, `gym.html` are generated from `content/*.md`.
- `today.html` is the newest day. `days/YYYY-MM-DD.html` is one file per day. `days/index.html` is the archive, grouped by month, with a note that sessions are posted Monday–Saturday.
- `feed.xml` is the RSS 2.0 feed of published days, newest first. Each item links to that day's archive page (`/days/YYYY-MM-DD.html`), not `today.html`.
- `404.html` is the GitHub Pages not-found page.
- `favicon.svg` and `favicon.ico` are the icon. `og.png` is the share image.
- `style.css` is mobile-first, supports dark mode, and includes print rules (nav and the RSS link drop out; Home and Gym stack full width).
- `sitelib.py` holds the shared page layout (head, nav, footer, canonical and social tags, RSS and favicon links) and a tiny Markdown converter (standard library only). Inline `<span class="tag">` in headings and table cells is preserved so the HARD badges render.
- `publish_day.py` is the daily publisher.
- `drafts/` and `preview/` are local only and listed in `.gitignore`.

## Publish a day
Write the day's Home and Gym sessions as Markdown (or HTML), then run:

    python3 publish_day.py --date 2026-11-04 --title "Upper" \
        --week "Week 1, about 85% volume" \
        --home drafts/2026-11-04-home.md --gym drafts/2026-11-04-gym.md

- It writes `days/2026-11-04.html` and rewrites `today.html` only when this is the newest date, so a backfill does not move "today" backwards.
- It rebuilds `days/index.html` and regenerates `feed.xml`.
- It refreshes the shared head and footer on today, every archived day, Start, both plans, the archive, and `404.html`, so the next publish picks up chrome changes. The workout already inside a page is left as published.
- Inputs ending in `.html` are inserted as-is; anything else is treated as Markdown (headings, `-`/`1.` lists with one nested level, tables, **bold**, links, and `<span class="tag">`).
- `-` reads that version from stdin.
- `--note "..."` adds a one-line intro above both versions.
- `--rebuild-pages` also regenerates index/home/gym from `content/`.
- Today and each day page include jump links to `#home` and `#gym`.

Re-running for the same date overwrites that day.

## Daily routine (once the repo exists)
1. Write today's Home and Gym sessions from the plan templates. Include no loads, no personal or health notes, and no names.
2. Run `publish_day.py`.
3. `git add -A && git commit -m "Day YYYY-MM-DD" && git push`. Pages deploys in about 1 minute.

## Privacy rule
Publish only generic outlines. Never include anyone's loads, logs, health details, names or locations.
