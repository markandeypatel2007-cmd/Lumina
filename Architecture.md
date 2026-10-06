# Lumina: System Architecture & Technical Specifications

## 1. System Overview
Lumina is architected as a modular, decoupled analytical pipeline designed for high-throughput batch analysis as well as real-time single-product deep dives.

```
+-----------------------------------------------------------------------------------------+
|                                    INGESTION LAYER                                      |
|                                                                                         |
|   +-----------------------+   +-----------------------+   +-------------------------+   |
|   | Amazon Products (URL) |   | Apple App Store (URL) |   | DTC / Shopify Store(URL)|   |
|   +-----------------------+   +-----------------------+   +-------------------------+   |
|               |                           |                            |                |
|   +-----------------------+               |               +-------------------------+   |
|   | OpenWeb Ninja / Scrape|               |               | BV / Yotpo / PowerRevs  |   |
|   +-----------------------+               |               +-------------------------+   |
|               \                           |                            /                |
|                +--------------------------+---------------------------+                 |
|                                           |                                             |
|                   +-----------------------------------------------+                     |
|                   | Option 2: Universal CSV / JSON Review Exports  |                     |
|                   +-----------------------------------------------+                     |
+-----------------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------------+
|                                 PROCESSING & SAFETY PIPELINE                            |
|                                                                                         |
|   [1. Text Cleaning & Normalization] ---> [2. Enterprise PII Redaction Layer (Regex/NER)]|
|                                           Scrubs emails, phone #, IP, cards, addresses  |
|                                                                                         |
|   [3. Reviewer Deduplication]       ---> [4. Parquet / In-Memory Columnar Vector Store] |
|       Eliminates duplicate submissions                                                  |
+-----------------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------------+
|                                  AI & ANALYTICS ENGINES                                 |
|                                                                                         |
|   [Dual Sentiment Engine]          [Theme Classification]       [Drift & Volatility]    |
|   - VADER (High-speed lexical)    - Keyword Regex Anchors      - Weekly Aggregations    |
|   - RoBERTa (Deep contextual)     - TF-IDF + Logistic Regr     - Anomaly Spikes         |
|   - Ground Truth Benchmark Val    - Zero-Shot Embeddings       - Rolling Shift Detection|
+-----------------------------------------------------------------------------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------------+
|                               PRESENTATION & INTEGRATION LAYER                          |
|                                                                                         |
|   +------------------------------------+   +----------------------------------------+   |
|   | Streamlit Executive UI (`app.py`)  |   | FastAPI Headless REST API (`lumina_api`)|  |
|   | - 6 Interactive Intelligence Tabs  |   | - OpenAPI / Swagger Docs               |   |
|   | - Verbatim Traceability Explorer   |   | - Webhook / Jira / Slack integrations  |   |
|   +------------------------------------+   +----------------------------------------+   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Ingestion Subsystem Details

### 2.1 Multi-Platform URL Extraction Engine (`url_analyzer.py`)
1. **Amazon Storefronts (`amazon.com`, `amazon.in`, `amazon.co.uk`, etc.):**
   - Automatically parses canonical ASIN (`/dp/<ASIN>`).
   - Routes to OpenWeb Ninja Amazon API if configured via `OPENWEBNINJA_API_KEY`.
   - Falls back to automated polite scraping with browser user-agent rotation, cookie warmup, and exponential backoff jitter.
2. **Apple App Store (`apps.apple.com/.../id<APP_ID>`):**
   - Parses country code and Apple item numeric ID.
   - Queries `https://itunes.apple.com/lookup?id={app_id}` for icon, seller, rating, and app metadata.
   - Fetches live customer reviews directly from Apple's public RSS JSON feed (`https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json`).
   - Requires zero API key or credentials; 100% SLA uptime.
3. **Flipkart (`flipkart.com`):**
   - Ingests verified product specifications, pricing, ratings, and live customer reviews directly from `flipkart.com`.
   - Parses Schema.org JSON-LD structured review catalogs and HTML review elements with browser session cookie warmup.
4. **Universal Open-Web Scraper (Platforms without Bot Walls):**
   - Ingests live customer feedback from open e-commerce stores (Shopify, WooCommerce, BigCommerce, Magento, blogs, and public forums).
   - Multi-layer extraction:
     - **Schema.org JSON-LD** (`@type: Product`, `@type: Review`)
     - **Microdata & RDFa** (`itemprop="review"`)
     - **Review Widget APIs** (Bazaarvoice, PowerReviews, Yotpo, Judge.me, Loox, Stamped)
     - **Heuristic Review Blocks** (ratings, author, text, date)

### 2.2 Universal CSV / JSON Uploader (`app.py`)
- Accepts arbitrary customer feedback spreadsheets.
- Intelligent column auto-mapping: recognizes `review`, `text`, `content`, `body`, `comment`, `rating`, `stars`, `score`, `date`, `created_at`, `timestamp`.
- Supports exports from Google Play Console, Trustpilot, G2, Zendesk, SurveyMonkey, and Kaggle.
