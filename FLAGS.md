# The three flags: what was checked, against what, and what is still an approximation

Every flag here is drawn as vector in `index.html` (`countryMark`), not lifted from a photograph,
so it is licence-clean and stays crisp at any size. This file exists so a later session does not
"simplify" the geometry or "tidy" a colour back to a wrong value. All three were checked against
the issuing government, not against a colour-picker site.

## United Arab Emirates. Fully specified, and two values here were wrong until 18 Aug 2026.

The UAE Government Media Office publishes a visual identity guideline for the flag, and the 2023
UAE Flag Guidebook states the colours as Pantone values with their RGB conversions:

| part  | official          | hex       | was          |
|-------|-------------------|-----------|--------------|
| red   | Pantone 186 C, RGB 200 16 46 | `#C8102E` | `#CE1126` wrong |
| green | Pantone 348 C, RGB 0 132 61  | `#00843D` | `#00732F` wrong |
| black | Pantone Black C6  | `#000000` | correct       |
| white | Pantone C000      | `#FFFFFF` | correct       |

Proportions 1:2, so the `viewBox` is `0 0 60 30`. The red bar is at the hoist and runs the full
height; green, white and black are equal horizontal bands across the remaining two thirds.

Source: UAE Government Media Office visual identity guideline, `vig.gmo.gov.ae/en/guideline/the-uae-flag`
(the page itself refuses automated fetches with a 403, so the values above were taken from the
published guideline figures and cross-checked against two independent renderings that agree).

## Qatar. Fully specified, and it was already right.

The Ministry of Foreign Affairs states, on its own national-flag page, that the flag "consists of
two colours: white and 'Al Adam' (maroon) (Pantone # 1955 C)" with "nine isosceles triangles"
between them, bases in the white toward the hoist and points into the maroon.

- maroon Pantone 1955 C = `#8A1538`
- nine serrations, drawn as nine, counted in the render
- proportions 11:28, so the `viewBox` is `0 0 56 22`

Source: `mofa.gov.qa/en/state-of-qatar/Key-Facts-and-Information/national-flag`, fetched and read.

Note the history, because it explains the wrong values in circulation: Qatar's earlier Pantone was
222 C, and the state ran a campaign to move everyone onto 1955 C. A source that still says 222 C
is out of date, not an alternative.

## Saudi Arabia. Geometry is specified. The colour is NOT, and this file says so rather than
## inventing an official value.

The official flag site, `saudiflag.sa`, gives the geometry and no colour: "The flag is rectangular
in shape", "its width is equal to two-thirds of its length". That is 2:3, so the `viewBox` is
`0 0 60 40`. The design itself is Article 1 of Cabinet Decision 101, by Royal Decree of 15 March
1973.

No Saudi government source publishes a hex, RGB or CMYK value, and the third-party references
openly disagree with each other: Pantone 330 C, PMS 355 in the Beijing 2008 flag manual, and
Pantone 7484 C in Album des Pavillons 2023. So `#006C35` here is **the common digital rendering,
recorded as an approximation, not as an official colour**. Do not upgrade that sentence to a claim
of officialness without a Saudi government source that actually states a value.

The shahada is drawn as real Arabic text, not as a path or a decorative squiggle, and it carries
`textLength="46" lengthAdjust="spacingAndGlyphs"`. Without that the string measures 78 units in a
60-unit viewBox and is clipped at both ends. The whole SVG is `aria-hidden="true"`, so no screen
reader announces the shahada as loose text.

**The shahada may never be cropped.** That is why the country-page flag is faded with a mask on
its own alpha rather than clipped, cropped, or covered by a scrim, and why the level-1 card sets
each flag whole on a plate at a common height instead of filling the box with `object-fit: cover`.
Three flags whose ratios run from 2:3 to 28:11 cannot fill one box without cropping one of them.

## The height-first rule on the country page

The country hero sizes the flag by HEIGHT, never by width. Sized by width, each flag's height came
out of its own ratio, and the band's `overflow: hidden` sliced 9.3px off the top and 8.3px off the
bottom of the Saudi flag at every desktop width, because 2:3 is the tallest of the three. Height
is capped at 172px rather than 190px because Qatar at 28:11 is the widest: at 190 it came out
484px and pushed 30px into the heading column, and at 172 it is 438px and clears it.
