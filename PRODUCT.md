# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

A mixed public audience, designed for the hardest case: a cold reader who arrives from a social feed or a news link, knows nothing about the project, and decides in seconds whether to keep looking. The same page must also hold up for journalists, researchers, and policy readers who want a figure they can cite, and for the client's professional network (lawyers, executives) when it is shown to them directly.

The client is Mark Nomellini (Kirkland & Ellis), who commissioned the research. Dauren runs the project and the pipeline.

## Product Purpose

The Homogenization Tracker is a weekly, public measurement of whether the web is converging on one voice. Every week it asks Google the same 100 everyday questions (20 each in finance, health, law, science, tech), reads the first 5 readable pages behind each answer, and measures how much those pages say the same thing.

The worry behind it: AI-written content is making online writing, and human expression more broadly, converge. The tracker is the forward-looking companion to a retrospective research study (paper in `paper/`) that measured the same question on dated public corpora.

The one-page public summary exists to make that measurement felt in a single glance and to send serious readers one click deeper to the methodology. Success: a cold reader understands "the web's answers are starting to sound alike, and here is the number" without reading any methodology, and a careful reader finds nothing on the page that overstates the data.

## Positioning

It measures this live rather than arguing it. The panel is fixed, the data is real Google results, the code and data are public in the repository, and the measure is the same one the paper uses. Opinion pieces about "AI sameness" cannot claim a frozen panel, a weekly run, or a public record. The tracker can.

## Operating Context

- A weekly GitHub Actions job collects results, analyses pages, rebuilds the pages, and commits data back. Git is the datastore. Pages are served on GitHub Pages: https://biddy1618.github.io/ai-homogenization/tracker/dashboard/
- The one-pager is a shareable link. It must work as a web page and produce a strong preview card when the link is shared. Printing is not a requirement.
- A full dashboard and a methodology page sit behind the one-pager. Technical detail (search-provider changes, methodology versions, page-count rules) lives there, never on the one-pager itself.

## Capabilities and Constraints

- **Measures** (per question, per week, on the first 5 readable pages):
  - `mean_pairwise_cosine`, "similarity": 0 to 1. Higher means the pages are more alike. This is the headline.
  - `vendi`, "distinct pages out of 5": 5 means all different, 1 means all the same.
- **Data:** `tracker/data/runs_top5.csv` (one row per question per week), `tracker/data/_runs_meta.csv` (one row per run), `tracker/queries.txt` (the panel). Every number on the page is computed from these on each build. No hard-coded figures.
- **Panel:** 100 questions. The first 9 per domain (the original 45) have been tracked since 2026-10-04; the other 55 were added on 2026-10-26. Queries are never edited or removed.
- **Honesty constraints:** week-to-week movement is small and the series is young. The chart uses the full 0–1 scale, so the images at each end keep their meaning, and the latest weekly change is stated as a labelled number rather than shown through a zoomed axis. No implied trend the data cannot support. The search provider changed between 2026-10-12 and 2026-10-19, and the largest step in the line sits on that change. It stays off the one-pager but must be stated on the methodology page.
- **Stack:** the existing pipeline is Python generating self-contained static HTML (`tracker/dashboard/build.py`). The one-pager follows the same pattern.
- **Title the client likes:** "AI-driven homogenization of expression — real-time tracker".

## Brand Commitments

- **The client's core idea is binding:** a single line over time, with the low end evoking distinct human genius and the high end evoking identical copies.
- **Low end:** Albert Einstein, as the client suggested. Dauren will clear the rights to Einstein's likeness with the client before the page goes public. His likeness is commercially licensed.
- **High end:** "identical copies", shown as an original helmeted trooper repeated identically. This carries Mark's "clone army" / stormtrooper image without being a franchise character (Disney/Lucasfilm IP on a public site). Bone armour, one horizontal wrap-around visor, viridian joints, marigold hazard stripes — clearly distinct from stormtrooper trade dress (no T-visor, twin lenses, frown grille, ear caps).
- **Mark's composition (2026-11-09):** only two images, so the chart doesn't get crowded: Einstein at the lower left, just right of where the axes meet, and the identical copies at the top right ("where we're heading"). No figures stacked along the axis; he disliked that. The line starts a little right of the y-axis, leaving a gap for the period before 2026-10-04 with no data.

## Evidence on Hand

- Eight weekly runs, 2026-10-04 to 2026-11-16, in `tracker/data/runs_top5.csv`.
- Latest run (2026-11-16): mean similarity 0.780; 1.96 distinct pages out of 5 on average; 48% of questions above 0.80; 59% with fewer than 2 distinct pages.
- Weekly mean similarity: 0.702, 0.732, 0.743, 0.788, 0.780, 0.773, 0.778, 0.780. The rise sits in the first weeks, and the line has been flat since 2026-10-19.
- Latest extremes: most alike, "is intermittent fasting healthy" (0.913); least alike, "how are capital gains taxed" (0.401). Most alike domain: health (0.822); least: finance (0.741).
- The retrospective study (`paper/`, `docs/research/project-briefing.md`) found no broad style homogenization but real topic-level homogenization. The one-pager must not claim more than the tracker measures.
- No testimonials, press coverage, or endorsements exist. Do not fabricate them.

## Product Principles

1. **Felt first, proven one click later.** The page lands the idea instantly; the rigour lives behind a link.
2. **Never louder than the data.** Small movement is shown as small. The strength of the image comes from the framing, not from distorting the chart.
3. **Live, not a one-off.** Every view reflects the latest weekly run; the page is a living instrument, not a static infographic.
4. **Human versus copy.** Every choice reinforces one contrast: distinct voices at one end, identical copies at the other.
5. **Original means only.** No borrowed franchise imagery, no uncleared likenesses at launch.

## Accessibility & Inclusion

Body text contrast of at least 4.5:1. The chart's meaning must survive without images: values and the trend stay available as text.
