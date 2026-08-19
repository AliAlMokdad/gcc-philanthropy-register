# What has actually been verified in this register, and what has not

Written 19 August 2026. The point of this file is that a later session can see the evidence
position without redoing the work, and cannot mistake "a researcher said so" for "checked".

## The strongest evidence: reconciliation against the governments' own registries

### Oman. Reconciled against jood.om, the Ministry of Social Development platform.

101 licensed bodies were pulled from the registry and matched against the 124 Omani rows.

- **99 rows confirmed** by name against the registry.
- **13 of the 14 rows that carry no website, email or phone were confirmed.** Those were the
  weakest rows in the whole register, the wilayat charity teams, and they are now evidenced
  against the state's own list rather than a researcher's word.
- 1 row was RENAMED from the registry: "Halaniyat Charity" came from a garbled research line
  and is properly the Shalim and Al Hallaniyat Islands team, فريق شليم وجزر الحلانيات.
- 1 row is absent from the registry and verified another way: the International Istiqama
  Muslim Charitable Association, whose own live site states a registered Omani non-profit in
  Al-Khoudh, Muscat. Jood lists domestically focused societies, and this one works in East
  Africa, which explains the absence.
- The registry holds one body the register does not: جمعية هواة الطيور, a bird enthusiasts
  association, which is not a funder.

### Kuwait. Reconciled against kuwaitaid.org, the national charitable platform.

The platform states **153 licensed organisations, 83 societies and 70 mabarrat**. The page
renders 78 of them, so this reconciliation covers 51% of the registry.

- **44 rows confirmed** on a distinctive proper noun, never on generic wording. Dashti,
  Al Wazzan, Bou Khamseen, Al Babtain, Al Baharna, Al Fowadrah, Al Adaween, Al Kanadra,
  Al Rashaidah, Baqer, Ghanaim, Al Naqi and the rest.
- **13 of the 42 contactless rows confirmed.** The other 29 are not disproved: the capture is
  half the registry, so absence from it is not evidence of anything.
- **31 registry entries have NO counterpart in the register.** That is a coverage gap, listed
  in `C:\w\recon`, and worth closing.
- Incidental confirmation: the Kuwait Charitable Union's own site links to manabi3.org and
  alestkama.org, two domains that were cleared as dead. The organisations are real; only the
  domains had lapsed, which is why the rows were kept and only the links removed.

### Bahrain. NOT reconciled against a registry.

This is the weakest of the three and should be read that way. khairplus.com, the national
donation platform, does not publish a scrapable list of societies, and no other Bahraini
registry was reachable. Bahrain's evidence is therefore only:

- 119 of 179 rows have a website whose domain resolves.
- 11 of the remaining 60 carry a phone number.
- **49 Bahraini rows carry no website, no email and no phone, and no registry match.** They
  came from the SADAD platform listing per the research, and that has not been independently
  confirmed. These are the least evidenced rows in the register.

## What has NOT been checked anywhere, for any country

- **The mandate text.** What each organisation actually funds is the field a fundraiser reads
  most, and it was written by the researchers from what they read. It has not been checked
  against source, row by row.
- **Emails were checked for shape, never sent. Phones were never dialled.**
- The independent review covered 60 of the 518 new rows. Of three partners asked, only Codex
  delivered: Gemini fabricated every URL it proposed, and Grok was out of quota.

## What every row HAS passed

- Its website, where it has one, resolves by DNS and usually by HTTP. Checked twice, from
  scratch, on the whole set.
- Its Type is one of the 26 the site groups by. No 27th category has ever been introduced.
- It is not a duplicate of another row, on a normalised name within a country.
- No em dashes, no malformed emails, no malformed URLs.

## The search, rewritten 19 August 2026, and what was measured

The word pass used to be a single whole-string `indexOf` over eight concatenated fields,
sorted alphabetically. Two consequences, both measured against this `data.json` rather than
estimated:

- A two word query only matched when those words sat adjacent in that order. **"orphan
  education" returned 0** while 31 mandates cover both. So did "Saudi orphans",
  "entrepreneurship women" and "refugees education".
- It matched inside words. **"men" returned 863 rows** on the strength of "development" and
  "management". "ship" returned 291 on "partnerships". "art" returned 261 on "partner".
- A query written in Arabic normalised to the empty string, and empty meant no filter, so it
  **returned all 1,862 rows as though every one had matched**. There is no Arabic anywhere in
  the data, so the honest answer is none.

### What was checked

- **All 1,862 row strings are byte-identical under the old and new normaliser.** Every field
  in data.json was also checked for a non-ASCII character: there are none. So widening the
  normaliser to keep Unicode letters changes what a QUERY can be and nothing about the data.
- **54 assertions** run against the engine sliced verbatim out of `index.html`, so the test
  cannot drift from what ships. Word pass only, no network, so every number is repeatable.
  They live in `tools/search-test/`, and `node tools/search-test/run.js` re-runs them. A test
  that is not in the repository cannot be checked by anyone else, which a reviewer rightly
  said of the earlier version of this claim.
- Precision was checked against the data itself, not against the engine's own opinion:
  Kuwait plus "orphan" returns exactly the 12 Kuwaiti rows whose text says orphan, no more and
  no fewer; "cancer" and "widows" each return every row whose text carries the word.
- Three independent review passes. The first returned NOT READY with 8 accuracy findings and
  5 bug findings. The second, after those fixes, returned NOT READY again with 8 more,
  including one the first round's fix had introduced: a coercion inside the id check changed
  a local copy while the filter kept the original, so a fractional id could pass a check
  meant for a whole one. It also caught four claims in code comments that were false as
  written, among them a stale architecture note still describing 1,344 rows, a 504 KB vector
  file and a rank-fusion step the code no longer performs. All of those were fixed.
  A sentence in an earlier draft of THIS section said the second review found no defects.
  That was written before the second review returned, and it was false.

### Counts, and the distinction that matters

A word-pass count and a final count are different numbers, because the meaning pass adds rows
the words never reached. Quoting one as the other is how a figure here would become wrong.

| Query | Word pass | Final, after the meaning pass |
|---|---:|---:|
| orphan education | 31 | 34 |
| waqf | 199 | 201 |
| support for widows | 6 | 24 |
| clean water | 3 | 3 |

### What the search does NOT do

- **No negation.** "no cancer" is not read as "everything except cancer". The words are left in
  rather than deleted, so the answer falls through to the labelled partial set instead of
  confidently returning the opposite, which is what deleting them did.
- **No Arabic.** The normaliser no longer destroys an Arabic query, but the data is English and
  the embedding model is English, so an Arabic search is not supported, it merely fails
  honestly now.
- **The synonym and broadening maps are hand-written.** They are grounded in vocabulary counted
  from the corpus, not invented, but they are a judgement. Where a row is reached through one
  rather than through the reader's own words, the count says so.

## The rule that produced this file

Domain resolution proves a domain exists. It does not prove an organisation funds anything,
and it says nothing at all about a row with no domain. Those are different claims and this
file keeps them apart.
