# -*- coding: utf-8 -*-
"""One crawlable page per toolkit paper, because the deepest content on the site had no URL.

Run from the repo root:
    python tools/build_paper_pages.py                report only
    python tools/build_paper_pages.py --write        apply

WHAT WAS WRONG. The thirty-five papers are the register's richest material and every one of
them lived behind toolkit/#/<section>/<slug>, a hash route. A hash route is not a URL a server
can serve, so to Google the entire research corpus was one line in the toolkit's description.
The country pages already proved the answer: a static page per thing, with the thing's own
words on it.

NO NEW PROSE. Every word on these pages comes from toolkit/papers/<slug>.json and
toolkit/catalog.json, which are themselves the corpus. Title, abstract, sections, references:
copied verbatim, structured as HTML, nothing summarised and nothing added.

THE CHROME IS PARSED, NOT COPIED. The masthead and footer are read out of faq/index.html at
build time, because that page sits at the same directory depth and its chrome is maintained.
A pasted copy would be the third duplicate of the footer, and the footer duplicate in
index.html has already silently swallowed two shared-sheet changes this week.

Each page carries its own complete head: title, description from the abstract, canonical,
the og/twitter card, and a ScholarlyArticle JSON-LD naming the author and the countries the
paper covers. tools/build_seo.py lists whatever exists in papers/ in the sitemap; it does not
touch these files.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://gccphilanthropy.org"
OUT = os.path.join(ROOT, "papers")
WRITE = "--write" in sys.argv


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def chrome():
    """The theme script, the toggle, the product bar with the masthead, and the footer, all
    read from faq/index.html, which sits at the same directory depth as papers/."""
    src = io.open(os.path.join(ROOT, "faq", "index.html"), encoding="utf-8").read()
    head = re.search(r"(<script>.*?localStorage\.getItem\('gccp-theme'\).*?</script>)", src, re.S)
    bar = re.search(r'(<div class="pbar">.*?</header>)', src, re.S)
    foot = re.search(r'(<footer class="sig">.*?</footer>)', src, re.S)
    toggle = re.search(r'(<button class="themetoggle".*?</button>)', src, re.S)
    if not (head and bar and foot and toggle):
        sys.exit("faq/index.html no longer carries the chrome this script parses")
    pbar = bar.group(1)
    # the faq marks nothing current in the pbar; a paper belongs to the toolkit
    pbar = pbar.replace(' aria-current="page"', "")
    pbar = pbar.replace('<a href="../toolkit/">', '<a href="../toolkit/" aria-current="page">')
    # its orange tab names where the reader is
    pbar = re.sub(r'(<span class="pagetab"[^>]*>)[^<]*(</span>)', r"\g<1>Toolkit\g<2>", pbar)
    return head.group(1), pbar, foot.group(1), toggle.group(1)


# the toolkit's SECDEF, replicated: a paper's route section is its volume's section, or the
# first jurisdiction section that claims it. Kept in this order so the link opens the same
# section the toolkit itself files the paper under.
VOL2SEC = {"Foundations and context": "foundations",
           "Regulation, governance and integrity": "regulation",
           "Capital, partnerships and engagement": "capital",
           "Impact, stewardship and learning": "impact"}
JUR2SEC = [("GCC-wide", "gcc"), ("Qatar", "qatar"), ("Saudi Arabia", "saudi"),
           ("United Arab Emirates", "uae"), ("Dubai", "dubai")]


def section_of(meta):
    sec = VOL2SEC.get(meta.get("volume"))
    if sec:
        return sec
    juris = meta.get("jurisdictions") or []
    for name, sid in JUR2SEC:
        if name in juris:
            return sid
    sys.exit("%s: no toolkit section claims this paper" % meta.get("slug"))


def main():
    cat = json.load(io.open(os.path.join(ROOT, "toolkit", "catalog.json"), encoding="utf-8"))
    notes = {n["slug"]: n for n in cat["notes"]}
    theme_script, pbar, footer, toggle = chrome()
    compiled = cat.get("compiled") or ""

    written = []
    for slug, meta in sorted(notes.items()):
        body = json.load(io.open(os.path.join(ROOT, "toolkit", "papers", slug + ".json"),
                                 encoding="utf-8"))
        url = "%s/papers/%s.html" % (SITE, slug)
        title = meta["title"]
        desc = re.sub(r"\s+", " ", meta.get("abstract") or "").strip()
        if len(desc) > 300:
            desc = desc[:297].rsplit(" ", 1)[0] + "..."
        juris = meta.get("jurisdictions") or []
        sec_html = []
        for sec in body.get("sections") or []:
            h = sec.get("heading")
            if h:
                sec_html.append("<h2>%s</h2>" % esc(h))
            for para in sec.get("paras") or []:
                sec_html.append("<p>%s</p>" % esc(para))
        refs = body.get("refs") or []
        ref_html = ""
        if refs:
            items = []
            for r in refs:
                txt = r.get("text") if isinstance(r, dict) else str(r)
                items.append("<li>%s</li>" % esc(txt))
            ref_html = ("<h2>References</h2><ol class=\"paper-refs\">%s</ol>" % "".join(items))

        ld = {"@context": "https://schema.org", "@type": "ScholarlyArticle",
              "@id": url, "url": url,
              "headline": title, "description": desc, "inLanguage": "en-GB",
              "author": {"@type": "Person", "name": "Ali Al Mokdad",
                         "url": SITE + "/alialmokdad/"},
              "isPartOf": {"@id": SITE + "/#website"},
              "about": [{"@type": "Country", "name": j} for j in juris],
              "wordCount": meta.get("words"),
              "dateModified": compiled}

        page = """<!doctype html>
<!-- NO data-theme ATTRIBUTE. Every other page ships none, so a reader with no stored choice
     gets what their system says. Shipping "light" here forced 35 light pages on a dark-mode
     reader whose other 14 pages were dark. The head script still applies a stored choice. -->
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(t)s | GCC Philanthropy Toolkit</title>
<meta name="description" content="%(d)s">
<link rel="canonical" href="%(u)s">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Gulf Cooperation Council (GCC) Philanthropy">
<meta property="og:url" content="%(u)s">
<meta property="og:title" content="%(t)s">
<meta property="og:description" content="%(d)s">
<meta property="og:image" content="%(site)s/og-card.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Gulf Cooperation Council (GCC) Philanthropy, with the flags of the United Arab Emirates, Saudi Arabia, Kuwait, Bahrain, Qatar and Oman.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="%(site)s/og-card.png">
<meta name="twitter:title" content="%(t)s">
<meta name="twitter:description" content="%(d)s">
<link rel="icon" type="image/svg+xml" href="../gcc-emblem.svg">
<link rel="stylesheet" href="../shared/tokens.css">
<link rel="stylesheet" href="../shared/chrome.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="../shared/doc.css">
<script type="application/ld+json">%(ld)s</script>
%(theme)s
<style>
/* the reading column, in the doc idiom the faq and legal pages already use.
   THE SHEET IS NOT OPTIONAL. The first build set prose straight onto the skyline
   background; on a phone the abstract's last lines ran into the saturated blue and
   every other document page (faq, legal) reads off a white sheet. Same construction
   here: .doc-wrap > .container > .sheet from shared/doc.css, prose capped inside it. */
.paper-wrap{max-width:860px;margin:0 auto}
/* the faq's sheet opens to 1200 because a section-index rail rides beside its prose.
   A paper has no rail, so at that width the sheet is half empty on the right; it closes
   up to hold just the reading column. */
.sheet{max-width:960px}
.paper-meta{margin:14px 0 0;font:600 11px/1.6 var(--mono);letter-spacing:.12em;
  text-transform:uppercase;color:var(--ink-3)}
.paper-abstract{margin:22px 0 0;font:500 17.5px/1.6 var(--serif);color:var(--ink-2)}
.paper-body h2{margin:38px 0 12px;font:600 22px/1.25 var(--serif);color:var(--ink)}
.paper-body p{margin:0 0 14px;font:400 16px/1.65 var(--serif);color:var(--ink);max-width:72ch}
.paper-refs{margin:8px 0 0;padding-left:22px}
.paper-refs li{margin:0 0 10px;font:400 13.5px/1.55 var(--serif);color:var(--ink-2);
  overflow-wrap:anywhere}
.paper-back{display:inline-flex;align-items:center;min-height:44px;margin:26px 0 0;
  font:600 12.5px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);text-decoration:none}
.paper-back:hover{text-decoration:underline}
h1{margin:6px 0 0;font:600 clamp(26px,3.4vw,38px)/1.18 var(--serif);
  letter-spacing:-.015em;color:var(--ink);max-width:26ch}
</style>
</head>
<body>
%(toggle)s
%(pbar)s
<main>
 <div class="doc-wrap"><div class="container"><div class="sheet">
  <div class="paper-wrap">
    <p class="paper-meta">%(vol)s · %(juris)s · %(min)s min read · %(nref)s reference%(refpl)s</p>
    <h1>%(t)s</h1>
    <p class="paper-abstract">%(abs)s</p>
    <div class="paper-body">
%(body)s
%(refs)s
    </div>
    <a class="paper-back" href="../toolkit/#/%(fam)s/%(slug)s">Read in the interactive toolkit</a>
  </div>
 </div></div></div>
</main>
%(footer)s
</body>
</html>
""" % {"t": esc(title), "d": esc(desc), "u": url, "site": SITE,
            "ld": json.dumps(ld, ensure_ascii=False, separators=(",", ":")),
            "theme": theme_script, "toggle": toggle, "pbar": pbar, "footer": footer,
            "vol": esc(meta.get("volume") or "Toolkit"),
            "juris": esc(", ".join(juris) or "GCC"),
            "min": esc(meta.get("minutes") or "?"),
            "nref": len(refs), "refpl": "" if len(refs) == 1 else "s",
            "abs": esc(re.sub(r"\s+", " ", meta.get("abstract") or "").strip()),
            "body": "\n".join(sec_html), "refs": ref_html,
            "fam": esc(section_of(meta)), "slug": esc(slug)}
        written.append((slug + ".html", page))

    print("  papers: %d, chrome parsed from faq/index.html" % len(written))
    if not WRITE:
        print("nothing written. Re-run with --write to apply.")
        return
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for fn, page in written:
        tmp = os.path.join(OUT, fn + ".tmp")
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(page)
        os.replace(tmp, os.path.join(OUT, fn))
    print("  written: %d pages under papers/" % len(written))


if __name__ == "__main__":
    main()
