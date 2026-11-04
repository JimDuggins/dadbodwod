"""Shared layout + tiny Markdown converter for Dad Bod WOD. Standard library only."""
import html, re

SITE = "Dad Bod WOD"
DISCLAIMER = ("General programming for healthy adults, not medical advice. If you have an injury, "
              "a medical condition, or pain, check with a qualified professional before you start. "
              "Train at your own risk and scale anything that hurts.")
NAV = [("index.html", "Start"), ("today.html", "Today"), ("home.html", "Home plan"),
       ("gym.html", "Gym plan"), ("days/index.html", "Archive")]


def page(title, body_html, current="", depth=0, description=""):
    pre = "../" * depth
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{pre}{href}"{cur if href == current else ""}>{label}</a>'
                    for href, label in NAV)
    t = SITE if title == SITE else f"{title} | {SITE}"
    desc = html.escape(description or "Move fast, lift heavy, breathe hard. About 45 min, Mon-Sat, 2 hard days.")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(t)}</title>
<meta name="description" content="{desc}">
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
<footer class="disclaimer">{DISCLAIMER}</footer>
</body>
</html>
"""


def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md(text):
    """Small Markdown subset: headings, ul/ol (one level), tables, paragraphs, raw HTML lines."""
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
