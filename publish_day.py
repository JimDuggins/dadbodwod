#!/usr/bin/env python3
"""Publish one day's session to Dad Bod WOD.

Writes days/YYYY-MM-DD.html and, when this date is the newest, rewrites
today.html from the same session. Then keeps the public site in sync:

  - feed.xml is regenerated (newest day first). Each item's permalink is
    https://dadbodwod.org/days/YYYY-MM-DD.html, never today.html.
  - days/index.html is rebuilt, grouped by month, with the Monday–Saturday note.
  - Shared chrome (head, nav, footer) is refreshed on today, every archived
    day, Start, both plans, the archive, and 404.html. Workout text already
    inside a page is left as published.

Usage:
  python3 publish_day.py --date 2026-11-04 --title "Upper" --week "Week 1, about 85 percent volume" --home drafts/2026-11-04-home.md --gym drafts/2026-11-04-gym.md
  # files ending in .html are inserted as-is; anything else is treated as Markdown.
  # use "-" for --home or --gym to read that one from stdin.
Optional: --note "one-line intro shown above both versions"
          --rebuild-pages   also regenerate index.html, home.html, gym.html from content/*.md

Day pages and today.html get jump links to #home and #gym. Titles and
descriptions include the date and the session type (Lower, Upper, Engine, …).
"""
import argparse, datetime as dt, email.utils, html, pathlib, re, sys
from sitelib import (ARCHIVE_DESC, ARCHIVE_NOTE, FEED_DESC, GYM_DESC, HOME_DESC,
                     NOT_FOUND_DESC, SITE_URL, TAGLINE, md, page)

ROOT = pathlib.Path(__file__).resolve().parent
DAYS = ROOT / "days"
DAY_FILE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.html$")
STATIC_PAGES = [
    ("index.html", "Dad Bod WOD", "index.html", TAGLINE),
    ("home.html", "Home plan", "home.html", HOME_DESC),
    ("gym.html", "Gym plan", "gym.html", GYM_DESC),
]


def load(src):
    text = sys.stdin.read() if src == "-" else pathlib.Path(src).read_text()
    return text if str(src).endswith(".html") else md(text)


def day_page_title(date, title):
    return f"{date.strftime('%a, %b %-d, %Y')}: {title}"


def today_page_title(date, title):
    return f"Today: {date.strftime('%a, %b %-d, %Y')} — {title}"


def day_description(date, title, week=""):
    text = f"{date.strftime('%A, %B %-d, %Y')}: {title}."
    if week:
        text += f" {week}."
    return text + " Home and Gym sessions."


def today_description(date, title, week=""):
    return "Today. " + day_description(date, title, week)


def day_body(date, title, week, note, home_html, gym_html, depth):
    pre = "../" * depth
    nice = date.strftime("%A, %b %-d, %Y")
    meta = html.escape(" · ".join(x for x in (title, week) if x))
    note_html = f"<p>{html.escape(note)}</p>\n" if note else ""
    return f"""<!-- day:{date.isoformat()} title:{html.escape(title)} -->
<h1>{nice}</h1>
<p class="lede">{meta}</p>
{note_html}<p class="jumps">Jump to <a href="#home">Home version</a> · <a href="#gym">Gym version</a></p>
<p class="muted">No loads here: pick weights that leave the listed reps in reserve (RIR). Full templates: <a href="{pre}home.html">Home plan</a> · <a href="{pre}gym.html">Gym plan</a>.</p>
<div class="versions">
<section class="card" id="home"><h2>Home version</h2>
{home_html}
</section>
<section class="card" id="gym"><h2>Gym version</h2>
{gym_html}
</section>
</div>"""


def extract_main(text):
    m = re.search(r"<main>\n(.*)\n</main>", text, re.S)
    if not m:
        raise SystemExit("generated page is missing <main>")
    return m.group(1)


def day_meta(main):
    m = re.search(r"<!-- day:(\d{4}-\d{2}-\d{2}) title:(.*?) -->", main)
    if not m:
        raise SystemExit("day page is missing its day comment")
    date = dt.date.fromisoformat(m.group(1))
    title = html.unescape(m.group(2))
    lede_m = re.search(r'<p class="lede">(.*?)</p>', main)
    lede = html.unescape(lede_m.group(1)) if lede_m else ""
    prefix = title + " · "
    week = lede[len(prefix):] if lede.startswith(prefix) else ""
    return date, title, week


def iter_days():
    return sorted((f for f in DAYS.glob("*.html") if DAY_FILE.match(f.name)),
                  key=lambda f: f.stem, reverse=True)


def write_day(date, title, week, note, home_html, gym_html):
    body = day_body(date, title, week, note, home_html, gym_html, 1)
    (DAYS / f"{date.isoformat()}.html").write_text(page(
        day_page_title(date, title), body, depth=1,
        description=day_description(date, title, week),
        path=f"days/{date.isoformat()}.html"))


def write_today(date, title, week, note, home_html, gym_html):
    body = day_body(date, title, week, note, home_html, gym_html, 0)
    (ROOT / "today.html").write_text(page(
        today_page_title(date, title), body, current="today.html",
        description=today_description(date, title, week), path="today.html"))


def rebuild_archive():
    groups, feed = [], []
    for f in iter_days():
        main = extract_main(f.read_text())
        date, title, week = day_meta(main)
        month = date.strftime("%B %Y")
        if not groups or groups[-1][0] != month:
            groups.append((month, []))
        label = date.strftime("%a, %b %-d, %Y")
        groups[-1][1].append(
            f'<li><a href="{f.name}">{label}</a> <span class="muted">{html.escape(title)}</span></li>')
        url = f"{SITE_URL}/days/{date.isoformat()}.html"
        stamp = dt.datetime(date.year, date.month, date.day, 12, tzinfo=dt.timezone.utc)
        feed.append({
            "title": f"{date.strftime('%A, %b %-d, %Y')}: {title}",
            "url": url,
            "pub": email.utils.format_datetime(stamp, usegmt=True),
            "desc": day_description(date, title, week),
        })
    parts = ["<h1>Archive</h1>", f'<p class="muted">{html.escape(ARCHIVE_NOTE)}</p>']
    for month, items in groups:
        parts.append(f"<h2>{month}</h2>\n<ul class=\"archive\">\n" + "\n".join(items) + "\n</ul>")
    body = "\n".join(parts)
    (DAYS / "index.html").write_text(page(
        "Archive", body, current="days/index.html", depth=1,
        description=ARCHIVE_DESC, path="days/index.html"))
    write_feed(feed)
    return feed


def write_feed(items):
    built = email.utils.formatdate(usegmt=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        "<title>Dad Bod WOD</title>",
        f"<link>{SITE_URL}/</link>",
        f'<atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>',
        f"<description>{html.escape(FEED_DESC)}</description>",
        "<language>en</language>",
        f"<lastBuildDate>{built}</lastBuildDate>",
    ]
    for it in items:
        lines += [
            "<item>",
            f"<title>{html.escape(it['title'])}</title>",
            f"<link>{it['url']}</link>",
            f'<guid isPermaLink="true">{it["url"]}</guid>',
            f"<pubDate>{it['pub']}</pubDate>",
            f"<description>{html.escape(it['desc'])}</description>",
            "</item>",
        ]
    lines += ["</channel>", "</rss>", ""]
    (ROOT / "feed.xml").write_text("\n".join(lines))


def rebuild_pages():
    c = ROOT / "content"
    for name, title, current, desc in STATIC_PAGES:
        src = {"index.html": "index.md", "home.html": "home.md", "gym.html": "gym.md"}[name]
        body = md((c / src).read_text())
        (ROOT / name).write_text(page(title, body, current=current, description=desc, path=name))


def write_404():
    body = """<h1>Page not found</h1>
<p class="lede">Nothing lives at that address.</p>
<ul class="big-links">
<li><a href="/today.html">Today <small>Home and gym versions</small></a></li>
<li><a href="/index.html">Start <small>How the week works</small></a></li>
<li><a href="/days/index.html">Archive <small>Every past day</small></a></li>
</ul>"""
    (ROOT / "404.html").write_text(page(
        "Page not found", body, description=NOT_FOUND_DESC, path="404.html", abs_root=True))


def refresh_chrome():
    """Rewrap generated pages with the current shared head and footer.

    The workout (or plan) markup inside <main> is preserved. today.html and
    each days/YYYY-MM-DD.html get a fresh title and description from the
    date and session type already published on the page.
    """
    for name, title, current, desc in STATIC_PAGES:
        path = ROOT / name
        if not path.exists():
            continue
        main = extract_main(path.read_text())
        path.write_text(page(title, main, current=current, description=desc, path=name))
    for f in iter_days():
        main = extract_main(f.read_text())
        date, title, week = day_meta(main)
        f.write_text(page(
            day_page_title(date, title), main, depth=1,
            description=day_description(date, title, week),
            path=f"days/{date.isoformat()}.html"))
    today = ROOT / "today.html"
    if today.exists():
        main = extract_main(today.read_text())
        date, title, week = day_meta(main)
        today.write_text(page(
            today_page_title(date, title), main, current="today.html",
            description=today_description(date, title, week), path="today.html"))
    archive = DAYS / "index.html"
    if archive.exists():
        main = extract_main(archive.read_text())
        archive.write_text(page(
            "Archive", main, current="days/index.html", depth=1,
            description=ARCHIVE_DESC, path="days/index.html"))
    write_404()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--title", required=True, help='e.g. "Upper", "Lower", "Engine"')
    ap.add_argument("--week", default="", help="e.g. Week 1, about 85 percent volume")
    ap.add_argument("--note", default="")
    ap.add_argument("--home", required=True)
    ap.add_argument("--gym", required=True)
    ap.add_argument("--rebuild-pages", action="store_true")
    a = ap.parse_args()

    date = dt.date.fromisoformat(a.date)
    home_html, gym_html = load(a.home), load(a.gym)
    DAYS.mkdir(exist_ok=True)
    write_day(date, a.title, a.week, a.note, home_html, gym_html)

    newest = max(dt.date.fromisoformat(f.stem) for f in iter_days())
    if newest == date:  # only move "today" forward, never back when backfilling
        write_today(date, a.title, a.week, a.note, home_html, gym_html)
    if a.rebuild_pages:
        rebuild_pages()
    rebuild_archive()
    refresh_chrome()
    print(f"published days/{date.isoformat()}.html"
          + (" + today.html" if newest == date else " (backfill)")
          + "; archive, feed, and chrome refreshed")


if __name__ == "__main__":
    main()
