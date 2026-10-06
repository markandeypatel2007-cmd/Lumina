"""Shared theme lexicons, PII redaction, sentiment helpers, URL parsing."""

from __future__ import annotations

import re
from typing import Iterable

ASPECT_LEXICONS: dict[str, list[str]] = {
    "Quality": [
        "build quality", "well made", "solid build", "poor quality", "flimsy",
        "craftsmanship", "cheaply made", "cheap material", "feels cheap",
        "premium feel", "finish", "weak build", "loose", "sturdy", "materials",
    ],
    "Durability": [
        "durable", "durability", "long lasting", "broke", "broken", "break",
        "falling apart", "stopped working", "damage", "damaged", "wear and tear",
        "longevity", "holds up", "quit working", "lasted", "lasted only",
        "still going strong", "reliable", "unreliable",
    ],
    "Price": [
        "price", "cost", "expensive", "overpriced", "good value",
        "value for money", "worth it", "worth the money", "waste of money",
        "affordable", "great price", "cheaper elsewhere", "cost too much",
        "bang for the buck", "over priced", "inexpensive",
    ],
    "Delivery": [
        "shipping", "delivery", "delivered late", "late arrival", "arrived on time",
        "fast delivery", "shipped fast", "shipping delay", "transit",
        "arrived quickly", "took forever to arrive", "delivered on time",
    ],
    "Packaging": [
        "packaging", "package", "box was crushed", "poor packaging", "flimsy packaging",
        "package damaged", "arrived damaged", "crushed box", "unopened",
        "well packaged", "protective packaging", "bubble wrap",
    ],
    "Battery": [
        "battery", "batteries", "battery life", "charge", "charged", "charging",
        "charger", "drains quickly", "battery dies", "overheating", "power button",
        "backup battery", "battery drain", "battery lasts", "recharge",
    ],
    "Comfort": [
        "comfortable", "comfort", "fits well", "hurts ears", "too tight", "too loose",
        "soft", "lightweight", "ergonomic", "runs small", "runs large", "painful",
        "uncomfortable", "cushion", "fit nicely", "too heavy",
    ],
    "Audio / Sound": [
        "sound quality", "audio quality", "headset", "headphones",
        "low volume", "too much noise", "speaker", "speakers",
        "hurts ears", "sound cuts out", "clear sound", "great sound",
        "bass", "treble", "distortion",
    ],
    "Usability / Setup": [
        "hard to install", "setup issue", "difficult to use",
        "not easy to use", "hard to use", "easy to use", "easy to set up",
        "simple to use", "user friendly", "intuitive", "instructions",
    ],
    "Connectivity": [
        "wifi", "wi-fi", "bluetooth", "won't connect",
        "keeps disconnecting", "connection drops", "poor reception",
        "gps not working", "weak signal", "paired easily", "pairing",
    ],
    "Camera": [
        "camera", "lens", "photo", "photos", "picture", "pictures",
        "video", "recording", "camera quality", "selfie",
    ],
    "Display": [
        "display", "screen", "resolution", "colors", "brightness",
        "sharpness", "oled", "lcd", "pixel", "viewing angle",
    ],
    "Customer Support": [
        "customer service", "support", "customer care", "warranty",
        "refund", "return policy", "agent", "representative", "helpdesk",
    ],
}

DOMAIN_LEXICON_UPDATES: dict[str, float] = {
    'dies': -2.8, 'died': -2.8, 'drains': -2.2, 'draining': -2.2,
    'incredible': 2.9, 'superb': 2.8, 'comfortable': 2.6, 'comfortably': 2.6,
    'uncomfortable': -2.5, 'drops': -2.0, 'disconnects': -2.5,
    'cracked': -2.6, 'broken': -2.8, 'broke': -2.8,
    'overheating': -2.7, 'overheats': -2.7, 'lasts': 2.2, 'lasting': 2.2,
    'flimsy': -2.4, 'cheaply': -2.3, 'overpriced': -2.7,
}

# Two-level sub-theme taxonomy.
# Each top-level key maps to a list of sub-themes.
# Each sub-theme has: name, keywords (used for matching), sentiment_hint
# sentiment_hint: "negative" means this sub-theme is generally a complaint
#                 "positive" means it's generally a praise
#                 "mixed"    means it goes both ways
SUB_THEME_LEXICONS: dict[str, list[dict]] = {
    "Battery": [
        {"name": "Battery Life",     "keywords": ["battery life", "short battery", "dies quickly", "doesn't last", "lasts all day", "hours of battery", "battery lasts", "all day battery", "standby"], "sentiment_hint": "mixed"},
        {"name": "Overheating",      "keywords": ["overheating", "overheats", "gets hot", "too hot", "burning hot", "heat up", "runs warm", "warm to touch"], "sentiment_hint": "negative"},
        {"name": "Charging Speed",   "keywords": ["slow charge", "fast charge", "takes forever to charge", "charging time", "quick charge", "charges fast", "charges slowly", "recharge time"], "sentiment_hint": "mixed"},
        {"name": "Charger / Cable",  "keywords": ["charger broke", "cable broke", "charging port", "cable quality", "usb cable", "charging cable", "charging adapter", "no charger"], "sentiment_hint": "negative"},
    ],
    "Audio / Sound": [
        {"name": "Sound Quality",    "keywords": ["sound quality", "audio quality", "crisp", "clear sound", "muddy", "muffled", "tinny", "rich sound", "balanced sound"], "sentiment_hint": "mixed"},
        {"name": "Bass",             "keywords": ["bass", "low end", "thump", "boom", "sub-bass", "punchy bass", "weak bass", "lacks bass", "heavy bass"], "sentiment_hint": "mixed"},
        {"name": "Microphone",       "keywords": ["microphone", "mic quality", "call quality", "voice", "recording quality", "mic cuts out", "mic echo", "background noise"], "sentiment_hint": "mixed"},
        {"name": "Volume / Loudness","keywords": ["too quiet", "loud enough", "volume level", "max volume", "low volume", "not loud", "volume drops", "gets loud"], "sentiment_hint": "mixed"},
        {"name": "Noise Cancellation", "keywords": ["noise cancellation", "anc", "noise cancelling", "active noise", "blocks noise", "leaks sound", "sound isolation", "passive noise"], "sentiment_hint": "mixed"},
    ],
    "Connectivity": [
        {"name": "Bluetooth Pairing","keywords": ["pairing", "pair", "won't connect", "failed to pair", "pairing issues", "can't pair", "reconnect", "connect automatically"], "sentiment_hint": "mixed"},
        {"name": "Signal Drops",     "keywords": ["drops", "disconnects", "cutting out", "unstable connection", "keeps dropping", "signal loss", "frequent drops", "connection issues"], "sentiment_hint": "negative"},
        {"name": "Wireless Range",   "keywords": ["range", "distance", "far away", "out of range", "strong range", "limited range", "20 feet", "10 feet", "10 metres"], "sentiment_hint": "mixed"},
        {"name": "Multi-device",     "keywords": ["multipoint", "two devices", "switch between", "multi device", "dual device", "switch devices", "multiple connections"], "sentiment_hint": "mixed"},
        {"name": "Latency / Lag",    "keywords": ["latency", "lag", "delay", "out of sync", "audio delay", "video sync", "lipsync", "slow response"], "sentiment_hint": "negative"},
    ],
    "Comfort": [
        {"name": "Ear Comfort",      "keywords": ["hurts ears", "ear pain", "uncomfortable", "ear fatigue", "ear tips", "ear cushion", "seal", "fits ears", "ear pressure"], "sentiment_hint": "mixed"},
        {"name": "Head Pressure",    "keywords": ["clamp force", "too tight", "head pressure", "headband", "squeezes", "tight fit", "head hurts", "clamping"], "sentiment_hint": "negative"},
        {"name": "Weight",           "keywords": ["too heavy", "lightweight", "heavy on head", "light weight", "bulky", "feels heavy", "not light", "very light"], "sentiment_hint": "mixed"},
        {"name": "Ear Tip Size",     "keywords": ["ear tip", "tip size", "small tips", "large tips", "ear tip fit", "wrong size", "tip fell out", "seal", "included tips"], "sentiment_hint": "mixed"},
    ],
    "Quality": [
        {"name": "Build Materials",  "keywords": ["cheap plastic", "plastic feels", "metal build", "material quality", "premium material", "solid feel", "hollow feel", "feels flimsy"], "sentiment_hint": "mixed"},
        {"name": "Buttons / Controls", "keywords": ["button", "control button", "hard to press", "volume button", "power button", "button stuck", "clicks well", "tactile button"], "sentiment_hint": "mixed"},
        {"name": "Hinge / Folding",  "keywords": ["hinge", "fold", "folding", "swivel", "pivot", "creak", "hinge loose", "snaps open", "fold mechanism"], "sentiment_hint": "mixed"},
        {"name": "Finish / Coating", "keywords": ["peeling", "paint chips", "coating", "scratches easily", "glossy finish", "matte finish", "flaking", "fades"], "sentiment_hint": "mixed"},
    ],
    "Durability": [
        {"name": "Early Failure",    "keywords": ["stopped working", "broke after", "died after", "failed after", "quit working", "only lasted", "gave out", "defective"], "sentiment_hint": "negative"},
        {"name": "Physical Damage",  "keywords": ["cracked", "snapped", "broke in half", "fell apart", "pieces", "broken hinge", "cracked housing", "snapped off"], "sentiment_hint": "negative"},
        {"name": "Water / Sweat Resistance", "keywords": ["water proof", "waterproof", "sweat proof", "water resistant", "rain", "sweat damage", "moisture", "got wet"], "sentiment_hint": "mixed"},
        {"name": "Long-term Hold",   "keywords": ["still going strong", "years later", "very durable", "built to last", "lasted years", "holds up", "great longevity"], "sentiment_hint": "positive"},
    ],
    "Usability / Setup": [
        {"name": "Initial Setup",    "keywords": ["hard to set up", "setup issue", "complicated setup", "easy to set up", "plug and play", "quick setup", "setup instructions", "out of box"], "sentiment_hint": "mixed"},
        {"name": "App / Software",   "keywords": ["app crashes", "app freeze", "app glitchy", "companion app", "app not working", "firmware update", "software issue", "app won't open"], "sentiment_hint": "negative"},
        {"name": "Controls / UX",    "keywords": ["difficult to use", "not intuitive", "confusing controls", "easy to use", "user friendly", "intuitive", "simple controls"], "sentiment_hint": "mixed"},
        {"name": "Compatibility",    "keywords": ["compatible", "not compatible", "works with android", "works with ios", "windows compatible", "mac compatible", "doesn't work with", "works on"], "sentiment_hint": "mixed"},
    ],
    "Delivery": [
        {"name": "Late Arrival",     "keywords": ["late delivery", "arrived late", "shipping delay", "took forever", "still waiting", "delayed", "never arrived", "not delivered"], "sentiment_hint": "negative"},
        {"name": "Fast Shipping",    "keywords": ["arrived quickly", "fast delivery", "shipped fast", "arrived early", "on time", "quick shipping", "next day", "same day"], "sentiment_hint": "positive"},
        {"name": "Damaged in Transit", "keywords": ["arrived damaged", "damaged in transit", "dented box", "crushed", "broken on arrival", "damaged package", "box destroyed"], "sentiment_hint": "negative"},
        {"name": "Missing Items",    "keywords": ["missing parts", "not included", "missing accessory", "no cable included", "incomplete", "wrong item", "missing manual"], "sentiment_hint": "negative"},
    ],
    "Price": [
        {"name": "Good Value",       "keywords": ["good value", "great price", "worth it", "bang for the buck", "affordable", "worth the money", "price is right", "budget friendly"], "sentiment_hint": "positive"},
        {"name": "Overpriced",       "keywords": ["overpriced", "too expensive", "not worth the price", "rip off", "way too much", "highway robbery", "cheaper elsewhere"], "sentiment_hint": "negative"},
        {"name": "Price Drop",       "keywords": ["went on sale", "price dropped", "bought at discount", "on sale", "discounted", "coupon", "deal"], "sentiment_hint": "positive"},
    ],
    "Display / Image Quality": [
        {"name": "Brightness",       "keywords": ["too dim", "not bright enough", "brightness", "glare", "visibility outdoors", "sunlight", "bright screen"], "sentiment_hint": "mixed"},
        {"name": "Resolution",       "keywords": ["blurry", "pixelated", "sharp", "crisp image", "resolution", "high definition", "720p", "1080p", "4k", "hd"], "sentiment_hint": "mixed"},
        {"name": "Color Accuracy",   "keywords": ["colors", "washed out", "vivid colors", "color accuracy", "color reproduction", "pale", "saturated"], "sentiment_hint": "mixed"},
        {"name": "Camera Quality",   "keywords": ["camera quality", "photo quality", "camera blurry", "low light camera", "camera noise", "camera resolution", "grainy"], "sentiment_hint": "mixed"},
    ],
}


THEMES: dict[str, list[str]] = {
    **ASPECT_LEXICONS,
    "Quality / Durability": list(set(ASPECT_LEXICONS["Quality"] + ASPECT_LEXICONS["Durability"])),
    "Price / Value": ASPECT_LEXICONS["Price"],
    "Shipping / Delivery": ASPECT_LEXICONS["Delivery"],
    "Battery / Charging": ASPECT_LEXICONS["Battery"],
    "Size / Fit / Weight": ASPECT_LEXICONS["Comfort"],
    "Technical / Performance": [
        "error", "fail", "failed", "failure", "doesn't work",
        "does not work", "stopped working", "performance issue",
        "malfunction", "driver issue", "software issue",
        "installation problem", "freezes", "crashes", "very slow",
    ],
    "Returns / Refunds": [
        "return", "returned", "returning", "refund",
        "replacement", "replace it", "money back", "refused refund",
    ],
    "Display / Image Quality": [
        "display quality", "screen quality", "blurry image",
        "poor picture", "bad picture", "dull colors",
        "picture quality", "image quality", "camera quality",
    ],
    "Missing / Incomplete Product": [
        "missing parts", "parts missing", "not included",
        "missing manual", "incomplete package",
    ],
}

CORE_ASPECTS: list[str] = [
    "Quality",
    "Durability",
    "Price",
    "Delivery",
    "Packaging",
    "Battery",
    "Comfort",
    "Audio / Sound",
    "Usability / Setup",
    "Connectivity",
    "Camera",
    "Display",
    "Customer Support",
]

PRIORITY_OPTIONS: list[str] = [
    "Price",
    "Quality",
    "Durability",
    "Battery",
    "Delivery",
    "Comfort",
    "Sound",
    "Usability",
]

PRIORITY_ASPECT_MAP: dict[str, list[str]] = {
    "Price": ["Price", "Price / Value"],
    "Quality": ["Quality", "Quality / Durability"],
    "Durability": ["Durability", "Quality / Durability"],
    "Battery": ["Battery", "Battery / Charging"],
    "Delivery": ["Delivery", "Shipping / Delivery"],
    "Comfort": ["Comfort", "Size / Fit / Weight"],
    "Sound": ["Audio / Sound"],
    "Usability": ["Usability / Setup"],
}

COMPLAINT_PHRASES: list[tuple[str, list[str]]] = [
    ("Battery drains quickly", ["battery drain", "drains quickly", "battery dies", "doesn't last", "battery life is poor", "short battery"]),
    ("Poor packaging", ["poor packaging", "package damaged", "arrived damaged", "flimsy packaging", "box was crushed", "broken box"]),
    ("Product feels cheap", ["feels cheap", "cheaply made", "cheap material", "poor quality", "flimsy", "weak build"]),
    ("Delivery delays", ["late delivery", "shipping delay", "delivered late", "took forever", "still waiting", "arrived late"]),
    ("Stopped working", ["stopped working", "doesn't work", "does not work", "quit working", "died after", "no longer works"]),
    ("Battery overheating", ["overheating", "overheats", "too hot", "gets hot", "battery hot", "burning hot"]),
    ("Won't connect", ["won't connect", "keeps disconnecting", "connection drops", "bluetooth issue", "cannot pair", "fails to connect"]),
    ("Hard to return / refund", ["no refund", "refused refund", "return problem", "money back", "difficult to return"]),
    ("Overpriced", ["overpriced", "too expensive", "waste of money", "not worth the price", "not worth it", "rip off"]),
    ("Uncomfortable / poor fit", ["uncomfortable", "hurts ears", "too tight", "doesn't fit", "too loose", "painful to wear"]),
]

PRAISE_PHRASES: list[tuple[str, list[str]]] = [
    ("Good build quality", ["well made", "solid build", "build quality", "good quality", "excellent quality", "premium feel", "sturdy"]),
    ("Comfortable", ["comfortable", "comfort", "fits well", "fits nicely", "ergonomic", "soft and light"]),
    ("Good value for money", ["good value", "great price", "worth the money", "worth it", "bang for the buck", "affordable", "great deal"]),
    ("Fast delivery", ["fast delivery", "arrived quickly", "arrived on time", "shipped fast", "quick shipping", "prompt delivery"]),
    ("Works as expected", ["works great", "works perfectly", "as expected", "does the job", "flawless", "performs well"]),
    ("Great sound", ["great sound", "sound quality", "clear sound", "crisp audio", "excellent sound", "rich bass"]),
    ("Easy to use", ["easy to use", "easy to set up", "simple to use", "user friendly", "intuitive", "plug and play"]),
    ("Long battery life", ["battery lasts", "long battery", "great battery", "battery life is amazing", "lasts all day"]),
    ("Durable / Long lasting", ["durable", "long lasting", "holds up well", "still working after years", "very durable"]),
]

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "this", "that", "was", "are", "be", "as", "from",
    "by", "not", "have", "has", "had", "i", "you", "we", "they", "my", "your",
    "so", "just", "very", "really", "one", "get", "got", "can", "would", "could",
    "when", "what", "which", "who", "how", "all", "out", "up", "about", "into",
    "than", "then", "them", "these", "those", "also", "more", "some", "any",
    "no", "yes", "do", "did", "does", "been", "were", "their", "me", "im",
    "ive", "dont", "doesnt", "cant", "wont", "product", "item", "amazon",
}

ASIN_RE = re.compile(
    r"(?:/dp/|/gp/product/|/product/|/gp/aw/d/|/d/|/product-reviews/|/gp/legacy/product/|/ASIN/)([a-zA-Z0-9]{10})",
    re.IGNORECASE,
)
ASIN_QUERY_RE = re.compile(r"[?&](?:asin|pd_rd_i|productId)=([a-zA-Z0-9]{10})", re.IGNORECASE)
ASIN_BARE_RE = re.compile(r"^[a-zA-Z0-9]{10}$")


def compile_theme_patterns() -> dict[str, re.Pattern]:
    compiled = {}
    for theme, keywords in THEMES.items():
        patterns = [r"\b" + re.escape(k.lower()) + r"\b" for k in keywords]
        compiled[theme] = re.compile("|".join(patterns), re.IGNORECASE)
    return compiled


COMPILED_THEMES = compile_theme_patterns()


def redact_pii(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]", text)
    text = re.sub(r"https?://\S+|www\.\S+", "[URL]", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)", "[PHONE]", text)
    text = re.sub(
        r"\b(?:order|order\s*id|tracking|tracking\s*id)\s*[:#-]?\s*[A-Z0-9-]{6,}\b",
        "[ORDER_ID]",
        text,
        flags=re.IGNORECASE,
    )
    return text


def classify_sentiment(score: float) -> str:
    if score >= 0.05:
        return "Positive"
    if score <= -0.05:
        return "Negative"
    return "Neutral"


POSITIVE_IDIOM_PATTERNS: list[tuple[re.Pattern, float, str]] = [
    (re.compile(r"\b(couldn['’]?t|could not|can['’]?t|cannot)\s+be\s+happier\b", re.I), 0.85, "Superlative satisfaction idiom ('couldn't be happier')"),
    (re.compile(r"\b(couldn['’]?t|could not|can['’]?t|cannot)\s+ask\s+for\s+(anything\s+)?more\b", re.I), 0.80, "High praise idiom ('couldn't ask for more')"),
    (re.compile(r"\b(can['’]?t|cannot|hard to|nothing to)\s+complain\b", re.I), 0.65, "Praise idiom ('can't complain')"),
    (re.compile(r"\b(can['’]?t|cannot|hard to|tough to)\s+be\s+beat\b", re.I), 0.80, "Praise idiom ('can't be beat')"),
    (re.compile(r"\b(can['’]?t|cannot)\s+beat\b", re.I), 0.75, "Praise idiom ('can't beat')"),
    (re.compile(r"\bsecond\s+to\s+none\b", re.I), 0.85, "Superlative praise ('second to none')"),
    (re.compile(r"\b(cannot|can['’]?t)\s+recommend\s+(it\s+|this\s+)?enough\b", re.I), 0.85, "Superlative recommendation ('cannot recommend enough')"),
    (re.compile(r"\b(no|zero)\s+regrets?\b", re.I), 0.75, "High satisfaction ('no regrets')"),
    (re.compile(r"\b(never|not|hasn['’]?t|doesn['’]?t|does not)\s+disappoint(ed)?\b", re.I), 0.75, "Consistent quality praise ('never disappoints')"),
    (re.compile(r"\bnot\s+bad(\s+at\s+all)?\b", re.I), 0.50, "Affirmative satisfaction ('not bad at all')"),
    (re.compile(r"\bworth\s+every\s+(penny|cent|dollar|rupee|dime)\b", re.I), 0.85, "Maximum price-to-value satisfaction"),
    (re.compile(r"\bexceeded\s+(all\s+my\s+|my\s+)?expectations\b", re.I), 0.85, "High satisfaction ('exceeded expectations')"),
    (re.compile(r"\bblown\s+away\b", re.I), 0.80, "High delight ('blown away')"),
    (re.compile(r"\bworks\s+like\s+a\s+charm\b", re.I), 0.80, "Reliability praise ('works like a charm')"),
    (re.compile(r"\b(no|zero|without\s+any)\s+(negative\s+feedback|issues?|problems?|complaints?|hassle)\b", re.I), 0.70, "Absence of problems ('no negative feedback / no issues')"),
]

NEGATIVE_COMPLAINT_PATTERNS: list[tuple[re.Pattern, float, str]] = [
    (re.compile(r"\b(cheaply\s+made|cheap\s+material|feels\s+cheap|poor\s+quality|flimsy(\s+build|\s+feel)?)\b", re.I), -0.65, "Defective/flimsy build quality complaint"),
    (re.compile(r"\b(overpriced|too\s+expensive(\s+for)?|not\s+worth\s+(the|it|any|what)|waste\s+of\s+money|waste\s+of\s+cash|rip\s*off)\b", re.I), -0.70, "Severe price-to-value complaint"),
    (re.compile(r"\b(stopped\s+working|quit\s+working|died\s+after|broke\s+(within|after|on)|stopped\s+charging|no\s+longer\s+works)\b", re.I), -0.75, "Critical hardware breakdown"),
    (re.compile(r"\b(subpar|garbage|trash|horrible|terrible|worthless|useless)\b", re.I), -0.75, "Extreme product dissatisfaction"),
    (re.compile(r"\bdo\s+not\s+buy\b", re.I), -0.80, "Explicit warning not to purchase"),
    (re.compile(r"\bavoid\s+(this|at\s+all\s+costs?)\b", re.I), -0.80, "Buyer warning to avoid"),
    (re.compile(r"\b(if\s+i\s+could\s+(leave|give)\s+0\s+stars|wish\s+i\s+could\s+give\s+0\s+stars|zero\s+stars?|0\s+stars?)\b", re.I), -0.85, "Zero star complaint ('would give 0 stars')"),
    (re.compile(r"\b(did\s+not\s+work|didn['’]?t\s+work|does\s+not\s+work|doesn['’]?t\s+work|ruined)\b", re.I), -0.75, "Functional failure ('did not work / ruined')"),
]

SARCASM_IRONY_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(great|wonderful|perfect|nice|expensive|best|handy|fancy|lovely)\s+(paperweight|doorstop|brick|coaster|ornament)\b", re.I), "Mocking product failure as paperweight/doorstop"),
    (re.compile(r"\b(love|great)\s+how\s+it\s+(broke|died|stopped|quit|overheated|cracked|melted)\b", re.I), "Cynical praise ('love how it broke/died')"),
    (re.compile(r"\b(10/10|five\s+stars?|5\s+stars?)\s+if\s+you\s+(like|want|enjoy)\s+(throwing|wasting|burning)\b", re.I), "Ironic review ('10/10 if you want to waste money')"),
    (re.compile(r"\b(works|lasted)\s+for\s+a\s+whole\s+\d+\s*(minute|hour|day)s?\b", re.I), "Sarcastic longevity ('worked for a whole X minutes')"),
    (re.compile(r"\bthanks\s+for\s+nothing\b", re.I), "Bitter ironic sign-off"),
    (re.compile(r"\bwhat\s+a\s+joke\b", re.I), "Derisive cynicism ('what a joke')"),
    (re.compile(r"\b(genius|great)\s+engineering\s*(/s|\.|\!)\b", re.I), "Sarcastic engineering comment"),
    (re.compile(r"\bif\s+you\s+call\s+this\s+(quality|working|durable)\b", re.I), "Cynical quality questioning"),
]

VISIBILITY_HIJACK_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(giving|rated?|stars?)\s*5\s*stars?\s*(so|to)\s*(this|it)\s*(gets?|stays?)\s*(seen|at\s*the\s*top|noticed)\b", re.I),
    re.compile(r"\b5\s*stars?\s*for\s*visibility\b", re.I),
]

LOGISTICS_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(delivery|courier|fedex|ups|shipping|transit|carrier|package|box)\b", re.I),
]

LOGISTICS_DAMAGE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(crushed|dented|damaged\s+box|arrived\s+late|delayed|lost\s+in\s+transit|took\s+\d+\s*weeks?)\b", re.I),
]


def calibrate_sentiment_score(text: str, raw_score: float) -> tuple[float, str, bool, list[str]]:
    """
    Calibrates VADER raw compound score by adjusting for:
    1. Positive negation idioms ("couldn't be happier", "can't complain", etc.)
    2. Subtle complaints and quality criticisms ("cheaply made", "overpriced", etc.)
    3. Sarcastic mockery ("great paperweight", "love how it died", etc.)
    4. 5-star visibility hijacking alerts.

    Returns: (calibrated_score, sentiment_label, is_sarcasm, detected_signals)
    """
    if not text:
        return raw_score, classify_sentiment(raw_score), False, []

    adjusted = raw_score
    notes = []
    is_sarcasm = False

    # Check for sarcasm first (sarcasm inverts apparent positive words to negative)
    for pat, desc in SARCASM_IRONY_PATTERNS:
        if pat.search(text):
            adjusted = -0.75
            is_sarcasm = True
            notes.append(f"Sarcasm: {desc}")
            break

    # Visibility hijacking: rated 5-star to warn buyers
    for pat in VISIBILITY_HIJACK_PATTERNS:
        if pat.search(text):
            adjusted = -0.80
            notes.append("Visibility hijack alert")
            break

    if not is_sarcasm:
        # Check positive idioms
        for pat, val, desc in POSITIVE_IDIOM_PATTERNS:
            if pat.search(text):
                # Ensure it's not followed by a harsh contrast like 'until it broke'
                if not re.search(r"\b(until|before)\s+it\s+(broke|died|stopped)\b", text, re.I):
                    if adjusted < val:
                        adjusted = val
                    notes.append(desc)

        # Check negative patterns
        for pat, val, desc in NEGATIVE_COMPLAINT_PATTERNS:
            if pat.search(text):
                if adjusted > val:
                    adjusted = val
                notes.append(desc)

    label = classify_sentiment(adjusted)
    return adjusted, label, is_sarcasm, notes


def extract_asin(url: str) -> str | None:
    if not url:
        return None
    cleaned = url.strip()
    if ASIN_BARE_RE.match(cleaned):
        return cleaned.upper()
    m = ASIN_RE.search(cleaned) or ASIN_QUERY_RE.search(cleaned)
    return m.group(1).upper() if m else None


def infer_category_from_text(text: str) -> str | None:
    t = (text or "").lower()
    mapping = [
        ("refrigerator", "Appliances · Refrigerators"),
        ("fridge", "Appliances · Refrigerators"),
        ("freezer", "Appliances · Refrigerators"),
        ("washing machine", "Appliances · Washing Machines"),
        ("washer", "Appliances · Washing Machines"),
        ("air conditioner", "Appliances · Air Conditioners"),
        ("microwave", "Appliances · Kitchen"),
        ("oven", "Appliances · Kitchen"),
        ("kitchen", "Appliances · Kitchen"),
        ("television", "Electronics · Smart TVs"),
        ("oled", "Electronics · Smart TVs"),
        ("qled", "Electronics · Smart TVs"),
        ("tv", "Electronics · Smart TVs"),
        ("smartphone", "Electronics · Mobile Phones"),
        ("phone", "Electronics · Mobile Phones"),
        ("laptop", "Computers & Laptops"),
        ("macbook", "Computers & Laptops"),
        ("notebook", "Computers & Laptops"),
        ("fashion", "Amazon Fashion"),
        ("clothing", "Amazon Fashion"),
        ("shoe", "Fashion · Footwear"),
        ("sneaker", "Fashion · Footwear"),
        ("music", "Digital Music"),
        ("mp3", "Digital Music"),
        ("craft", "Arts, Crafts and Sewing"),
        ("sewing", "Arts, Crafts and Sewing"),
        ("headphone", "Electronics · Audio"),
        ("earphone", "Electronics · Audio"),
        ("earbud", "Electronics · Audio"),
        ("battery", "Electronics · Mobile Power"),
        ("power bank", "Electronics · Mobile Power"),
        ("electronic", "Electronics"),
    ]
    for needle, cat in mapping:
        if needle in t:
            return cat
    return None


def match_themes(text: str) -> list[str]:
    if not text:
        return []
    return [theme for theme, rx in COMPILED_THEMES.items() if rx.search(text)]


def count_phrases(texts: Iterable[str], phrase_groups: list[tuple[str, list[str]]]) -> list[dict]:
    docs = [str(t).lower() for t in texts]
    n = max(len(docs), 1)
    rows = []
    for label, keys in phrase_groups:
        hits = sum(any(k in doc for k in keys) for doc in docs)
        rows.append({
            "phrase": label,
            "count": hits,
            "pct_of_reviews": round(100.0 * hits / n, 2),
        })
    rows.sort(key=lambda r: r["count"], reverse=True)
    return rows


# =========================================================
# DYNAMIC CATEGORY TAXONOMY & ATTRIBUTE EVALUATION SYSTEM
# =========================================================

CATEGORY_TAXONOMY: dict[str, dict] = {
    "audio_headphones": {
        "key": "audio_headphones",
        "name": "Audio & Headphones",
        "icon": "🎧",
        "description": "Headphones, earbuds, speakers, headsets, soundbars, and acoustic hardware.",
        "detection_keywords": [
            "headphone", "headphones", "earphone", "earphones", "earbuds", "earbud",
            "soundbar", "speaker", "speakers", "audio", "headset", "earpiece", "in-ear",
            "over-ear", "on-ear", "anc", "subwoofer", "wh-1000", "airpods", "iem", "tws",
            "acoustic", "drivers", "ear tips", "headband"
        ],
        "attributes": [
            "Sound Quality & Bass",
            "Comfort & Ergonomics",
            "Battery & Charging",
            "Connectivity & Bluetooth",
            "Noise Cancellation (ANC)",
            "Microphone & Calls",
            "Build & Durability",
            "Price & Value",
        ],
        "attribute_lexicons": {
            "Sound Quality & Bass": [
                "sound quality", "audio quality", "bass", "treble", "vocals", "clarity",
                "crisp sound", "distortion", "muddy", "tinny", "low volume", "loud", "soundstage", "mids"
            ],
            "Comfort & Ergonomics": [
                "comfortable", "comfort", "hurts ears", "ear pain", "ear cups", "headband",
                "clamp force", "ear tips", "lightweight", "heavy on head", "fatigue", "ear cushion"
            ],
            "Battery & Charging": [
                "battery", "battery life", "charging", "charger", "usb-c", "battery drain",
                "dies quickly", "playtime", "fast charge", "battery lasts", "case battery"
            ],
            "Connectivity & Bluetooth": [
                "bluetooth", "pairing", "connect", "disconnects", "cutting out", "dropouts",
                "latency", "audio lag", "multipoint", "range", "reconnect", "signal"
            ],
            "Noise Cancellation (ANC)": [
                "noise cancellation", "anc", "noise cancelling", "ambient mode", "transparency",
                "blocks noise", "wind noise", "isolation", "background noise"
            ],
            "Microphone & Calls": [
                "microphone", "mic", "call quality", "phone calls", "voice clarity", "muffled mic",
                "recipient couldn't hear", "mic cuts out"
            ],
            "Build & Durability": [
                "build quality", "hinge", "cracked", "snapped", "plastic", "sturdy", "durable",
                "feels premium", "feels cheap", "materials", "wear and tear"
            ],
            "Price & Value": [
                "price", "cost", "expensive", "good value", "worth it", "overpriced", "affordable", "deal"
            ],
        },
        "complaint_phrases": [
            ("Connectivity dropouts", ["disconnects", "connection drops", "cutting out", "bluetooth issue", "won't pair", "pairing issue"]),
            ("Ear fatigue / tight clamp", ["hurts ears", "too tight", "headband clamp", "ear pain", "uncomfortable"]),
            ("Rapid battery drain", ["battery dies", "drains quickly", "poor battery", "doesn't last", "battery life is short"]),
            ("ANC hiss or weak isolation", ["anc is weak", "wind noise", "hissing sound", "doesn't block noise", "weak noise cancellation"]),
        ],
        "praise_phrases": [
            ("Acoustic clarity & deep bass", ["great sound", "crisp audio", "punchy bass", "clear vocals", "amazing sound", "sound quality"]),
            ("All-day listening comfort", ["very comfortable", "lightweight", "soft ear cushions", "no ear fatigue", "fits well"]),
            ("Seamless device pairing", ["paired instantly", "multipoint works great", "reliable bluetooth", "easy to connect"]),
            ("Long-lasting battery life", ["battery lasts days", "quick charge", "impressive battery life", "long battery"]),
        ],
    },
    "apparel_clothing": {
        "key": "apparel_clothing",
        "name": "Apparel & Clothing",
        "icon": "👕",
        "description": "T-shirts, shirts, hoodies, jackets, pants, dresses, sportswear, and fashion apparel.",
        "detection_keywords": [
            "shirt", "t-shirt", "tshirt", "tee", "hoodie", "jacket", "pants", "trousers", "jeans",
            "dress", "cotton", "polyester", "fabric", "cloth", "garment", "wear", "apparel",
            "sweater", "shorts", "sweatshirt", "top", "sleeve", "collar", "underwear", "boxer",
            "knit", "fleece", "crewneck", "v-neck",
            # Fits, washes and denim vocabulary (titles often omit the garment noun)
            "denim", "baggy", "baggy fit", "loose fit", "slim fit", "skinny fit", "straight fit",
            "relaxed fit", "regular fit", "tapered fit", "bootcut", "heavy washed", "stone washed",
            "acid wash", "mid rise", "high rise", "low rise", "fashion", "clothing",
            # Common garment types incl. Indian ethnic wear
            "chinos", "cargo", "cargos", "joggers", "track pants", "trackpants", "tracksuit",
            "leggings", "jeggings", "blazer", "coat", "waistcoat", "polo", "kurta", "kurti",
            "saree", "sari", "lehenga", "dupatta", "salwar", "pyjama", "pajama", "nightwear",
            "innerwear", "lingerie", "vest", "shrug", "cardigan", "skirt", "jumpsuit"
        ],
        "attributes": [
            "Fabric & Material Quality",
            "Fit & Sizing Accuracy",
            "Comfort & Breathability",
            "Stitching & Seam Durability",
            "Wash Care & Shrinkage",
            "Color & Visual Style",
            "Price & Value",
            "Packaging & Delivery",
        ],
        "attribute_lexicons": {
            "Fabric & Material Quality": [
                "fabric", "material", "cotton", "polyester", "linen", "thin fabric", "thick material",
                "see through", "feels cheap", "high quality cloth", "soft material", "rough fabric", "breathable", "pure cotton"
            ],
            "Fit & Sizing Accuracy": [
                "fit", "sizing", "size", "runs small", "runs large", "true to size", "too tight", "too loose",
                "baggy", "length", "sleeves", "shoulder fit", "chest fit", "slim fit", "boxy", "size chart"
            ],
            "Comfort & Breathability": [
                "comfortable", "comfort", "soft on skin", "itchy", "scratchy", "breathable", "sweaty",
                "lightweight", "cozy", "tagless", "skin irritation", "feels good"
            ],
            "Stitching & Seam Durability": [
                "stitching", "stitch", "seam", "seams", "loose threads", "hem", "ripped", "tore", "hole",
                "tear", "unraveled", "durable", "sturdy stitching"
            ],
            "Wash Care & Shrinkage": [
                "shrink", "shrunk", "shrank", "after wash", "dryer", "wash cycle", "bleeding color",
                "color faded after wash", "wrinkles", "hand wash", "machine wash", "pilling", "lint"
            ],
            "Color & Visual Style": [
                "color", "colour", "shade", "print", "graphic", "faded", "looks like picture",
                "vibrant", "dull color", "stylish", "pattern", "design", "look"
            ],
            "Price & Value": [
                "price", "cost", "good value", "worth the money", "cheap quality", "overpriced",
                "affordable", "great value for money", "bargain"
            ],
            "Packaging & Delivery": [
                "packaging", "shipping", "delivery", "arrived on time", "fast shipping", "sealed package", "wrinkled in package"
            ],
        },
        "complaint_phrases": [
            ("Shrunk significantly after washing", ["shrunk", "shrank in wash", "shrunk in dryer", "unwearable after wash", "shrinkage"]),
            ("Inaccurate sizing (runs small/tight)", ["runs small", "runs very small", "size chart inaccurate", "too tight", "too short"]),
            ("Loose threads & weak seams", ["loose threads", "seam came undone", "stitching ripped", "unraveled", "poor stitching"]),
            ("Thin or see-through fabric", ["very thin", "see through", "cheap fabric", "rough material", "scratchy", "low quality cloth"]),
            ("Color fading / bleeding after wash", ["color faded", "colour faded", "faded after", "color bleeding", "colour bleeding", "bleeds color", "lost its color", "fading"]),
            ("Fit too loose / inconsistent sizing", ["too loose", "too big", "runs large", "size mismatch", "wrong size", "not as per size", "waist is loose", "length is too long"]),
            ("Zipper, button or hardware defects", ["zipper broke", "zip broke", "zipper stuck", "button fell", "button came off", "broken button", "missing button"]),
            ("Product differs from photos", ["not as shown", "different from picture", "different from image", "colour is different", "color is different", "not same as picture", "looks different"]),
            ("Overpriced for the quality", ["overpriced", "too expensive", "not worth the price", "waste of money", "not worth it"]),
            ("Late delivery / damaged parcel", ["late delivery", "delivered late", "arrived late", "delivery delay", "damaged package", "torn packet"]),
        ],
        "praise_phrases": [
            ("Ultra-soft & comfortable fabric", ["super soft", "great fabric", "feels amazing on skin", "breathable cotton", "comfortable"]),
            ("True to size & flattering fit", ["fits perfectly", "true to size", "great fit", "flattering cut", "fits as expected"]),
            ("Maintains shape & color after wash", ["didn't shrink", "washed well", "colors stay vibrant", "no fading", "holds shape"]),
            ("Great quality for the price", ["great value", "worth the price", "affordable price", "worth every penny"]),
        ],
    },
    "footwear_shoes": {
        "key": "footwear_shoes",
        "name": "Footwear & Shoes",
        "icon": "👟",
        "description": "Sneakers, running shoes, athletic footwear, boots, sandals, and formal shoes.",
        "detection_keywords": [
            "shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "sandal", "sandals",
            "footwear", "running shoe", "heel", "sole", "insole", "arch support", "cleats", "loafer",
            "outsole", "slippers", "clogs"
        ],
        "attributes": [
            "Cushioning & Underfoot Comfort",
            "Fit & Width Sizing",
            "Traction & Outsole Grip",
            "Durability & Sole Integrity",
            "Breathability & Temperature",
            "Style & Aesthetics",
            "Price & Value",
            "Packaging & Delivery",
        ],
        "attribute_lexicons": {
            "Cushioning & Underfoot Comfort": [
                "cushion", "cushioning", "comfortable", "insole", "midsole", "arch support", "heel pain",
                "blister", "walking all day", "standing all day", "cloud", "shock absorption", "foot pain"
            ],
            "Fit & Width Sizing": [
                "fit", "size", "sizing", "true to size", "toe box", "narrow", "wide feet", "tight toe",
                "half size small", "half size large", "heel slip", "snug fit"
            ],
            "Traction & Outsole Grip": [
                "traction", "grip", "slippery", "slip resistant", "outsole", "rubber sole", "wet surfaces",
                "skid", "non-slip", "tread"
            ],
            "Durability & Sole Integrity": [
                "durability", "sole detached", "glue peeling", "tread wore off", "ripped mesh",
                "fell apart", "long lasting", "sturdy", "holds up", "broke down"
            ],
            "Breathability & Temperature": [
                "breathable", "mesh", "sweaty feet", "hot feet", "air circulation", "lightweight", "heavy shoe"
            ],
            "Style & Aesthetics": [
                "looks great", "stylish", "design", "colorway", "appearance", "sleek", "compliments"
            ],
            "Price & Value": [
                "price", "worth the money", "expensive", "affordable", "overpriced", "good value"
            ],
            "Packaging & Delivery": [
                "box", "shoebox crushed", "delivery", "shipping", "fast arrival"
            ],
        },
        "complaint_phrases": [
            ("Sole detached or wore out quickly", ["sole separated", "sole fell off", "tread wore down", "glue coming apart", "sole broke"]),
            ("Blisters & heel rubbing", ["gave me blisters", "rubs heel", "painful to walk", "stiff heel counter", "blister"]),
            ("Narrow / cramped toe box", ["too narrow", "cramped toes", "pinches foot", "runs half size small", "toe box tight"]),
            ("Slippery on wet ground", ["no grip", "slippery on wet", "slid on tile", "poor traction", "slippery"]),
        ],
        "praise_phrases": [
            ("All-day walking comfort", ["walk all day", "like walking on clouds", "great arch support", "zero foot pain", "comfortable"]),
            ("Solid grip & stable traction", ["excellent grip", "solid traction", "stable rubber outsole", "non-slip"]),
            ("Perfect true-to-size fit", ["fits like a glove", "true to size", "plenty of toe room", "fits well"]),
            ("Stylish design & compliments", ["looks great", "stylish sneaker", "get compliments", "sharp look"]),
        ],
    },
    "electronics_computing": {
        "key": "electronics_computing",
        "name": "Electronics & Computing",
        "icon": "💻",
        "description": "Laptops, smartphones, tablets, monitors, smartwatches, computer components, and office tech.",
        "detection_keywords": [
            "laptop", "computer", "notebook", "pc", "macbook", "smartphone", "phone", "tablet",
            "ipad", "monitor", "screen", "keyboard", "mouse", "gpu", "cpu", "processor", "ram",
            "smartwatch", "desktop", "charger", "power bank", "gadget"
        ],
        "attributes": [
            "Display & Screen Quality",
            "Performance & Processing Speed",
            "Battery Life & Thermals",
            "Build Quality & Chassis",
            "Software & Operating System",
            "Ports & Connectivity",
            "Price & Value",
        ],
        "attribute_lexicons": {
            "Display & Screen Quality": [
                "display", "screen", "resolution", "colors", "brightness", "refresh rate", "oled", "pixel", "glare", "viewing angle"
            ],
            "Performance & Processing Speed": [
                "speed", "fast", "lag", "freezes", "snappy", "multitasking", "gaming", "ram", "processor", "boot time", "slow"
            ],
            "Battery Life & Thermals": [
                "battery", "battery life", "overheating", "hot", "fan noise", "charger", "fast charging", "battery drain", "thermals"
            ],
            "Build Quality & Chassis": [
                "build quality", "metal chassis", "plastic feel", "hinge", "keyboard feel", "trackpad", "sturdy", "premium feel"
            ],
            "Software & Operating System": [
                "software", "os", "windows", "macos", "android", "bloatware", "crashes", "bugs", "glitches", "updates"
            ],
            "Ports & Connectivity": [
                "wifi", "bluetooth", "ports", "usb-c", "hdmi", "webcam", "speakers", "dongle", "connectivity"
            ],
            "Price & Value": [
                "price", "specs for the price", "value", "expensive", "affordable", "overpriced", "worth it"
            ],
        },
        "complaint_phrases": [
            ("Thermal throttling / fan noise", ["overheating", "gets very hot", "loud fan", "fan constantly running", "hot to touch"]),
            ("System freezes or software lag", ["freezes", "lags", "sluggish", "slow performance", "crashed"]),
            ("Disappointing battery endurance", ["battery dies fast", "poor battery life", "must stay plugged in", "short battery"]),
            ("Chassis / hinge build defects", ["broken hinge", "flimsy build", "cheap plastic feel", "trackpad rattle"]),
        ],
        "praise_phrases": [
            ("Blazing fast & smooth performance", ["blazing fast", "very fast", "snappy performance", "handles heavy load", "smooth"]),
            ("Vibrant, high-resolution screen", ["gorgeous display", "crisp screen", "bright display", "vibrant colors"]),
            ("Solid premium aluminum chassis", ["premium build", "solid metal chassis", "well built", "sturdy"]),
            ("All-day battery efficiency", ["all day battery", "great battery life", "lasts entire work day"]),
        ],
    },
    "home_kitchen": {
        "key": "home_kitchen",
        "name": "Home & Kitchen Appliances",
        "icon": "🍳",
        "description": "Air fryers, blenders, coffee makers, vacuum cleaners, microwaves, cookware, and home goods.",
        "detection_keywords": [
            "fryer", "air fryer", "blender", "coffee", "vacuum", "cookware", "pan", "pot", "kitchen",
            "appliance", "microwave", "toaster", "kettle", "knife", "grill", "refrigerator", "oven",
            "cooker", "dishwasher", "mixer"
        ],
        "attributes": [
            "Cooking & Performance",
            "Ease of Cleaning",
            "Controls & Ease of Use",
            "Noise Level & Operation",
            "Build Quality & Durability",
            "Size & Countertop Footprint",
            "Price & Value",
        ],
        "attribute_lexicons": {
            "Cooking & Performance": [
                "cooking", "cooks evenly", "crispy", "heating", "blends smoothly", "suction power", "works fast", "temperature", "power"
            ],
            "Ease of Cleaning": [
                "easy to clean", "cleaning", "dishwasher safe", "non-stick", "residue", "hard to clean", "grease", "wipes down"
            ],
            "Controls & Ease of Use": [
                "easy to use", "simple controls", "presets", "digital display", "buttons", "intuitive", "instructions", "timer"
            ],
            "Noise Level & Operation": [
                "noise", "loud", "quiet", "motor noise", "humming", "rattling", "quiet motor", "silent"
            ],
            "Build Quality & Durability": [
                "build quality", "sturdy", "durable", "broke after months", "plastic smell", "smoke", "leaks", "well built"
            ],
            "Size & Countertop Footprint": [
                "size", "capacity", "counter space", "compact", "bulky", "fits on counter", "basket size", "fits easily"
            ],
            "Price & Value": [
                "price", "worth the money", "saves time", "expensive", "affordable", "overpriced", "good value"
            ],
        },
        "complaint_phrases": [
            ("Difficult to clean / coating peeled", ["hard to clean", "coating peeled", "food sticks", "hand wash only", "burnt on residue"]),
            ("Loud or vibrating motor noise", ["extremely loud", "loud motor", "rattling noise", "unbearable sound"]),
            ("Stopped heating or working early", ["stopped heating", "died after a month", "quit working", "element broke", "defective"]),
            ("Strong burning plastic odor", ["plastic smell", "burnt odor", "smoke came out", "chemical smell"]),
        ],
        "praise_phrases": [
            ("Cooks evenly & crisps food perfectly", ["cooks evenly", "crispy results", "delicious food", "heats quickly", "works amazing"]),
            ("Effortless non-stick cleaning", ["so easy to clean", "dishwasher safe", "wipes clean in seconds", "non stick works great"]),
            ("Intuitive one-touch controls", ["easy to use", "simple presets", "intuitive buttons", "clear digital display"]),
            ("Saves time & kitchen countertop space", ["saves time", "compact footprint", "fits counter nicely", "daily essential"]),
        ],
    },
    "beauty_personal_care": {
        "key": "beauty_personal_care",
        "name": "Beauty & Personal Care",
        "icon": "✨",
        "description": "Skincare, moisturizers, serums, shampoos, cosmetics, perfumes, and grooming items.",
        "detection_keywords": [
            "skin", "skincare", "cream", "lotion", "serum", "moisturizer", "shampoo", "conditioner",
            "soap", "face wash", "makeup", "cosmetics", "sunscreen", "perfume", "fragrance", "cleanser",
            "oil", "acne", "hair", "lipstick"
        ],
        "attributes": [
            "Effectiveness & Visible Results",
            "Skin Tolerance & Safety",
            "Texture & Absorption",
            "Fragrance & Scent",
            "Packaging & Dispenser",
            "Price & Value",
        ],
        "attribute_lexicons": {
            "Effectiveness & Visible Results": [
                "results", "effective", "hydrating", "glowing skin", "cleared acne", "wrinkles", "soft skin", "moisturized", "visible difference"
            ],
            "Skin Tolerance & Safety": [
                "breakout", "irritation", "burning", "allergic reaction", "redness", "gentle", "sensitive skin", "safe", "rash"
            ],
            "Texture & Absorption": [
                "texture", "absorbs quickly", "lightweight", "non-greasy", "sticky", "oily residue", "thick cream", "smooth finish"
            ],
            "Fragrance & Scent": [
                "fragrance", "scent", "smells good", "strong perfume", "unscented", "chemical smell", "pleasant smell", "odor"
            ],
            "Packaging & Dispenser": [
                "pump", "bottle", "leaks", "dropper", "dispenser", "sealed", "easy to apply", "jar", "packaging"
            ],
            "Price & Value": [
                "price", "bottle lasted", "expensive", "affordable", "worth the price", "good value for size"
            ],
        },
        "complaint_phrases": [
            ("Caused skin breakout / irritation", ["caused breakout", "irritated skin", "burning sensation", "redness", "broke me out"]),
            ("Greasy or sticky residue", ["too greasy", "sticky feeling", "heavy on skin", "leaves oily film", "doesn't absorb"]),
            ("Overwhelming chemical fragrance", ["too strong scent", "artificial perfume", "overpowering smell", "chemical fragrance"]),
            ("Defective pump or leaky bottle", ["pump broke", "bottle leaked in transit", "dispenser doesn't work", "cap cracked"]),
        ],
        "praise_phrases": [
            ("Noticeable skin improvement & hydration", ["glowing skin", "deeply hydrating", "cleared my skin", "visible results", "smoother"]),
            ("Lightweight & fast absorbing", ["absorbs immediately", "non-greasy", "lightweight texture", "feels weightless"]),
            ("Gentle on sensitive skin", ["no irritation", "gentle formula", "great for sensitive skin", "no breakouts"]),
            ("Pleasant subtle scent", ["smells divine", "subtle fragrance", "unscented and clean", "delightful aroma"]),
        ],
    },
    "software_apps": {
        "key": "software_apps",
        "name": "Software & Digital Apps",
        "icon": "📱",
        "description": "Mobile applications, SaaS tools, productivity software, and digital services.",
        "detection_keywords": [
            "app", "software", "application", "ui", "login", "download", "saas", "platform",
            "subscription", "update", "mobile app", "desktop app", "website", "account", "tool"
        ],
        "attributes": [
            "UI & Navigation Experience",
            "Reliability & Bug Stability",
            "Speed & Responsiveness",
            "Features & Integrations",
            "Customer Support & Updates",
            "Pricing & Subscription Value",
        ],
        "attribute_lexicons": {
            "UI & Navigation Experience": [
                "ui", "interface", "intuitive", "easy to navigate", "confusing layout", "clean design", "modern look", "user experience"
            ],
            "Reliability & Bug Stability": [
                "crashes", "bugs", "glitches", "freezes", "loading error", "server down", "sync issue", "stable", "login error"
            ],
            "Speed & Responsiveness": [
                "speed", "fast", "responsive", "laggy", "battery drain", "slow load", "performance", "smooth"
            ],
            "Features & Integrations": [
                "features", "integration", "missing feature", "workflow", "customization", "automation", "export", "capability"
            ],
            "Customer Support & Updates": [
                "customer support", "support team", "response time", "resolved ticket", "update broke", "release notes"
            ],
            "Pricing & Subscription Value": [
                "subscription", "price", "monthly cost", "free tier", "paywall", "expensive", "good value", "overpriced"
            ],
        },
        "complaint_phrases": [
            ("Frequent app crashes or login bugs", ["app crashes", "keeps freezing", "login error", "buggy update", "sync failed"]),
            ("Aggressive paywalls / pricey tiers", ["expensive subscription", "locked behind paywall", "overpriced", "no free tier"]),
            ("Cluttered or confusing user interface", ["confusing navigation", "cluttered ui", "hard to find settings", "steep learning curve"]),
            ("Slow or unhelpful support", ["support never replied", "unhelpful agents", "ticket ignored", "poor customer support"]),
        ],
        "praise_phrases": [
            ("Clean, intuitive, and modern UI", ["beautiful interface", "intuitive to use", "clean layout", "seamless user experience"]),
            ("Reliable rock-solid performance", ["never crashes", "super reliable", "smooth performance", "fast loading"]),
            ("Powerful features & seamless sync", ["great feature set", "syncs across devices effortlessly", "saves hours of work"]),
            ("Responsive and helpful support", ["support fixed it fast", "friendly customer service", "great developer team"]),
        ],
    },
    "general_consumer": {
        "key": "general_consumer",
        "name": "General Consumer Products",
        "icon": "📦",
        "description": "General consumer goods, household items, tools, and multi-category products.",
        "detection_keywords": [],
        "attributes": [
            "Quality & Craftsmanship",
            "Durability & Longevity",
            "Usability & Ease of Use",
            "Comfort & Design",
            "Price & Value",
            "Packaging & Shipping",
        ],
        "attribute_lexicons": {
            "Quality & Craftsmanship": [
                "build quality", "well made", "solid build", "poor quality", "flimsy", "craftsmanship", "materials", "premium feel"
            ],
            "Durability & Longevity": [
                "durable", "durability", "long lasting", "broke", "broken", "wear and tear", "reliable", "lasted"
            ],
            "Usability & Ease of Use": [
                "easy to use", "simple to use", "user friendly", "intuitive", "instructions", "hard to use"
            ],
            "Comfort & Design": [
                "comfortable", "comfort", "ergonomic", "lightweight", "design", "look", "fits well"
            ],
            "Price & Value": [
                "price", "cost", "expensive", "good value", "worth the money", "affordable", "overpriced"
            ],
            "Packaging & Shipping": [
                "packaging", "shipping", "delivery", "arrived on time", "fast shipping", "damaged box"
            ],
        },
        "complaint_phrases": [
            (label, kws) for label, kws in COMPLAINT_PHRASES
            if label not in ("Battery drains quickly", "Battery overheating", "Won't connect")
        ],
        "praise_phrases": [
            (label, kws) for label, kws in PRAISE_PHRASES
            if label not in ("Great sound", "Long battery life")
        ],
    },
}

_COMPILED_CATEGORY_ASPECTS_CACHE: dict[str, dict[str, re.Pattern]] = {}


def get_category_info(cat_key_or_name: str | None) -> dict:
    """Retrieve category definition dict by key or name, defaulting to general_consumer."""
    if not cat_key_or_name:
        return CATEGORY_TAXONOMY["general_consumer"]
    
    clean = str(cat_key_or_name).lower().strip()
    if clean in CATEGORY_TAXONOMY:
        return CATEGORY_TAXONOMY[clean]
    
    for key, data in CATEGORY_TAXONOMY.items():
        if clean in data["name"].lower() or data["name"].lower() in clean:
            return data
    
    return CATEGORY_TAXONOMY["general_consumer"]


def get_compiled_category_aspects(category_key: str) -> dict[str, re.Pattern]:
    """Returns precompiled regex patterns for all attributes of a category."""
    if category_key in _COMPILED_CATEGORY_ASPECTS_CACHE:
        return _COMPILED_CATEGORY_ASPECTS_CACHE[category_key]
    
    cat = get_category_info(category_key)
    compiled = {}
    for attr, kws in cat["attribute_lexicons"].items():
        pats = [r"\b" + re.escape(k.lower()) + r"\b" for k in kws]
        compiled[attr] = re.compile("|".join(pats), re.I)
    
    _COMPILED_CATEGORY_ASPECTS_CACHE[category_key] = compiled
    return compiled


def detect_product_category(title: str = "", reviews_text: str | list[str] = None, metadata_category: str = None) -> dict:
    """
    Intelligently identifies the product category using:
    1. Explicit metadata category (if provided)
    2. Product Title / Brand semantics
    3. Corpus vocabulary distribution across reviews
    Returns the resolved category definition with confidence and source.
    """
    # 1. Check explicit metadata category
    if metadata_category and isinstance(metadata_category, str):
        meta_low = metadata_category.lower()
        for key, cat in CATEGORY_TAXONOMY.items():
            if key == "general_consumer":
                continue
            if key in meta_low or cat["name"].lower() in meta_low:
                res = dict(cat)
                res["confidence"] = 0.98
                res["detection_source"] = f"Dataset Metadata ('{metadata_category}')"
                return res
            if any(k in meta_low for k in cat["detection_keywords"]):
                res = dict(cat)
                res["confidence"] = 0.95
                res["detection_source"] = f"Dataset Metadata ('{metadata_category}')"
                return res

    # 2. Check Product Title
    title_low = str(title or "").lower()
    if title_low:
        title_scores = {}
        for key, cat in CATEGORY_TAXONOMY.items():
            if key == "general_consumer":
                continue
            score = 0
            for kw in cat["detection_keywords"]:
                if re.search(r"\b" + re.escape(kw) + r"\b", title_low):
                    score += 3
                elif kw in title_low:
                    score += 1
            if score > 0:
                title_scores[key] = score
        
        if title_scores:
            best_key = max(title_scores.items(), key=lambda x: x[1])[0]
            res = dict(CATEGORY_TAXONOMY[best_key])
            res["confidence"] = 0.92
            res["detection_source"] = f"Product Title Keyword Match"
            return res

    # 3. Check Review Corpus Vocabulary
    if reviews_text:
        if isinstance(reviews_text, (list, tuple)):
            sample_str = " ".join(str(r) for r in reviews_text[:250]).lower()
        elif hasattr(reviews_text, "tolist"):
            sample_str = " ".join(str(r) for r in reviews_text.tolist()[:250]).lower()
        else:
            sample_str = str(reviews_text)[:15000].lower()
        corpus_scores = {}
        for key, cat in CATEGORY_TAXONOMY.items():
            if key == "general_consumer":
                continue
            matches = sum(sample_str.count(kw) for kw in cat["detection_keywords"][:12])
            if matches > 0:
                corpus_scores[key] = matches
        
        if corpus_scores:
            best_key, best_count = max(corpus_scores.items(), key=lambda x: x[1])
            if best_count >= 5:
                res = dict(CATEGORY_TAXONOMY[best_key])
                res["confidence"] = 0.85
                res["detection_source"] = f"Review Corpus Vocabulary Analysis ({best_count} signals)"
                return res

    # Fallback to general consumer
    fallback = dict(CATEGORY_TAXONOMY["general_consumer"])
    fallback["confidence"] = 0.60
    fallback["detection_source"] = "Universal Consumer Goods Baseline"
    return fallback

