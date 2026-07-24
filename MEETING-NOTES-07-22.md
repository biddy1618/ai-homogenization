# Meeting Notes — July 22, 2026 (Mark Nomellini)

## Action Items

| # | Owner | Item | Status |
|---|-------|------|--------|
| 1 | Dauren | Send three Stack Exchange prototype candidates to Mark | ✅ Done (07/22) |
| 2 | Mark | Review three candidates and email Dauren feedback | ✅ Done — picked Cross Validated |
| 3 | Dauren | Set up GitHub repository with research files and scripts for Mark | ✅ Done |
| 4 | Dauren | Check if companies will object to data usage for research | Pending |
| 5 | Dauren | Review papers for data sharing and referencing best practices | Pending |
| 6 | Dauren | Build Cross Validated prototype (download dump, parse, analyze) | **Next** |

## Key Decisions

- **Primary platform**: Stack Exchange (available data dumps)
- **Approach**: Start simple (TTR + cosine similarity), sophisticate later
- **Content scope**: Start with articles/posts first, then incorporate comments
- **Temporal framing**: Measure trends over time, with pre-ChatGPT baseline for comparison

## Data Sources

**High expertise**: Stack Overflow, Stack Exchange network, Hacker News, academic journals (PubMed data dumps available)  
**Low expertise**: Amazon reviews, YouTube comments, general review platforms  
**Dropped**: Quora (crawling challenges, no data dumps)

## Metrics (Agreed)

- **First iteration**: Type-token ratio (TTR) + cosine similarity
- **Later**: Centroid distance, divergence, perplexity
- Simple heuristics first → sophisticated embeddings later

## Platform Categorization

- Categorize by posting difficulty and required domain expertise
- High cognitive load = significant domain knowledge required
- Comments vary by platform (Stack Exchange comments are substantive vs YouTube which are low-content)

## Research Context

- Internet homogenization affects Google search utility and academic research quality
- Homogenization trends should be visible in post data if properly measured
