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
