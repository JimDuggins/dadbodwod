#!/usr/bin/env python3
"""Publish one day's session to Dad Bod WOD.

Writes days/YYYY-MM-DD.html, rewrites today.html (copy of the newest day),
and rebuilds days/index.html from every file in days/.

Usage:
  python3 publish_day.py --date 2026-11-04 --title "Upper" --week "Week 1, ~85% volume" \
      --home drafts/2026-11-04-home.md --gym drafts/2026-11-04-gym.md
  # files ending in .html are inserted as-is; anything else is treated as Markdown.
  # use "-" for --home or --gym to read that one from stdin.
Optional: --note "one-line intro shown above both versions"
          --rebuild-pages   also regenerate index.html, home.html, gym.html from content/*.md
"""
import argparse, datetime as dt, html, pathlib, re, sys
from sitelib import md, page

ROOT = pathlib.Path(__file__).resolve().parent
DAYS = ROOT / "days"


def load(src):
    text = sys.stdin.read() if src == "-" else pathlib.Path(src).read_text()
    return text if str(src).endswith(".html") else md(text)


def day_body(date, title, week, note, home_html, gym_html, depth):
    pre = "../" * depth
    nice = date.strftime("%A, %b %-d, %Y")
    meta = html.escape(" · ".join(x for x in (title, week) if x))
    note_html = f'<p>{html.escape(note)}</p>' if note else ""
    return f"""<!-- day:{date.isoformat()} title:{html.escape(title)} -->
<h1>{nice}</h1>
<p class="lede">{meta}</p>
{note_html}
<p class="muted">No loads here: pick weights that leave the listed reps in reserve (RIR). Full templates: <a href="{pre}home.html">Home plan</a> · <a href="{pre}gym.html">Gym plan</a>.</p>
<div class="versions">
<section class="card"><h2>Home version</h2>
{home_html}
</section>
<section class="card"><h2>Gym version</h2>
{gym_html}
</section>
</div>"""


def rebuild_archive():
    items = []
    for f in sorted(DAYS.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].html"), reverse=True):
        m = re.search(r"<!-- day:(\S+) title:(.*?) -->", f.read_text())
        d = dt.date.fromisoformat(f.stem)
        label = d.strftime("%a, %b %-d, %Y")
        title = m.group(2) if m else ""
        items.append(f'<li><a href="{f.name}">{label}</a> <span class="muted">{title}</span></li>')
    body = "<h1>Archive</h1>\n<ul class=\"archive\">\n" + "\n".join(items) + "\n</ul>"
    (DAYS / "index.html").write_text(page("Archive", body, current="days/index.html", depth=1))
    return items


def rebuild_pages():
    c = ROOT / "content"
    (ROOT / "index.html").write_text(page("Dad Bod WOD", md((c / "index.md").read_text()), current="index.html"))
    (ROOT / "home.html").write_text(page("Home plan", md((c / "home.md").read_text()), current="home.html"))
    (ROOT / "gym.html").write_text(page("Gym plan", md((c / "gym.md").read_text()), current="gym.html"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--title", required=True, help='e.g. "Upper", "Lower", "Engine (HARD)"')
    ap.add_argument("--week", default="", help='e.g. "Week 1, ~85% volume"')
    ap.add_argument("--note", default="")
    ap.add_argument("--home", required=True)
    ap.add_argument("--gym", required=True)
    ap.add_argument("--rebuild-pages", action="store_true")
    a = ap.parse_args()

    date = dt.date.fromisoformat(a.date)
    home_html, gym_html = load(a.home), load(a.gym)
    DAYS.mkdir(exist_ok=True)
    t = f"{date.strftime('%a %b %-d')}: {a.title}"
    (DAYS / f"{date.isoformat()}.html").write_text(
        page(t, day_body(date, a.title, a.week, a.note, home_html, gym_html, 1), depth=1))

    newest = max(dt.date.fromisoformat(f.stem) for f in DAYS.glob("[0-9]*-*-*.html"))
    if newest == date:  # only move "today" forward, never back when backfilling
        (ROOT / "today.html").write_text(
            page(f"Today: {a.title}", day_body(date, a.title, a.week, a.note, home_html, gym_html, 0),
                 current="today.html"))
    rebuild_archive()
    if a.rebuild_pages:
        rebuild_pages()
    print(f"published days/{date.isoformat()}.html" + (" + today.html" if newest == date else " (backfill)"))


if __name__ == "__main__":
    main()
