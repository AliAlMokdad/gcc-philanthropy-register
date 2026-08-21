# -*- coding: utf-8 -*-
"""The one definition of a register entity's identity.

WHY THIS FILE EXISTS. Two live relationships were keyed to a row's POSITION in data.json:
vectors.json declares "row i of vectors.bin corresponds to row i of data.json rows[]", and
tools/news/pipeline.py issued register_id as "r%d" % n. The runtime guard compared only counts,
so deleting one row and adding another, or sorting the workbook, passed validation while pointing
every semantic search result and every news-to-organisation link at a different organisation.
The same id is also the key for editorial decisions in news-decisions.json, so a reorder would
have silenced the wrong organisation.

The exporter emits rows in workbook order, and the workbook is edited by hand, so a reorder is
not a hypothetical.

WHY DERIVED RATHER THAN ASSIGNED. An assigned id (a counter in a new spreadsheet column) has to be
maintained by hand on every new row, forever, and a forgotten cell is a silent gap. A derived id
cannot be forgotten and needs no new discipline. The cost is that renaming an organisation changes
its id, which is the correct behaviour here: the embedding is derived from that same text and the
news matcher matches on that same name, so a rename genuinely is a different record until it is
re-embedded.

WHY (name, country) AND NOT NAME. Dolphin Energy is a UAE and Qatar joint venture and holds two
legitimate rows. It is the only name in the register that repeats, and export_site_data.py already
keys its region lookup by (name, country) for exactly this row. Measured across all 1,862 rows:
(name, country) is unique, name alone collides once.

WHY THE NORMALISER IS THIS TIMID. PROJECT-BRIEF.md records that a stronger one, stripping country
words and legal forms, reduced "Oman Charitable Organization" to the empty string, and every
all-stopword name then keyed to "" and deduped away. Case and whitespace are the only safe
reductions, so they are the only ones made.
"""
import hashlib
import re

PREFIX = "g"
LENGTH = 10           # 2^40 of space; 1,862 rows give collision odds near 1.6e-06, and callers
                      # assert uniqueness anyway so a future collision fails loudly


def norm_key(s):
    """Case and whitespace only. See the docstring on why nothing else is touched."""
    return re.sub(r"\s+", " ", str(s if s is not None else "")).strip().lower()


def entity_id(name, country):
    """The stable id for one register row. Same name and country in, same id out, forever."""
    name = norm_key(name)
    if not name:
        raise ValueError("a register row with no name cannot be identified")
    seed = "%s|%s" % (name, norm_key(country))
    return PREFIX + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:LENGTH]


def ids_for_rows(keys, rows):
    """Ids for a data.json rows[] block, in its own order.

    Raises on a collision rather than returning a list with a duplicate in it, because a duplicate
    id would reintroduce exactly the ambiguity this file exists to remove."""
    ni, ci = keys.index("name"), keys.index("country")
    out, seen = [], {}
    for n, row in enumerate(rows):
        eid = entity_id(row[ni], row[ci])
        if eid in seen:
            raise ValueError(
                "id collision: rows %d and %d both derive %s\n  %r\n  %r"
                % (seen[eid], n, eid, rows[seen[eid]][ni], row[ni]))
        seen[eid] = n
        out.append(eid)
    return out


# The columns a positional index actually depends on. A fingerprint over the NAME alone was the
# first version and it had three holes, all found by review and all reproduced before this changed.
#
#   The register contains two rows named "Dolphin Energy", the UAE and Qatar arms of one joint
#   venture. Swapping them changed nothing a name-only fingerprint or a name-by-name comparison
#   could see, while exchanging their vectors and their theme tags: culture and sport for education
#   and environment. Measured, both guards passed.
#
#   The theme index is derived from the FOCUS column and was protected by a fingerprint over the
#   name. Editing a mandate without rebuilding therefore served the old classification silently.
#
#   The vectors are embedded from the mandate text too, so the same edit invalidates them and was
#   equally invisible.
#
# name, country and focus together close all three: country separates the two Dolphin rows, and
# focus is what both derived artefacts are actually built from.
FINGERPRINT_COLUMNS = ("name", "country", "focus")


def row_fingerprint(keys, rows, columns=FINGERPRINT_COLUMNS):
    """FNV-1a 32 over the columns a positional index depends on.

    Fields are joined by a unit separator and rows by a newline. The separator is chr(31) rather
    than a printable character because the exporter collapses all whitespace but does not strip
    control characters, so a value cannot contain it and two different registers cannot collide by
    a field boundary landing inside a value.

    Ten lines here and ten in index.html, and both are run over the real register in the tests: they
    agree on plain ASCII, on Arabic, on accented Latin, on emoji and on a value containing the
    joiner itself."""
    idx = [keys.index(c) for c in columns]
    sep, rowsep = chr(31), chr(10)
    parts = []
    for r in rows:
        parts.append(sep.join(str(r[i] if r[i] is not None else "") for i in idx))
    h = 0x811c9dc5
    for byte in rowsep.join(parts).encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h
