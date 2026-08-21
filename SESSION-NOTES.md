# Session notes, 20 August 2026

Two Claude sessions worked this repository at the same time today. This file is what the other
one needs to know, written by the session that shipped `members/`, the Toolkit door and the
panorama move. Same purpose as `FLAGS.md`: stop a later session undoing a deliberate choice, or
re-deriving something that was already measured.

---

## 1. READ THIS FIRST: an open conflict on `members/`

**We were given opposite instructions about the same eight files.**

Ali told this session, in his own words and twice:

> cut everything on top from the boxes of those profiles and everything down those boxes
>
> I only want exactly what's on the boxes and the flags of those profiles and what is inside them
>
> Make sure it's only the boxes and what's inside them

So `members/index.html` and the six profile pages were stripped of the header, the Member States
banner, the breadcrumb, the Views Count strip and the footer. Committed and live, the page begins
with `<main class="page">` and the six boxes and ends with them.

The other session is adding the register's masthead and footer **back** onto those pages, with the
stated aim of making the members section belong to the register rather than read as a replica of
gcc-sg.org. 37 `gccp-` rules in `members/style.css`, 8 in `members/index.html`, 260 insertions
across all eight files, carefully scoped with a prefix so nothing collides.

It is good work and it contradicts the instruction above.

**At the time of writing that work is uncommitted, `HEAD` and `origin/main` are both `8b3afc7`,
and the live site serves the boxes-only version.** This session has not touched or reverted any of
it: not ours to undo.

**Ali has to pick one.** Please do not resolve it by guessing, in either direction.

---

## 2. What this session shipped

Five commits, all pushed and verified on the live site with the browser cache disabled.

| commit | what |
|---|---|
| `aec287c` | the `GCC Members` door, first of three, and `members/` behind it |
| `807061c` | the panorama as a horizon on the members page |
| `df19cf3` | that horizon fills the space that exists instead of space padded out for it |
| `9379b26` | the panorama leaves `footer.sig` and becomes the `#gulf` page layer |
| `8b3afc7` | `#gulf` scoped to the front page and the intelligence only |

### The front door

Three links now, `GCC Members` first, then `News & Developments`, then `Toolkit`. `.portal-news`
went from two columns to three and from `max-width:560px` to `852px`, which is what keeps the
longest label on one line: at 768px the cells were 248px and `News & Developments` wrapped to two
lines. Six lines of `index.html`, nothing else on that page touched.

### `#gulf`, and why the footer got its height back

The panorama used to be `footer.sig::after`, and the footer carried
`padding-top:clamp(118px,13vw,214px)` to make room for it. That padding was the whole reason the
footer read as too long: at 1440 it stood **276px tall to carry an 88px credit line**, 188px of it
empty ground existing only to host an image. Ali asked for the picture to span the list and the
foot without the foot growing.

So the picture is now `#gulf`, a fixed page layer, and the footer is **89px with zero top
padding** in every view. One image sits behind the organisation list and carries on through the
footer as a single picture.

It is a band at the foot, not the whole window, because at full height the skyline lies across the
middle of the screen behind the reading column. Framed at 44 per cent so `cover` lands the slice
on the city rather than the water, faded upward, fixed so it holds while the page scrolls.

**The 10 per cent light / 14 per cent dark ceilings from the old footer note were kept, and
re-measured rather than assumed.** The framing changed what sits under the credit, so the credit
was measured against the actual rendered ground: worst pixel **4.66:1 light, 4.60:1 dark**, against
the 4.5 that 12.5px text needs. That lands on the 4.67 the earlier note computed for ten per cent,
which says that arithmetic was sound. Do not raise these without re-measuring.

### Where `#gulf` shows

Two views only, keyed to flags this sheet already used rather than new ones:

```css
body:has(#l1:not([hidden])) #gulf,
body:has(#intel:not([hidden])) #gulf{display:block}
```

`#l1` unhidden is the front page. `#intel` unhidden is the whole-register view, which is the
Intelligence page. Because `#intel` is hidden on a country page, a category page and the news
desk, those three switch it off without needing a rule each. Verified on all five.

---

## 3. Facts about gcc-sg.org that were measured, so nobody re-derives them

- **The Council's ENGLISH member-state pages carry no English body text.** The labels, the state
  name and the capital are English; the body of every profile is Arabic. Measured: zero Latin
  words in the body on all six. The English on the landing cards **is** real source English. The
  profile bodies are not, and any English there is a translation.
- **`Area` and `Website Link` are empty at source** on all six. Left empty here on purpose.
  Filling them from elsewhere would stop this being a copy.
- **Their Oman card literally displays the characters `&nbsp;`** mid-sentence. That is a fault on
  their page and it is reproduced deliberately, as `&amp;nbsp;`.
- **The map is one inline SVG**, 19 paths, shipped byte-identical on all six of their pages and
  coloured in CSS. **The colouring is not uniform**, so a single rule is wrong: labels are grey
  except on the KSA and Oman pages, which whiten their own; markers are tan except the active one,
  which is white, and Bahrain's own, which is transparent. Read off each of their six pages and
  compared value for value.
- Geometry, measured not eyeballed: box 416x392, three columns on a 24px gutter, profile box 1296
  wide, name 20px/400, description 16px `#757575`, map active `#D1A770` on `#FBF4E4`, gold
  `#C39827`, page `#FEFBF0`, footer tan `#E0D2AC`.
- They set **SuisseIntl**, which is licensed and not redistributable, so **Inter** stands in. That
  is the one visual substitution and it is why the letterforms are near rather than identical.
- Each member profile wears its own flag as a background at 7 per cent. Their flag files are
  **87x52**, so a full-bleed use is blurred, or the upscale shows as blocks; at that opacity the
  blur cannot be seen and the blocks could. Saudi Arabia uses the repo's own 1280px
  `flag-saudi-arabia.webp` and needs no blur.

---

## 4. Traps that cost time here

- **`WebFetch` is a summariser, not a transcriber.** Asked to transcribe a page verbatim it
  returned confident English prose with invented section headings, having silently translated the
  Arabic. It also reported a leadership fact that is years out of date. Read the real DOM for
  anything that has to be exact.
- **A live check can lie because of your own cache.** A verification pass reported the old
  background still in place; the CDN had the new file all along and the browser was reusing
  `style.css` from its ten-minute cache while the HTML was cache-busted. Verify with the cache
  disabled.
- **A dead-CSS sweep by regex swallows the comment above each rule** into the selector, so every
  rule with a comment above it is judged alive. Strip comments before matching.
- **Assertions can be wrong in the direction that hides a bug.** One check searched for the word
  `lengthAdjust` and found it in the explanatory comment it had just written. Another matched
  `"success"` from an unrelated workflow run and declared a build green while the real one was
  still queued. Anchor checks on something only the real thing can satisfy.

---

## 5. Coexisting in this repo

`index.html` was edited by both sessions within minutes today, and it cost real work:

1. A door added to `index.html` was **wiped** by the other session's checkout.
2. On re-applying it, the other session had written more in-flight work into the same file
   between the `git status` and the edit, so a plain `git add index.html` would have swept their
   unfinished changes into this session's commit.

That was resolved with plumbing: the commit's `index.html` was built from `HEAD` plus only this
session's six lines, staged with `git update-index --cacheinfo`, leaving their 44 lines
uncommitted and intact in the working tree.

**So, in this repo:** re-read `index.html` immediately before editing it, stage exact paths, and
never `git add -A`. If the diff is bigger than what you changed, stop and look at it before
committing.

---

## 6. Session of 21 August 2026: the four site-meta pages, and a live 404 they were fixing

Written by the session that shipped `privacy/`, `terms/`, `faq/`, `connect/`, `shared/doc.css` and
`tools/build-legal.py`. Two sessions were again in this repository at the same time.

### What happened to the footer, and why a commit message does not describe its own contents

`footer.sig` in `index.html` became a three-column layout: FAQ and Connect on the left, the
existing credit paragraph unchanged in the middle, Terms of Use and Privacy Policy on the right,
stacking credit-first below 700px. Those 35 added lines were **swept into commit `ed2725a`**, whose
message is about door hover states. Nothing was lost, and git recorded the change as pure
insertions around a byte-identical credit paragraph, but `ed2725a` contains footer work it does not
mention.

**The consequence was a live defect.** `ed2725a` put four footer links on the live site while the
pages behind them did not exist, so `/faq/`, `/connect/`, `/terms/` and `/privacy/` returned 404 on
gccphilanthropy.org until `3bfcc14`. If `index.html` is ever reverted, keep the `.sig-cols` block or
the live footer loses those links again.

### THE FOUR PAGES ARE GENERATED. Do not hand-edit them.

`tools/build-legal.py` renders them from a Python content module that also produces the Word
edition of the same three notices. One source of words, two renderers, for the reason
`shared/tokens.css` is checked against the `:root` block in `index.html`: a legal statement written
twice will differ, and the difference is found by the person the notice protects. A hand edit is
silently overwritten by the next build.

The only strings the build contributes are the connect form's field labels, its button, its human
check and its two result lines. A check over the built pages finds zero sentences absent from the
source.

**Known weakness: the content module lives outside the repository**, in a session scratchpad. It
has been flagged to Ali. Until it moves in, the generator cannot be re-run by anyone who does not
have that file.

### Decisions that were measured, so nobody re-derives them

- **The sheet is capped at 920px with the column centred.** At the register's full 1280 measure the
  sheet came out 1217px around a 582px text column, leaving a 507px void on ONE side, which reads
  as broken rather than as a wide margin. Measured before and after.
- **Weights are 400 and 600 only.** Source Serif 4 is a variable face that will render 200 if asked,
  and the font URL on these pages requests only 400 and 600 for that reason.
- **The four pages carry the product bar but mark no entry current.** They are not products. The
  page tab names the surface, as on the toolkit and the member states.
- A partner review caught the three part standfirsts hardcoded in BOTH builders. They now live in
  the content module and both renderers read them from there. The rebuild after that refactor was
  byte-identical, which is what a pure de-duplication should be.

### The connect form, and the mail that now exists

The form posts to `alialmokdadleadership.com/gccp-connect.php` on the shared cPanel, because GitHub
Pages cannot run a script. It sends one message to `connect@gccphilanthropy.org` and one to a
personal address, and reports success only when the first is accepted. Honeypot, minimum elapsed
time and the human check are all enforced server-side; the client checks are advisory. The form has
a real `action` and `method`, so it works without JavaScript.

**It is origin-locked to `https://gccphilanthropy.org`, so it returns 403 from localhost. That is
correct behaviour, not a bug**, and it means the form cannot be tested from a preview server.

`connect@gccphilanthropy.org` is now a real mailbox on that cPanel. The domain's DNS changed with
it: MX to `mail.gccphilanthropy.org`, new A records for `mail` and `webmail`, and an SPF record
naming `ip4:198.187.31.178`. **The four GitHub Pages A records and the www CNAME were not touched
and the site still serves 200.** DKIM and DMARC are still missing and Ali knows.

Note for anyone reading the SPF: `.178` is this domain's sending IP per cPanel's own Email
Deliverability page, and `ailiteracyfoundation.eu` on the same server uses it too. The `.64` in
`alialmokdadleadership.com`'s SPF is a different node and copying it here would have published an
SPF that fails.

### Untracked, deliberately

Two files in the repository root, `GCC Philanthropy Register - Privacy, Terms and FAQ.docx` and
`.pdf`. Deliverables Ali asked to keep in the project folder. **Do not `git add -A`**: committing
them would make them publicly downloadable from the live site.

### The shared working tree, and why `git add <path>` is not safe here

Both sessions of 21 August were in ONE working tree, not merely one repository. That is the whole
explanation for two near-losses, and it is worth stating as a rule rather than as an anecdote.

First, commit `ed2725a` carried this session's footer rewrite without mentioning it, because the
footer edit was sitting uncommitted in `index.html` when the other session ran `git add index.html`.

Then the reverse. Ali asked for one word changed in every page footer, `Compiled by` becoming
`Owned and managed by`. That phrase lives in the seven `members/*.html` files, and staging them
picked up **257 lines** of the other session's in-flight work: the `seo:start` blocks from
`tools/build_seo.py`, the `country-hub:start` sections from `tools/build_member_hubs.py`, and the
removal of `<meta name="robots" content="noindex">`. Committing that would have published generated
pages while their generators were still untracked, and silently made the member pages indexable.

**THE RULE. In a shared working tree, `git add <path>` commits whatever is in that file, not what
you changed in it.** For a small edit to a file another session may be holding, build the blob and
stage it directly:

    git show "HEAD:$f" > tmp          # the file WITHOUT anyone's uncommitted work
    ...apply only your own change to tmp...
    sha=$(git hash-object -w --no-filters tmp)
    git update-index --cacheinfo 100644,"$sha","$f"

The commit then contains your change alone and the other session's work stays in the working tree.
Verify it worked by reading `git show --stat HEAD`: if a one-word change reports more than one line
changed, stop.

`git status` is also not a safe guard here. It shows the shared tree, so a file can appear modified
because of work that is not yours, and it can appear clean seconds after someone else commits.
