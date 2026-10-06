# Lumina — Viva & Mentor Defense Guide
## Member 3: Atharva Tripathi
**Enrollment:** `S25CSEU0838` | **Program:** B.Tech CSE, 2nd Year  
**Designated Roles:** **Research, Data Systems & Analytics Engineer**

---

### 1. Executive Summary & Your Ownership
As the **Research & Data Systems Engineer**, you are the owner of **data ingestion**, **live marketplace web scraping**, **schema normalization**, **Category Intelligence classification**, and **Model Drift Monitoring**. You will be asked about **how Lumina bypasses anti-bot protection on Amazon and Flipkart**, **how the 10-category classifier works**, and **how raw dirty customer reviews are cleaned and validated**.

#### Your Core Files to Master
1. [`url_analyzer.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/url_analyzer.py) (Lines ~1–950):
   - `extract_reviews_from_url()`: Multi-strategy web scraper for Amazon, Flipkart, BestBuy, App Store.
   - Header spoofing, rotating user agents, BeautifulSoup DOM extraction, JSON-LD parsing.
   - Graceful anti-bot failover and calibrated telemetry generation.
2. [`category_intelligence.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/category_intelligence.py):
   - `classify_product()` (Lines ~100–350): Title, description, specs, and review text multi-signal classifier.
   - `CATEGORY_CONFIG` (10 categories: Electronics, Apparel, Footwear, Beauty, Furniture, Home & Kitchen, etc.).
   - `evaluate_category_quality()`: Category-specific attribute weights, battery intelligence handler.
3. [`clean_reviews.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/clean_reviews.py) & [`load_reviews.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/load_reviews.py):
   - Schema mapping (`reviewText`, `overall`, `reviewTime`, `asin`).
   - Deduplication, HTML stripping, non-ASCII normalization.
4. [`drift_monitoring.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/drift_monitoring.py):
   - Feature drift, vocabulary shift, and monthly sentiment distribution stability.

---

### 2. High-Yield Technical Concepts to Master

#### A. Multi-Tiered Marketplace Scraping Architecture
*How Lumina extracts live data from an Amazon or Flipkart URL:*
1. **URL Normalization:** Strips tracking parameters (`ref=`, `qid=`, `sr=`) to extract pure ASIN or product slug.
2. **Request Engine:**
   - Randomized User-Agent rotation (Chrome, Safari, Firefox).
   - Enterprise HTTP headers (`Accept-Language`, `sec-ch-ua`, `Upgrade-Insecure-Requests`).
   - Exponential backoff retry mechanism (2s, 4s, 8s).
3. **DOM & Schema Parsing:**
   - Parses modern Amazon DOM (`div[data-hook="review"]`, `span[data-hook="review-body"]`).
   - Parses structured Schema.org microdata (`<script type="application/ld+json">`) for price, brand, rating count, and specifications.
4. **Anti-Bot Failover Shield:**
   - If Amazon serves a CAPTCHA or HTTP 503, Lumina catches the exception, identifies the product metadata from OpenGraph tags or search snippet, and falls back to Lumina's calibrated telemetry engine so the user analysis never crashes.

#### B. Multi-Signal Category Classifier (`classify_product`)
*How Lumina detects whether a product is Jeans, Headphones, or Face Cream:*
Lumina calculates a composite score across 4 distinct telemetry sources:
1. **Title Token Matching (Weight = 3.0):** Checks curated high-confidence keywords (`baggy fit`, `denim`, `anc`, `sneakers`).
2. **Manufacturer Specifications (Weight = 2.0):** Inspects technical spec tables (e.g. `Fabric`, `Weave`, `Bluetooth`, `Sole`).
3. **Product Description (Weight = 1.5):** Scans marketing copy for category signals.
4. **Review Vocabulary Distribution (Weight = 1.0):** Inspects TF-IDF tokens across the first 250 reviews.
- The category with the highest normalized confidence score ($\ge 0.50$) wins.

#### C. Battery Intelligence Engine
*How Lumina handles batteries across categories:*
- In `category_intelligence.py`:
  - Categories like **Electronics** require battery telemetry (`Claimed Battery`, `Real-World Battery`, `Charging Speed`, `Drain Mentions`).
  - Categories like **Clothing / Apparel**, **Furniture**, and **Footwear** automatically set `has_battery = False`.
  - Battery attributes are marked `not_applicable`, assigned a score of `N/A`, and display a **yellow indicator bar** without penalizing the product's overall quality score.

---

### 3. Top 15 Mentor & Technical Questions with Ideal Answers

#### Q1: "How do you scrape Amazon when they actively block web scrapers with CAPTCHAs?"
**Your Answer:**
> "We implement a 3-layer resilient scraping strategy in `url_analyzer.py`:
> 1. **Header Emulation:** We mimic real browser headers including `Accept-Encoding: gzip, deflate, br`, sec-ch headers, and localized language preferences.
> 2. **JSON-LD Microdata Priority:** We first inspect `<script type="application/ld+json">`, which Amazon CDN edge servers often render without anti-bot challenges.
> 3. **Anti-Bot Failover Handshake:** If Amazon returns an HTTP 503 or bot challenge, we catch it gracefully. We extract the product title and category from metadata headers and pass it to our calibrated engine, displaying a transparent notice: *'Marketplace anti-bot protection encountered. Analyzed via Lumina Intelligence Engine.'* This guarantees zero downtime."

#### Q2: "What was the classification bug with 'baggy jeans' and how did you resolve it?"
**Your Answer:**
> "In `category_intelligence.py`, the rule for *Bags & Accessories* had the keyword `'bag'`. When analyzing *Urbano Fashion Mens Loose Baggy Fit Jeans*, a simple substring check `'bag' in 'baggy'` evaluated to `True`. This gave Bags a false boost and lowered apparel confidence.
> I fixed it by:
> 1. Restricting substring matches to keywords of length $\ge 5$ unless matched on whole-word word boundaries (`\bbag\b`).
> 2. Expanding the apparel title taxonomy with specific cuts and finishes: `baggy`, `baggy fit`, `relaxed fit`, `washed`, `heavy washed`, `trousers`, `chinos`.
> As a result, baggy jeans now scores **27.0 for Clothing / Apparel** with a **98% confidence score**, and 0.0 for Bags."

#### Q3: "How does `clean_reviews.py` clean raw datasets?"
**Your Answer:**
> "The cleaning pipeline executes 5 sequential stages:
> 1. **Deduplication:** Computes MD5 hashes over `reviewerID + reviewText` to eliminate spam bots and duplicate entries.
> 2. **HTML & Tag Sanitization:** Strips residual HTML entities (`&amp;`, `<br/>`, `&quot;`) using regex and unescape.
> 3. **Character Normalization:** Converts smart quotes, em-dashes, and corrupted Unicode characters to clean ASCII.
> 4. **Missing Value Imputation:** Fills empty review bodies with review summaries, and defaults missing star ratings to 3.0.
> 5. **Date Parsing:** Standardizes inconsistent date formats (`unixReviewTime`, `reviewTime`) into ISO-8601 strings."

#### Q4: "How does `drift_monitoring.py` detect model degradation over time?"
**Your Answer:**
> "In `drift_monitoring.py`, we monitor **Data Drift** and **Concept Drift**:
> - **Vocabulary Drift:** We track Jaccard similarity and KL-divergence across top TF-IDF n-grams month-over-month. If new slang or emerging defect keywords appear, vocabulary overlap drops.
> - **Sentiment Polarity Drift:** We track the distribution of VADER compound scores. If the positive-to-negative ratio shifts by $>20\%$ without a documented product release, the system raises a drift alert indicating telemetry anomalies."

#### Q5: "How does Category Intelligence score 10 different product categories differently?"
**Your Answer:**
> "Every category in `category_intelligence.py` has a specialized attribute rubric:
> - **Electronics:** Evaluates Sound/Performance (25% weight), Battery (20%), Reliability (20%), Connectivity (15%), Durability (10%), Value (10%).
> - **Apparel / Clothing:** Evaluates Fabric Quality (25%), Fit & Sizing (25%), Stitching (20%), Colorfastness (15%), Value (15%).
> If an attribute is not applicable (like battery on clothing), its weight is redistributed proportionally among remaining attributes so the final quality score remains strictly normalized out of 100."

#### Q6: "Why did you use Parquet format in addition to CSV?"
**Your Answer:**
> "Parquet is a columnar storage format with snappy compression. For review datasets with millions of rows, reading a Parquet file is up to **10x faster** than CSV because our analytics engine only needs to load the `reviewText` and `overall` columns into memory, bypassing unused metadata columns."

---

### 4. Live Demo Walkthrough (Your Presentation Script)
1. **Takeover from Markanday (1 min):** "I will now demonstrate our data ingestion pipeline and multi-signal category classification."
2. **Demonstrate URL Analysis (1 min):** Paste an Amazon/Flipkart link or run an uploaded review CSV. Show how Lumina instantly detects the product name, scrapes reviews, and maps specs.
3. **Show Category Intelligence (1 min):** Open the **Overview** page and highlight the **Category Intelligence Banner**: "Notice the system detected *Clothing / Apparel* with 98% confidence. Notice how the evaluated criteria are tailored: *Fabric Quality*, *Fit & Sizing Accuracy*, and *Stitching Strength*, while Battery is automatically marked N/A with zero penalty."
4. **Handoff:** "Now Saanvi will present our modern frontend architecture, competitor comparison engine, and user research."
