---
name: Homogenization Tracker — Saga
description: One edited sequence from a 1977-style practical-effects space epic — matte horizon, twin-sun amber, hard optical wipes.
world: "saga"
colors:
  void: "#0e1014"
  horizon: "#30271a"
  ember: "#4c2f1d"
  bone: "#dbd8cf"
  amber: "#e18f2a"
  amber-hot: "#f0a84a"
  crawl-gold: "#f2d06b"
  navy: "#1a2740"
  steel: "#a8b0bc"
typography:
  display:
    fontFamily: "Teko, Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "clamp(22px, 3.9cqw, 52px)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "0.02em"
  headline:
    fontFamily: "Teko, Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "clamp(1.85rem, 3.8vw, 2.9rem)"
    fontWeight: 600
    lineHeight: 1.02
  crawl:
    fontFamily: "Barlow Condensed, Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "clamp(1.2rem, 2.6vw, 1.65rem)"
    fontWeight: 700
    fontStyle: italic
    color: "#f2d06b"
  figure:
    fontFamily: "Saira, Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "clamp(56px, 11cqw, 140px)"
    fontWeight: 700
    lineHeight: 0.92
    letterSpacing: "0.02em"
    fontFeature: "\"tnum\""
  title:
    fontFamily: "Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "clamp(12px, 1.55cqw, 18px)"
    fontWeight: 500
    letterSpacing: "0.03em"
  body:
    fontFamily: "Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 500
    lineHeight: 1.45
  label:
    fontFamily: "Saira Semi Condensed, system-ui, sans-serif"
    fontSize: "clamp(10px, 1.1cqw, 13px)"
    fontWeight: 500
    letterSpacing: "0.08em"
  readout:
    fontFamily: "Share Tech Mono, ui-monospace, monospace"
    fontSize: "0.92rem"
    fontWeight: 400
    fontFeature: "\"tnum\""
rounded:
  none: "0"
  hair: "2px"
spacing:
  sm: "0.55em"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  section: "clamp(36px, 6vw, 72px)"
  page-x: "clamp(16px, 4vw, 40px)"
  page-y: "clamp(40px, 7vw, 88px)"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.void}"
    rounded: "{rounded.none}"
    padding: "0.55em 0.9em"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "{colors.bone}"
    textColor: "{colors.void}"
  fact-plate:
    backgroundColor: "rgb(26 39 64 / 0.55)"
    textColor: "{colors.bone}"
    rounded: "{rounded.none}"
    padding: "1rem 1rem 1.1rem"
  extreme-plate:
    backgroundColor: "rgb(26 39 64 / 0.55)"
    textColor: "{colors.bone}"
    rounded: "{rounded.none}"
    padding: "1rem 1.1rem 1.15rem"
  change-box:
    backgroundColor: "rgb(14 16 20 / 0.55)"
    textColor: "{colors.amber}"
    rounded: "{rounded.none}"
    padding: "0"
---

# Design System: Homogenization Tracker — Saga

## Overview

**Creative North Star: "The Optical Wipe"**

The page is one edited sequence from a 1977-style practical-effects space epic: deep-space void, a dusty matte-painted twin-sun horizon, and shots joined by hard optical wipes. The establishing shot is the chart itself — Einstein low-left, identical armoured ranks top-right, one warm amber line on a full 0–1 axis. It refuses both the neon data dashboard and the painted one-sheet with a chart pasted under it.

Hardware language runs through every surface below the fold: navy hull plates, hazard striping, stencilled markings, and scanline phosphor readouts. Twin-sun amber owns the live number, the plot, the axes, and the CTAs; bone carries readable body; steel is mute metadata only.

**Key Characteristics:**
- Deep void black with a matte twin-sun horizon, never a flat dashboard canvas
- One amber light source for every live figure, axis, and wipe
- Condensed epic display (Teko) + italic Barlow Condensed crawl + mono phosphor readouts
- Hard wipes (horizontal, diagonal, iris) as the only transitions
- Square hull plates; almost no corner radius
- Original bone-armour ranks with navy joints and amber hazard stripes — never franchise armour

## Colors

A dark practical-effects palette: void sky, warm horizon dust, twin-sun amber as the single live accent, navy hardware, bone type.

### Primary
- **Twin-Sun Amber** (`amber`): Live figures, plot line and dots, axes, domain scores, CTA fills, focus rings, selection. Owns every “this is the number” moment.
- **Amber Hot** (`amber-hot`): Hover brightening on text links only — the sun flaring, not a second brand color.
- **Crawl Gold** (`crawl-gold`): Perspective crawl type only — warmer than franchise `#ffe81f`, tied to the twin-sun grade.

### Secondary
- **Hull Navy** (`navy`): Fact plates, extreme cards, hazard-stripe gaps — armour and instrument housing.

### Neutral
- **Void** (`void`): Page ground, chart field, change-box fill, theme-color.
- **Horizon Dust** (`horizon`) / **Ember** (`ember`): Matte-painting warm midtones reserved for plates and atmosphere, not UI chrome.
- **Bone** (`bone`): Primary readable type on void; primary-button hover fill.
- **Steel** (`steel`): Muted metadata, colophon, “not read” states — never the headline.

### Named Rules
**The Twin-Sun Rule.** Amber is the only live accent. It paints the headline figure, weekly change, plot, axes, hazard accents, and primary CTAs. No second chroma for “emphasis.”

**The Exposure-Ramp Rule.** Neutrals stay on one stepped dark-to-bone ramp (void → horizon/ember → navy → steel → bone). Do not introduce cool greys or teal fills that break the matte-painting grade.

## Typography

**Display Font:** Teko (with Saira Semi Condensed, system-ui)
**Crawl Font:** Barlow Condensed Bold Italic
**Body Font:** Saira Semi Condensed (system-ui)
**Figure Font:** Saira (tabular nums, weight 700)
**Readout Font:** Share Tech Mono (ui-monospace)

**Character:** A condensed epic display for the title and section heads; italic condensed gothic for the perspective crawl (genre-adjacent, not franchise logo lettering and not News Gothic); stencil UI for hull markings; heavy Saira for cockpit figures; mono phosphor for small scored data.

### Hierarchy
- **Display** (600, uppercase, `clamp(22px, 3.9cqw, 52px)` / `clamp(1.85rem, 3.8vw, 2.9rem)`, lh 1.02): Page title (one line on desktop) and band headlines.
- **Crawl** (700 italic Barlow Condensed, twin-sun gold `#f2d06b`): Perspective story block under the establishing shot.
- **Figure** (700, `clamp(56px, 11cqw, 140px)`, lh 0.92, tabular): Establishing-shot headline number and change value; fact plate numerals.
- **Title** (500, `clamp(12px, 1.55cqw, 18px)`): Figure labels and supporting chart copy.
- **Body** (500, ~1.05rem, lh 1.45, max ~58ch in methodology): How-it-works prose.
- **Label** (500, uppercase, tracking ~0.08em): Brand strip, week stamp, link strip, domain heads.
- **Readout** (Share Tech Mono, tabular): Domain and per-question scores — fixed character cells.

### Named Rules
**The Split-Flap Rule.** Live figures change inside fixed tabular cells (`font-variant-numeric: tabular-nums`). Never proportional digits for the headline number, change, or scored lists.

**The Phosphor Rule.** Scanline overlay (`.scan`) belongs on brand, week, change value, tick labels, and scored readouts — not on long body prose.

## Layout

Desktop first viewport is a 1280×720 establishing shot inside a max 1440px stage (`aspect-ratio: 1280 / 720`), absolute-layered like an optical composite. Thin top strip (brand, week, two links), hairline rule, one-line title, amber figure + change box left, formation plate right, chart field with Einstein low-left and full 0–1 axes. Below the fold: max-width 1100px, wipe separators, perspective crawl, then fact / extreme / domain / methodology bands.

At container ≤760px the stage stacks; chart axes hide; formation and Einstein stay as absolute overlays and **edge-crop inward** rather than uniformly scaling down. Phone from 320px: no horizontal overflow. Below-fold grids collapse to one column under 760px.

### Named Rules
**The Establishing-Shot Rule.** Desktop first viewport must hold the one-line title, the headline number, and the full chart with both figures. Do not demote the chart to a card under the fold.

**The Edge-Crop Rule.** Trooper ranks and Einstein crop from the edges on narrow screens; never shrink the whole formation to a tiny sticker.

## Elevation & Depth

Depth is tonal and optical, not Material elevation. The matte backdrop + dual scrim gradients set space; plates use translucent navy fills and 1px bone/amber hairlines; figures use soft drop shadows only on the Einstein and formation plates (`drop-shadow(0 6–8px 14–18px rgb(0 0 0 / .55))`). UI chrome stays flat.

### Shadow Vocabulary
- **Plate cast** (`filter: drop-shadow(0 8px 18px rgb(0 0 0 / .55))` on formation; `0 6px 14px` on Einstein): Grounds the two chart figures in the matte painting.
- **Inset hull** (`box-shadow: inset 0 0 0 1px …` on fact/extreme plates): Instrument bezel, not lift.

### Named Rules
**The Flat-Hull Rule.** Interactive surfaces do not float. Depth comes from the backdrop, scrim, and plate insets — not stacked card shadows.

## Shapes

Almost entirely square. Fact plates, extreme cards, change box, and primary links use `border-radius: 0`. Plot segment caps use a hair radius (2px); plot dots are circles (50%). Hazard accents are repeating linear stripes (vertical on fact plates, diagonal on the no-data hatch). Wipes are geometric optical shapes: horizontal bar, 135° diagonal band, radial iris.

### Named Rules
**The Hull-Plate Rule.** Content containers are squared instrument plates with 1px borders — never rounded cards or soft chips.

## Components

### Buttons
- **Shape:** Square (`0`)
- **Primary:** Amber fill, void text, uppercase, tracking 0.06em, padding `0.55em 0.9em`, weight 700
- **Hover:** Bone fill, void text (links in body use amber-hot text hover instead)
- **Focus:** 3px amber outline, 3px offset

### Fact plates
- **Character:** Stencilled hull instruments with a left hazard stripe
- **Background:** `rgb(26 39 64 / .55)` + bone border + inset amber hairline
- **Stripe:** 4px repeating amber / navy (`6px / 6px`)
- **Figure:** Amber Saira 700 tabular; label bone ~0.95rem

### Extreme plates
- **Border:** `1px solid rgb(225 143 42 / .45)`
- **Background:** Vertical navy→void gradient
- **Stencil head:** Amber uppercase tracking 0.12em (hull marking, not a marketing eyebrow)
- **Meta:** Steel

### Change box
- **Border:** `2px solid rgb(225 143 42 / .85)` over void scrim
- **Contents:** Amber tabular change + bone “since …” label; scanline on the value

### Chart / plot
- **Axes & frame:** Amber bars (~4px at reference width)
- **Grid:** Dashed bone-muted repeats (`#9a968c`)
- **Line:** Amber segments 3.5px; dots 10px with void stroke
- **Gap hatch:** Diagonal amber stripes marking no-data before 04 Oct
- **Composition (binding):** Einstein just right of origin; identical ranks top-right; line starts ~one Einstein-width right of the y-axis; full 0–1 scale always

### Navigation / strip
- Brand in amber uppercase with scanlines; week in bone; methodology + dashboard as underlined bone links
- Hairline rule under the strip uses a warmer copper (`#c9883a`) as a one-shot optical splice — not a second accent token

### Wipes
- Horizontal, diagonal, and iris amber optical wipes between below-fold shots
- Motion: `wipeIn` 0.7s `cubic-bezier(.16,1,.3,1)`; crawl 34s linear; both gated by `prefers-reduced-motion`

### Perspective crawl
- Twin-sun gold (`#f2d06b`) Barlow Condensed italic on void, `rotateX(30deg)`, masked fade — **not** franchise logo lettering, **not** News Gothic, **not** `#ffe81f` crawl yellow
- Auto-flows only (no pause/scroll control). Reduced-motion: static untransformed text.

## Do's and Don'ts

### Do:
- **Do** keep twin-sun amber as the sole live accent for figures, plot, axes, and primary CTAs.
- **Do** set the chart on a full 0–1 axis and state weekly change as a labelled number.
- **Do** place only Einstein (low-left) and identical original troopers (top-right) on the chart — no stacked axis figures, no search-provider marker.
- **Do** leave a no-data gap (~one Einstein-width) before 04 Oct, marked with the hatch.
- **Do** use Teko for display, Barlow Condensed for the crawl, Saira for figures, Saira Semi Condensed for UI, Share Tech Mono for scored readouts.
- **Do** join below-fold sections with hard optical wipes only.
- **Do** edge-crop the formation on narrow viewports; keep tabular figures in fixed cells.
- **Do** use an **original** helmeted trooper: single wrap-around visor; bone / ivory armour with navy or charcoal joints and amber hazard stripes; original plate layout; every image generated for the page.

### Don't:
- **Don't** use pure white-and-black stormtrooper trade dress, ear-caps, frown grille, twin lenses, T-visor, or any helmet silhouette near Halo, Cylons, Destiny, Mass Effect, Starship Troopers, or Daft Punk.
- **Don't** introduce franchise weapons, ships, backdrops, droids, creatures, names, words, logo lettering (including Star Jedi), music, sound, or stills.
- **Don't** use the franchise crawl typeface (News Gothic / Trade Gothic / News Cycle) or `#ffe81f` yellow-on-black logo treatment.
- **Don't** zoom the chart axis to dramatize small weekly movement.
- **Don't** add rounded cards, neon dashboard glows, purple accents, or soft Material elevation.
- **Don't** put marketing kickers/eyebrows above headlines; stencil uppercase is hull marking only (brand strip, domain heads, extreme plate stamps).
- **Don't** scale the trooper ranks down uniformly on mobile — crop from the edge.
