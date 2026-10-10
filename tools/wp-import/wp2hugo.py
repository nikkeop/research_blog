#!/usr/bin/env python3
"""Convert a WordPress export (WXR) into Hugo posts for the trips section.

    python3 tools/wp-import/wp2hugo.py EXPORT.xml content/en/trips

Each post becomes `content/en/trips/<trip>/<slug>.md`, where the trip is the
post's WordPress category (see TRIPS below; anything else goes to
`short-trips`). Pages, attachments and theme objects in the export are
skipped — the trip overview pages are written by hand.

The Gutenberg blocks map onto this site's markdown and shortcodes:

    paragraph / heading / list / quote   markdown
    image                                {{< photo >}}
    gallery, jetpack slideshow / tiled   {{< photos >}} of {{< photo >}}
    table                                markdown table
    [googlemaps …] in an html block      {{< routemap >}}
    group / columns / media-text         their content, flattened

Images are not linked to WordPress but to the media bucket: an upload such as
`…/wp-content/uploads/2024/06/img_6239-1.jpg?w=1024` becomes the key
`trips/import/2024/06/img_6239-1.jpg`, which `layouts/_partials/media.html`
resolves against `params.media.base`. The files themselves are made by
`tools/media/optimize.py` from the media export, with the same prefix.

Links between posts of the old blog are rewritten to the new paths. Private and
draft posts are imported with `draft: true`. Comments are not imported.

Re-running overwrites the generated files, so edit the posts only once the
import is final — or re-run before editing anything.
"""
import argparse
import html
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}
# WordPress category slug -> folder under content/en/trips/
TRIPS = {"norway-2024": "norway-2024", "china-2025": "china-2025"}
DEFAULT_TRIP = "short-trips"
MEDIA_PREFIX = "trips/import"
MEDIA_BASE = "https://site-media.oppernik.de"  # params.media.base, for plain links
BLOG_HOSTS = r"niksradventures\.(?:wordpress\.com|files\.wordpress\.com)"
UPLOAD_RE = re.compile(rf"https?://{BLOG_HOSTS}/(?:wp-content/uploads/)?(\d{{4}}/\d{{2}}/[^/?\"#\s]+\.[A-Za-z0-9]+)(?:[?#]|$)")
POST_RE = re.compile(rf"https?://{BLOG_HOSTS}/\d{{4}}/\d{{2}}/\d{{2}}/([^/?#\"]+)/?")
CATEGORY_RE = re.compile(rf"https?://{BLOG_HOSTS}/category/([^/?#\"]+)/?")

warnings = []


# -- urls ---------------------------------------------------------------------

def clean_slug(raw):
    """`tag-30-…-%f0%9f%87%a9-goodbye` -> `tag-30-…-goodbye`."""
    s = urllib.parse.unquote(raw).lower()
    s = re.sub(r"[^a-z0-9-]+", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def media_key(url):
    m = UPLOAD_RE.match(html.unescape(url))
    return f"{MEDIA_PREFIX}/{m.group(1)}" if m else None


def rewrite_url(url, paths):
    url = html.unescape(url)
    m = POST_RE.match(url)
    if m:
        slug = clean_slug(m.group(1))
        if slug in paths:
            return paths[slug]
        warnings.append(f"link to unknown post {url}")
    key = media_key(url)
    if key:
        return f"{MEDIA_BASE}/{key}"
    m = CATEGORY_RE.match(url)
    if m and m.group(1) in TRIPS:
        return f"/trips/{TRIPS[m.group(1)]}/"
    return url


# -- inline html -> markdown --------------------------------------------------

def escape_md(text):
    text = text.replace("\\", "\\\\").replace("*", "\\*").replace("`", "\\`")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text


def inline(fragment, paths):
    """Paragraph-level html to markdown. Unknown tags keep their text."""
    out = []
    pos = 0
    stack = []
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)([^>]*)>", fragment):
        out.append(escape_md(html.unescape(fragment[pos:m.start()])))
        pos = m.end()
        closing, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag == "br":
            out.append("\\\n")
        elif tag in ("strong", "b"):
            out.append("**")
        elif tag in ("em", "i"):
            out.append("_")
        elif tag in ("s", "del"):
            out.append("~~")
        elif tag == "code":
            out.append("`")
        elif tag == "a":
            if closing:
                href = stack.pop() if stack else ""
                out.append(f"]({href})" if href else "")
            else:
                h = re.search(r'href="([^"]*)"', attrs)
                href = rewrite_url(h.group(1), paths) if h else ""
                stack.append(href)
                out.append("[" if href else "")
    out.append(escape_md(html.unescape(fragment[pos:])))
    text = "".join(out).replace("\ufffc", "")  # placeholder WordPress leaves for inline media
    text = re.sub(r"\*\*(\s*)\*\*", r"\1", text)  # adjacent bold runs
    text = re.sub(r"[ \t ]+\n", "\n", text).strip()
    # A line that would turn into a list, heading or quote is escaped.
    text = re.sub(r"(?m)^(\d+)\. ", r"\1\\. ", text)
    text = re.sub(r"(?m)^([-+#>]) ", r"\\\1 ", text)
    return text


def param(value):
    """A shortcode parameter value, quoted so that any caption survives."""
    value = value.replace("\n", " ").strip()
    if '"' not in value:
        return f'"{value}"'
    if "`" not in value:
        return f"`{value}`"
    return '"' + value.replace('"', "'") + '"'


# -- blocks -------------------------------------------------------------------

class Block:
    def __init__(self, name, attrs):
        self.name, self.attrs, self.children, self.html = name, attrs, [], []

    def inner(self):
        return "".join(self.html)


BLOCK_RE = re.compile(r"<!--\s+(/?)wp:([a-z0-9/-]+)(?:\s+(\{.*?\}))?\s*(/?)-->", re.S)


def parse_blocks(body):
    root = Block("root", {})
    stack = [root]
    pos = 0
    for m in BLOCK_RE.finditer(body):
        stack[-1].html.append(body[pos:m.start()])
        pos = m.end()
        closing, name, attrs, selfclosing = m.groups()
        if closing:
            if len(stack) > 1:
                stack.pop()
            continue
        try:
            attrs = json.loads(attrs) if attrs else {}
        except json.JSONDecodeError:
            attrs = {}
        block = Block(name, attrs)
        stack[-1].children.append(block)
        stack[-1].html.append(f"\0{len(stack[-1].children) - 1}\0")
        if not selfclosing:
            stack.append(block)
    stack[-1].html.append(body[pos:])
    return root


def figure_parts(fragment):
    img = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', fragment)
    alt = re.search(r'<img\b[^>]*\balt="([^"]*)"', fragment)
    cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", fragment, re.S)
    return (img.group(1) if img else None,
            html.unescape(alt.group(1)) if alt else "",
            cap.group(1) if cap else "")


def photo(src, alt, caption, paths):
    key = media_key(src) if src else None
    if not key:
        if src:
            warnings.append(f"image outside the uploads: {src}")
            key = html.unescape(src)
        else:
            return ""
    parts = [f"src={param(key)}"]
    caption_md = inline(caption, paths) if caption else ""
    if caption_md:
        parts.append(f"caption={param(caption_md)}")
    if alt and alt != html.unescape(re.sub(r"<[^>]+>", "", caption)).strip():
        parts.append(f"alt={param(alt)}")
    return "{{< photo " + " ".join(parts) + " >}}"


def photos(items, cols=None):
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    head = "{{< photos" + (f' cols="{cols}"' if cols else "") + " >}}"
    return "\n".join([head, *items, "{{< /photos >}}"])


def table(fragment, paths):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", fragment, re.S):
        cells = [inline(c, paths).replace("|", "\\|").replace("\\\n", " ")
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    # The old blog bolds its first row instead of using <th>; it is the header.
    head = [re.sub(r"^\*\*(.*)\*\*$", r"\1", c) for c in rows[0]]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def render(block, paths):
    """One block to markdown. Returns a list of markdown chunks."""
    name, a = block.name, block.attrs
    inner = re.sub(r"\0\d+\0", "", block.inner())

    if name == "paragraph":
        text = inline(re.sub(r"^\s*<p[^>]*>|</p>\s*$", "", inner.strip()), paths)
        return [text] if text else []
    if name == "heading":
        level = a.get("level", 2)
        text = inline(re.sub(r"</?h\d[^>]*>", "", inner.strip()), paths)
        return [f"{'#' * max(level, 2)} {text}"] if text else []
    if name == "image":
        src, alt, cap = figure_parts(inner)
        return [photo(src, alt, cap, paths)]
    if name == "gallery":
        items = [photo(*figure_parts(c.inner()), paths) for c in block.children if c.name == "image"]
        if not items:  # older galleries keep their images inline
            items = [photo(*figure_parts(f), paths) for f in re.findall(r"<figure.*?</figure>", inner, re.S)]
        return [photos(items, a.get("columns"))]
    if name in ("jetpack/slideshow", "jetpack/tiled-gallery", "jetpack/story"):
        srcs = re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', block.inner())
        srcs += [f.get("url", "") for f in a.get("mediaFiles", []) if f.get("type", "image").startswith("image")]
        seen, items = set(), []
        for s in srcs:
            k = media_key(s) or s
            if k not in seen:
                seen.add(k)
                items.append(photo(s, "", "", paths))
        return [photos(items)]
    if name in ("list", "list-item"):
        items = re.findall(r"<li[^>]*>(.*?)</li>", inner, re.S) if name == "list" else []
        if name == "list" and block.children:
            items = [re.sub(r"^\s*<li[^>]*>|</li>\s*$", "", c.inner().strip()) for c in block.children]
        ordered = a.get("ordered", False)
        return ["\n".join(f"{i + 1}. " * ordered + "- " * (not ordered) + inline(t, paths) for i, t in enumerate(items))]
    if name in ("quote", "pullquote"):
        text = "\n\n".join(c for child in block.children for c in render(child, paths))
        if not text:
            text = inline(re.sub(r"</?(blockquote|p|cite)[^>]*>", "\n", inner), paths)
        return ["\n".join("> " + line if line else ">" for line in text.splitlines())]
    if name == "table":
        return [table(inner, paths)]
    if name == "html":
        maps = re.findall(r"\[googlemaps\s+([^\]\s]+)\]", inner)
        if maps:
            out = []
            for url in maps:
                url = html.unescape(url)
                url = re.sub(r"&(w|h)=\d+", "", url)
                out.append("{{< routemap src=" + param(url) + " >}}")
            return out
        warnings.append("raw html block kept as is")
        return [inner.strip()]
    if name in ("spacer", "separator", "jetpack/subscriptions", "jetpack/contact-form", "more"):
        return []
    if name == "media-text":
        src, alt, cap = figure_parts(inner)
        out = [photo(src, alt, cap, paths)] if src else []
        for child in block.children:
            out += render(child, paths)
        return out
    if block.children or name in ("group", "columns", "column", "cover"):  # wrappers
        out = []
        for child in block.children:
            out += render(child, paths)
        return out
    warnings.append(f"unhandled block wp:{name}, kept as html")
    return [inner.strip()] if inner.strip() else []


def convert(body, paths):
    root = parse_blocks(body)
    if not root.children:  # classic-editor post: no blocks
        chunks = [inline(p, paths) for p in re.split(r"\n\s*\n", body)]
    else:
        chunks = [c for child in root.children for c in render(child, paths)]
    return "\n\n".join(c for c in chunks if c and c.strip()) + "\n"


# -- front matter -------------------------------------------------------------

def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export", type=Path)
    ap.add_argument("out", type=Path, help="e.g. content/en/trips")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = ET.parse(args.export).getroot()
    items = list(root.iter("item"))
    attachments = {
        i.findtext("wp:post_id", namespaces=NS): i.findtext("wp:attachment_url", namespaces=NS)
        for i in items if i.findtext("wp:post_type", namespaces=NS) == "attachment"
    }

    posts = []
    for it in items:
        if it.findtext("wp:post_type", namespaces=NS) != "post":
            continue
        status = it.findtext("wp:status", namespaces=NS)
        if status not in ("publish", "private", "draft"):
            continue
        cats = [c.get("nicename") for c in it.findall("category") if c.get("domain") == "category"]
        trip = next((TRIPS[c] for c in cats if c in TRIPS), DEFAULT_TRIP)
        slug = clean_slug(it.findtext("wp:post_name", namespaces=NS) or it.findtext("title"))
        meta = {pm.findtext("wp:meta_key", namespaces=NS): pm.findtext("wp:meta_value", namespaces=NS)
                for pm in it.findall("wp:postmeta", NS)}
        posts.append(dict(item=it, status=status, trip=trip, slug=slug, meta=meta))

    paths = {p["slug"]: f"/trips/{p['trip']}/{p['slug']}/" for p in posts}

    for p in posts:
        it = p["item"]
        warnings.clear()
        gmt = it.findtext("wp:post_date_gmt", namespaces=NS)
        if gmt and not gmt.startswith("0000"):
            date = datetime.strptime(gmt, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).isoformat()
        else:
            date = it.findtext("wp:post_date", namespaces=NS).replace(" ", "T")
        title = html.unescape(it.findtext("title") or p["slug"]).strip()
        image = media_key(attachments.get(p["meta"].get("_thumbnail_id"), "") or "")
        body = convert(it.findtext("content:encoded", namespaces=NS) or "", paths)

        fm = ["---", f"title: {yaml_str(title)}", f"date: {date}"]
        if p["status"] != "publish":
            fm.append(f"draft: true  # was {p['status']} on WordPress")
        if image:
            fm.append(f"image: {image}")
        fm += ["content_language: de", f"wordpress_url: {it.findtext('link')}", "---", ""]

        target = args.out / p["trip"] / f"{p['slug']}.md"
        for w in warnings:
            print(f"{target}: {w}", file=sys.stderr)
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(fm) + "\n" + body, encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
