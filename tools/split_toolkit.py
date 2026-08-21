# -*- coding: utf-8 -*-
"""Split the toolkit corpus so reading one paper costs one paper.

Run from the repo root:
    python tools/split_toolkit.py                report only
    python tools/split_toolkit.py --write        apply

WHY. toolkit/notes.json is 279 KB, 65 KB over the wire, and it is fetched in full before the router
decides which paper you asked for. Opening one 7 KB paper therefore downloads all thirty-five. That
was tolerable while the toolkit was reached only through its own landing page. The country hubs now
link straight to individual papers from six member pages, so that path is the common one rather than
the rare one. Measured: the catalog plus one paper is 12.1 KB gzipped against 65.3 KB, an 81 per cent
saving on a deep link.

WHAT IS WRITTEN.
  toolkit/catalog.json      everything except the body: ids, slugs, titles, volumes, jurisdictions,
                            topics, keywords, minutes, reference counts and abstracts. Enough to
                            build every section, every list and the landing page. 8.3 KB gzipped.
  toolkit/papers/<slug>.json  one paper, with its sections and its references.

notes.json IS KEPT AND STILL SHIPPED, unchanged, because the toolkit's search reads the full body
text of every paper and that is the right behaviour to preserve. It is now fetched only when someone
types in the search box, instead of on every visit. Nobody who arrives to read one paper pays for
the search index any more.

Nothing is derived, summarised or rewritten. Every field is copied verbatim, and the check at the end
reassembles the corpus from the pieces and compares it to the original.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "toolkit", "notes.json")
CAT = os.path.join(ROOT, "toolkit", "catalog.json")
PAPERS = os.path.join(ROOT, "toolkit", "papers")
WRITE = "--write" in sys.argv

# what the landing page, the section lists and the router need. The body is what they do not.
LIGHT = ("id", "slug", "title", "volume", "family", "jurisdictions", "topic", "keywords",
         "minutes", "ref_count", "abstract", "words")
BODY = ("sections", "refs")


def dump(path, obj):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline=chr(10)) as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write(chr(10))
    os.replace(tmp, path)


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    notes = d["notes"]

    # anything on a note that is neither light nor body would be silently dropped, so find out
    extra = set()
    for n in notes:
        extra |= set(n.keys()) - set(LIGHT) - set(BODY)
    if extra:
        # the private search fields the page builds at runtime are not in the file
        print("  fields that are neither catalog nor body: %s" % sorted(extra))
        print("  they would be lost. Add them to LIGHT or BODY before writing.")
        if WRITE:
            sys.exit(2)

    slugs = [n["slug"] for n in notes]
    if len(set(slugs)) != len(slugs):
        sys.exit("duplicate slugs, so one paper file would overwrite another")

    catalog = {k: v for k, v in d.items() if k != "notes"}
    catalog["notes"] = [{k: n[k] for k in LIGHT if k in n} for n in notes]

    print("  papers                 : %d" % len(notes))
    print("  notes.json             : %6.1f KB" % (os.path.getsize(SRC) / 1024))
    cb = json.dumps(catalog, ensure_ascii=False, separators=(",", ":")).encode()
    print("  catalog.json would be  : %6.1f KB" % (len(cb) / 1024))
    per = [len(json.dumps({k: n[k] for k in BODY if k in n}, ensure_ascii=False,
                          separators=(",", ":")).encode()) for n in notes]
    print("  one paper file         : %6.1f KB median, %.1f KB largest"
          % (sorted(per)[len(per) // 2] / 1024, max(per) / 1024))

    if not WRITE:
        print()
        print("nothing written. Re-run with --write to apply.")
        return

    os.makedirs(PAPERS, exist_ok=True)
    dump(CAT, catalog)
    for n in notes:
        dump(os.path.join(PAPERS, n["slug"] + ".json"),
             {"slug": n["slug"], "id": n.get("id"),
              **{k: n[k] for k in BODY if k in n}})

    # REASSEMBLE AND COMPARE, because a split that loses a paragraph is worse than no split
    back_cat = json.load(io.open(CAT, encoding="utf-8"))
    rebuilt = []
    for lite in back_cat["notes"]:
        body = json.load(io.open(os.path.join(PAPERS, lite["slug"] + ".json"), encoding="utf-8"))
        merged = dict(lite)
        for k in BODY:
            if k in body:
                merged[k] = body[k]
        rebuilt.append(merged)
    original = [{k: n[k] for k in list(LIGHT) + list(BODY) if k in n} for n in notes]
    if rebuilt != original:
        bad = [i for i, (a, b) in enumerate(zip(rebuilt, original)) if a != b]
        sys.exit("the split does not reassemble: %d papers differ, first at %d (%s)"
                 % (len(bad), bad[0], notes[bad[0]]["slug"]))
    print()
    print("  written: catalog.json %.1f KB and %d files under toolkit/papers/"
          % (os.path.getsize(CAT) / 1024, len(notes)))
    print("  verified: the pieces reassemble into the original corpus exactly")


if __name__ == "__main__":
    main()
