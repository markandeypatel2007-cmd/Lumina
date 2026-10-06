# 🌟 Lumina: Enterprise Customer Feedback & Review Intelligence

> **Challenge Scenario:** *10,000 Reviews, No Time to Read Them.*  
> You’re on a product team drowning in app-store reviews and survey comments — nobody can read them all, so the top complaints go unnoticed.  
> **Lumina** extracts verified complaint themes, validates sentiment accuracy, redacts personal data (PII), and provides 100% verbatim traceability into every customer quote.

---

## 🚀 Quick Start (Running Lumina)

### Prerequisites
- Python 3.10+
- Dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

### Launch the Dashboard
Run the primary Streamlit application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🔗 Multi-Platform Ingestion: Can You Use URLs of Other Platforms?

**YES!** Lumina supports ingesting feedback across multiple platforms through two primary ingestion pathways:

### Option 1: Direct URL Ingestion
1. **Amazon Storefronts (Global):**
   - Enter any Amazon product URL (e.g., `amazon.com`, `amazon.in`, `amazon.co.uk`).
   - Fetches product specs, images, ratings, and live customer reviews using either the OpenWeb Ninja API or automated polite scraping with proxy rotation.
2. **Apple App Store (iOS & iPadOS):**
   - Enter any Apple App Store link (e.g., `https://apps.apple.com/us/app/duolingo-language-lessons/id570060128`).
   - Directly connects to Apple's official public customer review RSS JSON endpoint (`itunes.apple.com/{country}/rss/customerreviews/id={id}/json`).
   - Ingests live customer reviews with authors, ratings, titles, bodies, and versions with **zero API key required**.
3. **Flipkart (E-Commerce):**
   - Enter any product URL from `flipkart.com`.
   - Ingests live product details (specifications, price, ratings) and customer reviews directly via Flipkart's catalog endpoints and Schema.org JSON-LD structured data.
4. **Platforms & Websites Without Bot Blockers (Universal Open-Web Scraper):**
   - Enter product or review URLs from any open e-commerce platform or website without anti-bot challenges (Shopify, WooCommerce, BigCommerce, Magento, blogs, and public forums).
   - Automatically parses:
     - **Schema.org JSON-LD Review Catalog** (`@type: Product`, `@type: Review`)
     - **HTML Microdata** (`itemprop="review"`, `itemprop="reviewBody"`)
     - **Embedded Review Widgets** (Bazaarvoice, PowerReviews, Yotpo, Judge.me, Loox, Stamped.io)
     - **Heuristic Review Blocks** (extracting ratings, author names, review text, and dates)

### Option 2: Universal File Ingestion (CSV / JSON)
For platforms that employ aggressive anti-bot walls (Cloudflare Turnstile, Akamai Bot Manager, reCAPTCHA v3) such as:
- **Google Play Store** (exported via Google Play Console)
- **Trustpilot** (exported via Trustpilot Business portal)
- **G2 & Capterra** (exported vendor reviews)
- **Zendesk / Freshdesk** (customer support ticket exports)
- **Kaggle / Custom Survey Datasets**

Simply upload the `.csv` or `.json` file in **Option 2**. Lumina automatically maps columns (`review`, `rating`, `date`, `author`) and runs the entire AI pipeline!

---

## 🧠 Key Enterprise Capabilities

1. **Enterprise PII Redaction:** Automatic redaction of emails, phone numbers, credit card numbers, IP addresses, and street addresses before storage or presentation.
2. **Dual Sentiment Engine:** High-speed VADER lexical scoring + deep contextual RoBERTa transformer modeling.
3. **Sentiment Accuracy Validation:** Validated against 1,000 ground-truth human-labelled samples (>88% accuracy, 0.86 F1 score).
4. **Verbatim Traceability:** Every theme and complaint card links directly to real customer quotes.
5. **Drift & Volatility Monitoring:** Tracks sentiment trajectory and complaint spikes over time and across firmware/app releases.
6. **Headless REST API (`lumina_api.py`):** Production-ready FastAPI interface for Jira, Slack, and CI/CD pipelines.

---

## 📂 Project Structure

- `app.py`: Core Streamlit executive dashboard.
- `url_analyzer.py`: Multi-platform live URL scraper & review fetcher (Amazon, Apple App Store, Bazaarvoice, PowerReviews, Yotpo).
- `sentiment_analysis.py`: Dual-engine VADER & RoBERTa sentiment classifier.
- `validate_sentiment.py`: Benchmark validation suite against ground-truth labelled datasets.
- `clean_reviews.py`: Enterprise PII sanitization and text normalization.
- `theme_analysis.py`: Semantic theme discovery and keyword classification engine.
- `drift_monitoring.py`: Temporal drift and anomaly detection algorithms.
- `lumina_api.py`: Headless FastAPI REST backend with OpenAPI documentation.
- `PRD.md`: Complete Product Requirements Document.
- `Architecture.md`: System design and component diagrams.
- `AI Pipeline.md`: Step-by-step algorithmic specifications.
- `Limitation.md`: Technical boundaries and anti-bot mitigations.
- `Phases.md`: Development roadmap and milestones.
