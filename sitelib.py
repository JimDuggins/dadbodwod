"""Shared layout + tiny Markdown converter for Dad Bod WOD. Standard library only."""
import html, re

SITE = "Dad Bod WOD"
SITE_URL = "https://dadbodwod.org"
TAGLINE = "Move fast, lift heavy, breathe hard. About 45 min, Mon–Sat, 2 hard days."
HOME_DESC = ("Home plan (garage). Move fast, lift heavy, breathe hard. "
             "About 45 minutes, Monday to Saturday, two hard days.")
GYM_DESC = ("Gym plan. Same week, same templates, gym equipment. "
            "About 45 minutes, Monday to Saturday, two hard days.")
ARCHIVE_DESC = "Past sessions, posted Monday–Saturday. Each day has a Home version and a Gym version."
ARCHIVE_NOTE = "Sessions are posted Monday–Saturday, so a Sunday gap is a rest day."
NOT_FOUND_DESC = "That page isn't on Dad Bod WOD."
FEED_DESC = "Daily Home and Gym sessions, posted Monday–Saturday."
OG_ALT = "Dad Bod WOD. Move fast, lift heavy, breathe hard."
DISCLAIMER = ("General programming for healthy adults, not medical advice. If you have an injury, "
              "a medical condition, or pain, check with a qualified professional before you start. "
              "Train at your own risk and scale anything that hurts.")
NAV = [("index.html", "Start"), ("today.html", "Today"), ("home.html", "Home plan"),
       ("gym.html", "Gym plan"), ("days/index.html", "Archive")]

# Inline HTML the plans use on purpose. Anything else stays escaped.
_TAG_SPAN = re.compile(r'&lt;span class="tag"&gt;(.*?)&lt;/span&gt;')


def canonical(path):
    if path in ("", "index.html"):
        return SITE_URL + "/"
    return f"{SITE_URL}/{path}"


def page(title, body_html, current="", depth=0, description="", path="", abs_root=False):
    pre = "/" if abs_root else "../" * depth
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{pre}{href}"{cur if href == current else ""}>{label}</a>'
                    for href, label in NAV)
    full = SITE if title == SITE else f"{title} | {SITE}"
    esc_title = html.escape(full)
    desc = html.escape(description or TAGLINE)
    canon = canonical(path or current)
    image = f"{SITE_URL}/og.png"
    alt = html.escape(OG_ALT)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc_title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{image}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc_title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{image}">
<meta name="twitter:image:alt" content="{alt}">
<link rel="icon" href="{pre}favicon.ico" sizes="any">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{SITE}" href="{pre}feed.xml">
<link rel="stylesheet" href="{pre}style.css">
</head>
<body>
<header>
<a class="brand" href="{pre}index.html">Dad Bod <span>WOD</span></a>
<nav>{links}</nav>
</header>
<main>
{body_html}
</main>
<footer>
<p class="subscribe"><a href="{pre}feed.xml">RSS</a></p>
<p class="disclaimer">{DISCLAIMER}</p>
</footer>
</body>
</html>
"""


def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = _TAG_SPAN.sub(lambda m: f'<span class="tag">{m.group(1)}</span>', s)
    return s


def md(text):
    """Small Markdown subset: headings, ul/ol (one level), tables, paragraphs, raw HTML lines.

    A line that starts with '<' is copied through as HTML. Inside headings, paragraphs,
    and table cells, only <span class="tag">...</span> is kept; other markup is escaped.
    """
    out, para, lst, tbl = [], [], None, []

    def flush():
        nonlocal para, lst, tbl
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>"); para = []
        if lst:
            tag, items = lst
            def li(i):
                sub = "<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in i[1]) + "</ul>" if i[1] else ""
                return f"<li>{_inline(i[0])}{sub}</li>"
            out.append(f"<{tag}>" + "".join(li(i) for i in items) + f"</{tag}>"); lst = None
        if tbl:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tbl
                    if not re.match(r"^\|?\s*:?-{2,}", r.strip())]
            head, *rest = rows
            h = "".join(f"<th>{_inline(c)}</th>" for c in head)
            b = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rest)
            out.append(f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')
            tbl = []

    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush(); continue
        if s.startswith("<"):
            flush(); out.append(s); continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            flush(); n = len(m.group(1)); out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>"); continue
        if s.startswith("|"):
            if para or lst: flush()
            tbl.append(s); continue
        m = re.match(r"^([-*]|\d+[.)])\s+(.*)", s)
        if m and lst and raw.startswith(("  ", "\t")):
            lst[1][-1][1].append(m.group(2)); continue
        if m:
            tag = "ul" if m.group(1) in "-*" else "ol"
            if para or tbl or (lst and lst[0] != tag): flush()
            if not lst: lst = (tag, [])
            lst[1].append([m.group(2), []]); continue
        if lst and raw.startswith(("  ", "\t")):
            tgt = lst[1][-1]
            if tgt[1]: tgt[1][-1] += " " + s
            else: tgt[0] += " " + s
            continue
        if lst or tbl: flush()
        para.append(s)
    flush()
    return "\n".join(out)
