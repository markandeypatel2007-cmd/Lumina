# Lumina: Product Requirements Document (PRD)

## 1. Executive Summary & Vision
**Lumina** is an enterprise-grade Customer Feedback & Review Intelligence platform designed to bridge the gap between massive, unstructured customer feedback and strategic product decision-making.

In modern organizations, product and engineering teams drown in tens of thousands of app store reviews, e-commerce feedback, and survey responses. Critical customer pain points, regression bugs, and churn drivers go unnoticed because teams cannot manually read and categorize feedback at scale.

Lumina ingests high-volume customer feedback from multiple platforms (Amazon, Apple App Store, Shopify/Direct E-Commerce, and arbitrary CSV/JSON exports), redacts Personal Identifiable Information (PII), extracts core complaint themes, tracks sentiment drift over time, validates classification confidence, and renders an executive intelligence dashboard with 100% verbatim traceability.

---

## 2. Core Personas & Problem Scenarios

### Personas
1. **VP of Product / Head of Product:** Needs executive-level visibility into net customer sentiment, top emerging complaints, and competitive quality metrics without reading raw feedback.
2. **Product Managers (PMs):** Need verifiable complaint themes with direct traceability to real customer quotes to justify roadmap priorities and sprint tickets.
3. **Engineering Leads & QA:** Need rapid identification of post-release regressions (e.g., battery drain, firmware crashes, Bluetooth dropouts) with semantic evidence.
4. **Customer Experience / Support Leads:** Need triage automation, SLA impact tracking, and draft responses to severe negative sentiment.

### Challenge Scenario (Round 1 / Student Edition Challenge)
> *"10,000 Reviews, No Time to Read Them: You’re on a product team drowning in app-store reviews and survey comments — nobody can read them all, so the top complaints go unnoticed."*

---

## 3. Supported Ingestion Channels

| Source | Mode | Ingestion Mechanism | Notes |
|---|---|---|---|
| **Amazon** | Direct URL | OpenWeb Ninja API + Polite Scraper Fallback | Supports all international stores (`.com`, `.in`, `.co.uk`, etc.) |
| **Apple App Store** | Direct URL | Apple iTunes Public RSS API (`rss/customerreviews`) | Ingests real iOS/iPadOS customer reviews without API key |
| **Flipkart** | Direct URL | Live HTML scraper & Schema.org JSON-LD extractor | Live customer reviews & specifications from `flipkart.com` |
| **Shopify / DTC Stores** | Direct URL | Bazaarvoice, PowerReviews, Yotpo, Judge.me, Loox | Ingests direct review feeds and widget APIs |
| **Universal Open Web** | Direct URL | Schema.org JSON-LD, Microdata & Open Review Scraper | Live scraping for any platform without anti-bot challenges |
| **Google Play Store** | CSV / JSON | Option 2 File Uploader | Exported via Google Play Console |
| **Trustpilot / G2** | CSV / JSON | Option 2 File Uploader | Bypasses Cloudflare anti-bot botwalls gracefully |
| **Enterprise Data Lakes** | Parquet / CSV | Scalable Parquet backend (`load_reviews.py`) | Handles 6.8M+ review corpus with sub-second queries |

---

## 4. Key Functional Requirements

### 4.1 Ingestion & PII Redaction
- Ingest batches from 10 to 6,800,000+ reviews.
- Automatically scrub emails, phone numbers, credit cards, IP addresses, and physical addresses before storing or displaying (`redact_pii`).

### 4.2 Theme & Complaint Discovery
- Rule-based keyword anchoring + zero-shot semantic matching (`sentence-transformers` / TF-IDF + Logistic Regression).
- Hierarchy of customer experience categories: Hardware/Build, Audio Quality, Software & Connectivity, Battery Life, Customer Service, Pricing/Value.

### 4.3 Verbatim Traceability
- Every discovered theme must link directly to real review verbatims with reviewer ID, star rating, submission date, and raw quote.

### 4.4 Sentiment & Accuracy Validation
- Dual-engine sentiment analysis (VADER Lexicon + RoBERTa Transformer).
- Statistical accuracy benchmarking against ground-truth human labels (Confusion Matrix, Precision, Recall, F1-Score).

### 4.5 Drift & Regression Monitoring
- Temporal tracking of theme share across product firmware/app releases.
- Automated anomaly detection flagging rising complaints before app store ratings degrade.

### 4.6 Executive Dashboard & API
- Interactive Streamlit Dashboard (`app.py`) with 6 focused analytical tabs.
- Production FastAPI endpoint (`lumina_api.py`) for external integration with Jira, Slack, and Linear.
