---
name: Homogenization Tracker, Codex
description: One sheet torn from an inventor's codex. The chart is the drawing; the words are its margin.
colors:
  sanguine: "#7A2A1B"
  sanguine-deep: "#5E1F13"
  ink: "#1A0B07"
  lead: "#F7ECDF"
  lead-2: "#F4BFA6"
  gall: "#160E0B"
  gall-2: "#B9A595"
  chalk: "#DD6A4B"
typography:
  numeral:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "min(10.4vw, 19vh)"
    fontWeight: 300
    lineHeight: 0.86
    letterSpacing: "-0.035em"
    fontFeature: "\"tnum\", \"lnum\""
  sheet-title:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "min(3.02vw, 6.2vh)"
    fontWeight: 500
    lineHeight: 1.12
    letterSpacing: "-0.012em"
  headline:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(30px, 4.2vw, 64px)"
    fontWeight: 500
    lineHeight: 1.02
    letterSpacing: "-0.02em"
  study-numeral:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(34px, 2.8vw, 46px)"
    fontWeight: 300
    lineHeight: 1
    letterSpacing: "-0.03em"
  lead-in:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(17px, 1.35vw, 21px)"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"lnum\""
  margin-note:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.25
  label:
    fontFamily: "Jost, ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.14em"
rounded:
  none: "0px"
  point: "50%"
spacing:
  gutter: "clamp(16px, 2.2vw, 40px)"
  sheet-column-gap: "clamp(18px, 2.4vw, 44px)"
  band: "clamp(64px, 10vw, 150px)"
  band-mobile: "64px 18px"
  block: "clamp(36px, 5vw, 70px)"
  row: "6px"
components:
  action-link:
    textColor: "{colors.lead}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "0.55em 0"
  folio-link:
    textColor: "{colors.lead}"
    typography: "{typography.label}"
    padding: "0.5em 0"
  readout:
    backgroundColor: "{colors.sanguine-deep}"
    textColor: "{colors.lead}"
    rounded: "{rounded.none}"
    padding: "0.55em 0.8em"
  chart-point:
    backgroundColor: "{colors.sanguine}"
    rounded: "{rounded.point}"
    size: "11px"
  chart-point-latest:
    backgroundColor: "{colors.lead}"
    rounded: "{rounded.point}"
    size: "15px"
  question-dot:
    backgroundColor: "{colors.lead}"
    rounded: "{rounded.point}"
    size: "22px"
  study:
    textColor: "{colors.gall-2}"
    padding: "12px 4px 14px"
  plate:
    backgroundColor: "{colors.gall}"
    textColor: "{colors.lead}"
    padding: "{spacing.band}"
---

# Design System: Homogenization Tracker, Codex

## Overview

**Creative North Star: "The Codex Sheet"**

The page is one leaf from an inventor's notebook, drawn on red-prepared ground. The data is the drawing and every word is a margin note around it. Two media do all the work: iron-gall ink builds the construction (hairlines, compass arcs, dimension marks, pricked points) and white lead heightens whatever carries meaning (the measured line, the numbers, the text). Deeper sections turn over to the reverse of the sheet, an iron-gall plate drawn in red chalk.

Density is a draughtsman's: generous ground, fine lines, nothing boxed. Regions are told apart by construction lines and by switching ground (sanguine sheet, gall plate), never by cards. One constructed geometric face, Jost, carries every role through weight, caps and italic alone. The motion grammar is drawing: construction appears first, then the line in white lead, then the margin notes turn from mirror script to readable.

The world rejects the dashboard hero (metric cards over a boxed chart) and the cream-parchment antique souvenir. The ground is dark red chalk, not aged paper.

**Key Characteristics:**
- Drenched sanguine ground with a chalk grain, never flat colour.
- Two media: ink for construction, white lead for meaning.
- Gall plates in red chalk for the deeper sections.
- No boxes or cards; construction lines and dimension marks separate regions.
- One face (Jost): light for big numerals, medium for headings, spaced caps for labels, italic for notes.
- Drawings (red chalk and white heightening studies) act as scale anchors, never as decoration or data.

## Colors

A two-ground palette: red chalk sheet and iron-gall plate, each drawn in its own pair of media.

### Primary
- **Sanguine Ground** (sanguine): the prepared paper of the sheet and of every non-plate band. Also `theme-color`, the selection text colour, and the hollow centre of chart points. It covers the whole surface, carrying a soft-light fractal grain and two radial washes (a warm light at top left, a dark pool at bottom right).
- **Deep Sanguine** (sanguine-deep): the shadowed ground. Used for the probe readout's fill and the scrollbar track.

### Secondary
- **Iron-Gall Plate** (gall): the ground of the deeper bands (scale anchors, domain studies, close). Carries a low-opacity warm noise grain at normal blend.
- **Red Chalk** (chalk): the drawing medium on gall plates only. Domain study lines, study and caption labels, scale-rule markers. Contrast on gall is 5.66:1. On sanguine it falls to 2.87:1, which is why it never appears there.

### Neutral
- **White Lead** (lead): heightening. Body text, headings, the measured line, the latest point, the y-axis and zero line, focus rings, link underline on hover. 8.29:1 on sanguine, 10.72:1 on deep sanguine, 16.35:1 on gall.
- **Warm Lead** (lead-2): secondary heightening on sanguine. Ledger terms, axis captions, dates, the title dash, quiet notes, the resting link underline, the one-line (y = 1) graticule. 5.91:1 on sanguine.
- **Gall Wash** (gall-2): secondary text on gall plates, the plate counterpart of Warm Lead. Captions, study notes, scale-rule ticks, colophon. 8.06:1 on gall. Its alpha forms (`rgb(185 165 149 / .2–.7)`) draw study gridlines, baselines and the colophon rule.
- **Iron-Gall Ink** (ink): construction only. Compass and guide lines on the numeral, gap and steady-state dimension marks, the line's under-stroke. Ruling lines are ink at reduced alpha: `rgb(26 11 7 / .42)` for rules and `rgb(26 11 7 / .22)` for soft rules and minor graticule. 1.99:1 on sanguine, so it is never used for text.

### Named Rules
**The Two Media Rule.** Ink draws how something is built; white lead draws what it means. If removing a mark would lose information, it is lead. If it only shows construction, it is ink.

**The Chalk Stays on the Plate Rule.** Red chalk is used only on gall grounds. On a sanguine ground, secondary emphasis is Warm Lead.

**The Ground Swap Rule.** On a plate, Warm Lead gives way to Gall Wash for quiet text; Lead stays the primary text on both grounds.

## Typography

**Display Font:** Jost (variable 100–900, roman and italic, self-hosted, OFL) with ui-sans-serif, system-ui fallback
**Body Font:** Jost
**Label Font:** Jost, in spaced caps

**Character:** a constructed geometric face, the kind a draughtsman would build with compass and rule. Light weights make the numerals look drawn rather than set. Italic plays the hand of the margin note.

### Hierarchy
- **Numeral** (300, min(10.4vw, 19vh), 0.86): the headline number in the sheet margin, tabular lining figures, built over cap and base guide lines with a compass circle.
- **Sheet Title** (500, min(3.02vw, 6.2vh), 1.12): the one-line title across the sheet. It never wraps on desktop. The em dash drops to weight 300 in Warm Lead.
- **Headline** (500, clamp(30px, 4.2vw, 64px), 1.02): band headings, max 18ch, balanced wrap, written as declarative sentences ending in a full stop.
- **Study Numeral** (300, clamp(34px, 2.8vw, 46px), 1): the current value in each domain study.
- **Lead-in** (400, clamp(17px, 1.35vw, 21px), 1.5): band introductions, max 58ch. Method paragraphs run clamp(17px, 1.3vw, 20px) at 1.55, max 60ch.
- **Body** (400, 17px, 1.5; 16px under 760px): lining figures by default, tabular figures in every numeric cell.
- **Margin Note** (italic 400, 15px, 1.25): chart notes, dimension-mark labels, captions, hints. The pull statement runs larger: italic clamp(20px, 1.9vw, 28px) at 1.4 behind an ink rule.
- **Label** (600, 14px, 0.14em, uppercase): domain and index headings, study names. The folio uses the same caps at weight 400. Axis captions use 13px at 0.12em, and note heads use 12.5px.

### Named Rules
**The One Face Rule.** Jost carries every role. Hierarchy comes from weight (300 / 400 / 500 / 600), caps and italic, never from a second family.

**The Drawn Numeral Rule.** Large figures are set at weight 300 with tight negative tracking, so they read as drawn strokes. Medium weight is for headings and inline values.

## Layout

The first viewport is one sheet: `100svh` tall (capped at 1180px), on a two-column grid with a margin column of `minmax(280px, 25.5%)` and the chart filling the rest. A folio strip on top (38–50px, ruled below), then the one-line title, then the margin and the chart side by side. The margin stacks the numeral, a one-sentence lede (max 30ch), a dotted-leader ledger (max 32ch) and the action links pinned to its foot. Fluid sizes inside the sheet clamp against both `vw` and `vh`, so title, number and full chart fit together in a 1280×720 viewport.

The chart is a size container. Every length derives from container units and custom properties (`--top`, `--bot`, `--left`, `--x0`, `--x1`), so the figures, the pre-data gap (one Einstein width) and the line keep their proportions at any size.

Below the sheet, full-width bands alternate between sanguine and gall plate, padded by the band spacing, with the side gutter. Each band opens with a dimension-mark rule at the top (a hairline with end ticks and a centre tick, at 32% opacity in the current colour). Content grids: scale anchors `1fr / 1.1fr / 1fr`, question rows beside a `minmax(260px, 30%)` pick column, five domain studies in a row, method `1.25fr / 1fr`.

Responsive behaviour: 761–1100px puts the studies in 3 columns. At 760px and below, the sheet un-pins its height and becomes a single column. The numeral sits beside the lede, the folio nav and margin actions hide (the method band repeats them), the title wraps and balances, secondary chart labels drop, and the anchors, measures, studies (2 columns) and method all reflow. Below 380px only the study gaps tighten.

## Elevation & Depth

The sheet is flat paper. Depth comes from the ground's grain and radial washes, from switching to the darker gall plate, and, in the close, from multiplane layering: a back rank of automata at 30% opacity with `brightness(.55) blur(1px)` behind a full-strength front rank, the two drifting opposite ways as the band scrolls through view.

### Shadow Vocabulary
- **Readout lift** (`box-shadow: 0 10px 30px -10px rgb(20 4 0 / .6)`): only on the transient chart readout, the one object floating above the sheet.
- **Ink under-stroke** (a 7px ink stroke at 35% under the 3.2px lead stroke): seats the measured line into the ground. A drawn stroke, not a box shadow.

### Named Rules
**The Flat Sheet Rule.** Nothing at rest casts a shadow. Only the readout, which appears while the chart is probed, is lifted.

## Shapes

Square-cornered everywhere (0 radius). The only curves are drawn ones: circular chart points, question dots, scale markers and the compass circle (50%). Forms are open and linear: hairline rules (1px; 1.5px for axes and the pick rule), dotted leaders, dimension marks with end ticks, and corner registration crosses (14px arms at 70% Gall Wash) framing each domain study. Arrows are drawn as stroked SVG (1.3 stroke), never glyphs.

## Components

### Action Links
Ruled lines in a column, read like an index of plates.
- **Shape:** full-width rows between 1px rules (top on each, bottom on the last), no fill, no radius.
- **Default:** Lead, weight 500, clamp(15px, 1.2vw, 18px), a drawn arrow pushed to the right edge. In the method band they grow to clamp(18px, 1.6vw, 24px) with 0.75em padding.
- **Hover:** the label slides in 0.5em (padding, 400ms on the house ease).
- **Focus:** a 2px Lead outline, 3px offset (global).

### Inline Links
Underlined text at 1px, 0.22em offset, in Warm Lead (Gall Wash in the colophon). On hover the underline turns Lead at 2px. Folio nav links drop the underline for a 1px bottom rule that appears on hover.

### Chart (signature component)
The plate's drawing. A graticule at every 0.1 (soft rule, every 0.5 a full rule, 0 in Lead at 1.5px, 1 in Warm Lead), with half-ticks on the axis. Lead axis, Warm Lead dates, the measured line in Lead over the ink under-stroke, hollow sanguine points ringed in Lead, the latest point filled with an outer ring. Dimension marks in ink label the pre-data gap, the distance below 1 and the steady stretch. Einstein sits at the origin and four identical automata at top right, each with an italic note headed in caps.
- **Probe:** pointer or arrow keys show a dashed Lead plumb line and the readout (Deep Sanguine fill, 1px Warm Lead border, 0 radius, 14px text with a 20px value). It fades in over 200ms, and the steady-stretch note hides while probing.
- **Draw-in:** see Motion in the sidecar. Graticule lines rule out by value, guides and compass construct, figures bleed in from blur, the line wipes left to right, points prick in along the line's time, notes un-mirror.

### Question Rule
Each domain is a row: a caps label with its mean, then a hairline track with ticks at every 0.1, a 2px Lead mean stroke, and one dot per question, offset into lanes so close values don't overlap. Dots are 22px hit areas with a 10px Lead core at 82%. Hover and pressed states scale the core 1.7× (250ms) and add a 1px ring when pressed. Arrow keys move along the row (roving tabindex). The pick panel beside it has a 1.5px Lead top rule, a balanced quoted question, and the facts with medium-weight values.

### Domain Study
A small study on the plate: corner registration crosses, a Gall Wash baseline, a Red Chalk caps name, a light Study Numeral, and a full 0–1 sparkline in Red Chalk (2.4 stroke) with Gall Wash gridlines and a Lead end dot.

### Disclosure
A ruled summary row (18px, weight 500) with a drawn plus that loses its vertical stroke when open (scale, 300ms). It opens onto auto-filling columns (min 330px) of caps-headed lists with dotted leaders between rows.

## Do's and Don'ts

### Do:
- **Do** cover every surface in a grained ground (sanguine or gall). Never leave a flat colour field.
- **Do** draw construction (guides, dimension marks, gridlines, leaders) in ink or ink alpha, and everything meaningful in Lead.
- **Do** separate regions with hairline rules, dimension marks or a switch of ground.
- **Do** set big figures in Jost 300 with tabular lining numerals and negative tracking.
- **Do** use italic for margin notes and spaced caps (0.12–0.16em) for scale and section labels.
- **Do** keep the chart on the full 0–1 scale, every graticule line a measured division.
- **Do** gate all draw-in and parallax motion behind `prefers-reduced-motion: no-preference`, so the static sheet is complete.
- **Do** keep text at 4.5:1 or better on its own ground (Lead and Warm Lead on sanguine or Deep Sanguine; Lead, Gall Wash and Red Chalk on gall).

### Don't:
- **Don't** put content in filled cards or boxes. The readout is the only filled box, and only while the chart is probed.
- **Don't** use Red Chalk on a sanguine ground (2.87:1), or ink for any text (1.99:1).
- **Don't** introduce a second typeface or a system display face.
- **Don't** round corners. Curves are reserved for points, dots and compass circles.
- **Don't** lean on a cream or parchment ground; the sheet is red-prepared paper.
- **Don't** add drop shadows to resting elements.
- **Don't** use glyph or icon-font arrows. Arrows and plus marks are stroked SVG.
