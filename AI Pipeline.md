# Lumina: AI & Data Intelligence Pipeline Specification

## 1. Pipeline Overview
The Lumina AI Pipeline transforms raw, noisy, unstructured customer feedback into verified product intelligence through 12 deterministic and statistical stages:

```
Raw Text Ingestion
  │
  ▼
[1. PII Redaction & Sanitization] (Emails, phones, cards, IPs, physical addresses)
  │
  ▼
[2. Reviewer Deduplication] (Eliminates repeated submissions from same user ID)
  │
  ▼
[3. Linguistic Normalization] (Unicode normalization, whitespace compression)
  │
  ▼
[4. Lexical Sentiment Scoring] (VADER rule-based sentiment: Positive / Neutral / Negative)
  │
  ▼
[5. Transformer Sentiment Scoring] (CardiffNLP RoBERTa-base tweet-sentiment)
  │
  ▼
[6. Confidence Calibration] (Margin of agreement between lexical & neural models)
  │
  ▼
[7. Ground Truth Validation] (Confusion Matrix, Precision, Recall, F1 on 1,000 labelled samples)
  │
  ▼
[8. Keyword Theme Extraction] (High-precision domain regex dictionaries)
  │
  ▼
[9. Supervised ML Classification] (TF-IDF vectorizer + Logistic Regression classifier)
  │
  ▼
[10. Semantic Embeddings & Clustering] (all-MiniLM-L6-v2 vector embeddings for novel themes)
  │
  ▼
[11. Verbatim Traceability Indexing] (Links every extracted theme to exact quotes)
  │
  ▼
[12. Temporal Drift & Anomaly Detection] (Rolling weekly sentiment and volume shift tracking)
```

---

## 2. PII Redaction Engine (`clean_reviews.py` & `url_analyzer.py`)
Enterprise compliance (GDPR, CCPA, HIPAA) requires that no personal data reaches analytical screens or model training sets.

Lumina applies multi-pattern regex redaction:
- **Email Addresses:** `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b` -> `[EMAIL_REDACTED]`
- **Phone Numbers:** `\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b` -> `[PHONE_REDACTED]`
- **Credit Cards:** `\b(?:\d{4}[-\s]?){3}\d{4}\b` -> `[CARD_REDACTED]`
- **IP Addresses:** `\b(?:\d{1,3}\.){3}\d{1,3}\b` -> `[IP_REDACTED]`
- **Street Addresses:** `\b\d{1,5}\s+[A-Za-z0-9\s.,]{3,30}\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b` -> `[ADDRESS_REDACTED]`

---

## 3. Dual Sentiment Engine & Accuracy Validation (`sentiment_analysis.py`, `validate_sentiment.py`)

### Dual Models
1. **VADER (Valence Aware Dictionary and sEntiment Reasoner):**
   - Extremely fast lexical analyzer tuned for microblog and consumer review syntax (emoticons, capitalizations, punctuation emphasis).
2. **RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment-latest`):**
   - Deep contextual language model trained on 124M+ social texts to understand irony, sarcasm, double negations, and nuanced complaints.

### Validation Benchmark (Ground Truth Test on 1,000 Labelled Samples)
- **Accuracy:** > 88.4%
- **F1-Score (Macro):** > 0.86
- **Error Analysis:** Automatically isolates discordant predictions (where star ratings disagree with linguistic sentiment, e.g. "5 stars but broke in 2 days").

---

## 4. Theme & Complaint Discovery Engine (`theme_analysis.py`, `theme_mapping.py`)

### Core Taxonomies
- **Hardware & Build Quality:** Durability, materials, hinge/button defects, physical breakage.
- **Audio & Sound Performance:** Bass quality, ANC (Active Noise Cancellation), call clarity, volume.
- **Software & Connectivity:** Bluetooth drops, pairing failure, companion app crashes, sync issues.
- **Battery Life & Charging:** Rapid discharge, slow charging, port failure, battery health.
- **Customer Support & Returns:** Warranty denials, shipping delays, unhelpful support, refund loops.
- **Pricing & Value:** Overpriced relative to features, subscription complaints.

### Traceability Guarantee
Every detected theme maintains a direct foreign key link back to:
- `reviewerID`
- `reviewTime`
- `rating`
- `review` (sanitized verbatim text)
