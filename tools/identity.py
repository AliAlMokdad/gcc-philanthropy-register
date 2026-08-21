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


def name_fingerprint(keys, rows):
    """FNV-1a 32 over the name column, joined by newlines.

    A cheap, complete integrity check for any file that indexes the register BY ROW POSITION.
    vectors.json can afford to carry all 1,862 names because it is fetched only when meaning search
    runs. A runtime index cannot: carrying the names costs 19KB gzipped against 2.4KB for the index
    itself. One integer covers every row instead of a sample, and FNV-1a is ten lines in either
    language with no crypto and nothing async.

    Verified against a JavaScript implementation over the real register: both produce 4270336304,
    and the browser computes it in 1.07ms."""
    ni = keys.index("name")
    joined = chr(10).join(str(r[ni] if r[ni] is not None else "") for r in rows)
    h = 0x811c9dc5
    for byte in joined.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h
