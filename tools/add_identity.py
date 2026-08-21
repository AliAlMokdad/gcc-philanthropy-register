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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from identity import row_fingerprint, FINGERPRINT_COLUMNS      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the vector builder lives OUTSIDE this repository. Saying "re-run build_vectors.py" without
# saying where sends the reader looking for a file that is not here.
BUILDER = "Desktop/UAE-Philanthropy-Project/scripts/build_vectors.py"
DATA = os.path.join(ROOT, "data.json")
VEC = os.path.join(ROOT, "vectors.json")
WRITE = "--write" in sys.argv
FORCE = "--force" in sys.argv
# States that the vectors were rebuilt immediately before this run. See the block in main() on why
# an index carrying no identity at all cannot be blessed without someone asserting this.
JUST_BUILT = "--vectors-just-built" in sys.argv


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
        sys.exit("vectors.json count %s does not match %d register rows. The index is already "
                 "out of step. Rebuild it first with %s"
                 % (vec.get("count"), len(rows), BUILDER))
    print("vectors.json        : count %d matches the register" % vec["count"])

    fp = row_fingerprint(keys, rows)
    print("fingerprint         : %d over %s" % (fp, ", ".join(FINGERPRINT_COLUMNS)))

    if vec.get("names") == names and vec.get("fingerprint") == fp:
        print("index               : already in step, nothing to do")
        return

    # NO IDENTITY AT ALL IS NOT THE SAME AS BEING IN STEP, and the first version treated it as if
    # it were. With neither names nor fingerprint present there is nothing here that says which rows
    # vectors.bin encodes, so writing the current register's identity into it asserts a
    # correspondence on no evidence whatever. The dangerous sequence is precise: take an index built
    # before identity existed, reorder or edit the workbook, export, run this. Every check passes,
    # because there was never anything to disagree with, and the browser then trusts a file that
    # says the vectors are in an order they are not.
    #
    # This cannot be settled by reading vectors.bin: it holds 1,862 unlabelled 384-dimension
    # vectors and nothing in it names a row. Only whoever just ran the builder knows. So they say
    # so. build_vectors.py writes only model, dims, count and scale, so a genuinely fresh index
    # always lands here, which is why this is a flag and not a refusal.
    fresh = "names" not in vec and "fingerprint" not in vec
    if fresh and not (JUST_BUILT or FORCE):
        print()
        print("REFUSING TO WRITE. vectors.json carries no names and no fingerprint, so there is")
        print("nothing here that says which rows vectors.bin holds, and this script cannot find out:")
        print("the file is unlabelled vectors and only the person who built them knows.")
        print()
        print("  If you have JUST rebuilt the vectors from the current data.json, say so:")
        print("      python tools/add_identity.py --write --vectors-just-built")
        print("  The builder is outside this repository, at")
        print("      %s" % BUILDER)
        print("  and it writes only model, dims, count and scale, so a fresh index always looks")
        print("  like this one.")
        print()
        print("  If you have NOT just rebuilt them, rebuild before running this. Attaching the")
        print("  current register's identity to an older index is how a reorder becomes invisible.")
        sys.exit(3)

    # THIS SCRIPT MUST NOT BLESS A BROKEN INDEX, and the first version did exactly that. It wrote
    # whatever the register currently said into vectors.json without touching vectors.bin. So the
    # sequence "reorder the workbook, export, run this" produced a file claiming an order the
    # vectors did not have, and the browser then compared the register against that file and passed.
    # The guard was made to agree with itself rather than with the embeddings.
    #
    # An index that is already out of step is a re-embed, not a relabel. Only build_vectors.py can
    # fix it, because only it can recompute the vectors for the rows that moved.
    stale = ("fingerprint" in vec and vec["fingerprint"] != fp) or             ("names" in vec and vec["names"] != names)
    if stale and not FORCE:
        print()
        print("REFUSING TO WRITE. vectors.json describes a different register from the one on disk.")
        if "names" in vec and vec["names"] != names:
            diff = [i for i, (a, b) in enumerate(zip(vec["names"], names)) if a != b]
            print("  rows whose name moved : %d" % len(diff))
            for i in diff[:5]:
                print("     row %-5d index says %r, data says %r"
                      % (i, vec["names"][i][:34], names[i][:34]))
        if "fingerprint" in vec and vec["fingerprint"] != fp:
            print("  fingerprint          : index %s, data %s" % (vec["fingerprint"], fp))
            print("                         so a name, a country or a mandate has changed, or rows")
            print("                         have moved, even where every name still matches")
        print()
        print("  vectors.bin holds one embedding per row IN THAT OLD ORDER. Relabelling here would")
        print("  make the browser's check pass while moved rows answered with another")
        print("  organisation's mandate. Rebuild the vectors, which re-embeds every row, then run")
        print("  this again. The builder is outside this repository, at")
        print("      %s" % BUILDER)
        print()
        print("  --force overrides this and is only correct when the vectors have already been")
        print("  rebuilt and it is the labels alone that are behind.")
        sys.exit(3)

    if stale:
        print("index               : FORCED over a stale index")
    elif fresh:
        print("index               : fresh index, attaching %d names and the fingerprint on your"
              % len(names))
        print("                      assurance that the vectors were just rebuilt")
    elif "names" not in vec:
        print("index               : fingerprint present and matching, attaching %d names"
              % len(names))
    else:
        print("index               : names in step, attaching the fingerprint")

    vec["names"] = names
    vec["fingerprint"] = fp
    vec["fingerprint_columns"] = list(FINGERPRINT_COLUMNS)
    vec["note"] = ("row i of vectors.bin is the organisation at row i of data.json rows[]. "
                   "names[i] records which organisation that is, and fingerprint covers name, "
                   "country and focus across every row. The name alone was not enough: two rows "
                   "are called Dolphin Energy, so swapping them was invisible to both a name "
                   "fingerprint and a name-by-name comparison, and the vectors are embedded from "
                   "the mandate text, so editing a focus invalidates them without changing a name.")

    if not WRITE:
        print()
        print("nothing written. Re-run with --write to apply.")
        return

    save(VEC, vec)
    back = load(VEC)
    assert back["names"] == names, "vectors.json did not read back with the names written"
    assert back["fingerprint"] == fp, "vectors.json did not read back with the fingerprint written"
    assert back["count"] == len(rows)
    print()
    print("written             : vectors.json (%.0f KB), verified on re-read"
          % (os.path.getsize(VEC) / 1024))
    print("data.json           : untouched, so the first-load payload does not change")


if __name__ == "__main__":
    main()
