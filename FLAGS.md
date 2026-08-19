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

---

# The three added on 19 August 2026: Kuwait, Bahrain, Oman

Same rule as the first three. Drawn as vector, checked against the issuing state, and the
places where the source is silent are recorded as silent rather than filled in.

## Kuwait. Geometry is specified in law. The colour is not.

Law No. 26 of 1961 defines the flag: length twice the width, three equal horizontal bands,
green over white over red, with a black trapezium standing on the hoist. The trapezium is
the whole construction, and it is drawn from the rule rather than by eye: its base is the
full height at the hoist and it narrows to exactly the height of the white band, so its
slanted edges land on the band boundaries. In a `0 0 60 30` viewBox that puts its corners
at `0,0 15,10 15,20 0,30`.

Colour is where the sources disagree. Some give Pantone 186 C red with 340 C green, the
Beijing 2008 flag manual gives PMS 032 red with PMS 355 green. No Kuwaiti government source
publishes a hex. So `#007A3D` green and `#CE1126` red are **the common digital rendering,
recorded as an approximation**, exactly as Saudi Arabia is above.

## Bahrain. The count of the points is the one detail that must be right.

Ratio 3:5, so the viewBox is `0 0 50 30`. White at the hoist, red field, separated by a
serrated line of **exactly five** white isosceles triangles. The number is not decorative:
it was fixed at five in 2002 for the Five Pillars of Islam, having previously been higher.
The loop that builds the polygon produces five apexes by construction, so the count cannot
drift if the geometry is ever retuned.

Red is `#CE1126` here. Sources split between Pantone 186 C and 485 C, so this too is the
common digital rendering rather than a claimed official value.

## Oman. The flag is specified. The emblem is simplified on purpose.

The Ministry of Foreign Affairs states it plainly: "three horizontal bands of white, green
and red, with a vertical red band on the left (hoist) side that contains the National
Emblem of Oman in white". The emblem is "a sheathed Khanjar and belt, superimposed on two
crossed swords". Official ratio 4:7 since 22 May 2004, so the viewBox is `0 0 70 40`.
Colours `#FFFFFF`, `#DB171B`, `#028002`.

**The emblem here is a simplification and should be read as one.** Getting there took three
attempts, and the two failures are the reason the third looks as it does:

1. Thin strokes collapsed into a white asterisk. Crossing lines at this size read as a star.
2. Filled shapes stacked on one centre fused into a single lump.
3. What worked was composition, not detail: the swords cross LOW, the khanjar stands ABOVE
   and in front, and the khanjar carries a stroke in the band's own red so its silhouette
   survives where it overlaps the blades.

A faithful tracing of the ornamented sheath and belt would turn to mud at the size this
renders. **A muddy national emblem is a worse outcome than a clean simplified one**, which
is the same principle as never cropping the shahada. Do not "improve" it by adding detail
without looking at it at card size and at 120px first.

## The rule this file exists to protect

Every one of these was judged by RENDERING it and looking, not by reading the path data.
The asterisk and the lump both passed every automated check that was run against them.
