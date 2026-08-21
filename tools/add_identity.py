# -*- coding: utf-8 -*-
"""Make the vector index name what it indexes, so a reorder cannot go unnoticed.

Run from the repo root:
    python tools/add_identity.py                 report only, writes nothing
    python tools/add_identity.py --write         apply

THE PROBLEM. Two live relationships were keyed to a row's POSITION in data.json. vectors.json
declares "row i of vectors.bin corresponds to row i of data.json rows[]", and
tools/news/pipeline.py issued register_id as "r%d" % n. The runtime guard compared COUNTS, so
deleting one row and adding another, or sorting the workbook the exporter reads in sheet order,
kept the count identical and moved every row. Semantic search would answer with one organisation's
mandate under another's name, news would credit the wrong body, and the register_id is also the
key for editorial drops in news-decisions.json, so a suppressed false match would have started
suppressing a real one.

WHAT IT WRITES. vectors.json gains "names": the register's own name column, in vectors.bin row
order. The browser then compares what row i claims to be against what row i actually is.

WHY NAMES AND NOT AN ID COLUMN IN data.json. Both work. An id column was built first and measured:
it cost 17.5 KB gzipped on EVERY first load, because the portal fetches the whole register for its
search box. The names already exist in the register, so echoing them into vectors.json costs 19 KB
gzipped on a file that is fetched only when meaning search is first used and never on load. Zero on
the critical path, for a check that is stronger rather than weaker: comparing the actual name needs
no hash, no crypto and no agreement about a hashing rule between Python and the browser.

The compact hashed id from tools/identity.py is still the right thing for a reference that has to
travel between files, which is why the news pipeline uses it. It is not needed here.

WHAT IT DOES NOT DO. It does not re-embed. The vectors are unchanged and still correct; this
records what the existing rows ARE, in the order they already sit in. Re-embedding is
build_vectors.py's job and is only needed when mandate text changes.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
VEC = os.path.join(ROOT, "vectors.json")
WRITE = "--write" in sys.argv


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def save(path, obj):
    """Temp file then rename, so a crash cannot leave a half file for the page to fetch."""
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def main():
    data = load(DATA)
    keys, rows = data["keys"], data["rows"]
    ni = keys.index("name")
    names = [str(r[ni] or "") for r in rows]
    blank = [i for i, s in enumerate(names) if not s.strip()]
    print("register            : %d rows" % len(rows))
    if blank:
        sys.exit("rows %s have no name and cannot be identified" % blank[:5])

    vec = load(VEC)
    if vec.get("count") != len(rows):
        sys.exit("vectors.json count %s does not match %d register rows.\n"
                 "The index is already out of step. Re-run build_vectors.py first."
                 % (vec.get("count"), len(rows)))
    print("vectors.json        : count %d matches the register" % vec["count"])

    if vec.get("names") == names:
        print("names               : already present and in step, nothing to do")
        return

    if "names" in vec:
        diff = [i for i, (a, b) in enumerate(zip(vec["names"], names)) if a != b]
        print("names               : present but %d rows differ" % len(diff))
        for i in diff[:5]:
            print("     row %-5d %r -> %r" % (i, vec["names"][i][:38], names[i][:38]))
    else:
        print("names               : absent, attaching %d" % len(names))

    vec["names"] = names
    vec["note"] = ("row i of vectors.bin is the organisation at row i of data.json rows[]. "
                   "names[i] records which organisation that is, so a reorder is detectable: "
                   "count alone is not, because a reorder keeps the count.")

    if not WRITE:
        print()
        print("nothing written. Re-run with --write to apply.")
        return

    save(VEC, vec)
    back = load(VEC)
    assert back["names"] == names, "vectors.json did not read back with the names written"
    assert back["count"] == len(rows)
    print()
    print("written             : vectors.json (%.0f KB), verified on re-read"
          % (os.path.getsize(VEC) / 1024))
    print("data.json           : untouched, so the first-load payload does not change")


if __name__ == "__main__":
    main()
