"""
Review Link Ingestion & Analysis Engine.

Fetches the LIVE product page + visible customer reviews for the exact
product a URL points to. Two honesty rules this file is built around,
both fixes for bugs in the previous version:

  1. Reviews shown for a URL always belong to THAT product. They never
     come from Lumina's bulk offline dataset (processed/reviews_sentiment.csv
     or reviews_10000.csv), because that dataset only tracks broad
     categories (Electronics / Fashion / ...), not individual products —
     sampling it "for a product" was actually sampling from every other
     product in the same category, which is what produced mismatched
     results before.

  2. A review is only ever removed as a "duplicate" when the SAME
     reviewer id posted the exact same text more than once. Two
     different customers who happen to write similar or identical short
     text ("Great product!") are always both kept — that's not a
     duplicate, that's two different people.

Flow for a URL:
  - If it's an Amazon product URL: try a real live fetch of the product
    page and its visible reviews.
      - Success -> is_live_scraped=True, real product data.
      - Blocked/CAPTCHA'd/no reviews found -> if this exact ASIN is one
        of our curated benchmark products, fall back to that product's
        OWN small demo review set (never a different product's data)
        with is_live_scraped=False and an honest status message saying
        why. Otherwise, raise a clear error — we do NOT invent a fake
        product from the URL slug.
  - If it's a non-Amazon URL we don't know how to scrape: only a
    curated-benchmark match can serve it; otherwise a clear error.

Setup (once):
    pip install requests beautifulsoup4

Note: Amazon actively fights automated requests (CAPTCHAs, 503s, rate
limiting). Getting blocked on some fraction of requests is expected
behavior of the live web, not a bug in this script — that's exactly
why the fallback path above exists instead of pretending it succeeded.
"""

from __future__ import annotations

import os
import random
import re
import time
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests

try:
    from bs4 import BeautifulSoup
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "url_analyzer.py needs BeautifulSoup. Install it with:\n"
        "    pip install beautifulsoup4\n"
    ) from e

from lumina_config import extract_asin, redact_pii

REQUEST_TIMEOUT = 12
MAX_REVIEW_PAGES = 3          # extra /product-reviews/ pages to try, beyond the product page itself
POLITE_DELAY_RANGE = (1.5, 3.0)  # seconds between requests, so we don't hammer the server
MAX_RETRIES = 3                  # retry attempts per page before giving up
RETRY_BACKOFF_BASE = 2.5         # seconds; grows exponentially with jitter between retries

# Third-party Amazon data API (RapidAPI) — tried first for Amazon URLs when
# configured, since it sidesteps bot-detection entirely instead of fighting it.
# Get a free key at: https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data
# Set it as an environment variable, never hardcode it here:
#   Windows (PowerShell): setx RAPIDAPI_KEY "your-key-here"
#   macOS/Linux:          export RAPIDAPI_KEY="your-key-here"
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "real-time-amazon-data.p.rapidapi.com"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

BLOCK_SIGNALS = [
    "api-services-support@amazon.com",
    "to discuss automated access",
    "enter the characters you see below",
    "sorry, we just need to make sure you're not a robot",
    "captcha",
]


class ScrapeBlocked(Exception):
    """Raised when Amazon serves a CAPTCHA/robot-check/rate-limit page instead of real content."""


# ============================================================
# CURATED FALLBACK PROFILES
# ------------------------------------------------------------
# Used ONLY when a live scrape of one of these exact products fails.
# Each product carries its OWN small review set (never another
# product's reviews), each review tagged with a distinct reviewerID so
# the reviewer-based dedup logic has something real to demonstrate.
# ============================================================

CURATED_PRODUCT_BENCHMARKS: dict[str, dict[str, Any]] = {
    "Sony WH-1000XM5 Wireless Noise-Canceling Headphones": {
        "url": "https://www.amazon.com/dp/B09XS7JWHH",
        "asin": "B09XS7JWHH",
        "category": "Electronics",
        "brand": "Sony",
        "model": "WH-1000XM5",
        "image": "https://m.media-amazon.com/images/I/61+elLndqVL._AC_SL1500_.jpg",
        "description": (
            "The Sony WH-1000XM5 wireless noise-canceling headphones rewrite the rules for "
            "distraction-free listening. Two processors control 8 microphones for adaptive noise "
            "cancellation, paired with a 30mm carbon fiber driver unit, up to 30-hour battery life "
            "with quick charging, and a soft-fit synthetic leather design."
        ),
        "features": [
            "Industry-leading active noise cancellation with 8 microphones & Auto NC Optimizer",
            "30mm carbon composite drivers for high-resolution sound",
            "Crystal-clear hands-free calling with 4 beamforming mics",
            "Up to 30-hour battery life with quick 3-minute charge for 3 hours playback",
            "Multipoint connection for switching between two Bluetooth devices",
        ],
        "specs": {
            "Brand": "Sony", "Model Name": "WH-1000XM5", "Form Factor": "Over Ear, Closed-Back",
            "Connectivity": "Bluetooth 5.2, 3.5mm Aux", "Battery Life": "30 hours (ANC On)",
            "Weight": "250 grams (8.8 oz)",
        },
        "demo_reviews": [
            {"reviewerID": "A1K3PLM9X", "review": "The noise cancellation is genuinely incredible, I can't hear my coworkers anymore.", "rating": 5, "reviewTime": "2025-03-04"},
            {"reviewerID": "A2Q7TBV21", "review": "Sound quality is fantastic but the touch controls on the ear cup are way too sensitive.", "rating": 4, "reviewTime": "2025-03-19"},
            {"reviewerID": "A3ZXPLQ88", "review": "Battery lasts exactly as advertised, easily gets me through a full week of commuting.", "rating": 5, "reviewTime": "2025-04-02"},
            {"reviewerID": "A1K3PLM9X", "review": "The noise cancellation is genuinely incredible, I can't hear my coworkers anymore.", "rating": 5, "reviewTime": "2025-03-04"},
            {"reviewerID": "A4WQXQ102", "review": "Comfortable for long sessions but they do get warm after a couple hours.", "rating": 4, "reviewTime": "2025-04-15"},
            {"reviewerID": "A9PLVX330", "review": "Great sound quality!", "rating": 5, "reviewTime": "2025-04-22"},
            {"reviewerID": "A6NQZR774", "review": "Great sound quality!", "rating": 5, "reviewTime": "2025-04-25"},
            {"reviewerID": "A5MZQP219", "review": "Had to return mine — one earcup developed a rattling sound after a month.", "rating": 2, "reviewTime": "2025-05-01"},
        ],
    },
    "Anker 737 Power Bank (PowerCore 24K)": {
        "url": "https://www.amazon.com/dp/B09VPHVT2Z",
        "asin": "B09VPHVT2Z",
        "category": "Electronics",
        "brand": "Anker",
        "model": "PowerCore 24K (A1289)",
        "image": "https://m.media-amazon.com/images/I/61bX26Vcz7L._AC_SL1500_.jpg",
        "description": (
            "The Anker 737 Power Bank (PowerCore 24K) features ultra-powerful two-way 140W fast "
            "charging with Power Delivery 3.1 and bi-directional technology, plus a smart digital "
            "display showing output/input power and time to full charge."
        ),
        "features": [
            "Two-way charging with Power Delivery 3.1 up to 140W",
            "Smart digital display shows real-time wattage and remaining charge time",
            "24,000mAh capacity for multiple laptop/phone/tablet charges",
            "Triple-port simultaneous output: 2x USB-C, 1x USB-A",
        ],
        "specs": {"Brand": "Anker", "Capacity": "24,000 mAh / 86.4 Wh", "Max Output": "140W Max", "Weight": "630 grams (22.2 oz)"},
        "demo_reviews": [
            {"reviewerID": "B1RTQX441", "review": "The display showing exact wattage is such a small but genuinely useful touch.", "rating": 5, "reviewTime": "2025-02-11"},
            {"reviewerID": "B2LMNP882", "review": "Heavy, but that's the trade-off for this much capacity. Charges my laptop twice over.", "rating": 4, "reviewTime": "2025-02-27"},
            {"reviewerID": "B3QZXX120", "review": "Stopped holding a charge properly after about 3 months of daily use.", "rating": 2, "reviewTime": "2025-03-15"},
            {"reviewerID": "B4TPLK933", "review": "Fast charging works exactly as advertised, tops up my phone in under 30 minutes.", "rating": 5, "reviewTime": "2025-03-28"},
        ],
    },
    "Kindle Paperwhite (16 GB) 6.8 Display": {
        "url": "https://www.amazon.com/dp/B08KTZ8249",
        "asin": "B08KTZ8249",
        "category": "Electronics",
        "brand": "Amazon",
        "model": "Kindle Paperwhite 11th Gen",
        "image": "https://m.media-amazon.com/images/I/61U0gY8e-LL._AC_SL1000_.jpg",
        "description": (
            "The Kindle Paperwhite features a 6.8\" glare-free 300 ppi display, adjustable warm "
            "light, up to 10 weeks of battery life, 20% faster page turns, and an IPX8 waterproof rating."
        ),
        "features": [
            "6.8\" glare-free 300 ppi display with adjustable warm light",
            "Up to 10 weeks of battery life on a single USB-C charge",
            "IPX8 waterproof rating",
            "16 GB storage for thousands of titles and audiobooks",
        ],
        "specs": {"Brand": "Amazon", "Display": "6.8-inch, 300 ppi", "Storage": "16 GB", "Battery Life": "Up to 10 weeks"},
        "demo_reviews": [
            {"reviewerID": "C1PQRS220", "review": "The warm light feature makes reading before bed so much easier on the eyes.", "rating": 5, "reviewTime": "2025-01-20"},
            {"reviewerID": "C2LMTX771", "review": "Battery genuinely lasts weeks, not days. Best upgrade from my old Kindle.", "rating": 5, "reviewTime": "2025-02-09"},
            {"reviewerID": "C3ZZPQ004", "review": "Page turns are noticeably snappier than my old one, no more lag.", "rating": 4, "reviewTime": "2025-02-24"},
            {"reviewerID": "C4WQXN550", "review": "Screen picked up a hairline scratch within the first week despite a case.", "rating": 3, "reviewTime": "2025-03-10"},
        ],
    },
    "Nike Air Zoom Pegasus Road Running Shoes": {
        "url": "https://www.nike.com/running/pegasus-zoom",
        "asin": None,
        "category": "Fashion",
        "brand": "Nike",
        "model": "Air Zoom Pegasus",
        "image": "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/1e93dae2-c0cb-46a2-9e2c-5668b5ea3f45/air-zoom-pegasus-road-running-shoes.png",
        "description": (
            "The Nike Air Zoom Pegasus Road Running Shoes are engineered as the trusted daily "
            "trainer, with lightweight, durable Nike React foam delivering a smooth, springy ride."
        ),
        "features": [
            "Nike React foam for high-energy return and durable cushioning",
            "Dual Zoom Air units in forefoot and heel for springy toe-off",
            "Engineered circular knit mesh upper for breathability",
        ],
        "specs": {"Brand": "Nike", "Style": "Road Running / Marathon Training", "Drop": "10 mm heel-to-toe"},
        "demo_reviews": [
            {"reviewerID": "D1KPLM220", "review": "Perfect for daily mileage, my knees feel noticeably better than my old trainers.", "rating": 5, "reviewTime": "2025-02-02"},
            {"reviewerID": "D2QZTX881", "review": "Runs about half a size small, order up if you're between sizes.", "rating": 4, "reviewTime": "2025-02-18"},
            {"reviewerID": "D3LMNP004", "review": "Outsole started separating from the upper after about 200 miles.", "rating": 2, "reviewTime": "2025-03-05"},
        ],
    },
    "Logitech MX Master 3S Wireless Performance Mouse": {
        "url": "https://www.logitech.com/mx-master-3s",
        "asin": None,
        "category": "Electronics",
        "brand": "Logitech",
        "model": "MX Master 3S",
        "image": "https://resource.logitech.com/w_1600,c_limit,q_auto,f_auto,dpr_1.0/d_transparent.gif/content/dam/logitech/en/products/mice/mx-master-3s/gallery/mx-master-3s-mouse-top-view-graphite.png",
        "description": (
            "The Logitech MX Master 3S is an ergonomic performance mouse with Quiet Click buttons "
            "(90% less noise), MagSpeed scrolling, and an 8,000 DPI Darkfield sensor that tracks on "
            "virtually any surface, including glass."
        ),
        "features": [
            "MagSpeed electromagnetic scrolling at 1,000 lines/sec",
            "8,000 DPI Darkfield sensor tracks on glass and other tricky surfaces",
            "Quiet Click buttons with 90% less acoustic noise",
        ],
        "specs": {"Brand": "Logitech", "Sensor": "8,000 DPI Darkfield Optical", "Battery Life": "Up to 70 days"},
        "demo_reviews": [
            {"reviewerID": "E1PQXX441", "review": "The scroll wheel alone is worth the price, so satisfying for spreadsheets.", "rating": 5, "reviewTime": "2025-01-14"},
            {"reviewerID": "E2LMTQ992", "review": "Works flawlessly on my glass desk, first mouse that's ever managed that.", "rating": 5, "reviewTime": "2025-02-01"},
            {"reviewerID": "E3ZZNP330", "review": "Thumb button stopped registering clicks reliably after a few months.", "rating": 3, "reviewTime": "2025-02-19"},
        ],
    },
}


# ============================================================
# LIVE SCRAPING
# ============================================================

def _build_headers(referer: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin" if referer else "none",
        "DNT": "1",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _warm_up_session(session: requests.Session, domain: str) -> None:
    """
    Visit the site's homepage first so the session picks up normal
    cookies (session id, region, currency, etc.) before hitting the
    product page — a cold request with zero cookies is one of the
    easiest signals for a bot-detector to flag. Failure here is not
    fatal; we just proceed without the warm cookies if it doesn't work.
    """
    try:
        session.get(f"https://{domain}/", headers=_build_headers(), timeout=REQUEST_TIMEOUT)
        time.sleep(random.uniform(*POLITE_DELAY_RANGE))
    except requests.RequestException:
        pass


def _get(session: requests.Session, url: str, referer: str | None = None) -> requests.Response:
    headers = _build_headers(referer)
    resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    lowered = resp.text.lower()
    if resp.status_code in (503, 429) or any(sig in lowered for sig in BLOCK_SIGNALS):
        raise ScrapeBlocked(f"Blocked or rate-limited fetching {url} (status {resp.status_code})")
    resp.raise_for_status()
    return resp


def _get_with_retry(session: requests.Session, url: str, referer: str | None = None) -> requests.Response:
    """Retry with exponential backoff + jitter, rotating headers each attempt."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _get(session, url, referer=referer)
        except (ScrapeBlocked, requests.RequestException) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = (RETRY_BACKOFF_BASE ** attempt) + random.uniform(0, 1.5)
                time.sleep(delay)
    raise last_error  # type: ignore[misc]


def _parse_product_page(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("#productTitle")
    product_name = title_el.get_text(strip=True) if title_el else None

    bullets = [
        li.get_text(strip=True)
        for li in soup.select("#feature-bullets li span.a-list-item")
        if li.get_text(strip=True)
    ]

    desc_el = soup.select_one("#productDescription") or soup.select_one("#bookDescription_feature_div")
    description = re.sub(r"\s+", " ", desc_el.get_text(" ", strip=True)) if desc_el else ""

    img_el = soup.select_one("#landingImage") or soup.select_one("#imgTagWrapperId img")
    image = (img_el.get("data-old-hires") or img_el.get("src")) if img_el else ""

    specs: dict[str, str] = {}
    for row in soup.select("#productDetails_techSpec_section_1 tr"):
        key_el, val_el = row.select_one("th"), row.select_one("td")
        if key_el and val_el:
            specs[key_el.get_text(strip=True)] = val_el.get_text(strip=True)
    if not specs:
        for row in soup.select("#detailBullets_feature_div li"):
            text = row.get_text(" ", strip=True)
            if ":" in text:
                k, v = text.split(":", 1)
                specs[k.strip()] = v.strip()

    return {
        "product_name": product_name,
        "product_features": bullets,
        "product_description": description,
        "product_image": image or "",
        "product_specs": specs,
    }


def _parse_reviews(html: str) -> list[dict[str, Any]]:
    """Pull visible reviews out of a product page or a /product-reviews/ page."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for block in soup.select("div[data-hook='review']"):
        profile_link = block.select_one("a.a-profile")
        reviewer_id = None
        if profile_link and profile_link.get("href"):
            m = re.search(r"account\.([A-Za-z0-9]+)", profile_link["href"])
            if m:
                reviewer_id = m.group(1)
        if not reviewer_id:
            name_el = block.select_one(".a-profile-name")
            # Fall back to the display name as the best identity signal we have —
            # not as reliable as the real account id, but still ties a review to
            # a specific person rather than to nothing at all.
            reviewer_id = f"name:{name_el.get_text(strip=True)}" if name_el else None

        rating_el = block.select_one("i[data-hook='review-star-rating'] span, i[data-hook='cmps-review-star-rating'] span")
        rating = None
        if rating_el:
            m = re.search(r"([\d.]+)", rating_el.get_text())
            if m:
                rating = float(m.group(1))

        body_el = block.select_one("span[data-hook='review-body']")
        review_text = body_el.get_text(" ", strip=True) if body_el else ""

        date_el = block.select_one("span[data-hook='review-date']")
        review_time = date_el.get_text(strip=True) if date_el else ""

        if review_text and reviewer_id:
            rows.append({
                "reviewerID": reviewer_id,
                "review": redact_pii(re.sub(r"\s+", " ", review_text)),
                "rating": rating,
                "reviewTime": review_time,
            })
    return rows


# ============================================================
# THIRD-PARTY REVIEW WIDGET APIs
# ------------------------------------------------------------
# A lot of retailers (Nike, Logitech, Target, Best Buy, and many
# mid-size e-commerce sites) don't build their own review system —
# they embed a widget from Bazaarvoice, PowerReviews, or Yotpo, which
# renders by calling that platform's own JSON API. Those APIs are
# meant to be called client-side by a browser, so they're generally
# far less bot-guarded than a page like Amazon's. If we find one of
# these embedded in the page, we call it directly instead of trying
# to parse rendered HTML.
#
# NOTE: exact JSON field names vary a bit by integration/version for
# each platform. The parsing below uses the most common shape for
# each API as of general documentation, with defensive .get() lookups
# — but treat this as a strong first pass that may need small field-
# name tweaks once tested against a specific real site.
# ============================================================

def _detect_bazaarvoice(html: str) -> dict[str, str] | None:
    passkey_match = re.search(r'passkey["\']?\s*[:=]\s*["\']([A-Za-z0-9]+)["\']', html) \
        or re.search(r'"apiKey"\s*:\s*"([^"]+)"', html)
    product_match = re.search(r'data-bv-product-id=["\']([\w\-\.]+)["\']', html) \
        or re.search(r'productId["\']?\s*[:=]\s*["\']([\w\-\.]+)["\']', html)
    deploy_match = re.search(r'apps\.bazaarvoice\.com/deployments/([^/]+)/([^/]+)/([^/]+)/([^/"\']+)', html)

    if not (passkey_match and product_match):
        return None
    result = {"passkey": passkey_match.group(1), "product_id": product_match.group(1)}
    if deploy_match:
        result["locale"] = deploy_match.group(4)
    return result


def _fetch_bazaarvoice_reviews(session: requests.Session, info: dict[str, str]) -> list[dict[str, Any]]:
    api_url = (
        "https://api.bazaarvoice.com/data/reviews.json"
        f"?apiversion=5.4&passkey={info['passkey']}&Filter=ProductId:{info['product_id']}"
        "&Sort=SubmissionTime:desc&Limit=100"
    )
    resp = _get_with_retry(session, api_url)
    data = resp.json()
    rows = []
    for r in data.get("Results", []):
        text = r.get("ReviewText") or ""
        author = r.get("AuthorId") or r.get("UserNickname")
        if text and author:
            rows.append({
                "reviewerID": str(author),
                "review": redact_pii(text),
                "rating": r.get("Rating"),
                "reviewTime": (r.get("SubmissionTime") or "")[:10],
            })
    return rows


def _detect_powerreviews(html: str) -> dict[str, str] | None:
    merchant_match = re.search(r'data-pr-merchant-id=["\'](\d+)["\']', html) \
        or re.search(r'merchant_id["\']?\s*[:=]\s*["\']?(\d+)["\']?', html)
    page_match = re.search(r'data-pr-page-id=["\']([\w\-\.]+)["\']', html) \
        or re.search(r'page_id["\']?\s*[:=]\s*["\']([\w\-\.]+)["\']', html)
    if not (merchant_match and page_match):
        return None
    return {"merchant_id": merchant_match.group(1), "page_id": page_match.group(1)}


def _fetch_powerreviews_reviews(session: requests.Session, info: dict[str, str]) -> list[dict[str, Any]]:
    api_url = (
        f"https://display.powerreviews.com/m/{info['merchant_id']}/l/en_US/product/"
        f"{info['page_id']}/reviews?_noconfig=true&paging.size=100"
    )
    resp = _get_with_retry(session, api_url)
    data = resp.json()
    rows = []
    for result in data.get("results", []):
        for r in result.get("reviews", []):
            details = r.get("details", {})
            text = details.get("comments") or ""
            author = details.get("author_id") or details.get("nickname") or r.get("review_id")
            if text and author:
                rows.append({
                    "reviewerID": str(author),
                    "review": redact_pii(text),
                    "rating": r.get("metrics", {}).get("rating"),
                    "reviewTime": str(details.get("created_date", ""))[:10],
                })
    return rows


def _detect_yotpo(html: str) -> dict[str, str] | None:
    app_key_match = re.search(r'staticw2\.yotpo\.com/([A-Za-z0-9]+)/widget', html) \
        or re.search(r'yotpo_app_key["\']?\s*[:=]\s*["\']([A-Za-z0-9]+)["\']', html)
    product_match = re.search(r'data-product-id=["\']([\w\-\.]+)["\']', html)
    if not (app_key_match and product_match):
        return None
    return {"app_key": app_key_match.group(1), "product_id": product_match.group(1)}


def _fetch_yotpo_reviews(session: requests.Session, info: dict[str, str]) -> list[dict[str, Any]]:
    api_url = (
        f"https://api.yotpo.com/v1/widget/{info['app_key']}/products/"
        f"{info['product_id']}/reviews.json?page=1&per_page=100"
    )
    resp = _get_with_retry(session, api_url)
    data = resp.json()
    rows = []
    for r in data.get("response", {}).get("reviews", []):
        text = r.get("content") or ""
        user = r.get("user") or {}
        author = user.get("id") or user.get("display_name")
        if text and author:
            rows.append({
                "reviewerID": str(author),
                "review": redact_pii(text),
                "rating": r.get("score"),
                "reviewTime": str(r.get("created_at", ""))[:10],
            })
    return rows


def _try_widget_apis(session: requests.Session, html: str) -> tuple[str, list[dict[str, Any]]] | None:
    """Detect and call whichever third-party review widget (if any) this page uses."""
    for platform_name, detector, fetcher in [
        ("Bazaarvoice", _detect_bazaarvoice, _fetch_bazaarvoice_reviews),
        ("PowerReviews", _detect_powerreviews, _fetch_powerreviews_reviews),
        ("Yotpo", _detect_yotpo, _fetch_yotpo_reviews),
    ]:
        info = detector(html)
        if not info:
            continue
        try:
            rows = fetcher(session, info)
        except (requests.RequestException, ValueError, KeyError):
            continue
        if rows:
            return platform_name, rows
    return None


# ============================================================
# THIRD-PARTY AMAZON DATA API (RapidAPI)
# ------------------------------------------------------------
# Real product data + real review text via a service that has already
# solved the anti-bot problem, instead of us fighting it. Only used
# when RAPIDAPI_KEY is set; otherwise this is skipped silently and we
# fall through to live scraping / demo fallback as before.
#
# NOTE: field names below match this provider's documented response
# shape as of general docs — if RapidAPI have changed their schema,
# the defensive .get() lookups mean we'd just get fewer/no reviews
# back rather than crash, but let me know if that happens so I can
# adjust the field names against a real response.
# ============================================================

def _fetch_via_rapidapi(asin: str) -> dict[str, Any] | None:
    if not RAPIDAPI_KEY or not asin:
        return None

    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}

    try:
        details_resp = requests.get(
            f"https://{RAPIDAPI_HOST}/product-details",
            headers=headers, params={"asin": asin, "country": "US"}, timeout=REQUEST_TIMEOUT,
        )
        details_resp.raise_for_status()
        details = details_resp.json().get("data", {})

        reviews_resp = requests.get(
            f"https://{RAPIDAPI_HOST}/product-reviews",
            headers=headers, params={"asin": asin, "country": "US", "page": 1}, timeout=REQUEST_TIMEOUT,
        )
        reviews_resp.raise_for_status()
        raw_reviews = reviews_resp.json().get("data", {}).get("reviews", [])
    except (requests.RequestException, ValueError):
        return None

    if not details or not raw_reviews:
        return None

    rows = []
    for r in raw_reviews:
        text = r.get("review_comment") or r.get("review_text") or ""
        author = r.get("review_author_id") or r.get("review_author") or r.get("review_id")
        if text and author:
            rows.append({
                "reviewerID": str(author),
                "review": redact_pii(text),
                "rating": r.get("review_star_rating"),
                "reviewTime": str(r.get("review_date", ""))[:10],
            })
    if not rows:
        return None

    bullets = details.get("about_product") or []
    specs = details.get("product_details") or {}

    return {
        "product_name": details.get("product_title") or f"Amazon Product ({asin})",
        "product_features": bullets,
        "product_description": details.get("product_description") or " ".join(bullets[:3]),
        "product_image": details.get("product_photo") or "",
        "product_specs": specs,
        "reviews": rows,
    }


def _scrape_live(url: str, asin: str | None) -> dict[str, Any]:
    domain = urlparse(url).netloc
    session = requests.Session()

    # Warm up with real-looking cookies before the actual request.
    _warm_up_session(session, domain)

    product_resp = _get_with_retry(session, url, referer=f"https://www.google.com/search?q=site:{domain}")
    product_info = _parse_product_page(product_resp.text)

    # Prefer a third-party review widget API (Bazaarvoice/PowerReviews/Yotpo)
    # if this page uses one — those JSON endpoints are far less bot-guarded
    # than parsing rendered HTML, and many non-Amazon retailers use one.
    widget_result = _try_widget_apis(session, product_resp.text)
    if widget_result:
        _, review_rows = widget_result
    else:
        review_rows = _parse_reviews(product_resp.text)

    # Try a few dedicated review pages too, if we have an ASIN to build the URL from
    # (Amazon-style pagination — only relevant when no widget API handled it above).
    if asin and not widget_result:
        for page in range(1, MAX_REVIEW_PAGES + 1):
            time.sleep(random.uniform(*POLITE_DELAY_RANGE))
            reviews_url = f"https://{domain}/product-reviews/{asin}/?pageNumber={page}&sortBy=recent"
            try:
                resp = _get_with_retry(session, reviews_url, referer=url)
            except (ScrapeBlocked, requests.RequestException):
                break
            page_rows = _parse_reviews(resp.text)
            if not page_rows:
                break
            review_rows.extend(page_rows)

    if not product_info.get("product_name") or not review_rows:
        raise ScrapeBlocked("Product page loaded but no title/reviews could be parsed (layout change or block page).")

    return {**product_info, "reviews": review_rows}


# ============================================================
# REVIEWER-ID DEDUPLICATION
# ============================================================

def _dedupe_by_reviewer(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """
    Remove a review only when the SAME reviewer id posted the exact same
    text more than once. Different reviewers with identical or similar
    short text (e.g. "Great sound quality!") are always both kept —
    that's two different customers, not a duplicate.
    """
    seen: set[tuple[str, str]] = set()
    kept = []
    for r in rows:
        key = (str(r.get("reviewerID") or ""), (r.get("review") or "").strip().lower())
        if key in seen:
            continue
        seen.add(key)
        kept.append(r)
    return kept, len(rows) - len(kept)


# ============================================================
# CURATED FALLBACK
# ============================================================

def _match_benchmark(url: str, asin: str | None) -> tuple[str, dict[str, Any]] | None:
    for name, bench in CURATED_PRODUCT_BENCHMARKS.items():
        if bench["url"] in url or (asin and asin == bench.get("asin")):
            return name, bench
    return None


def _demo_fallback(name: str, bench: dict[str, Any], url: str, reason: str) -> dict[str, Any]:
    rows, removed = _dedupe_by_reviewer(bench["demo_reviews"])
    reviews_df = pd.DataFrame(rows)
    reviews_df["category"] = bench["category"]
    reviews_df["product"] = name

    dedupe_note = f" Removed {removed} duplicate post(s) from the same reviewer." if removed else ""
    return {
        "product_name": name,
        "source_url": url,
        "product_description": bench["description"],
        "product_image": bench.get("image", ""),
        "product_features": bench.get("features", []),
        "product_specs": bench.get("specs", {}),
        "total_reviews": len(reviews_df),
        "reviews_df": reviews_df,
        "is_live_scraped": False,
        "status_message": (
            f"Live fetch unavailable ({reason}). Showing this product's own offline demo "
            f"reviews instead ({len(reviews_df):,} reviews, not another product's data)."
            f"{dedupe_note}"
        ),
    }


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def extract_reviews_from_url(url: str) -> dict[str, Any]:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    asin = extract_asin(url)
    benchmark = _match_benchmark(url, asin)
    is_amazon = "amazon." in domain

    if is_amazon:
        # Try the paid data API first, if configured — it already handles
        # Amazon's bot-detection for us, so it's the most reliable path.
        api_result = _fetch_via_rapidapi(asin) if asin else None
        if api_result:
            rows, removed = _dedupe_by_reviewer(api_result["reviews"])
            reviews_df = pd.DataFrame(rows)
            reviews_df["category"] = "Amazon Data API"
            reviews_df["product"] = api_result["product_name"]

            dedupe_note = f" Removed {removed} duplicate post(s) from the same reviewer." if removed else ""
            return {
                "product_name": api_result["product_name"],
                "source_url": url,
                "product_description": api_result["product_description"],
                "product_image": api_result["product_image"],
                "product_features": api_result["product_features"],
                "product_specs": api_result["product_specs"],
                "total_reviews": len(reviews_df),
                "reviews_df": reviews_df,
                "is_live_scraped": True,
                "status_message": (
                    f"Fetched {len(api_result['reviews']):,} reviews for this exact product via the "
                    f"Amazon Data API.{dedupe_note}"
                ),
            }

        try:
            scraped = _scrape_live(url, asin)
            raw_rows = scraped["reviews"]
            rows, removed = _dedupe_by_reviewer(raw_rows)
            reviews_df = pd.DataFrame(rows)
            reviews_df["category"] = "Live Scraped"
            reviews_df["product"] = scraped["product_name"]

            dedupe_note = f" Removed {removed} duplicate post(s) from the same reviewer." if removed else ""
            return {
                "product_name": scraped["product_name"],
                "source_url": url,
                "product_description": scraped["product_description"],
                "product_image": scraped["product_image"],
                "product_features": scraped["product_features"],
                "product_specs": scraped["product_specs"],
                "total_reviews": len(reviews_df),
                "reviews_df": reviews_df,
                "is_live_scraped": True,
                "status_message": (
                    f"Live-scraped {len(raw_rows):,} reviews for this exact product from {domain}."
                    f"{dedupe_note}"
                ),
            }
        except (ScrapeBlocked, requests.RequestException) as e:
            if benchmark:
                return _demo_fallback(benchmark[0], benchmark[1], url, str(e))
            raise ValueError(
                f"Couldn't fetch live reviews for this URL — Amazon blocked or rate-limited the "
                f"request ({e}). This product also isn't in the offline demo catalog, so there's no "
                f"fallback data to show. Try again in a bit, pick one of the benchmark products, or "
                f"upload a reviews CSV instead."
            ) from e

    # Non-Amazon domain: we have no general scraper for arbitrary retailers.
    if benchmark:
        return _demo_fallback(benchmark[0], benchmark[1], url, f"no live scraper configured for {domain}")

    raise ValueError(
        f"'{domain}' isn't a supported retailer for live scraping yet (only Amazon product pages are "
        f"scraped live). This product also isn't in the offline demo catalog. Try an Amazon product "
        f"link, pick one of the benchmark products, or upload a reviews CSV instead."
    )


SAMPLE_URL_OPTIONS = {name: bench["url"] for name, bench in CURATED_PRODUCT_BENCHMARKS.items()}