# Data Sources Research: LOW-COGNITIVE-LOAD Platforms

## Summary Table

| # | Platform | Access Method | Pre-2022 Data? | Scraping Difficulty | Best For |
|---|----------|--------------|----------------|--------------------:|----------|
| 1 | X / Twitter | Paid API (pay-per-use) | Limited | 4 | Short text, high volume |
| 2 | Reddit | Free API + Pushshift archives | ✅ Yes | 2 | Medium text, topic-segmented |
| 3 | Amazon Reviews | Academic datasets (McAuley) | ✅ Yes | 4 | Product reviews, categorized |
| 4 | Yelp | Yelp Dataset (official) | ✅ Yes | 3 | Local business reviews |
| 5 | TripAdvisor | Scraping only | ✅ Yes | 4 | Travel reviews |
| 6 | YouTube Comments | YouTube Data API v3 (free) | ✅ Yes | 2 | Short comments, massive volume |
| 7 | Goodreads | Scraping only (API dead) | ✅ Yes | 4 | Long-form book reviews |
| 8 | App Store / Google Play | Scraping + libraries | ✅ Yes | 3 | Short reviews, categorized |
| 9 | IMDb | Official datasets (no reviews) | ✅ Yes (ratings) | 3 | Movie reviews |
| 10 | Trustpilot | Scraping only | ✅ Yes | 4 | Business reviews, categorized |

---

## 1. X / Twitter (x.com)

### Data Access Method
- **API**: X API v2, pay-per-usage (no subscription tiers anymore)
- Sign up at console.x.com, purchase credits, pay per resource returned
- Full-archive search available (historical tweets)
- Endpoints: `GET /2/tweets/search/all` (full archive), `GET /2/tweets/search/recent` (last 7 days)

### Rate Limits / Restrictions
- **Pay-per-use model**: $0.005 per Post read, $0.010 per User read
- **Cap**: 2 million Post reads per monthly billing cycle (pay-per-use)
- Enterprise plan required for higher volume
- 24-hour deduplication (same resource only charged once per day)
- No free tier anymore (credits must be purchased)

### Time Coverage
- Full-archive search goes back to **2006** (Twitter's founding)
- ✅ Pre-2022 data accessible via full-archive search endpoint

### Volume
- ~500M+ tweets posted per day historically
- Billions of tweets in the archive

### Text Length
- **Short**: 280 characters max (was 140 pre-2017)
- Average tweet ~30-50 words

### Topic Segmentation
- Filter by keyword, hashtag, user, conversation_id
- Annotations provide entity/topic tagging
- Language filter available

### Scraping Difficulty: 4/5
- Aggressive anti-scraping (rate limiting, IP bans, Cloudflare)
- API is the only viable path; scraping TOS-violating and technically hard

### Terms of Service
- ⚠️ Scraping explicitly prohibited
- API usage governed by Developer Agreement
- Academic research use allowed but must comply with data redistribution rules
- Cannot redistribute tweet text in bulk (only tweet IDs)
- **Cost estimate for study**: 100K tweets = ~$500; 1M tweets = ~$5,000

---

## 2. Reddit (Casual Subreddits)

### Data Access Method
- **Official API**: Free OAuth2 API at oauth.reddit.com
- **Pushshift (Arctic Shift)**: Historical data dumps (2005-2023) — Reddit restricted access in 2023 but academic archives exist on Academic Torrents and the-eye.eu
- **Arctic Shift**: Community successor to Pushshift, provides monthly dumps

### Rate Limits / Restrictions
- Official API: **100 requests/minute** per OAuth client
- Listing endpoints return max 100 items per request, 1000 items total depth
- Reddit's official API is free for non-commercial research
- Rate limit header: `X-Ratelimit-Remaining`

### Time Coverage
- Reddit founded 2005; Pushshift archives go back to **2005**
- ✅ Extensive pre-2022 data available via Pushshift/Arctic Shift dumps
- Official API: only ~1000 most recent posts per listing (limited historical reach)

### Volume
- r/AskReddit: ~45M+ members, thousands of posts/day
- r/Showerthoughts: ~25M+ members
- r/tifu: ~18M+ members
- Pushshift contains **billions** of comments and posts

### Text Length
- **Medium**: Self-posts average 100-500 words; comments 20-150 words
- r/tifu posts tend to be longer (300-1000+ words)
- r/Showerthoughts: very short (1-2 sentences)

### Topic Segmentation
- ✅ Excellent — subreddits ARE the topic segmentation
- Can filter by subreddit, flair, time period
- Pushshift allows SQL-like queries on subreddit, author, score, etc.

### Scraping Difficulty: 2/5
- Official API is well-documented and free
- Pushshift dumps are downloadable (TB-scale but manageable)
- Old Reddit JSON endpoints still work (append .json to any URL)

### Terms of Service
- API terms require attribution; no bulk redistribution
- Pushshift archives: legal gray area after Reddit's 2023 crackdown
- Academic use generally tolerated
- **Recommendation**: Use Pushshift/Arctic Shift dumps for pre-2022; official API for recent data

---

## 3. Amazon Product Reviews

### Data Access Method
- **NO public API** for reviews
- **McAuley Datasets** (UC San Diego): https://cseweb.ucsd.edu/~jmcauley/datasets/amazon_v2/
  - Amazon Review Data (2018): 233M reviews across all categories
  - Newer version exists (2023 update by McAuley group)
- **Ni et al. dataset**: Updated Amazon reviews dataset
- Scraping: Possible but heavily defended

### Rate Limits / Restrictions
- No API = no rate limits for academic datasets
- Scraping: Amazon has aggressive anti-bot (CAPTCHA, IP blocking, browser fingerprinting)
- Product Advertising API exists but does NOT include review text

### Time Coverage
- McAuley dataset: **1996-2018** (reviews from Amazon's founding)
- ✅ Excellent pre-2022 coverage via academic datasets
- Newer scrapes may extend to 2023

### Volume
- McAuley 2018 dataset: **233.1 million reviews**
- Categories: Books, Electronics, Clothing, etc. (29 categories)

### Text Length
- **Medium**: Average 50-150 words
- Range from 1-word ("Great!") to 1000+ word detailed reviews

### Topic Segmentation
- ✅ Excellent — organized by product category (29 categories)
- Also segmentable by star rating, product type, verified purchase status

### Scraping Difficulty: 4/5
- Academic datasets: 1/5 (just download)
- Live scraping: 4/5 (CAPTCHAs, bot detection, dynamic rendering)

### Terms of Service
- Amazon prohibits scraping in ToS
- Academic datasets (McAuley) are widely used in NLP research — de facto acceptable
- **Recommendation**: Use McAuley datasets — they are the gold standard for this

---

## 4. Yelp Reviews (yelp.com)

### Data Access Method
- **Yelp Open Dataset**: https://www.yelp.com/dataset — official academic dataset
  - Released for academic/educational use
  - Requires agreement to dataset terms
- **Yelp Fusion API**: Provides business info but NOT full review text (only snippets)
- Scraping: Moderately defended

### Rate Limits / Restrictions
- Yelp Fusion API: 5,000 requests/day (free tier)
- API does NOT return full review text — only 160-char excerpts
- Dataset: no rate limits, one-time download

### Time Coverage
- Yelp Dataset: reviews from **2004-present** (updated periodically)
- ✅ Pre-2022 data well covered in the dataset

### Volume
- Yelp Open Dataset (latest): ~7 million reviews, 150K+ businesses
- Covers 8 metropolitan areas

### Text Length
- **Medium-Long**: Average 100-200 words
- Range from brief (20 words) to very detailed (500+ words)

### Topic Segmentation
- ✅ Good — categories include restaurants, shopping, nightlife, health, etc.
- Can filter by city, star rating, business category
- 1,300+ business categories

### Scraping Difficulty: 3/5
- Academic dataset: 1/5 (official download)
- Live scraping: 3/5 (moderate anti-bot, but HTML is relatively parseable)

### Terms of Service
- Yelp Dataset: explicitly for academic/educational use (non-commercial)
- Scraping violates Yelp ToS
- **Recommendation**: Use the official Yelp Open Dataset — purpose-built for research

---

## 5. TripAdvisor Reviews (tripadvisor.com)

### Data Access Method
- **No public API** for reviews (Content API is partner-only, requires business relationship)
- **Academic datasets**: Some older scraped datasets exist on Kaggle and in papers
- **Scraping**: Primary method for fresh data; moderately difficult

### Rate Limits / Restrictions
- No public API
- Anti-scraping: Cloudflare protection, rate limiting, CAPTCHA on suspicious activity
- Dynamic rendering (React-based pages)

### Time Coverage
- TripAdvisor founded 2000; reviews go back to early 2000s
- ✅ Pre-2022 data available in existing academic datasets
- Kaggle datasets typically cover 2010-2020

### Volume
- ~1 billion reviews total on platform (as of 2023)
- Covers hotels, restaurants, attractions across 8M+ listings

### Text Length
- **Medium-Long**: Average 100-300 words
- Travel reviews tend to be more detailed than other platforms

### Topic Segmentation
- ✅ Good — Hotels, Restaurants, Attractions, Flights
- Geographic filtering (city, country)
- Star rating (1-5 bubbles)

### Scraping Difficulty: 4/5
- Cloudflare protection
- Dynamic content loading
- Anti-bot measures
- Need rotating proxies and headless browsers

### Terms of Service
- ⚠️ Scraping explicitly prohibited in ToS
- No official research dataset program
- **Recommendation**: Look for existing academic datasets (e.g., Alam et al. TripAdvisor dataset on Kaggle) or negotiate data access for academic purposes

---

## 6. YouTube Comments

### Data Access Method
- **YouTube Data API v3** (free with quota)
- `commentThreads.list` — returns top-level comments for a video
- `comments.list` — returns replies to a comment
- Returns: `textDisplay`, `textOriginal`, `publishedAt`, `likeCount`, `authorDisplayName`
- ✅ **Confirmed: API returns full comment text**

### Rate Limits / Restrictions
- **10,000 quota units/day** (free)
- `commentThreads.list` costs 1 unit per request (returns up to 100 comments)
- Theoretical max: ~1M comments/day with efficient querying
- Can request quota increase for research (often granted)
- Some videos have comments disabled

### Time Coverage
- YouTube launched 2005; comments from day one
- ✅ Pre-2022 data fully accessible — API returns all comments for any video
- Comments include `publishedAt` timestamp

### Volume
- Billions of comments across the platform
- Popular videos: 10K-1M+ comments each
- No practical limit on historical access

### Text Length
- **Short**: Average 10-50 words
- Range from single emoji to paragraph-length responses
- Most comments are 1-3 sentences

### Topic Segmentation
- ✅ Moderate — segment by video category (Music, Gaming, Education, etc.)
- YouTube has 15+ content categories
- Can curate video lists by topic manually

### Scraping Difficulty: 2/5
- Official API is free and well-documented
- Returns full comment text including replies
- Easy to paginate through all comments on a video
- Libraries: google-api-python-client

### Terms of Service
- API usage governed by YouTube API ToS
- Must comply with YouTube API Services Terms (display requirements, data retention limits)
- Can store data for offline analysis but must refresh periodically
- **Recommendation**: Excellent source — free, rich historical data, easy API access

---

## 7. Goodreads Book Reviews (goodreads.com)

### Data Access Method
- **API discontinued** (December 2020 — Goodreads shut down their public API)
- **UCSD Book Graph** (Mengting Wan et al.): Academic dataset with Goodreads data
  - https://mengtingwan.github.io/data/goodreads.html
  - 15M reviews, 2M books
- **Scraping**: Possible but Amazon-owned = well-defended

### Rate Limits / Restrictions
- No API available
- Scraping: Rate limited, occasional CAPTCHAs
- Amazon/Goodreads anti-bot measures

### Time Coverage
- Goodreads founded 2007
- UCSD dataset: reviews from **2007-2017**
- ✅ Pre-2022 data available in academic datasets
- Live scraping can reach more recent data

### Volume
- UCSD Book Graph: ~15 million reviews
- Platform total: 100M+ reviews claimed by Goodreads
- Rich metadata (book genres, ratings, shelves)

### Text Length
- **Long**: Average 150-400 words
- Book reviews tend to be among the longest user-generated content
- Range from brief ratings to multi-paragraph analyses

### Topic Segmentation
- ✅ Excellent — books have genres/shelves (Fiction, Mystery, Romance, Sci-Fi, etc.)
- Can filter by genre, publication year, rating
- User-created "shelves" provide fine-grained categorization

### Scraping Difficulty: 4/5
- API dead, Amazon-owned (strong anti-bot)
- Academic datasets: 1/5 (just download)
- Pages are server-rendered HTML (somewhat parseable)

### Terms of Service
- ⚠️ Scraping violates ToS (Amazon/Goodreads)
- Academic datasets (UCSD Book Graph) widely cited in NLP papers
- **Recommendation**: Use UCSD Book Graph dataset for pre-2022; scraping for recent data is risky

---

## 8. App Store / Google Play Reviews

### Data Access Method
- **Google Play**: No official API for reviews; use `google-play-scraper` (Python/Node.js library)
- **Apple App Store**: No official API for reviews; use `app-store-scraper` library
- **Both**: Well-maintained open-source scraping libraries exist
- Libraries:
  - Python: `google-play-scraper`, `app_store_scraper`
  - Node.js: `google-play-scraper`, `app-store-scraper`

### Rate Limits / Restrictions
- Google Play: Unofficial scraping — moderate rate limiting
- App Store: RSS feeds provide some reviews (limited to most recent)
- Libraries handle pagination and rate limiting
- Risk of IP blocking with high-volume requests

### Time Coverage
- App Store: 2008+; Google Play: 2012+
- ✅ Historical reviews accessible (sorted by date)
- Can retrieve reviews going back years for popular apps
- Libraries typically return up to ~5000-10000 most relevant reviews per app

### Volume
- Major apps have 1M+ reviews each
- Millions of apps × thousands of reviews = massive corpus
- Google Play tends to have more reviews than App Store

### Text Length
- **Short**: Average 20-80 words
- Many are 1-2 sentences
- Character limits: Google Play ~500 chars, App Store ~unlimited but usually brief

### Topic Segmentation
- ✅ Excellent — apps organized by category (Games, Productivity, Social, etc.)
- ~30+ categories on each store
- Can filter by star rating, version, country

### Scraping Difficulty: 3/5
- Well-maintained libraries make it relatively easy
- No official API but libraries are stable
- Rate limiting requires patience for large-scale collection
- Google occasionally changes page structure

### Terms of Service
- ⚠️ Both Apple and Google prohibit scraping in ToS
- Academic use is a gray area but common in research
- **Recommendation**: Use `google-play-scraper` / `app_store_scraper` libraries — widely used in research papers

---

## 9. IMDb Movie Reviews (imdb.com)

### Data Access Method
- **Official Datasets** (https://datasets.imdbws.com/):
  - `title.basics.tsv.gz` — titles, genres, year
  - `title.ratings.tsv.gz` — average rating, vote count
  - `name.basics.tsv.gz` — people
  - ⚠️ **NO review text in official datasets** — only metadata and ratings
- **IMDb Reviews**: Must be scraped or use existing academic datasets
- **Stanford Large Movie Review Dataset**: 50K labeled reviews (positive/negative)
  - https://ai.stanford.edu/~amaas/data/sentiment/ (from 2011)
- **Scraping**: IMDb HTML is relatively parseable

### Rate Limits / Restrictions
- Official datasets: No limits, freely downloadable
- Scraping: Moderate anti-bot (Amazon-owned since 1998)
- No official review API

### Time Coverage
- IMDb founded 1990; reviews from late 1990s onward
- ✅ Stanford dataset: reviews from 2011 and earlier
- Official datasets updated daily (but no review text)
- Scraping can access reviews from any era

### Volume
- Official datasets: ~10M titles, ratings for millions
- User reviews: Millions across all movies
- Stanford dataset: 50,000 reviews (balanced positive/negative)
- Popular movies: 1,000-10,000+ user reviews each

### Text Length
- **Long**: Average 200-500 words
- IMDb reviews tend to be thoughtful, paragraph-length
- Range from brief comments to multi-page analyses

### Topic Segmentation
- ✅ Good — movies have genres (Action, Comedy, Drama, Horror, etc.)
- Can segment by genre, year, rating score
- Official dataset includes genre metadata

### Scraping Difficulty: 3/5
- Academic datasets (Stanford): 1/5
- Official datasets (no reviews): 1/5
- Scraping reviews: 3/5 (Amazon-owned, but HTML is structured; no heavy JS rendering for reviews)

### Terms of Service
- Official datasets: **Non-commercial use only** (explicitly stated)
- Scraping: Prohibited by Amazon/IMDb ToS
- Stanford dataset: Academic use, widely cited
- **Recommendation**: Stanford dataset for sentiment-labeled data; scrape for larger/recent corpus (moderate risk)

---

## 10. Trustpilot Reviews (trustpilot.com)

### Data Access Method
- **No public API** (API endpoints exist but are private/partner-only)
- **Scraping**: Primary method
- `robots.txt` analysis: Disallows `/api/*`; blocks all unrecognized bots (`Disallow: /` for `*`)
- Business review pages are accessible to major search engines (Google, Bing)
- HTML structure is relatively clean

### Rate Limits / Restrictions
- No public API
- Anti-bot: Cloudflare protection, aggressive bot blocking
- `robots.txt` blocks most AI crawlers (GPTBot, ClaudeBot, CCBot all disallowed)
- Default rule for unknown agents: `Disallow: /`
- Requires realistic headers and rotation for scraping

### Time Coverage
- Trustpilot founded 2007
- ✅ Reviews dating back to ~2007 available on business pages
- Reviews display with full timestamps

### Volume
- ~300M+ reviews on platform (as of 2024)
- 1M+ businesses reviewed
- Popular companies: 10K-500K+ reviews each

### Text Length
- **Medium**: Average 50-150 words
- Structured format (title + body)
- Range from single-sentence to detailed paragraphs

### Topic Segmentation
- ✅ Excellent — businesses organized by category
- Categories: Banks, Insurance, Electronics, Travel, etc.
- Can filter by star rating, date, verified/unverified
- ~20+ top-level business categories

### Scraping Difficulty: 4/5
- Cloudflare protection
- Aggressive bot detection
- `robots.txt` blocks most crawlers
- Need residential proxies + realistic browser fingerprints
- Paginated content with anti-scraping measures

### Terms of Service
- ⚠️ Scraping prohibited; robots.txt explicitly blocks bots
- No academic dataset program
- GDPR considerations (EU company, reviewer data)
- **Recommendation**: High legal risk. Consider reaching out to Trustpilot for academic data access. Some Kaggle datasets exist from earlier scrapes.

---

## Recommended Strategy for the Study

### Tier 1: Easiest / Best Data Access (Start Here)
| Platform | Method | Cost |
|----------|--------|------|
| **YouTube Comments** | YouTube Data API v3 (free) | Free |
| **Reddit** | Pushshift/Arctic Shift dumps + API | Free |
| **Amazon Reviews** | McAuley dataset download | Free |
| **Yelp** | Yelp Open Dataset | Free |
| **IMDb** | Stanford dataset + scraping | Free |

### Tier 2: Moderate Effort
| Platform | Method | Cost |
|----------|--------|------|
| **App Store/Google Play** | Python scraping libraries | Free |
| **X / Twitter** | Paid API | $500-5000 |

### Tier 3: Hardest / Highest Risk
| Platform | Method | Cost |
|----------|--------|------|
| **Goodreads** | UCSD dataset (old) or risky scraping | Free (dataset) |
| **TripAdvisor** | Existing Kaggle datasets or heavy scraping | $50-200 (proxies) |
| **Trustpilot** | Scraping with proxies (legal risk) | $50-200 (proxies) |

### Key Considerations for Pre-2022 vs Post-2022 Comparison
- **Reddit**: Best option — Pushshift has complete archives pre-2022, API for post-2022
- **Amazon**: McAuley goes to 2018; need newer dataset or scraping for post-2022
- **YouTube**: API gives equal access to all time periods
- **Twitter/X**: Full-archive search covers all periods but expensive at scale
- **Yelp**: Dataset covers pre-2022 well; check latest version release date

### Total Budget Estimate (for ~100K samples per platform)
| Platform | Cost |
|----------|------|
| YouTube | Free |
| Reddit | Free |
| Amazon | Free |
| Yelp | Free |
| IMDb | Free |
| App stores | Free |
| Twitter/X | ~$500-2,000 |
| Goodreads | Free |
| TripAdvisor | $50-200 |
| Trustpilot | $50-200 |
| **Total** | **~$600-2,400** |
