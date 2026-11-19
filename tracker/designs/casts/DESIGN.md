---
name: Homogenization Tracker — Cast Gallery
description: Sculptor's dispatch floor — one hand-carved original against a rank of identical casts under hard raking light.
colors:
  graphite: "#131315"
  slate: "#1d1e20"
  slate-2: "#2a2a2b"
  plaster: "#ece6dd"
  plaster-dim: "#bdb6ac"
  chalk: "#8f8981"
  oxblood: "#2c0a0a"
  oxblood-2: "#4a1210"
  oxblood-cut: "#c94a3a"
  oxblood-ink: "#e2735d"
typography:
  display:
    fontFamily: "Big Shoulders Stencil, Arial Narrow, sans-serif"
    fontSize: "55px"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-0.01em"
  stencil-number:
    fontFamily: "Big Shoulders Stencil, Arial Narrow, sans-serif"
    fontSize: "clamp(4.5rem, 18vw, 14rem)"
    fontWeight: 700
    lineHeight: 0.9
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Sofia Sans Condensed, Arial Narrow, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0em"
  label:
    fontFamily: "Sofia Sans Condensed, Arial Narrow, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0.02em"
rounded:
  none: "0px"
  sm: "2px"
spacing:
  u: "1px"
  frame: "1280×720 design units via --u"
  section-y: "clamp(28px, 4vw, 56px)"
  section-x: "clamp(16px, 4vw, 56px)"
components:
  link:
    backgroundColor: "transparent"
    textColor: "{colors.plaster}"
    typography: "{typography.body}"
    padding: "0"
  band-oxblood:
    backgroundColor: "{colors.oxblood}"
    textColor: "{colors.plaster}"
    padding: "clamp(28px, 4vw, 56px) clamp(16px, 4vw, 56px)"
  label-plinth:
    backgroundColor: "rgb(14 14 15 / .82)"
    textColor: "{colors.plaster}"
    typography: "{typography.label}"
    padding: "6px 0"
---

## Overview

This surface is the cast workshop's dispatch floor: one original carved by hand, never numbered, set against a rank of identical plaster casts pulled from a single mould and stamped with edition numbers. The page refuses both the beige-marble museum souvenir and the generic dashboard hero-plus-cards template. Graphite and slate are the walls; plaster white is reserved for the data line, the figures, and the headline facts; oxblood marks the stencil cuts and the full-width section bands.

The first viewport is a living instrument on a long slate plinth under hard raking light from the upper left. Title, oxblood stencil headline number, stated weekly change, links, the cast rank, and the honest 0–1 chart with Einstein at the origin and identical helmeted casts at the far end all hold on one desktop screen. Below the fold the visitor walks the week's pull, calliper strips per question, the full ledger, and how the measure is built — still in workshop language, still on the same materials.

Motion is material, not decoration: scroll sweeps the raking light across the cast rank and plinth; hovering or focusing a run sets the calliper jaw and readout. Everything stops under `prefers-reduced-motion`.

## Colors

| Token | Hex | Role |
| --- | --- | --- |
| graphite | `#131315` | Page ground, Einstein plate backing |
| slate / slate-2 | `#1d1e20` / `#2a2a2b` | Plinth and wall planes |
| plaster | `#ece6dd` | Primary text, data line, bright faces |
| plaster-dim / chalk | `#bdb6ac` / `#8f8981` | Secondary text, ticks |
| oxblood | `#2c0a0a` | Full-width bands, deep recesses |
| oxblood-cut / oxblood-ink | `#c94a3a` / `#e2735d` | Stencil fill, change figure, selection |

Plaster white is the only bright. Do not introduce a second accent hue. Dark is forced by the studio scene (raking light on chalk forms in a graphite bay), not by dashboard habit.

## Typography

Display and the carved headline number use self-hosted **Big Shoulders Stencil** — crate-mark lettering, not a classical serif. Body, deck, labels, and ledger use self-hosted **Sofia Sans Condensed**. Both load via `@font-face` from `fonts/` beside the page; never a hosted stylesheet. Tabular figures stay on for data. Title stays one line at desktop; it may wrap only when the container truly cannot hold it.

## Layout

The hero is a 1280×720 design frame scaled with `--u: min(100cqw / 1280, 100svh / 720)` so title, number, casts, and full chart stay in the first viewport from 1280×720 through 1440×900 and wider. Below the fold: oxblood band ("This week's pull"), then calliper strips, ledger, and methodology in a max-width wrap. From `@container (max-width: 760px)` the frame stacks; whole casts drop as units — never crop a cast. No horizontal overflow from 320px up.

## Elevation & Depth

Depth comes from raking light, recessed stencil numerals, and soft offset shadows on labels (`0 2u 6u rgb(0 0 0 / .5)`). No zero-offset colored halos. The studio plate carries the wall and plinth; figures are transparent cutouts sitting on graphite or slate.

## Shapes

Square and hard. No card radii, no pill buttons, no soft dashboard tiles. Mould seam lines and calliper ticks are the rules. Edition numbers are the wayfinding.

## Components

- **Headline number** — oxblood-cut stencil plate (`big-number`), not live text digits.
- **Cast rank** — one helmeted cast asset repeated whole; stencilled 1–6 above.
- **Chart** — CSS segments on the plinth face; Einstein lower-left (scale anchor), gap ~bust width before first run, identical-cast metaphor only in imagery elsewhere / label at top-right of the line.
- **Run markers** — focus/hover sets jaw + readout; latest run is the default "now".
- **Calliper strips** — pointer reading per question on a 0–1 rule.
- **Links** — "Methodology and data" and "Full dashboard" only; no provider-change marker on this page.

## Do's and Don'ts

- Do keep plaster white reserved for data, figures, and headline facts.
- Do plot the line on an honest full 0–1 scale from the CSVs; never exaggerate week-to-week movement.
- Do state the weekly change as a number; do not zoom the axis to invent drama.
- Do leave a bust-width gap before the first dated run.
- Do stop raking-light and scroll motion under `prefers-reduced-motion`.
- Don't use beige marble, Roman serif, or museum-souvenir classicism.
- Don't put franchise robots or traced museum statues in the plates — only the original Einstein bust and original helmeted cast authored for this page.
- Don't clutter the chart with extra figures or a search-provider marker.
- Don't overwrite the project-root `DESIGN.md`; this file is the system for this surface only.
