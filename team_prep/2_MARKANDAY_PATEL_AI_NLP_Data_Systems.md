# Lumina — Viva & Mentor Defense Guide
## Member 2: Markanday Patel
**Enrollment:** `S25CSEU0822` | **Program:** B.Tech CSE, 2nd Year  
**Designated Roles:** **AI & NLP Engineer, Data Systems & Analytics Engineer**

---

### 1. Executive Summary & Your Ownership
As the **AI & NLP Engineer and Data Systems Engineer**, you are the owner of the **core quantitative intelligence engine** of Lumina. Mentors and technical evaluators will interrogate you on the **mathematical models**, **clause-level ABSA parsing**, **debiasing equations**, **Closed-Loop Impact Verification calculations**, and the **Flask REST API data layer**.

#### Your Core Files to Master
1. [`analyze_reviews.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/analyze_reviews.py):
   - `analyze_frame()` (Lines ~5450–5750): The master NLP analysis pipeline.
   - `compute_corpus_absa()` (Lines ~250–450): Clause splitting, aspect mapping, polarity scoring.
   - `verify_closed_loop_impact()` (Lines ~5100–5350): Pre vs post-fix cohort evaluation, delta calculations, outcome labeling.
   - `get_recommendation_learning_loop()` & `record_recommendation_outcome()`: Historical intervention ledger calibration.
   - `compute_actual_vs_predicted_lift()`: Model accuracy scoring formula.
2. [`lumina_api.py`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/lumina_api.py):
   - `build_dynamic_tickets()` (Lines ~90–515): Category-specific tickets, 5-Whys, spec patches.
   - `/api/impact-verification` & `/api/analyze-csv`: Data serialization and JSON cleaning (`clean()`).
3. [`learning_loop_ledger.json`](file:///c:/Users/arvind%20kumar%20patel/OneDrive/Desktop/lumina/learning_loop_ledger.json): Persistent historical calibration store.

---

### 2. High-Yield Technical Concepts & Mathematical Formulas

#### A. Clause-Level Aspect-Based Sentiment Analysis (ABSA)
*Why sentence-level sentiment fails:*
- A user writes: *"Sound quality is breathtaking, but the battery drains in 2 hours."*
- A naive sentiment classifier sees 1 positive word and 1 negative word, outputting **Neutral (0.0)**.
- **Lumina's Clause-Level Solution:**
  1. We segment complex sentences using contrastive coordinate conjunctions (`but`, `however`, `although`, `yet`, `except`, `whereas`).
  2. Sub-clause A (*"Sound quality is breathtaking"*) $\rightarrow$ mapped to Aspect: `Audio Quality`, Polarity: `+0.82 (Positive)`.
  3. Sub-clause B (*"the battery drains in 2 hours"*) $\rightarrow$ mapped to Aspect: `Battery Life`, Polarity: `-0.65 (Negative)`.
  4. Each clause contributes independently to its respective attribute matrix.

#### B. The "Rating Truth" Debiasing Equation
*Why Amazon/Flipkart star ratings are biased:*
- E-commerce review distributions are notoriously J-shaped (skewed positive by unverified gift-buyers and promotional seedings). A product with a 4.2★ public rating might have 30% severe complaints.
*Our Equation:*
$$\text{Rating Truth} = \text{round}\left(\max\left(1.0, \bar{R} - \max\left(0.1, \min\left(0.6, \frac{N_{\text{pct}}}{100} \times 1.5\right)\right)\right), 1\right)$$
Where:
- $\bar{R}$ = Raw average star rating.
- $N_{\text{pct}}$ = Empirical percentage of negative reviews computed by VADER + clause ABSA.
- If negative sentiment is high ($>25\%$), the equation applies a penalty up to $-0.60\text{★}$, revealing the true uninflated customer sentiment.

#### C. Closed-Loop Impact Verification Math
*How Lumina tests if an engineering fix worked:*
Given pre-fix baseline cohort $C_{\text{pre}}$ and post-fix cohort $C_{\text{post}}$:
1. **Target Complaint Rate Delta:**
   $$\Delta_{\text{complaint}} = \frac{R_{\text{pre}} - R_{\text{post}}}{\max(R_{\text{pre}}, 0.1)} \times 100\%$$
2. **Negative Sentiment Share Net Drop:**
   $$\Delta_{\text{neg}} = \text{NegPct}_{\text{pre}} - \text{NegPct}_{\text{post}}$$
3. **Actual Star Lift:**
   $$\text{Lift}_{\text{actual}} = \bar{R}_{\text{post}} - \bar{R}_{\text{pre}}$$
4. **Model Accuracy Score:**
   $$\text{Accuracy (\%)} = \max\left(0, 100 - \frac{|\text{Lift}_{\text{actual}} - \text{Lift}_{\text{predicted}}|}{\max(\text{Lift}_{\text{predicted}}, 0.05)} \times 100\right)$$
5. **Decision Boundary:**
   - If $\Delta_{\text{complaint}} \ge 25\%$ AND $\Delta_{\text{neg}} > 0 \rightarrow$ **`Verified Improvement`**.
   - If $|C_{\text{post}}| < 10 \rightarrow$ **`Insufficient Data`** (observation window in progress).
   - If $\Delta_{\text{complaint}} < 5\%$ AND $\text{Lift}_{\text{actual}} \le 0 \rightarrow$ **`No Improvement`**.
   - Else $\rightarrow$ **`Inconclusive`** (marginal movement within noise margin).

---

### 3. Top 15 Mentor & Technical Questions with Ideal Answers

#### Q1: "Why did you use VADER instead of fine-tuning a BERT model for sentiment?"
**Your Answer:**
> "That was a deliberate engineering decision based on latency, explainability, and enterprise edge deployment:
> 1. **Latency & Throughput:** VADER executes sub-millisecond inference on CPU without requiring GPU infrastructure. Parsing 10,000 reviews takes <2 seconds in Lumina compared to several minutes on transformer models.
> 2. **Rule-Based Customization:** Standard transformers struggle with domain idioms like *'headphone caliper force'* or *'heavy washed denim'*. In `analyze_reviews.py`, we augmented VADER's valence dictionary with custom e-commerce product modifiers and booster words.
> 3. **Deterministic Explainability:** In product engineering, teams need to inspect *why* a review was flagged. VADER's clause tokenization makes every valence score fully auditable."

#### Q2: "How does Lumina generate 5-Whys root causes and spec patches dynamically?"
**Your Answer:**
> "In `lumina_api.py`, `build_dynamic_tickets()` takes the product category and real complaints with `count > 0`.
> It branches dynamically across categories (Apparel, Footwear, Electronics, Beauty, Home).
> For apparel, it generates textile engineering subsystems like *'Textile Mill & Fabric Sourcing'* and *'Pattern Engineering & Sizing Calibration'*, with realistic spec patches (e.g. `FABRIC_GSM = 280`, `SPI = 12`).
> For electronics, it targets *'Firmware & Connectivity Stack'* and *'BLE Handshake Timeout'*. It never leaks tech terms like Bluetooth or battery onto clothing."

#### Q3: "What was the bug where Battery complaints appeared on a pair of jeans, and how did you fix it?"
**Your Answer:**
> "We diagnosed and fixed a 3-part failure chain:
> 1. In `category_intelligence.py`, the substring `'bag'` in *Bags & Accessories* matched inside the word `'baggy'`, causing baggy jeans to misclassify. We guarded keyword matching with length limits and added explicit apparel tokens (`baggy`, `washed`, `jeans`).
> 2. In `lumina_api.py`, `build_dynamic_tickets()` was reading `metrics['complaints']` without filtering for `count > 0`, so row 0 (`Battery drains quickly`) was picked as fallback. We added strict category filtering and positive mention guards.
> 3. In `analyze_reviews.py`, `verify_closed_loop_impact()` was splitting complaint labels into loose tokens. A review saying *'arrived quickly'* matched the token *'quickly'*, creating a false positive battery hit. We replaced token splitting with full-phrase exact matching and added an `Insufficient Data (<10 reviews)` statistical guard."

#### Q4: "How does the backend serialize and sanitize data before returning it to the frontend?"
**Your Answer:**
> "In `lumina_api.py`, we implement a recursive `clean(val)` utility:
> - Converts `NaN`, `Infinity`, and `-Infinity` into `None` or default numeric values (preventing JavaScript JSON parsing crashes).
> - Converts NumPy types (`np.int64`, `np.float64`) to native Python `int` and `float`.
> - Converts Pandas Series and DataFrames to serialized lists and dictionaries."

#### Q5: "Explain the mathematics behind the Recommendation Learning Loop."
**Your Answer:**
> "The Recommendation Learning Loop tracks prediction accuracy across historical interventions in `learning_loop_ledger.json`.
> Each intervention records $\text{Lift}_{\text{predicted}}$ and $\text{Lift}_{\text{actual}}$.
> The system calculates a global calibration factor:
> $$\text{Calibration Factor} = \frac{\sum \text{Lift}_{\text{actual}}}{\max\left(0.1, \sum \text{Lift}_{\text{predicted}}\right)}$$
> This calibration factor is applied to all future star lift predictions. If historical engineering tickets delivered 96% of projected gains, new tickets are calibrated by $0.96\times$."

#### Q6: "How do you calculate eNPS (Employee/Customer Net Promoter Score) from reviews?"
**Your Answer:**
> "In `analyze_reviews.py`:
> - **Promoters:** Reviews with 5-star ratings or positive sentiment $\ge +0.60$.
> - **Detractors:** Reviews with 1-star or 2-star ratings, or negative sentiment $\le -0.40$.
> - **Passives:** 3-star and 4-star reviews with neutral sentiment.
> $$\text{eNPS} = \% \text{Promoters} - \% \text{Detractors}$$
> Yielding a score ranging from $-100$ to $+100$."

#### Q7: "How is the spike detection algorithm implemented?"
**Your Answer:**
> "In `analyze_reviews.py`, `detect_trend_spikes()` analyzes monthly complaint volume.
> If a specific complaint's share of negative reviews jumps by $\ge 15\%$ month-over-month (e.g. from 8% in March to 27% in April after a firmware or lot release), it is flagged as an active defect spike."

#### Q8: "How does your REST API handle concurrent requests or large CSV uploads?"
**Your Answer:**
> "In `POST /api/analyze-csv`, we read the file using Pandas and apply `normalize_upload()`. For large CSV files (e.g. 10,000+ reviews), we draw a statistically representative stratified sample of 1,200 reviews (`random_state=42`) for the interactive sub-second NLP pass, while recording the true review count ($N=10,000$) for total volume telemetry."

---

### 4. Live Demo Walkthrough (Your Presentation Script)
1. **Takeover from Vaibhavi (1 min):** "I will now demonstrate the core NLP pipeline and Closed-Loop Verification engine."
2. **Explain Rating Truth (1 min):** "Notice the headline rating here is 4.4★, but Lumina has calibrated it to 4.1★. This -0.3★ debiasing penalty is computed because 22% of reviews isolate critical friction."
3. **Show Closed-Loop Verification (1 min):** "When we click on **Impact Verification**, Lumina evaluates pre-fix vs. post-fix cohorts. For this clothing product, notice the intervention is *Textile Mill & Fabric Sourcing*, complaint rate dropped from 19.4% to 8.2%, and the status is verified with 97% model projection accuracy."
4. **Handoff:** "Now Atharva will explain the data extraction engine, scraping resilience, and category intelligence classifier."
