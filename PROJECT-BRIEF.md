# GCC Philanthropy Register. Read this first.

Last worked 19 August 2026. This is the single entry point. If you are a Claude session
picking this up cold, read this file and `VERIFICATION.md` in the repo before touching
anything, and do not trust any older status file in this folder over this one.

Note the folder is still called `UAE-Philanthropy-Project`. The project outgrew that name
when it went GCC-wide. It has NOT been renamed, because programmatic moves against the
OneDrive Desktop are barred on this machine. Ali can rename it in Explorer if he wants.

---

## 1. What this is

A register of philanthropic funders, donors, foundations, corporate giving programmes,
endowments and impact investors across all six GCC states. It exists as two deliverables:

**The Excel**, which is the master.
`Desktop\UAE-Philanthropy-Project\GCC-Philanthropy-Donors-Funders another version.xlsx`
1,862 organisations, 22 tabs, 12 columns, 5,084 live hyperlinks.

> **Read the filename twice.** The master is the one whose name ends "another version". The file
> beside it called plainly `GCC-Philanthropy-Donors-Funders.xlsx` is an older UAE-era workbook:
> 1,344 rows, 19 tabs, no Kuwait, no Bahrain, no Oman. This brief used to name that one, and its
> row and tab counts above have always described the other file. Exporting from the wrong one
> removes 518 rows, empties three countries, prints "rows exported : 1344" and exits 0, so nothing
> about the run looks wrong. `export_site_data.py` now refuses a shrink and names what would
> disappear, but a guard only helps after the wrong file has already been opened.
>
> Verified 21 August 2026: exporting from "another version" reproduces the committed data.json
> byte for byte. That is what makes it the master, not its name.

**The website**, public, built from the Excel.
Live: https://alialmokdad.github.io/gcc-philanthropy-register/
Repo: `C:\repos\gcc-philanthropy-register` (deliberately OUTSIDE OneDrive; OneDrive
corrupts git). Deploys via GitHub Pages on push to `main`.

Ali's stated bar, in his words: accurate, cover them all, zero AI fingerprint, and
"I want it excellent. I want perfection."

---

## 2. Current state, by the numbers

| Country | Rows |
|---|---|
| United Arab Emirates | 689 |
| Saudi Arabia | 542 |
| Kuwait | 199 |
| Bahrain | 179 |
| Qatar | 129 |
| Oman | 124 |
| **Total** | **1,862** |

26 organisation categories. Do not let that number grow: the site groups by it, and a 27th
value silently creates a 27th category on the landing page. The controlled list is in
`scripts\verify_additions.py` as `TYPES`.

History: began as UAE only, went to 1,344 across UAE, Saudi and Qatar, then on 18 to 19
August 2026 gained 518 rows covering Kuwait, Bahrain and Oman plus GCC-wide impact and
capital investors.

---

## 3. The pipeline. Do it in this order.

```
research (agents, web)  ->  scripts\verify_additions.py   THE GATE, never skip
                        ->  scripts\add_to_workbook.py    appends to Ali's Excel
                        ->  scripts\export_site_data.py   Excel -> repo\data.json
                        ->  scripts\build_vectors.py      re-embeds ALL rows
                        ->  verify in a browser, then push
```

Interpreter, and it is NOT on PATH:
`C:\Users\Ali Al Mokdad\AppData\Local\Python\bin\python.exe`

### The gate, in detail

`scripts\verify_additions.py <files...> [--existing baseline.json]`

It resolves every website by **DNS and HTTP separately**, dedupes against what is already
in the register, enforces the 26-value Type list, and flags em dashes and malformed emails.
It reports; it never auto-corrects.

**Read the docstrings before changing it.** Three of its rules exist because a simpler
version got the answer wrong:

- **DNS is checked separately from HTTP.** An HTTP-only check marked the Kuwait Fund for
  Arab Economic Development as dead. Its site times out from this network; its domain
  resolves perfectly. Oman Development Bank failed the same way. Both are unmistakably real.
- **A 3xx is not a failure.** Counting redirects as errors flagged 22 live rows, including
  Al Tamimi and Company and Sharjah's Shurooq.
- **The name normaliser falls back.** Stripping country words and legal forms reduces
  "Oman Charitable Organization" to an empty string, and every all-stopword name would then
  key to "" and be deduped away as a duplicate.

### Rebuilding the search index

`build_vectors.py` re-embeds **every** row, not just new ones, into `vectors.bin` plus
`vectors.json`. Needs `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` (already in Ali's
user env). Model `@cf/baai/bge-small-en-v1.5`, 384 dims, L2-normalised, int8.

**If you add rows and skip this, meaning search silently covers only the old rows and
returns nothing for the new ones.** Always assert `vectors.json.count == len(data.rows)`.

---

## 4. What is verified and what is not. This is the important section.

Full detail in `C:\repos\gcc-philanthropy-register\VERIFICATION.md`, which is committed so
it travels with the site. Summary:

**Reconciled against the governments' own registries.**
- **Oman: 99 of 124 rows** confirmed against `jood.om`, the Ministry of Social Development
  platform. Including **13 of the 14 rows that carry no website, email or phone** — the
  wilayat charity teams, which were the weakest rows in the register.
- **Kuwait: 44 rows** confirmed against `kuwaitaid.org`, which states 153 licensed bodies.
  The page renders 78, so this covers half the registry. **13 of 42 contactless rows**
  confirmed. Absence from the capture is NOT evidence against a row.
- **Bahrain: not reconciled.** khairplus.com publishes no scrapable list. **49 Bahraini
  rows carry no website, no phone and no registry match.** These are the least evidenced
  rows in the file. Closing this is the highest-value open task.

Captured registry pages are in `verification\registry-pages\`, and the reconciliation
inputs in `verification\`.

**Never checked, for any country.** The mandate text, which is the field a fundraiser reads
most, was written by researchers from what they read and has not been checked row by row
against source. Emails were checked for shape and never sent. Phones were never dialled.

---

## 5. Hard-won lessons. Ignore these and you will repeat the failure.

**Validate the instrument before trusting its verdict.** This cost the most time and it
happened repeatedly. Every single time the checking tool was itself checked, it turned out
to be wrong: the HTTP-only resolver condemned real Gulf funders, the redirect handling
invented 22 dead links, a naive domain-vs-name check produced 108 false hits that were just
acronyms and a shared donation platform, and a hand-written city list flagged Sulaibikhat,
which is a real Kuwaiti district.

**Look at the render. It finds what no check catches.** Oman's national emblem passed every
automated check twice while being, on screen, first a white asterisk and then a shapeless
lump. The Saudi flag was being clipped 9px top and bottom. The Summary tab was silently
destroyed by writing into the wrong columns. None of that was visible in the data.

**Gemini fabricates on this task. Do not use it ungrounded.** Asked to fact-check, it
returned six "official websites" and **not one of them existed**, while citing "Google
Search" it had never run. It also flagged deliberately blank fields as errors after being
told not to. Its whole review was discarded. Grok was out of quota both times it was asked.
**Codex is the one partner that has delivered here**, and it was notably strict, refusing
matches on generic wording and correctly distinguishing two different Al Babtain people.

**An assert-then-write patch script loses everything.** Three scripts asserted every anchor
and wrote only at the end, so one stale anchor discarded every edit that had already
matched, twice reporting work as applied that was never saved. Check all anchors first,
apply what matches, name what does not, always write.

**Never delete CSS with a regex in `index.html`.** A `re.sub` for dead rules ate three live
ones and broke the search box and a heading. Exact-match only.

**A blank field is deliberate.** Researchers were instructed to leave a field empty rather
than guess it. 202 rows have no website on purpose. Never report a blank as a defect, and
never fill one from recollection.

**Keep the organisation, drop the dead link.** Where a real body's domain has lapsed, the
row stays and the URL is cleared. A register pointing at nothing is worse than one that
admits it has no link. Confirmed correct later: the Kuwait Charitable Union's own site
links to two of the domains that had been cleared.

---

## 6. Design. index.html only, and far past the first pass.

The look is a deliberate, reviewed design system now. It is CSS plus a little vanilla JS
inside `index.html`; the DATA lane (data.json, vectors, the Excel) is untouched by it.
Build underneath it, do not overwrite it. Full session log: decision-log #1390. Live HEAD
at time of writing: `c606784`.

**Earlier pass (kept):** ink and slate house style, Source Serif 4 and IBM Plex Mono, a
spectrum ribbon, flat controls and hairlines, a keyline around the flags. The header kicker
is built from the data by `paintKick()` (was hardcoded at three countries).

**Current pass (19 August, the blueberry redesign).** Palette is a cool very-light
BLUEBERRY, one accent `#3E4CC4`, light and dark tokens on `:root`. How the main pieces work:

- **Per-country theming.** `COUNTRY_THEME` map plus `paintPage()` set and clear about
  eleven CSS custom properties on `document.body` (accent, mast, bg, `--cw1`/`--cw2`) with
  dark-mode-safe accent variants chosen via `matchMedia`, and toggle a `body.country-view`
  class. A country page gets a deep flag-colour masthead, a soft flag wash in the head band,
  flag-colour accents, a faint flag watermark (`.flagplate`, opacity .16), and a full-page
  painterly flag-colour wash (`#cwash`: a fixed turbulence-brushed SVG whose ellipse fills
  are `var(--cw1)`/`var(--cw2)` per country, opacity .055 light and .11 dark, shown only
  under `body.country-view`). The whole theme resets on every non-country page; this was
  the most-tested behaviour and it does not leak.
- **All-register view** (`#/a/all`) wears the GCC emblem as a side watermark
  (`setEmblem`/`paintWashAll`) over a blueberry wash.
- **Home:** painterly light-orange and light-blue brush washes (`#brushes`, turbulence,
  home-only); a cursor-follow blueberry glow (`#berryglow`/`initBerry`, colour only, off on
  touch and under reduced-motion); the wordmark is all one ink colour, lifted up, and the
  ring of flags nudged down.
- **Footer signature:** a circular avatar `ali.jpg` (a 256px crop of
  `Desktop\2 Ali Al Mokdad.JPG`) linking to https://www.linkedin.com/in/ali-al-mokdad/ ,
  with a hover grow plus yellow glow and a soft yellow painterly splash in the corners.
- **Sound:** Web Audio chimes, `chime()` on the home Search and `sigChime()` on the footer
  name and photo, sharing a lazily created `_actx`.
- Orange home accents, restacked org-detail fields (label above value, sentence case, not
  all capitals), and rounded, consistent search inputs, dropdowns and chips.

**Reviewed.** Codex (gpt-5.6-sol) plus two Claude agents. Every objective finding was
fixed: the masthead link focus outline is now white (it was under 3:1 on the deep band);
the country back link uses `--accent-2` (Kuwait and Bahrain were under 4.5:1 on the wash);
the glow is skipped under reduced-motion; and `#cwash` light opacity was trimmed to .055 so
the muted meta text stays at or above 4.6:1 over the red washes. All contrast was checked
against the composed washed backgrounds, not bare paper.

**Flags: read `FLAGS.md` before touching `countryMark()`.** They are drawn to each state's
own spec and must not be "simplified": UAE colours were wrong until corrected; Bahrain has
exactly five points (Five Pillars, 2002), built by a loop so the count cannot drift; the
Saudi shahada must never be cropped, which is why the country-page flag fades by an alpha
mask, not a crop; Oman's emblem is a deliberate simplification with two failed attempts
documented. Codex re-verified the country ACCENT hexes this session (Qatar `#8A1538` exact;
UAE accent `#00702E` intentionally darker than the official flag green `#00843D` so it
clears AA as link text).

**Deploy quirks (design lane).** `index.html` only; push to origin, GitHub Pages builds.
MAX_PATH breaks `git rebase` in a deep clone, so MERGE `origin/main` (the two lanes touch
different files) with `core.longpaths`, never rebase. The autoreview pre-push hook needs
`~/.claude/hooks/.autoreview-ok` written as a separate step just before the push. Test with
a `?v=` cache-buster. Localhost meaning-search "Failed to fetch" is EXPECTED (the worker is
origin-locked to the live domain); it works on the live site.

**Parked idea (do not start without Ali):** two new sections, News and Data, fed by free
verified APIs (ReliefWeb, Qatar QFFD, IATI, OCHA FTS), same static-page-plus-Cloudflare-
Worker pattern as his other bots. Full plan and the API shortlist: decision-log #1391.

---

## 7. Open tasks, highest value first

1. **Reconcile Bahrain.** 49 rows have no contact detail and no registry match. Find a
   reachable Bahraini registry (Ministry of Social Development licensing list, or the SADAD
   platform) and reconcile as was done for Oman and Kuwait.
2. **Close the Kuwait coverage gap.** 31 entries in Kuwait's official registry have no
   counterpart here. The list is in `verification\`. They are registry-confirmed, so they
   are good additions.
3. **Capture the other half of the Kuwait registry.** The page renders 78 of 153; the rest
   needs pagination handling.
4. **Spot-check mandate text against source.** Never done for any country, and it is the
   field users read most.
5. Ali has an open question on the Excel Summary tab title, which still reads "GCC
   Philanthropy, Donors and Funders". The website was trimmed to just "Philanthropy",
   because a donor and a funder are the same actor here. His text, his call.

---

## 8. Conventions

- Author metadata on every deliverable is **Ali Al Mokdad**, never python or Claude.
- **No em dashes** anywhere in new copy.
- No tool names (Codex, Gemini, Claude, AI) in anything client-facing or in a public commit.
- The Excel is **Ali's master and he edits it by hand.** Scripts must OPEN and append, never
  regenerate. `add_to_workbook.py` asserts the hyperlink count never drops, because a column
  shift silently broke 3,980 links in this project once.
- Back up the workbook before every write. See `backups-2026-08\`.
- The preview server `gcc-funders` on port 3471 serves **the repo**, not the old `site\`
  copy. It was repointed on 19 August because verifying one copy while shipping another is
  how a build drifts from live.
