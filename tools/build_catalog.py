# -*- coding: utf-8 -*-
"""Build shared/catalog.json: the one place that says what a country is and where its data is.

Run from the repo root:
    python tools/build_catalog.py                report only
    python tools/build_catalog.py --write        apply

WHY. One country currently answers to five different names across this site. Saudi Arabia is
"Saudi Arabia" in the register, in flows and in the toolkit, "SAU" in oecd.json, "saudi-arabia" as
the register's own route slug, "ksa" as a member page filename while Qatar's is "qatar", and
"saudi" as a toolkit section id. Country display name is the only dimension that joins all five
datasets, and nothing else joins at all. This file gives every one of those forms one owner, so a
join can be written once instead of guessed each time.

It also answers the question no dataset currently answers: is a gap an absence of data or an
absence of work? Bahrain looks missing from flows. It is not. It has one flow of $39,877 against
Saudi Arabia's $10.4bn, which is a fact about Gulf giving, not a hole in the collection. Calling
both "missing" would let absence read as evidence.

GENERATED, NOT WRITTEN. Every value here is read out of the datasets, the member filenames and the
toolkit's own section definitions. Nothing is asserted that is not observable, and re-running after
a data change updates it. The aliases are the variants that actually occur, not a guess at what
someone might type.
"""
import io
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shared", "catalog.json")
WRITE = "--write" in sys.argv

# ISO 3166-1 alpha-3 is the identifier because oecd.json already keys on it, so one of the five
# datasets needs no migration at all.
ISO = {
    "United Arab Emirates": "ARE",
    "Saudi Arabia": "SAU",
    "Qatar": "QAT",
    "Kuwait": "KWT",
    "Bahrain": "BHR",
    "Oman": "OMN",
}

# Coverage is stated per dataset per country, and these are the only values it may take.
#   covered           the dataset holds records for this country
#   aggregate_only    a total exists but no itemised records, which is a fact about the source
#   no_observations   the source was queried and reports nothing for this country
#   not_authored      nobody has written it yet, which says nothing about the country
STATUSES = ["covered", "aggregate_only", "no_observations", "not_authored"]


def _slug(s):
    """index.html's slug(), so the catalog names the route the register actually serves."""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", str(s).lower()))


def load(rel):
    p = os.path.join(ROOT, rel)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main():
    reg = load("data.json")
    flows = load("flows.json")
    news = load("news-feed.json")
    oecd = load("oecd.json")
    notes = load("toolkit/notes.json")

    K = reg["keys"]
    ci, ai = K.index("country"), K.index("area")
    reg_count = Counter(r[ci] for r in reg["rows"])
    reg_areas = {}
    for r in reg["rows"]:
        reg_areas.setdefault(r[ci], set()).add(r[ai])

    # member page slugs, read off the filenames rather than assumed
    mdir = os.path.join(ROOT, "members")
    slugs = sorted(f[:-5] for f in os.listdir(mdir)
                   if f.endswith(".html") and f != "index.html")
    # match a slug to a country: exact name match, else the abbreviation the file uses
    ABBREV = {"ksa": "Saudi Arabia", "uae": "United Arab Emirates"}
    slug_of = {}
    for s in slugs:
        for name in ISO:
            if s == name.lower().replace(" ", "-") or s == name.lower():
                slug_of[name] = s
        if s in ABBREV:
            slug_of[ABBREV[s]] = s
    unmatched = [s for s in slugs if s not in slug_of.values()]
    if unmatched:
        sys.exit("member page slugs with no country: %s" % unmatched)

    # toolkit section ids, read out of its own SECDEF rather than restated here
    tk = io.open(os.path.join(ROOT, "toolkit", "index.html"), encoding="utf-8").read()
    tk_ids = dict(re.findall(r'\{id:"([a-z]+)",name:"([^"]+)"', tk))
    tk_slug = {}
    for sid, nm in tk_ids.items():
        if nm in ISO:
            tk_slug[nm] = sid

    tk_juris = Counter()
    tk_papers = {}
    for n in notes["notes"]:
        for j in (n.get("jurisdictions") or []):
            tk_juris[j] += 1
            tk_papers.setdefault(j, []).append(
                {"slug": n.get("slug"), "title": n.get("title"), "minutes": n.get("minutes")})

    flow_rows = Counter(r["state"] for r in flows["rows"])
    news_primary = Counter(i["primary_gcc_country"] for i in news["items"]
                           if i.get("primary_gcc_country"))

    countries = {}
    for name, iso3 in ISO.items():
        st = (flows.get("states") or {}).get(name) or {}
        if flow_rows.get(name):
            fstatus = "covered"
        elif st.get("flows"):
            fstatus = "aggregate_only"
        else:
            fstatus = "no_observations"

        countries[iso3] = {
            "label": name,
            "aliases": sorted({name, iso3}),
            # the FIVE forms this one country is known by across the site, in one place, which is
            # the whole reason this file exists
            "register_slug": _slug(name),      # #/c/<slug> inside index.html
            "member_slug": slug_of.get(name),  # members/<slug>.html
            "toolkit_section": tk_slug.get(name),
            "papers": tk_papers.get(name, []),
            "register_areas": sorted(a for a in reg_areas.get(name, ()) if a),
            "coverage": {
                "register": {
                    "status": "covered" if reg_count.get(name) else "no_observations",
                    "count": reg_count.get(name, 0)},
                "flows": {
                    "status": fstatus,
                    "itemised_rows": flow_rows.get(name, 0),
                    "reported_usd": st.get("usd"),
                    "reported_flows": st.get("flows")},
                "news": {
                    "status": "covered" if news_primary.get(name) else "no_observations",
                    "count": news_primary.get(name, 0),
                    "window_days": news.get("horizon_days")},
                "toolkit": {
                    "status": "covered" if tk_juris.get(name) else "not_authored",
                    "count": tk_juris.get(name, 0)},
                "oecd": {
                    "status": "covered" if iso3 in (oecd.get("names") or {}) else "no_observations"},
            },
        }

    # places that are not countries. The register's area column and the toolkit's jurisdictions
    # both mix levels, so each value is placed under the country it belongs to and labelled.
    places = {}
    for name, iso3 in ISO.items():
        for a in sorted(a for a in reg_areas.get(name, ()) if a):
            if a == name:
                continue                      # the country itself, not a place within it
            places[a] = {"label": a, "country": iso3, "source": "register.area"}
    for j, n in tk_juris.items():
        if j in ISO:
            continue
        if j == "GCC-wide":
            places[j] = {"label": j, "country": None, "scope": "region",
                         "source": "toolkit.jurisdictions", "count": n}
        else:
            owner = places.get(j, {}).get("country")
            places.setdefault(j, {"label": j, "country": owner,
                                  "source": "toolkit.jurisdictions"})
            places[j]["count"] = n

    cat = {
        "region_papers": tk_papers.get("GCC-wide", []),
        "generated_from": {
            "data.json": len(reg["rows"]),
            "flows.json": flows["meta"].get("built"),
            "news-feed.json": news.get("generated_at"),
            "oecd.json": (oecd.get("meta") or {}).get("built"),
            "toolkit/notes.json": notes.get("compiled"),
        },
        "coverage_statuses": STATUSES,
        "countries": countries,
        "places": places,
    }

    print("countries          : %d" % len(countries))
    for iso3, c in sorted(countries.items(), key=lambda kv: -kv[1]["coverage"]["register"]["count"]):
        cv = c["coverage"]
        print("  %s %-22s reg %4d  flows %-14s news %2d  toolkit %2d  slug %-6s tk %s"
              % (iso3, c["label"], cv["register"]["count"], cv["flows"]["status"],
                 cv["news"]["count"], cv["toolkit"]["count"],
                 c["member_slug"], c["toolkit_section"]))
    print("places             : %d" % len(places))
    for k, v in sorted(places.items()):
        print("  %-24s %s" % (k, v.get("country") or v.get("scope")))

    if not WRITE:
        print()
        print("nothing written. Re-run with --write to apply.")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, OUT)
    back = json.load(io.open(OUT, encoding="utf-8"))
    assert back == cat, "catalog.json did not read back as written"
    print()
    print("written            : shared/catalog.json (%.1f KB), verified on re-read"
          % (os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
