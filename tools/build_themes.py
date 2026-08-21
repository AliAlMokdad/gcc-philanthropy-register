# -*- coding: utf-8 -*-
"""Derive a thematic index over the register, and record why every tag was applied.

Run from the repo root:
    python tools/build_themes.py                report and coverage only
    python tools/build_themes.py --write        write shared/themes.json
    python tools/build_themes.py --audit N      print N tagged rows with their evidence

WHY A THEME AXIS AT ALL. The register's `type` column is a legal FORM (Family Foundation, Islamic
Charity/Waqf, Sovereign/State Fund). The toolkit's `topic` is a PRACTICE area (Registration, Tax
treatment). Flows carries OCHA FTS SECTORS and oecd.json carries OECD DAC sectors. None of those is
what a reader means when they ask who funds education. That question has no answer anywhere on the
site, because the register's focus column is free text: 1,692 distinct strings across 1,862 rows.

WHY DERIVED AND WHY IT IS NOT A CLAIM ABOUT THE ORGANISATION. Assigning a theme by hand to 1,862
organisations is a research project, and guessing one is worse than having none: a wrong theme on a
funder is a factual error on a public register. So this asserts nothing about what an organisation
does. It records that its OWN stated focus mentions a term, and it keeps the matched terms with the
tag so any single tag can be traced back to the words that produced it and overruled. Nothing is
written into data.json: the index is a separate file, and the register's text stays the only source.

WHERE THE TERMS COME FROM. The corpus, not a standard. The commonest content words in the focus
column are community 446, social 363, education 337, charitable 322, support 265, development 249,
relief 229, health 193, research 180, sustainability 171. The groupings below are built around what
the register actually says, and each carries the DAC and FTS families it corresponds to so the
existing sector data can be crosswalked later rather than re-tagged. The DAC numbers are
deliberately absent: a partner's proposed crosswalk had 120 labelled as education infrastructure
when 120 is health and 110 is education, and had one code serving two themes, so the family names
are given and the codes are left to be taken from the source.

FOUR TERMS WERE REMOVED AFTER AUDITING THEM, and the removals matter more than the additions.
"charitable" drove 311 of the welfare rows and names the vehicle rather than the cause: "the Al
Jomaih charitable foundations", "family charitable and endowment giving". "family" drove 260 of the
439 women rows and in this corpus overwhelmingly means "family business group", a legal form.
"empowerment" is as often youth empowerment as women's. Bare "special" caught special projects and
special talent alongside special needs, so it is now the phrase. One term was suspected and cleared:
all ten uses of "down" are Down syndrome.

A row that matches nothing stays untagged. An empty result is the honest one.
"""
import io
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "shared", "themes.json")
AUDIT_OUT = os.path.join(ROOT, "shared", "themes-evidence.json")
WRITE = "--write" in sys.argv
AUDIT = 0
if "--audit" in sys.argv:
    i = sys.argv.index("--audit")
    AUDIT = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 12

# Each theme is a label, the terms that select it, and the vocabularies it lines up with.
# Terms are matched on word boundaries against the lowercased focus text, so "art" does not
# match "heart" and "aid" does not match "said".
THEMES = [
    ("education", "Education and research",
     ["education", "educational", "school", "schools", "schooling", "university",
      "universities", "scholarship", "scholarships", "student", "students", "literacy",
      "teaching", "teacher", "teachers", "vocational", "stem", "research",
      "academic", "curriculum", "learning"],
     {"dac": "Education", "fts": "Education"}),
    ("health", "Health and medical care",
     ["health", "healthcare", "medical", "hospital", "hospitals", "clinic", "clinics",
      "disease", "diseases", "cancer", "diabetes", "surgery", "surgical", "treatment",
      "patients", "nursing", "mental", "eye", "blood", "vaccination", "nutrition"],
     {"dac": "Health", "fts": "Health, Nutrition"}),
    ("relief", "Humanitarian relief",
     ["humanitarian", "relief", "emergency", "emergencies", "disaster", "disasters",
      "refugee", "refugees", "displaced", "famine", "earthquake", "crisis", "conflict",
      "shelter", "aid"],
     {"dac": "Humanitarian aid", "fts": "Shelter and NFI, Logistics, Coordination"}),
    ("welfare", "Poverty and social welfare",
     ["poverty", "poor", "needy", "welfare", "alms", "destitute",
      "underprivileged", "low-income", "housing", "food", "meals", "iftar", "debt",
      "assistance", "hardship"],
     {"dac": "Social infrastructure and services", "fts": "Food Security, Early Recovery"}),
    ("environment", "Water, environment and climate",
     ["water", "wells", "sanitation", "hygiene", "environment", "environmental", "climate",
      "sustainability", "sustainable", "renewable", "energy", "conservation", "biodiversity",
      "wildlife", "marine", "recycling", "carbon"],
     {"dac": "Water supply and sanitation, Environmental protection", "fts": "WASH"}),
    ("culture", "Culture, heritage and the arts",
     ["culture", "cultural", "heritage", "arts", "art", "museum", "museums", "music",
      "literature", "poetry", "film", "theatre", "library", "libraries", "archaeology",
      "language", "calligraphy"],
     {"dac": "Culture and recreation", "fts": None}),
    ("islamic", "Islamic giving and endowment",
     ["waqf", "awqaf", "zakat", "sadaqah", "endowment", "endowments", "mosque", "mosques",
      "quran", "quranic", "islamic", "hajj", "umrah", "pilgrimage", "orphan", "orphans",
      "orphanage"],
     {"dac": None, "fts": None}),
    ("children", "Children and youth",
     ["children", "child", "childhood", "youth", "young", "juvenile", "adolescent",
      "kindergarten", "paediatric", "pediatric", "infant", "infants"],
     {"dac": None, "fts": "Child Protection"}),
    ("disability", "Disability and inclusion",
     ["disability", "disabilities", "disabled", "autism", "blind", "blindness", "deaf",
      "hearing", "wheelchair", "rehabilitation", "special needs", "inclusion", "inclusive",
      "down"],
     {"dac": None, "fts": "Protection"}),
    ("women", "Women and girls",
     ["women", "woman", "girls", "girl", "mothers", "maternal", "widows", "gender"],
     {"dac": None, "fts": "Gender-Based Violence"}),
    ("enterprise", "Enterprise and livelihoods",
     ["entrepreneur", "entrepreneurs", "entrepreneurship", "enterprise", "enterprises",
      "startup", "startups", "sme", "smes", "microfinance", "micro-finance", "livelihood",
      "livelihoods", "employment", "jobs", "innovation", "incubator", "accelerator",
      "venture"],
     {"dac": "Banking and financial services, Industry", "fts": "Livelihoods"}),
    ("sport", "Sport and recreation",
     ["sport", "sports", "athletic", "athletics", "football", "recreation", "fitness"],
     {"dac": "Culture and recreation", "fts": None}),
]

COMPILED = [(k, lab, re.compile(r"\b(?:%s)\b" % "|".join(re.escape(t) for t in terms)), xw)
            for k, lab, terms, xw in THEMES]


def main():
    reg = json.load(io.open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
    K = reg["keys"]
    fi, ni, ci = K.index("focus"), K.index("name"), K.index("country")

    rows = []
    counts = Counter()
    per_row_theme_count = Counter()
    for n, r in enumerate(reg["rows"]):
        text = str(r[fi] or "").lower()
        hits = {}
        for key, _lab, rx, _xw in COMPILED:
            found = sorted(set(rx.findall(text)))
            if found:
                hits[key] = found
                counts[key] += 1
        per_row_theme_count[len(hits)] += 1
        rows.append({"i": n, "themes": sorted(hits), "evidence": hits})

    total = len(reg["rows"])
    tagged = sum(1 for r in rows if r["themes"])
    print("  rows                   : %d" % total)
    print("  rows with a theme      : %d  (%.1f%%)" % (tagged, 100.0 * tagged / total))
    print("  rows with none         : %d  (%.1f%%)" % (total - tagged,
                                                       100.0 * (total - tagged) / total))
    print()
    print("  themes per row:")
    for k in sorted(per_row_theme_count):
        print("     %d theme(s) %6d rows" % (k, per_row_theme_count[k]))
    print()
    print("  %-13s %-32s %6s  %s" % ("key", "label", "rows", "share"))
    print("  " + "-" * 62)
    for key, lab, _rx, _xw in COMPILED:
        c = counts[key]
        print("  %-13s %-32s %6d  %5.1f%%" % (key, lab, c, 100.0 * c / total))

    if AUDIT:
        print()
        print("  AUDIT: every tag with the words that produced it, so any one can be overruled")
        shown = 0
        for r in rows:
            if not r["themes"]:
                continue
            i = r["i"]
            print()
            print("   %s  (%s)" % (reg["rows"][i][ni][:66], reg["rows"][i][ci]))
            print("     focus: %s" % str(reg["rows"][i][fi])[:110])
            for k in r["themes"]:
                print("     %-12s <- %s" % (k, ", ".join(r["evidence"][k])))
            shown += 1
            if shown >= AUDIT:
                break

    if not WRITE:
        print()
        print("nothing written. Re-run with --write to apply, or --audit N to inspect.")
        return

    # TWO FILES, and the split is measured. The runtime index is a bitmask per row: one integer
    # whose bit n means themes[n]. That is 2.4KB gzipped. Carrying the matched terms as well is
    # 40KB gzipped, sixteen times more, for information a filter never reads. So the evidence goes
    # to its own file which no browser fetches, and stays the record that lets any single tag be
    # traced back to the words that produced it.
    #
    # The bitmask is keyed by ROW POSITION, which is the coupling this project has just finished
    # removing elsewhere, so it carries a fingerprint of the name column. One integer covers every
    # row. The browser recomputes it in about a millisecond and refuses the index if it disagrees,
    # rather than filtering the wrong organisations.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from identity import name_fingerprint

    order = [k for k, _l, _t, _x in THEMES]
    by_i = {r["i"]: r["themes"] for r in rows if r["themes"]}
    bits = []
    for i in range(total):
        m = 0
        for n, k in enumerate(order):
            if k in by_i.get(i, ()):
                m |= 1 << n
        bits.append(m)

    fp = name_fingerprint(K, reg["rows"])
    runtime = {
        "count": total,
        "name_fingerprint": fp,
        "fingerprint_method": ("FNV-1a 32 over the name column joined by newlines. Recompute it "
                               "before trusting bits[]: this index is keyed by row position and a "
                               "reorder keeps the count."),
        "order": "bits[i] is register row i; bit n of it is themes[n]",
        "themes": [{"key": k, "label": lab, "rows": counts[k]} for k, lab, _t, _x in THEMES],
        "bits": bits,
    }
    evidence = {
        "derived_from": "data.json focus column, %d rows" % total,
        "method": ("A theme is recorded when the organisation's own stated focus text contains one "
                   "of that theme's terms, matched on word boundaries. It is a statement about the "
                   "text, not a judgement about the organisation. Rows matching nothing are left "
                   "untagged."),
        "name_fingerprint": fp,
        "themes": [{"key": k, "label": lab, "terms": t, "crosswalk": x, "rows": counts[k]}
                   for k, lab, t, x in THEMES],
        "rows": [{"i": r["i"], "name": reg["rows"][r["i"]][ni],
                  "country": reg["rows"][r["i"]][ci],
                  "themes": r["themes"], "evidence": r["evidence"]}
                 for r in rows if r["themes"]],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for path, obj, compact in ((OUT, runtime, True), (AUDIT_OUT, evidence, False)):
        tmp = path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline=chr(10)) as f:
            if compact:
                json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
            else:
                json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write(chr(10))
        os.replace(tmp, path)

    back = json.load(io.open(OUT, encoding="utf-8"))
    assert back["bits"] == bits and back["name_fingerprint"] == fp, "runtime index did not read back"
    aud = json.load(io.open(AUDIT_OUT, encoding="utf-8"))
    assert len(aud["rows"]) == tagged, "audit file did not read back with every tagged row"
    # and the two agree about the same rows
    from_bits = sum(1 for m in bits if m)
    assert from_bits == tagged, "bitmask has %d tagged rows, evidence has %d" % (from_bits, tagged)
    print()
    print("  written: shared/themes.json %.1f KB runtime, shared/themes-evidence.json %.0f KB audit"
          % (os.path.getsize(OUT) / 1024, os.path.getsize(AUDIT_OUT) / 1024))
    print("  fingerprint %d, %d tagged rows, both files agree, verified on re-read"
          % (fp, tagged))


if __name__ == "__main__":
    main()
