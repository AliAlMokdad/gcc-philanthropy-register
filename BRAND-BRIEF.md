# Brand naming: the decision, and how to land it on this codebase

Ali's brand decision is section B below and it is settled. Section A is what a session needs in
order to execute it here without breaking the site or losing the work. **Read section A first.** The
brand system is straightforward; the codebase is where this goes wrong.

Section A was written from the repository, then adversarially reviewed against it, and **four of its
own claims came back wrong and are corrected here**: it said the homepage nav carried eight items
when every page carries six, it said page titles live in `tools/build_seo.py` when that tool reads
them out of the HTML, it told you to leave the `Dataset` node alone when the code makes renaming it
automatic, and it treated this as a nav-label job when the product names are written in eleven more
places. Anything stated as a count or a line number below was measured, not remembered.

---

# A. EXECUTION

## A1. The rename map, exact strings

| Current, verbatim | Becomes | Notes |
|---|---|---|
| `Donor Intelligence` | `Atlas` | nav label only; route and hooks unchanged |
| `News` | `News & Insights` | nav label; write the ampersand as `&amp;` in HTML |
| `Members` | `Countries` | **label only. Do not move `/members/`.** See A4 |
| `Main page` | *removed from the nav* | the wordmark already links home; the brief's nav has five items |
| `Register` | `Register` | unchanged |
| `Toolkit` | `Toolkit` | unchanged |

**The good news, counted rather than assumed: the bar is already uniform.** Parsing every
`<ul class="pbar-nav">` in all 14 HTML files returns exactly six items in every one, with identical
labels: `Main page | Donor Intelligence | Register | News | Toolkit | Members`. There is no drift to
reconcile and no page carrying `FAQ` or `Connect` in the bar. So this is one substitution applied in
fifteen places, not fourteen separate judgements.

Three details the markup turned up that will otherwise cost someone time.

**`class="pbar-main"` on the `Main page` link is dead.** It appears in nine files and is referenced by
**no** CSS and **no** JS. Removing that item removes the class with it and nothing breaks. By contrast
`pbar-brand` on the wordmark **is** styled in `shared/chrome.css`, so leave the wordmark alone.

**The hrefs differ by depth and must stay that way.** `index.html` links `href="#/a/all"`; every
subpage and the `PBAR` constant link `href="../#/a/all"`, `href="../toolkit/"`, `href="../"`. A
find-and-replace that normalises those breaks navigation from every subpage.

**`data-nav` exists only on `index.html`.** The `PBAR` constant carries none, correctly, because the
attribute only marks the active product on the page that hosts the routes.

## A2. Every place the nav markup exists. There are fifteen.

`grep -rln "pbar-nav" --include=*.html --include=*.py .`

- `index.html`: its own copy, and the only one carrying the `data-nav` hooks
- `toolkit/index.html`
- `members/index.html`, `members/{bahrain,ksa,kuwait,oman,qatar,uae}.html`, seven files
- **`tools/build-legal.py`, the `PBAR` constant**: this generates the bar for `privacy/`,
  `terms/`, `faq/`, `connect/` and `alialmokdad/`

Editing the five generated pages' HTML directly does nothing durable: the next build overwrites
them. **Edit the `PBAR` constant**, at `tools/build-legal.py:39`.

A sixteenth file mentions the row without containing markup: **`shared/chrome.css`** holds the
`.pbar-nav` styling and the breakpoints, which is why A6 exists. Do not count it as a copy to edit,
but do read it before changing a label.

## A2b. The product names are written in eleven more places outside the nav

**Renaming only the nav ships a site whose tab, heading, share card and browser title disagree with
its own navigation.** Every row below was found by grep and read in place. This is the checklist.

| What | Where | Currently | Note |
|---|---|---|---|
| The JS tab map | `index.html:7854` | `var TAB={news:"News", register:"Register", intel:"Donor Intelligence"}` | sets the **visible page tab** on each route |
| The route's own name | `index.html:3908` | `name:"Gulf Cooperation Council (GCC) Philanthropy Donor Intelligence"` | feeds the heading and the title |
| The route's name parts | `index.html:3909` | `parts:["Gulf Cooperation Council (GCC)","Philanthropy Donor Intelligence"]` | the two-line masthead split |
| The home portal door | `index.html:2493` | `<span class="pn-label">Donor Intelligence</span>` | inside `<a href="#/a/all" id="intellink">` |
| **The JS brand constant** | `index.html:4113` | `var SITE = "Gulf Cooperation Council (GCC) Philanthropy"` | **read A2c before touching this** |
| **The home title, in JS** | `index.html:4165` | `document.title="Gulf Cooperation Council (GCC) Philanthropy Register"` | **read A2c** |
| The news title, in JS | `index.html:7935` | `document.title = "News and Developments \| Gulf Cooperation Council (GCC) Philanthropy"` | not "News & Insights" |
| The toolkit titles, in JS | `toolkit/index.html:632, 761, 793` | three hardcoded `Toolkit \| Gulf Cooperation Council (GCC) Philanthropy` strings | Toolkit keeps its name, but the brand half changes |
| The members hub title | `members/index.html:6` | `GCC Member States \| ...` | the `<title>`, which A3b says is the source |
| The members hub tab | `members/index.html:56` | `<span class="pagetab">Member states</span>` | visible |
| The members hub h1 | `members/index.html:59` | `<h1 class="sr-only">GCC Member States</h1>` | screen readers only, still wrong if left |

Two of these need Ali, not a decision by the session:

**The six country pagetabs say `Member state`, singular, one per country page.** Saudi Arabia genuinely
is a member state of the Council, so that word is not wrong the way the hub's plural label is. Renaming
them to `Country` is defensible and so is leaving them. **Ask.**

**`News and Developments` at `index.html:7935` is a third name** for the product the nav calls `News`
and the brief calls `News & Insights`. Three names for one thing. The brief settles the nav label; it
does not say whether the browser title should match it. **Ask.**

## A2c. The two lines that will bite, and why they look harmless

**`index.html:4165` hardcodes the homepage title in JavaScript, and today it is
character-identical to the static `<title>`.** Verified: both read
`Gulf Cooperation Council (GCC) Philanthropy Register`. So changing the `<title>` alone appears to
work, and then the JavaScript writes the old name back the first time anyone lands on or returns to
the home portal. The tab says one thing, the search result says another, and nothing errors. This is
the same failure that has been logged on another of Ali's sites: the SPA reverts `document.title` on
every navigation, so updating the HTML tag is not enough. **Change both, in the same commit.**

**`index.html:4113`'s `SITE` constant is coupled to the route names by a prefix strip.** Line 4114
does `sel.name.indexOf(SITE) === 0 ? sel.name.slice(SITE.length).trim() : sel.name`, so a route
whose `name` starts with `SITE` gets the brand removed before the title is assembled as
`subject + " | " + SITE`. Change `SITE` without changing the `name` fields at 3908 and 3909 to match,
and the strip stops firing, and every route title prints the brand twice. **They move together or not
at all.** Test by loading each route and reading `document.title`.

## A3. THE GENERATED-FILE RULE. This is the largest risk in the job.

Four generators write into files a person would otherwise hand-edit. Anything typed inside their
output is destroyed on the next run, silently, with nothing looking broken.

| Marker or file | Generator | What to edit instead |
|---|---|---|
| `<!-- seo:start ... seo:end -->` in every `<head>` | `tools/build_seo.py` | see A3b, it is a mirror, not the owner |
| `<!-- country-hub:start ... -->` in the six country pages | `tools/build_member_hubs.py` | the generator, which reads `shared/catalog.json` |
| `privacy/`, `terms/`, `faq/`, `connect/`, `alialmokdad/`, **the entire page** | `tools/build-legal.py` | see A7 |
| `shared/catalog.json` | `tools/build_catalog.py` | the datasets |
| **`sitemap.xml` and `robots.txt`, whole files** | `tools/build_seo.py:258-259` | the generator |

Those last two are worth naming because they look hand-written and are not: every
`build_seo.py --write` overwrites both from the 14 discovered pages. There are other generated
artifacts in this repo that this job does not touch but a stray edit could damage:
`toolkit/catalog.json` and `toolkit/papers/*.json` (`tools/split_toolkit.py`), `shared/themes.json`
and `shared/themes-evidence.json` (`tools/build_themes.py`), `news-feed.json` and
`news-candidates.json` (`tools/news/build_news.py`), `oecd.json` (`tools/build-oecd/build_oecd.py`),
`vectors.json` (`tools/add_identity.py`). **If a file is JSON and sits beside a tool that names it,
assume it is generated and check before editing.**

## A3b. Where a page title actually lives, which is not where you would guess

**This was verified by reading `tools/build_seo.py` and by sampling four pages, because guessing it
wrong sends you to the wrong file.**

`build_seo.py` does not hold any title. `title_of()` at line 53 reads `<title>` out of the page, and
`block()` at line 63 mirrors that one string into the canonical URL, `og:title`, `og:description`,
`twitter:title`, `twitter:description` and the JSON-LD `name`. Sampled on `index.html`,
`toolkit/index.html`, `members/ksa.html` and `faq/index.html`: `og:title` and `twitter:title` are
character-identical to `<title>` on all four.

So the flow is **HTML is the source, the tool is the propagator**:

| The string | Where you change it | Then |
|---|---|---|
| `<title>` on `index.html`, `toolkit/index.html`, the 7 `members/*.html` | the HTML itself | run `python tools/build_seo.py --write` |
| `<title>` on the 5 generated pages | the out-of-repo content module, see A7 | `build-legal.py`, which calls `build_seo.py` itself |
| `og:site_name`, currently `Gulf Cooperation Council (GCC) Philanthropy` | **hardcoded, `tools/build_seo.py:68`. The only brand string the tool owns.** | run it with `--write` |
| `canonical`, `og:title`, `og:description`, `twitter:*`, JSON-LD `name` | **nowhere. Never hand-edit these.** | they are derived |
| `SITE`, the domain | `tools/build_seo.py:38` | not changing |

Two consequences.

**A title change is one edit, not three.** Change `<title>`, run the tool, and Open Graph and
Twitter follow. Hand-editing `og:title` to match is wasted work that the next run overwrites anyway.

**The country meta descriptions are structurally safe, and this is worth knowing before you worry
about it.** `ensure_desc()` at line 92 adds a description only where a page has none, with the
comment *"An existing one is the author's."* A dry run prints `description kept` for all six country
pages. Those descriptions lead with the data, for example *"542 funders recorded in Saudi Arabia,
reported outbound humanitarian flow of $10,394,551,759, 5 papers on its legal and regulatory
framework."* Nothing in this brand change touches them and nothing should: they are the strongest
search asset on the site, because they match a query like *Saudi Arabia humanitarian funding data*
in a way a generic sentence never will. Section B8 covers the home and product views only. **Do not
extend it to `members/*.html`.**

## A4. What must not change

- **The hash routes.** `#/a/all` is the Atlas, `#/a/list` is the Register, `#/news` is News &
  Insights. Rename the labels; leave the routes. Changing them breaks every internal link, the
  declared `SearchAction`, and any link anyone has saved.
- **The `data-nav` attribute values** `intel`, `register`, `news`. `index.html` around line 7836
  does `querySelectorAll(".pbar-nav a[data-nav]")` and compares `getAttribute("data-nav")` to the
  current view to mark it. Change the label freely; change the value and the current-product
  marking stops working with no error.
- **The `/members/` directory and its filenames.** The product becomes *Countries*; the path stays
  `/members/ksa.html` and so on. Those paths are in the canonical tags, the sitemap, the country
  hubs and the internal links, **and GitHub Pages cannot issue a redirect**, so moving them breaks
  live URLs permanently.
- **The `Dataset` node name.** It reads "Gulf Cooperation Council (GCC) Philanthropy Register" and
  that is correct under this brief, because the dataset *is* the Register product. **But this one is
  not a prohibition, it is a required code change, and it is the trap in the whole job.**
  `tools/build_seo.py:119` sets `"@type": "WebSite" ... "name": t` and `:125` sets
  `"@type": "Dataset" ... "name": t`. **The same variable.** `t` comes from
  `title_of(index.html)`. So the moment the homepage `<title>` becomes `GCC Philanthropy | ...`,
  the Dataset node is renamed with it, silently, and the site stops declaring that it publishes a
  register.
  **Fix before touching the title:** split the variable in `build_seo.py`, so the WebSite name and
  `alternateName` come from B9 while the Dataset keeps its own literal string. Verify afterwards by
  reading the rendered JSON-LD, not the source.

## A5. The strings that are wrong today

1. `index.html` `<title>` is `Gulf Cooperation Council (GCC) Philanthropy Register`, which section
   B3 explicitly rules out as the homepage identity.
2. The `WebSite` node at `index.html:2344` has
   `"name":"Gulf Cooperation Council (GCC) Philanthropy Register"` and **no `alternateName`**.
   Section B9 wants `name` = `GCC Philanthropy`, `alternateName` = `Gulf Cooperation Council
   Philanthropy`.
3. `members/index.html` `<title>` begins `GCC Member States | …`.

**A fourth thing needs Ali's decision rather than a fix, because it changes his own section.**
The proposed homepage title in B7, `GCC Philanthropy | Gulf Cooperation Council Philanthropy
Platform`, is **65 characters**. Google's title container is roughly 600 pixels, near 55 to 60
characters at this width, so it will truncate and the visible result loses the last word. The other
five proposed titles are 32 to 58 and are fine. Separately, the current homepage title contains the
word **Register** and the proposed one does not, which drops the exact term someone searching *GCC
philanthropy register* would type. Both are real, neither is mine to decide, and both are put to Ali
rather than patched here.

Note what is already right and does not need touching: the masthead brandline already reads
`Gulf Cooperation Council (GCC) Philanthropy` while the product bar wordmark already reads
`GCC Philanthropy`. The short-and-expanded balance section B5 asks for is partly built.

## A6. A trap worth knowing before you touch a label

`shared/chrome.css` has mobile breakpoints **tuned to the current label set**, and says so:

> FIVE LABELS, NOT FOUR. The wrap used to start at 344px, which was right while the row carried
> four products. With Members added the row is 14px over at 375px, so the last label is clipped on
> the commonest phone width there is.

Measured: the current six labels are 53 characters; the brief's five are 44. So this rename makes
the row **shorter by nine characters and one item**, and the longest single label goes from
`Donor Intelligence` at 18 to `News & Insights` at 15. The mobile bar should get easier, not
harder. Do not delete those breakpoints on the assumption that shorter labels made them unnecessary.

**Character count is a weak proxy and should not be the check.** The row is uppercase mono with
letter-spacing, per-item padding, a flex gap, `nowrap`, and a horizontal-scroll fallback, so width is
not a function of character count. The real check, run in the browser at 375px and 430px after fonts
have loaded:
```js
var n = document.querySelector('.pbar-nav');
console.log(n.scrollWidth, n.clientWidth, n.scrollWidth <= n.clientWidth);
```
plus a screenshot at both widths. `scrollWidth > clientWidth` means the row is clipped or scrolling.

## A7. Division of labour, and the content module is in the repository now

**`tools/content.py` is in the repo.** It was outside it, in a session scratchpad, which made the five
generated pages unbuildable by anyone else and put the only copy one directory away from being lost.
It holds every word of `TITLE`, `TAB`, `STANDFIRST`, `NOTICE`, `PRIVACY`, `TERMS`, `FAQ`, `ABOUT`,
`SOCIAL` and the form copy. Nothing in it is unpublished: all of it is already live as HTML.

**It is proven to be the real source, not a stale copy.** Regenerating all five pages from it into a
scratch directory and diffing against the deployed pages, with the `seo` block stripped from both
sides because a scratch build has none, returns identical on `privacy/`, `terms/`, `faq/`, `connect/`
and `alialmokdad/`.

Rebuild the five pages, from the repository root:

```
python tools/build-legal.py tools/content.py
```

Pass the path explicitly. `build-legal.py:27` defaults `SRC` to a bare `content.py` resolved against
the current directory, so the default only works if you happen to be standing in `tools/`. A third
argument sets the output root, which is how the proof above was run without touching the live pages:

```
python tools/build-legal.py tools/content.py C:/some/scratch/dir
```

That build also calls `tools/build_seo.py --write` at the end, deliberately, because it overwrites
those five heads wholesale and would otherwise destroy the SEO block. In a scratch root there is no
`tools/`, so it skips the step and says so.

**So the split is now about who is editing what, not about who can build.**

- **Nav and titles:** `index.html`, `toolkit/index.html`, the seven `members/*.html`,
  `tools/build_seo.py`, `shared/chrome.css`, and the `PBAR` constant at `tools/build-legal.py:39`.
- **The five generated pages:** `tools/content.py` for the words, then the rebuild command above.

One coordination rule, and it is the only one that matters: **`tools/build-legal.py` has two
independent regions.** `PBAR` at line 39 belongs to the nav rename. The `/alialmokdad/` block near the
end belongs to whoever is editing the bio. They do not overlap, so both can be worked at once, but
re-read the file immediately before writing and stage the exact path.

## A8. Prove it is finished, do not assume it

**The old version of this check would have passed a half-done rename**, because grepping three
strings does not see a JavaScript tab map. Run all of these.

Nothing should come back from any of these, and each one corresponds to a row in A2b:

```
grep -rn "Donor Intelligence"     --include=*.html --include=*.py --include=*.js .
grep -rn ">Main page<"            --include=*.html --include=*.py .
grep -rn "Member [Ss]tates"       --include=*.html .
grep -rn "News and Developments"  --include=*.html .
grep -rn "intel:\"Donor"          --include=*.html .
```

Then confirm every hardcoded title in JavaScript was moved, because grep for the old brand string
will still match the ones that legitimately keep part of it:

```
grep -rn "document.title" --include=*.html . 
```
Six assignments, `index.html:4117, 4165, 7935` and `toolkit/index.html:632, 761, 793`. Read each one
and confirm it says what the nav now says.

And these should hold:

- **`index.html`'s static `<title>` is character-identical to the string at `index.html:4165`.** See
  A2c. This is the single most likely thing to be left half-done:
  ```
  python - <<'EOF'
  import io, re
  s = io.open('index.html', encoding='utf-8').read()
  a = re.search(r'<title>(.*?)</title>', s, re.S).group(1)
  b = re.search(r'document\.title="([^"]*)";', s).group(1)
  print(repr(a)); print(repr(b)); print('MATCH' if a == b else 'MISMATCH')
  EOF
  ```
  Run as written it prints the two strings and `MATCH`, which is the state today.
- **the JSON-LD `Dataset` node still says Register while the `WebSite` node says the new name.** Read
  the rendered block, not `build_seo.py`. See A4.
- `grep -rln "pbar-nav" --include=*.html .` still lists **fourteen** HTML files. Nine of them will
  carry five items after your pass; the five generated pages still carry six until the other session
  rebuilds them, so a mixed state here is expected, not a bug. Say so when handing over.
- every `data-nav` value is still one of `intel`, `register`, `news`
- **`og:title` equals `<title>` on all 14 pages, and `twitter:title` too.** They are generated, so a
  mismatch means the tool was not re-run after the HTML was edited. This is the check that catches a
  half-finished rename:
  ```
  python -c "import io,re,glob;[print(f) for f in glob.glob('*.html')+glob.glob('*/*.html') if (lambda s:(re.search(r'<title>(.*?)</title>',s,re.S) and re.search(r'og:title\" content=\"([^\"]*)',s) and re.search(r'<title>(.*?)</title>',s,re.S).group(1)!=re.search(r'og:title\" content=\"([^\"]*)',s).group(1)))(io.open(f,encoding='utf-8').read())]"
  ```
  It should print nothing
- `/members/ksa.html` and its five siblings still return 200 on the live site
- the `WebSite` node has both `name` and `alternateName`
- the current-product marking still works: open the Atlas route and confirm the Atlas item carries
  `aria-current`

If a rename reports more changed lines than the labels you touched, stop and read the diff.

## A9. Two working rules for this repository

**We share one working tree.** `git add <path>` stages whatever is in that file, not what you
changed in it. A one-word edit to a file another session is holding has already swept 257 lines
once today. Stage exact paths, never `git add -A`, and read `git show --stat HEAD` before pushing:
if a label rename reports thirty changed lines, something else came with it. `SESSION-NOTES.md`
section 6 carries the plumbing route for editing a file someone else is in.

**A shorthand silently resets the longhands inside it, and a screenshot cannot tell you which rule
won.** Three separate defects today came from this: a `background:` shorthand wiping
`background-image` so the masthead wash never painted, a percentage `background-position` measured
against container-width-minus-image-width, and a `font:` shorthand eating family, size and weight
while leaving `letter-spacing` behind, which rendered a 21px italic subtitle as 15.5px upright
serif and looked entirely plausible. If you restyle a label, read the computed style.

## A10. What the rename does to search, and four wins it opens up

The rename is close to search-neutral if the mechanics in A3b are respected. These are the parts
that are not neutral, plus the cheap wins the work naturally passes through. **Every figure below was
counted in this repository, not estimated.**

### The two risks

**The homepage title truncates and loses a keyword.** Covered in A5. Both are Ali's call.

**Nothing else in B7 is at risk.** Measured character counts: Atlas 54, Register 58, Toolkit 48,
Countries 53, News 32. All inside the container.

### Four wins, ranked, all free and all possible on this stack

**1. Declare `Organization` and `sameAs`, and link the person to his real identifiers.**
The whole site currently declares **zero** `Organization` nodes and **zero** `sameAs` values, and the
`Person` node is bare: `"@type":"Person","name":"Ali Al Mokdad"`, nothing else. That is the single
largest gap. An entity is established in search and in AI answer engines by *corroboration across
independent sources*, and `sameAs` is how you point at yours. The three profiles already published on
`/alialmokdad/` are safe to use immediately. If Ali confirms his Wikidata item and his ORCID, those
two are worth more than the social profiles combined, because both are third-party registries rather
than self-published pages. **Ask him; do not guess an identifier.**
File: `tools/build_seo.py`, extending the existing `Person` node.

**2. Add `FAQPage` to `/faq/`, which needs no new writing at all.**
The page already carries the questions as clean `<h3>` elements: *What is this? Who is behind it? Who
is Ali Al Mokdad? Why does it exist? Where does it come from? How current is it? Why are some fields
blank? Can I download the whole dataset?* and more. A `FAQPage` node built from the existing markup
is the one structured-data win that requires zero invented text, which matters because inventing text
is forbidden here. It is also the node most likely to produce a visible result in a search listing.
Files: the content module plus `tools/build-legal.py`, or `tools/build_seo.py` reading the rendered
`<h3>` and answer text.

**3. Write `llms.txt`. There is none, and this site is an unusually good fit for one.**
Confirmed absent. It is a plain text file at the root, needs no infrastructure, and works on GitHub
Pages as-is. It matters more here than on a normal site for two reasons: three of the five products
live behind a hash route and are therefore invisible to a crawler, and the site's whole claim is to be
a citable independent reference. A file that states the scope, the six countries, the record count,
the two figures and what they are not, the independence notice, and a preferred citation form gives an
answer engine the thing it cannot otherwise get. The pattern already exists on two of Ali's other
sites, so copy the shape rather than inventing one.
File: new `llms.txt` at the root, plus a line in `robots.txt`.

**4. `BreadcrumbList` on the eight subpages.** Cheap, mechanical, and it is the node that makes a
listing show `gccphilanthropy.org > Countries > Kingdom of Saudi Arabia` instead of a bare URL. Do it
in the same pass as 1, since both are edits to the same function.
File: `tools/build_seo.py`.

### Two things to leave alone

**The hash routes.** Three of five products are fragments, so a crawler sees one page. That is a real
limitation and the honest answer is to accept it, because every fix is worse: real
`/atlas/`, `/register/` and `/news/` directories mean maintaining duplicate static shells and
cross-file routing state by hand, and the widely recommended `404.html` trick is **actively harmful
here**, since GitHub Pages sends a genuine `HTTP 404` before any JavaScript runs and a crawler drops a
404 from the index. So let `/`, `/toolkit/` and the seven `/members/` pages do the ranking work, which
is what they already do. Revisit only if the site ever moves off Pages.

**The six `Country` nodes on `index.html`.** A review suggested stripping these as duplication.
Recounted: there are six on `index.html`, six on `members/index.html`, six on `toolkit/index.html`
and one on each of the six country pages, twenty four in total. That is a coverage declaration on the
three hub pages and a subject declaration on each detail page, which is a defensible shape, not
duplication. **Leave it.** This is recorded because the suggestion was made and measured wrong, and a
later session should not act on it.

---

# B. THE BRAND DECISION

> **PARTLY SUPERSEDED. Read this before reviewing anything against section B.**
> Ali overrode four parts of this section in conversation after it was written, and the site is built
> to his later instruction, not to the text below. A review that flags these as defects is reading a
> stale document, which has already happened once.
>
> 1. **B3, the homepage headline.** B3 rules out the expanded form and makes "GCC Philanthropy" the
>    identity. He reversed that: the headline reads **Gulf Cooperation Council (GCC) Philanthropy**.
> 2. **B2, the tagline.** "One platform for Gulf philanthropy." is **removed from the home portal** on
>    his instruction.
> 3. **B3's third line.** His wording now stands: *"A donor intelligence, registry, data, news and
>    knowledge platform covering philanthropy across the Gulf Cooperation Council countries."* It adds
>    "donor intelligence" and drops "the six". Only the spelling of "intelligence" was corrected.
> 4. **B7's homepage title.** B7 proposes "GCC Philanthropy | Gulf Cooperation Council Philanthropy
>    Platform", which measures 65 characters and truncates. The title is **Gulf Cooperation Council
>    (GCC) Philanthropy**, 43 characters, per his instruction that the main page carry the expanded
>    form.
>
> Also his, and not in B6: the two-tier product heading on the Atlas and Register views reads
> **Gulf Cooperation Council (GCC) Philanthropy** above **Atlas** or **Register**.
>
> Everything else in section B stands as written.

## B1. Three forms of the name, all three in use

1. **GCC Philanthropy**: the short master brand and primary wordmark.
2. **Gulf Cooperation Council (GCC) Philanthropy**: the expanded form, for first reference,
   search visibility, metadata, accessibility and institutional context.
3. **Gulf philanthropy**: the natural editorial phrase, used selectively in the tagline and
   supporting copy.

Do not pick one and use it everywhere. "GCC Philanthropy" alone is concise but opaque to anyone who
does not know the abbreviation. "Gulf philanthropy" alone is natural but does not define the scope
as the six Gulf Cooperation Council states. Combine them deliberately.

## B2. Master brand and tagline

Brand: **GCC Philanthropy**

Tagline: **One platform for Gulf philanthropy.**

## B3. The homepage identity, in this order

> **GCC Philanthropy**
>
> One platform for Gulf philanthropy.
>
> A registry, data, news and knowledge platform covering philanthropy across the six Gulf
> Cooperation Council countries.

That third line is required. It makes the geographic and institutional scope explicit, lets a
search engine understand what GCC means, and tells a visitor which countries are covered.

The six are Saudi Arabia, the United Arab Emirates, Qatar, Kuwait, Bahrain and Oman. Their names
should appear naturally on the homepage, in relevant metadata and in the Countries section, without
forcing the full institutional name into every heading.

The homepage headline is **not** `Gulf Cooperation Council (GCC) Philanthropy Register` and **not**
`GCC Philanthropy Atlas`. Those are products inside the platform.

Do not replace the explanatory sentence with vague language: *a platform for regional impact*, *an
ecosystem for giving*, *the future of philanthropy*, *a gateway to Gulf impact*.

## B4. Five products

The master brand stays **GCC Philanthropy**. Each product has a short visible title, a full name
for context or SEO, and one descriptor.

| Visible title | Full name | Descriptor |
|---|---|---|
| **The Atlas** | GCC Philanthropy Atlas | Data and intelligence on philanthropy across the Gulf Cooperation Council. |
| **The Register** | GCC Philanthropy Register | The organizations shaping philanthropy across the Gulf Cooperation Council. |
| **News & Insights** | GCC Philanthropy News & Insights | What's happening across philanthropy in the six GCC countries. |
| **The Toolkit** | GCC Philanthropy Toolkit | Practical guidance for engaging philanthropy across the Gulf Cooperation Council. |
| **Countries** | none | Six Gulf Cooperation Council countries. One regional philanthropy landscape. |

Shorter descriptors, for compact layouts only, where the platform context is already obvious:
Atlas, *Data and intelligence across the Gulf philanthropy landscape*; Toolkit, *Practical guidance
for engaging Gulf philanthropy*. Use the expanded version on each product's own landing page,
because it is more precise and more search-friendly.

Supporting sentences where needed. Register: *Discover foundations, charities, funders, impact
investors and philanthropic institutions across Saudi Arabia, the UAE, Qatar, Kuwait, Bahrain and
Oman.* News & Insights: *News and developments from Saudi Arabia, the United Arab Emirates, Qatar,
Kuwait, Bahrain and Oman.*

Do not describe the whole website as the Register; the Register is the organizations product inside
it. Do not shorten News & Insights to "Gulf news", which is broad enough to include politics, oil
and countries outside the platform's scope. Do not keep "Members" as the product name: these are
member states of the Gulf Cooperation Council, not members of this platform.

## B5. Visible usage

**GCC Philanthropy** is the wordmark in the global navigation and the shared header.

**Gulf Cooperation Council (GCC) Philanthropy** belongs in the first explanatory reference on the
homepage, the About or FAQ page, structured metadata, accessibility labels where clarification
helps, legal and independence language, selected footer and institutional references, and
search-engine titles and descriptions where appropriate.

Do not put the expanded name in every navigation bar, product title and masthead. Visibility
without repetition.

## B6. Navigation and page hierarchy

```
GCC Philanthropy        Atlas   Register   News & Insights   Toolkit   Countries
```

Not `GCC Atlas`, `GCC Register`, `GCC News`, `GCC Toolkit`, `GCC Countries`. The wordmark already
supplies the family. On mobile keep the same words: do not substitute an unclear icon or
abbreviation for News & Insights.

Every page carries, in order: the shared **GCC Philanthropy** brand, one product title, one
descriptor, then the content. Never stack competing names such as *GCC Philanthropy / Gulf
Cooperation Council Philanthropy / Donor Intelligence / GCC Philanthropy Atlas / Philanthropy
Intelligence Dashboard*.

## B7. SEO titles

| Page | Title |
|---|---|
| Home | GCC Philanthropy \| Gulf Cooperation Council Philanthropy Platform |
| Atlas | GCC Philanthropy Atlas \| Gulf Cooperation Council Data |
| Register | GCC Philanthropy Register \| Gulf Funders and Organizations |
| News | GCC Philanthropy News & Insights |
| Toolkit | GCC Philanthropy Toolkit \| Guidance and Research |
| Countries | GCC Countries \| Gulf Cooperation Council Philanthropy |

Do not stuff every title with all six country names; those belong in descriptions and on
country pages.

## B8. Meta descriptions

- **Home**: Explore philanthropy across the Gulf Cooperation Council. GCC Philanthropy brings
  together organizations, funders, data, news and practical guidance covering Saudi Arabia, the
  UAE, Qatar, Kuwait, Bahrain and Oman.
- **Atlas**: Explore data, funding patterns, organizations, sectors and geographic intelligence
  across philanthropy in the six Gulf Cooperation Council countries.
- **Register**: Search foundations, charities, funders, impact investors and philanthropic
  institutions across Saudi Arabia, the UAE, Qatar, Kuwait, Bahrain and Oman.
- **News**: Follow philanthropy news, funding announcements, partnerships, policy developments and
  sector activity across the six GCC countries.
- **Toolkit**: Access practical guidance, research and frameworks for engaging philanthropy across
  the Gulf Cooperation Council.

Each must reflect what the page actually contains. No *most complete*, *leading* or *authoritative*.

## B9. Structured data

```json
{
  "@type": "WebSite",
  "name": "GCC Philanthropy",
  "alternateName": "Gulf Cooperation Council Philanthropy"
}
```

The site description should say the platform covers philanthropy across the six Gulf Cooperation
Council countries. Use individual country names in country page titles and descriptions, structured
country data, headings where relevant, internal links and image alt text where appropriate.

Do not hide the geographic meaning in metadata alone. The expanded scope must also be visible on
the homepage.

## B10. When to use which words

Use **GCC** for the formal six-country grouping, the platform name, product names, GCC-wide data,
comparisons across the six, page titles and navigation.

Use **Gulf Cooperation Council** when expanding the abbreviation for an unfamiliar visitor, making
the scope explicit, writing first-reference copy, in selected SEO descriptions, and when discussing
the Council as a formal regional body.

Use **Gulf philanthropy** for the tagline, natural editorial language, and where the six-country
scope is already clear from context.

Do not use "the Gulf" as a substitute for "the GCC" where the distinction matters, and do not imply
the site covers every country geographically associated with the Gulf.

## B11. Examples

**Good**

- GCC Philanthropy / One platform for Gulf philanthropy.
- A registry, data, news and knowledge platform covering philanthropy across the six Gulf
  Cooperation Council countries.
- Explore foundations and funders across Saudi Arabia, the UAE, Qatar, Kuwait, Bahrain and Oman.
- Data and intelligence on philanthropy across the Gulf Cooperation Council.

**Bad**

- GCC philanthropy for GCC users across GCC ecosystems.
- The leading Gulf platform transforming philanthropy across a dynamic regional ecosystem.
- Gulf philanthropy intelligence for the MENA region.
- The official GCC philanthropy platform.
- Gulf Cooperation Council (GCC) Philanthropy repeated in every header, subtitle, navigation item
  and footer.

The balance is: short brand, natural tagline, clear expanded explanation, precise country scope,
restrained repetition.

---

# C. Standing rules that apply to every word written here

- **No em dashes.** Commas, colons or full stops.
- **Nothing invented.** No claim the site cannot support, no figure that is not read from the data,
  no superlative. "The official GCC philanthropy platform" is false and would be damaging: this is
  an independent reference work with no affiliation to the Council, and the FAQ, terms and connect
  pages carry a standing notice saying so.
- **No political characterisation of any of the six states.** The country pages describe
  constitutional arrangements in the Council's own words. That boundary is deliberate.
- **Write in the register of the existing copy.** Plain, specific, no marketing cadence.
