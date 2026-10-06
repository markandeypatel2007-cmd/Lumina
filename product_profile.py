"""
Product Profiler & Specification Engine for Lumina.

Provides comprehensive product identity, model specifications, dimensions,
hardware attributes, and core functional capabilities.
"""

from __future__ import annotations

import re
from typing import Any
import pandas as pd
from lumina_config import detect_product_category, get_category_info

# Detailed specification profiles for benchmark and dataset products
KNOWN_PRODUCT_PROFILES: dict[str, dict[str, Any]] = {
    "Sony WH-1000XM5 Wireless Noise-Canceling Headphones": {
        "name": "Sony WH-1000XM5 Wireless Noise-Canceling Headphones",
        "brand": "Sony",
        "model": "WH-1000XM5",
        "asin": "B09XS7JWHH",
        "category": "Electronics · Audio / Premium ANC Headphones",
        "image": "https://m.media-amazon.com/images/I/61+elLndqVL._AC_SL1500_.jpg",
        "tagline": "Industry-leading active noise canceling headphones with Auto NC Optimizer, 30mm precision drivers, and 30-hour battery life.",
        "description": "The Sony WH-1000XM5 wireless noise-canceling headphones set a new standard for distraction-free listening and exceptional calling clarity. Equipped with two processors controlling eight microphones, an Auto NC Optimizer for automatically optimizing noise canceling based on wearing conditions and environment, and a specially designed 30mm driver unit.",
        "functions": [
            "Industry-Leading Noise Cancellation: Two processors control 8 microphones for unprecedented noise cancellation.",
            "Magnificent Sound Engineering: Specially designed 30mm driver unit with carbon fiber composite TPU edge.",
            "Crystal-Clear Hands-Free Calling: 4 beamforming microphones with AI-based noise reduction algorithms.",
            "Multipoint Device Connection: Seamlessly switch between two Bluetooth devices simultaneously.",
        ],
        "specs": {
            "Form Factor": "Over-Ear, Closed Back",
            "Weight": "250 grams (8.8 oz)",
            "Power / Battery": "Up to 30 hours (ANC On) / 40 hours (ANC Off)",
            "Charging": "USB-C Quick Charge (3 min = 3 hours playback)",
            "Connectivity": "Bluetooth 5.2 (LDAC, AAC, SBC), 3.5mm Aux",
            "Drivers": "30mm dome type carbon fiber composite",
            "Microphones": "8 microphones with AI beamforming",
        },
        "target_audience": "Frequent flyers, remote professionals, commuters, and audiophiles seeking premier noise isolation.",
    },
    "Koss Porta Pro Classic Headphones (B00004T8R2)": {
        "name": "Koss Porta Pro Classic On-Ear Portable Headphones",
        "brand": "Koss",
        "model": "Porta Pro Classic",
        "asin": "B00004T8R2",
        "category": "Electronics · Audio / Portable Headphones",
        "image": "https://m.media-amazon.com/images/I/71Y3yQ2oTXL._AC_SL1500_.jpg",
        "tagline": "Legendary lightweight on-ear portable headphones renowned for deep bass and retro 1984 acoustic tuning.",
        "description": "The acclaimed Koss Porta Pro has set performance and comfort standards for personal listening worldwide since 1984. Engineered with dynamic elements and oxygen-free copper voice coils, it delivers rich bass and remarkably wide frequency response (15-25,000 Hz). Features adjustable ComfortZone temporal pads to relieve pressure on the ears, and a collapsible design with locking ring for pocket portability.",
        "functions": [
            "Dynamic High-Fidelity Audio: Oxygen-free copper voice coils delivering 15-25,000 Hz frequency response with punchy bass.",
            "ComfortZone Temporal Pad Adjustment: Three-position switch shifts headband pressure between firm and light for customized comfort.",
            "Collapsible Portability: Iconic folding design with integrated locking ring folds into a pocket-sized bundle.",
            "Acoustic Semi-Open Design: Delivers wide stereo imaging while allowing natural situational awareness.",
        ],
        "specs": {
            "Form Factor": "On-Ear, Semi-Open Back",
            "Dimensions": "6.75 x 2.0 x 9.0 inches (Folds flat into 3.5-inch circle)",
            "Weight": "60 grams (2.1 oz) — Featherweight spring steel headband",
            "Power / Battery": "Passive wired (Zero battery required, always ready)",
            "Connectivity / Cord": "3.5 mm gold-plated audio jack, 4-foot (1.2 m) flexible straight cable",
            "Drivers / Impedance": "Mylar drivers, 60 ohms impedance, 101 dB SPL sensitivity",
            "Materials": "Tempered spring steel headband, ABS plastic hinge, replaceable poly-foam ear cushions",
            "Fit & Sizing": "Universal adjustable headband with dual temporal comfort pads",
        },
        "target_audience": "Audiophiles, commuters, retro hardware fans, budget sound enthusiasts.",
    },
    "Asics Tennis Athletic Shoes (B009MA34NY)": {
        "name": "Asics Court Athletic Tennis Shoes (B009MA34NY)",
        "brand": "Asics",
        "model": "GEL-Resolution Court Tennis Shoe",
        "asin": "B009MA34NY",
        "category": "Footwear · Athletic Tennis / Court Shoes",
        "tagline": "High-stability court shoe engineered for rapid lateral footwork and impact absorption on hard surfaces.",
        "functions": [
            "Forefoot & Rearfoot GEL Cushioning: Attenuates shock during impact and toe-off phases for joint protection.",
            "PGuard Toe Protector: Reinforced rubber toe guard guards against abrasion from heavy toe drags.",
            "Flexion Fit Upper: Proprietary synthetic upper offers form-fitting support without sacrificing flexibility.",
            "AHAR Plus Outsole: Critical high-wear areas reinforced with high-abrasion rubber for long court life.",
        ],
        "specs": {
            "Form Factor": "Low-top Court Athletic Sneaker",
            "Dimensions / Sizing": "Standard US Men's / Women's D-width; runs slightly snug in toe box (recommend 0.5 size up)",
            "Weight": "Approx. 360 grams (12.7 oz per shoe)",
            "Sole & Drop": "10 mm heel-to-toe drop, non-marking herringbone court tread",
            "Closure": "Traditional lace-up with padded tongue and collar",
            "Materials": "Breathable mesh with synthetic overlays, EVA midsole, AHAR rubber outsole",
            "Fit & Arch": "Medium-to-high arch support with rigid midfoot torsion shank",
        },
        "target_audience": "Tennis players, pickleball athletes, active runners seeking high lateral ankle stability.",
    },
    "Comfort Walking Shoes (B005AGO4LU)": {
        "name": "Comfort Slip-On Walking Athletic Shoes (B005AGO4LU)",
        "brand": "Comfort Walk",
        "model": "Everyday Cushion Walker",
        "asin": "B005AGO4LU",
        "category": "Footwear · Casual Walking / Orthotic Footwear",
        "tagline": "Plush lightweight walking shoe designed for long shifts on concrete floors and joint relief.",
        "functions": [
            "Memory Foam Cloud Insole: Molds to foot contour to reduce pressure points on heel and ball.",
            "Shock-Absorbing EVA Midsole: Dissipates ground reaction force for pain-free standing.",
            "Breathable Knit Upper: Expands with foot swelling during prolonged walking shifts.",
            "Slip-Resistant Tread: Textured rubber pods provide steady grip on tile and polished floors.",
        ],
        "specs": {
            "Form Factor": "Low-profile Slip-On Walking Sneaker",
            "Dimensions / Sizing": "Standard US sizing; roomy toe box suitable for wide feet and bunions",
            "Weight": "230 grams (8.1 oz per shoe) — Ultra-lightweight",
            "Closure": "Elastic slip-on collar with pull tab (hands-free entry)",
            "Materials": "Stretch engineered textile upper, high-density EVA midsole, dual-compound outsole",
            "Fit & Arch": "Neutral arch support with removable orthotic-friendly footbed",
        },
        "target_audience": "Nurses, retail staff, travelers, individuals seeking pain-free all-day walking comfort.",
    },
    "Flexible Cross-Training Shoes (B010RRWKT4)": {
        "name": "Flex-Fit Cross-Training Athletic Shoes (B010RRWKT4)",
        "brand": "FlexFit",
        "model": "Dynamic Trainer Pro",
        "asin": "B010RRWKT4",
        "category": "Footwear · Cross-Training / Gym Fitness",
        "tagline": "Versatile multi-directional training sneaker built for HIIT, weightlifting, and agility workouts.",
        "functions": [
            "Multi-Directional Flex Grooves: Soles flex naturally with foot movement during burpees and lunges.",
            "Flat Stable Heel Platform: Provides rigid foundation for squats and deadlifts without compression.",
            "Lateral Support Cages: Synthetic midfoot wraps lock foot down during quick lateral cuts.",
        ],
        "specs": {
            "Form Factor": "Low-top Gym Training Sneaker",
            "Dimensions / Sizing": "True to size with standard athletic width",
            "Weight": "290 grams (10.2 oz per shoe)",
            "Sole & Drop": "4 mm low-profile drop for grounded balance",
            "Materials": "Ripstop ballistic nylon, rubberized toe bumper, dual-density foam",
            "Fit & Arch": "Snug lockdown midfoot with moderate neutral arch",
        },
        "target_audience": "CrossFit athletes, gym enthusiasts, functional fitness trainees.",
    },
    "Lightweight Walking Shoes (B0014F7B98)": {
        "name": "Ultra-Light Foam Walking Shoes (B0014F7B98)",
        "brand": "CloudStep",
        "model": "FeatherLite Walker",
        "asin": "B0014F7B98",
        "category": "Footwear · Casual Lifestyle / Walking",
        "tagline": "Featherweight everyday sneaker offering effortless casual comfort for errands and travel.",
        "functions": [
            "FeatherLite Injection Foam: Lightweight single-piece sole unit provides soft step-in feel.",
            "Anti-Odor Breathable Lining: Keeps feet cool and dry in warm weather.",
            "Flexible Heel Counter: Soft collapsible heel prevents blistering and achilles rub.",
        ],
        "specs": {
            "Form Factor": "Casual Lace-Up Sneaker",
            "Dimensions / Sizing": "Runs true to size; relaxed forefoot profile",
            "Weight": "195 grams (6.9 oz per shoe)",
            "Materials": "Woven canvas/mesh upper, molded Phylon outsole",
            "Fit & Arch": "Soft relaxed fit with gentle arch contour",
        },
        "target_audience": "Casual walkers, seniors, travelers seeking lightweight luggage-friendly shoes.",
    },
    "Sony WH-1000XM5 Wireless Noise-Canceling Headphones": {
        "name": "Sony WH-1000XM5 Premium Wireless ANC Headphones",
        "brand": "Sony",
        "model": "WH-1000XM5",
        "asin": "B09XS7JWHH",
        "price": "$399.99 (MSRP)",
        "category": "Electronics · Audio / Premium Wireless Headphones",
        "tagline": "Industry-leading active noise cancellation with 8 microphones, 30-hour battery, and Hi-Res wireless audio.",
        "functions": [
            "Dual Processor ANC: HD Noise Cancelling Processor QN1 and Integrated Processor V1 control 8 microphones for unmatched silence.",
            "Auto NC Optimizer: Automatically optimizes cancellation based on wearing conditions and atmospheric pressure.",
            "Hi-Res Audio Wireless: Custom 30mm carbon fiber composite drivers support LDAC, DSEE Extreme, and 360 Reality Audio.",
            "Crystal-Clear Hands-Free Calls: 4 beamforming microphones with AI DNN noise reduction eliminate wind and background noise.",
            "Multipoint Bluetooth 5.2: Connects to two devices simultaneously with seamless audio handover.",
        ],
        "specs": {
            "Form Factor": "Over-Ear, Closed Back",
            "Dimensions": "8.85 x 3.03 x 10.24 inches (Fold-flat earcups with hard carry case)",
            "Weight": "250 grams (8.8 oz) — Lightweight stealth design",
            "Battery Life": "30 hours (ANC on) / 40 hours (ANC off); 3-minute USB-PD quick charge yields 3 hours",
            "Connectivity": "Bluetooth 5.2 (SBC, AAC, LDAC), 3.5mm analog audio cable, USB-C charging port",
            "Drivers / Sensor": "30mm precision-engineered drivers, capacitive touch sensor on right earcup",
            "Materials": "Soft-fit synthetic leather headband and ear cushions, recycled ABS body",
            "Fit & Comfort": "Stepless friction slider with pressure-free memory foam padding",
        },
        "target_audience": "Frequent flyers, office professionals, software engineers, premium audio lovers.",
    },
    "Anker 737 Power Bank (PowerCore 24K)": {
        "name": "Anker 737 Power Bank (PowerCore 24K, 140W Output)",
        "brand": "Anker",
        "model": "PowerCore 24K (A1289)",
        "asin": "B09VPHVT2Z",
        "category": "Electronics · Mobile Power / Fast Charging Battery Pack",
        "tagline": "Ultra-powerful 140W two-way fast charging battery with smart digital display and 24,000mAh capacity.",
        "functions": [
            "140W Two-Way Fast Charging: Latest Power Delivery 3.1 and bi-directional technology charges a 16\" MacBook Pro to 50% in 40 mins.",
            "Smart Digital Color Display: Real-time OLED screen reveals output wattage, input wattage, estimated recharge time, and battery health.",
            "ActiveShield 2.0 Temperature Protection: Real-time thermal sensor monitors temperature over 3,000,000 times per day to prevent overheating.",
            "Triple-Device Simultaneous Charging: 2 USB-C ports and 1 USB-A port power laptop, phone, and tablet all at once.",
        ],
        "specs": {
            "Form Factor": "High-Capacity Portable Power Brick",
            "Dimensions": "6.13 x 2.15 x 1.95 inches (155.7 x 54.6 x 49.5 mm)",
            "Weight": "630 grams (22.2 oz / 1.39 lbs) — Solid robust construction",
            "Battery Capacity": "24,000 mAh / 86.4 Wh (TSA Approved for airline carry-on luggage)",
            "Input / Output Ports": "2x USB-C (140W Max in/out), 1x USB-A (18W Max out); Total Max Output: 140W",
            "Recharge Time": "Under 60 minutes from 0% to 100% using a 140W wall charger",
            "Materials": "Fire-retardant poly-carbonate casing with ridged grip surface",
        },
        "target_audience": "Remote workers, MacBook / laptop travelers, photographers, outdoor drone pilots.",
    },
    "Kindle Paperwhite (16 GB) 6.8 Display": {
        "name": "Amazon Kindle Paperwhite (11th Generation, 16 GB)",
        "brand": "Amazon",
        "model": "Kindle Paperwhite 11th Gen",
        "asin": "B08KTZ8249",
        "category": "Electronics · E-Readers / Digital Tablets",
        "tagline": "6.8\" glare-free 300 ppi Paperwhite screen with adjustable warm backlight and 10-week battery life.",
        "functions": [
            "300 ppi Glare-Free Screen: Reads like real paper even under bright direct sunlight without glare.",
            "Adjustable Warm Backlight: Shifts display color temperature from crisp white to amber for nighttime reading.",
            "IPX8 Waterproof Rating: Built to withstand accidental immersion in up to 2 meters of fresh water for 60 minutes.",
            "20% Faster Page Turns: Snappier page rendering and pinch-to-zoom library navigation.",
            "Audible Bluetooth Audio: Seamlessly switch between reading and listening to audiobooks via Bluetooth headphones.",
        ],
        "specs": {
            "Form Factor": "Handheld E-Ink Reader",
            "Dimensions": "6.9 x 4.9 x 0.32 inches (174.2 x 124.6 x 8.1 mm)",
            "Weight": "205 grams (7.23 oz) — Lightweight one-handed hold",
            "Display": "6.8-inch E-Ink Carta 1200 touchscreen, 300 ppi, 17 LED illumination system",
            "Battery Life": "Up to 10 weeks of battery life (based on 30 mins reading/day with Wi-Fi off)",
            "Storage": "16 GB onboard storage (holds approximately 8,000 e-books)",
            "Connectivity": "Dual-Band Wi-Fi (2.4 GHz and 5.0 GHz), Bluetooth audio, USB-C charging",
        },
        "target_audience": "Avid book readers, students, travelers, beach and poolside bookworms.",
    },
    "Logitech MX Master 3S Wireless Performance Mouse": {
        "name": "Logitech MX Master 3S Advanced Ergonomic Wireless Mouse",
        "brand": "Logitech",
        "model": "MX Master 3S",
        "asin": "B09HM94VDS",
        "category": "Electronics · Computer Accessories / Ergonomic Mice",
        "tagline": "Iconic ergonomic performance mouse with 8,000 DPI track-on-glass sensor and MagSpeed electromagnetic scroll.",
        "functions": [
            "MagSpeed Electromagnetic Wheel: Scrolls 1,000 lines per second with pixel precision, shifting from ratchet to free-spin automatically.",
            "Quiet Click Technology: Delivers satisfying tactile feel with 90% less click acoustic noise compared to predecessor.",
            "8,000 DPI Darkfield Optical Sensor: Tracks with pinpoint accuracy on virtually any surface, including high-gloss glass tables.",
            "Logi Options+ & Flow Multi-Device Control: Move cursor, text, and files between up to 3 computers across macOS and Windows.",
            "Dedicated Thumb Scroll Wheel & Gesture Button: Effortless horizontal timeline scrolling in editing suites and spreadsheets.",
        ],
        "specs": {
            "Form Factor": "Sculpted Right-Hand Ergonomic Mouse",
            "Dimensions": "4.92 x 3.32 x 2.01 inches (124.9 x 84.3 x 51 mm)",
            "Weight": "141 grams (4.97 oz)",
            "Battery": "500 mAh rechargeable Li-Po battery; lasts up to 70 days per charge; 1 min quick-charge gives 3 hours",
            "Connectivity": "Bluetooth Low Energy & Logi Bolt USB Receiver; 3-device channel switcher",
            "Buttons": "7 programmable buttons (Left/Right, Back/Forward, App-Switch, Wheel mode-shift, Middle click)",
            "Materials": "Textured rubber grip with matte metallic scrolling wheel",
        },
        "target_audience": "Software developers, graphic designers, financial analysts, power office users.",
    },
    "Nike Air Zoom Pegasus Road Running Shoes": {
        "name": "Nike Air Zoom Pegasus Performance Road Running Shoes",
        "brand": "Nike",
        "model": "Air Zoom Pegasus",
        "asin": "B07T2K9R8V",
        "category": "Footwear · Athletic Running / Marathon Training",
        "tagline": "The trusted workhorse with wings: dual Zoom Air cushioning and Nike React foam for springy daily road runs.",
        "functions": [
            "Dual Air Zoom Units: High-pressure air pods placed in forefoot and heel provide springy bounce and propulsion.",
            "Nike React Foam Midsole: Lightweight, durable foam delivers responsive cushioning from mile 1 to mile 500.",
            "Engineered Circular Knit Upper: Zones of breathability keep feet cool while internal midfoot band ensures secure lockdown.",
            "Waffle-Inspired Outsole: Lugged rubber geometry provides superior traction on wet asphalt and sidewalks.",
        ],
        "specs": {
            "Form Factor": "Neutral Road Running Shoe",
            "Dimensions / Sizing": "Standard US sizing; medium arch; runs true to size with snug performance forefoot",
            "Weight": "285 grams (10 oz in Men's US 10)",
            "Heel-to-Toe Drop": "10 mm drop (33 mm heel / 23 mm forefoot)",
            "Materials": "100% recycled engineered mesh upper, React foam, carbon rubber outsole",
            "Fit & Ride": "Neutral road ride; balances plush comfort with firm energy return",
        },
        "target_audience": "Daily runners, marathon trainees, 5K/10K competitors, active fitness walkers.",
    }
}


def _clean_filename_for_product(filename: str) -> str:
    """Derive a clean, readable product name from a CSV filename."""
    if not filename:
        return "Uploaded Product Dataset"
    base = re.sub(r"\.csv$", "", filename, flags=re.I)
    base = re.sub(r"^lumina_upload_reviews_?", "", base, flags=re.I)
    base = re.sub(r"^upload_reviews_?", "", base, flags=re.I)
    base = re.sub(r"^amazon_reviews_?", "", base, flags=re.I)
    base = re.sub(r"[\s_]*\(\d+\)$", "", base)
    base = re.sub(r"[\s_]*_\d+$", "", base)
    base = re.sub(r"[\s_]*reviews?$", "", base, flags=re.I)
    base = re.sub(r"^reviews?[\s_]*", "", base, flags=re.I)
    cleaned = base.replace("_", " ").replace("-", " ").strip()
    if not cleaned or cleaned.isdigit() or len(cleaned) < 2:
        return "Uploaded Review Dataset"
    return cleaned.title()


def extract_csv_product_metadata(raw_df: pd.DataFrame, filename: str = "") -> dict[str, Any]:
    """
    Intelligently inspect an uploaded CSV DataFrame to extract product identity,
    brand, model, category, price, description, images, features, and specifications.
    
    Falls back to intelligent filename parsing and review body semantic scanning.
    """
    if raw_df is None or raw_df.empty:
        clean_name = _clean_filename_for_product(filename)
        return {
            "product_name": clean_name,
            "brand": "Generic / OEM",
            "category": "Consumer Products",
            "price": None,
            "product_description": None,
            "product_image": None,
            "asin": None,
            "product_specs": {},
            "product_features": [],
            "source_type": "CSV Upload"
        }

    col_map = {str(c).strip().lower(): c for c in raw_df.columns}

    # 1. Product Name Detection
    detected_name = None
    name_cols = [
        "product_name", "product_title", "productname", "producttitle",
        "prod_name", "prod_title", "item_name", "item_title", "itemname",
        "itemtitle", "product", "item", "device_name", "model_name", "asin"
    ]
    for cand in name_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            series = series[~series.str.lower().isin(["nan", "none", "null", ""])]
            if len(series) > 0:
                mode_val = series.mode().iloc[0]
                if len(mode_val) > 2:
                    detected_name = mode_val
                    break

    # If not found yet, check 'title' or 'name' carefully (ensuring it's not a review headline)
    if not detected_name:
        for cand in ["title", "name"]:
            if cand in col_map:
                series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
                series = series[~series.str.lower().isin(["nan", "none", "null", ""])]
                if len(series) > 0:
                    is_review_title = (len(raw_df) > 8) and (series.nunique() / len(series) > 0.7)
                    if not is_review_title:
                        mode_val = series.mode().iloc[0]
                        if len(mode_val) > 2:
                            detected_name = mode_val
                            break

    # 2. Brand Detection
    detected_brand = None
    brand_cols = ["brand", "brand_name", "brandname", "manufacturer", "vendor", "make"]
    for cand in brand_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            series = series[~series.str.lower().isin(["nan", "none", "null", ""])]
            if len(series) > 0:
                detected_brand = series.mode().iloc[0]
                break

    # 3. Category Detection
    detected_cat = None
    cat_cols = ["category", "product_category", "productcategory", "dept", "department", "sub_category", "main_category"]
    for cand in cat_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            series = series[~series.str.lower().isin(["nan", "none", "null", ""])]
            if len(series) > 0:
                detected_cat = series.mode().iloc[0]
                break

    # 4. Price Detection
    detected_price = None
    price_cols = ["price", "product_price", "sale_price", "cost", "retail_price", "list_price", "amount"]
    for cand in price_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna()
            if len(series) > 0:
                p_val = series.iloc[0]
                try:
                    num = float(re.sub(r"[^\d.]", "", str(p_val)))
                    detected_price = f"${num:,.2f}"
                except Exception:
                    detected_price = str(p_val)
                break

    # 5. Product Description Detection
    detected_desc = None
    desc_cols = ["description", "product_description", "productdescription", "about", "overview", "item_description", "details"]
    for cand in desc_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            series = series[~series.str.lower().isin(["nan", "none", "null", ""])]
            if len(series) > 0:
                detected_desc = series.iloc[0]
                break

    # 6. Product Image URL Detection
    detected_img = None
    img_cols = ["image", "image_url", "product_image", "img_url", "thumbnail", "photo", "picture"]
    for cand in img_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            for val in series:
                if val.startswith("http://") or val.startswith("https://"):
                    detected_img = val
                    break
            if detected_img:
                break

    # 7. ASIN / Model SKU Detection
    detected_asin = None
    asin_cols = ["asin", "parent_asin", "sku", "model_number", "item_model_number", "product_id"]
    for cand in asin_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            series = series[~series.str.lower().isin(["nan", "none", "null", ""])]
            if len(series) > 0:
                detected_asin = series.mode().iloc[0]
                break

    # 8. Specs & Features Mapping
    specs_dict = {}
    if detected_brand:
        specs_dict["Brand"] = detected_brand
    if detected_cat:
        specs_dict["Category"] = detected_cat
    if detected_asin:
        specs_dict["ASIN / SKU"] = detected_asin
    if detected_price:
        specs_dict["Price"] = detected_price

    # Check for dedicated specs / features columns
    features_list = []
    feat_cols = ["features", "feature_bullets", "bullet_points", "highlights", "specs", "specifications"]
    for cand in feat_cols:
        if cand in col_map:
            series = raw_df[col_map[cand]].dropna().astype(str).str.strip()
            if len(series) > 0:
                raw_feat = series.iloc[0]
                if "[" in raw_feat and "]" in raw_feat:
                    try:
                        import ast
                        parsed = ast.literal_eval(raw_feat)
                        if isinstance(parsed, list):
                            features_list.extend([str(x) for x in parsed[:6]])
                    except Exception:
                        pass
                if not features_list:
                    for item in re.split(r"[|;\n]", raw_feat):
                        if item.strip():
                            features_list.append(item.strip())
                break

    # 9. Fallback from Filename if no column had product name
    if not detected_name:
        detected_name = _clean_filename_for_product(filename)

    return {
        "product_name": detected_name,
        "brand": detected_brand,
        "category": detected_cat,
        "price": detected_price,
        "product_description": detected_desc,
        "product_image": detected_img,
        "asin": detected_asin,
        "product_specs": specs_dict,
        "product_features": features_list,
        "source_type": "CSV Upload"
    }


def extract_product_profile(
    product_name: str,
    reviews_df: pd.DataFrame | None = None,
    url_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Retrieve or dynamically generate a comprehensive product profile containing
    identity, model, size, functions, and hardware specifications.
    """
    prod_clean = product_name.strip()

    # 1. Exact match in curated library
    matched_prof = None
    if prod_clean in KNOWN_PRODUCT_PROFILES:
        matched_prof = dict(KNOWN_PRODUCT_PROFILES[prod_clean])
    else:
        for key, prof in KNOWN_PRODUCT_PROFILES.items():
            if key.lower() in prod_clean.lower() or prod_clean.lower() in key.lower():
                matched_prof = dict(prof)
                break
            model = prof.get("model", "").lower()
            if model and model in prod_clean.lower():
                matched_prof = dict(prof)
                break
            if prof.get("asin") and prof["asin"].lower() in prod_clean.lower():
                matched_prof = dict(prof)
                break

    if matched_prof:
        if not matched_prof.get("description"):
            matched_prof["description"] = f"{matched_prof.get('tagline', '')} Engineered with high-precision components, ergonomic design, and top-tier capabilities."
        if not matched_prof.get("image"):
            matched_prof["image"] = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80"
        if url_info:
            if url_info.get("product_description"):
                matched_prof["description"] = url_info["product_description"]
            if url_info.get("product_image"):
                matched_prof["image"] = url_info["product_image"]
            if url_info.get("source_url"):
                matched_prof["source_url"] = url_info["source_url"]
            if url_info.get("product_specs"):
                matched_prof.setdefault("specs", {}).update(url_info["product_specs"])
            if url_info.get("price"):
                matched_prof["price"] = url_info["price"]
        return matched_prof

    # 2. Dynamic Extraction from reviews, metadata and URL info
    inferred_brand = "Generic / OEM"
    inferred_model = prod_clean

    # Detect category using 3-tier taxonomy engine
    # Detect category using category_intelligence classification engine
    from category_intelligence import classify_product
    primary_cat, cat_conf, _ = classify_product(
        title=prod_clean,
        reviews_df=reviews_df,
        metadata={"category": url_info.get("category") if url_info else None}
    )
    inferred_category = primary_cat

    # Extract brand from product title
    words = prod_clean.split()
    if words:
        first_word = words[0]
        if first_word.lower() in ["sony", "anker", "nike", "asics", "apple", "samsung", "logitech", "koss", "bose", "kindle", "adidas", "zara", "h&m", "levis", "puma"]:
            inferred_brand = first_word.capitalize()

    detected_functions = []
    detected_specs = {
        "Product Title": prod_clean,
        "Identified Model / SKU": prod_clean.split("(")[-1].replace(")", "").strip() if "(" in prod_clean else "Standard Edition",
        "Evaluated Category": primary_cat,
        "Detection Source": f"Category Intelligence ({int(cat_conf*100)}% confidence)",
    }

    # Category-specific baseline specs & functions across all 10 primary categories
    if primary_cat == "Clothing / Apparel":
        detected_specs.update({
            "Form Factor": "Apparel / Garment (T-Shirt, Top, Outerwear)",
            "Materials & Fabric": "Breathable textile knit & reinforced weave",
            "Fit & Sizing": "Standard regular cut with ergonomic drape",
            "Wash Care & Shrinkage": "Machine wash cold with like colors, tumble dry low",
            "Seam Construction": "Double-needle sleeve and hem stitching",
        })
        detected_functions.extend([
            "Garment Comfort & Drape: Tailored cut providing natural mobility, breathable air circulation, and soft next-to-skin touch.",
            "Fabric Integrity & Colorfastness: Colorfast dyed yarn designed to prevent fading and seam warping across repeated washes.",
            "Moisture Management: Open textile weave promoting body heat dissipation during daily wear.",
        ])
    elif primary_cat == "Footwear":
        detected_specs.update({
            "Form Factor": "Athletic / Lifestyle Footwear",
            "Midsole & Cushioning": "Dual-density EVA foam midsole with heel impact dampening",
            "Outsole & Traction": "Multi-surface non-marking rubber tread",
            "Fit & Arch Profile": "Contoured anatomical footbed with reinforced arch bridge",
        })
        detected_functions.extend([
            "Impact Shock Absorption: Responsive sole cushioning dispersing vertical ground reaction force.",
            "Multi-Surface Traction: Engineered outsole grooves delivering slip-resistant grip on wet and dry surfaces.",
            "Anatomical Arch Support: Stabilizing cup structure designed to relieve plantar fatigue during extended standing.",
        ])
    elif primary_cat == "Electronics":
        detected_specs.update({
            "Form Factor": "Digital Tech Hardware / Electronic Device",
            "Chassis & Build": "Engineered composite / alloy housing",
            "Performance": "High-throughput responsive digital circuitry",
        })
        detected_functions.extend([
            "Digital Signal Processing: Low-latency circuitry delivering responsive performance.",
            "System Reliability: Stable operational firmware with predictable hardware handshake.",
        ])
    elif primary_cat == "Jewelry":
        detected_specs.update({
            "Form Factor": "Fine / Fashion Jewelry Piece",
            "Finish & Polish": "High-luster surface finish with protective anti-scratch coating",
            "Clasp & Setting": "Precision prong setting and secure tension clasp",
            "Skin Safety": "Hypoallergenic contact surface designed to prevent skin discoloration",
        })
        detected_functions.extend([
            "Luster & Brilliance: Surface polish reflecting light with refined clarity and shine.",
            "Tarnish Resistance: Protective atmospheric seal resisting environmental oxidation.",
            "Secure Retention: Reinforced clasp and prongs preventing accidental loss during daily wear.",
        ])
    elif primary_cat == "Furniture":
        detected_specs.update({
            "Form Factor": "Residential / Commercial Furniture",
            "Frame & Structure": "Reinforced structural frame with balanced weight distribution",
            "Assembly": "Modular assembly with included precision hardware",
            "Stability & Feet": "Anti-wobble leveling glides protecting flooring",
        })
        detected_functions.extend([
            "Structural Load Support: Heavy-duty frame engineered for continuous weight support without sagging.",
            "Ergonomic Living Comfort: Optimized contouring and support posture for extended daily use.",
            "Surface Finish Durability: Scratch-resistant protective coating resisting daily abrasion.",
        ])
    elif primary_cat == "Beauty / Personal Care":
        detected_specs.update({
            "Form Factor": "Topical Cosmetic / Skincare Formulation",
            "Skin Compatibility": "Dermatologist-evaluated, gentle topical formulation",
            "Dispenser Type": "Airtight pump / hygienic protective seal",
        })
        detected_functions.extend([
            "Targeted Treatment & Hydration: Rapidly absorbing formulation reinforcing barrier health.",
            "Gentle Daily Compatibility: Non-irritating ingredients balanced for frequent application.",
        ])
    elif primary_cat == "Bags & Accessories":
        detected_specs.update({
            "Form Factor": "Luggage / Everyday Carry Bag",
            "Material & Shell": "Durable high-denier textile / synthetic composite shell",
            "Zippers & Hardware": "Heavy-duty smooth-glide zippers and reinforced metal buckles",
            "Organization": "Dedicated compartments with padded protective sleeves",
        })
        detected_functions.extend([
            "Load Bearing Carry: Ergonomic strap geometry distributing pack weight evenly.",
            "Internal Organization: Divided partitions and quick-access utility pockets.",
            "Abrasion & Tear Resistance: Reinforced base and stress-point bar-tacking.",
        ])
    elif primary_cat == "Sports & Fitness":
        detected_specs.update({
            "Form Factor": "Athletic & Fitness Training Equipment",
            "Build & Material": "Heavy-gauge steel / high-density impact-resistant composite",
            "Safety & Grip": "Non-slip knurled grip and positive locking mechanism",
        })
        detected_functions.extend([
            "Training Performance: Consistent resistance curve and smooth mechanical movement.",
            "Safety & Stability: Secure footing and lock pins preventing workout accidents.",
        ])
    elif primary_cat == "Home & Kitchen":
        detected_specs.update({
            "Form Factor": "Culinary Appliance / Home Essential",
            "Food-Contact Safety": "100% BPA-free, food-grade materials & non-stick coating",
            "Cleaning & Maintenance": "Easy-clean surface with dishwasher-safe removable components",
        })
        detected_functions.extend([
            "Precision Culinary Processing: Calibrated mechanisms delivering uniform preparation.",
            "Effortless Maintenance: Non-stick surfaces preventing food residue adhesion for easy wipe-down.",
        ])
    else:
        detected_specs.update({
            "Form Factor": "Consumer Product / Daily Essential",
            "Materials & Build": "Durable composite and standard housing",
            "Fit / Ergonomics": "Ergonomic consumer design",
        })
        detected_functions.extend([
            "Core Product Utility: Reliable day-to-day operation fulfilling consumer functional demands.",
            "Everyday Durability: Built to withstand standard wear and tear over extended lifecycle.",
        ])

    if reviews_df is not None and not reviews_df.empty:
        rev_col = "review" if "review" in reviews_df.columns else reviews_df.columns[0]
        reviews_corpus = reviews_df[rev_col].dropna().astype(str).tolist()
        all_text = " ".join(reviews_corpus).lower()

        # Features detection
        if "bluetooth" in all_text or "wireless" in all_text:
            if not any("bluetooth" in f.lower() for f in detected_functions):
                detected_functions.append("Wireless Connectivity: Bluetooth wireless protocol for cable-free pairing.")
            detected_specs["Connectivity"] = "Bluetooth Wireless"
        if "noise cancel" in all_text or "anc" in all_text:
            if not any("noise cancel" in f.lower() for f in detected_functions):
                detected_functions.append("Active Noise Cancellation: Acoustic microphone cancellation of ambient environmental noise.")
        if "waterproof" in all_text or "water resistant" in all_text:
            detected_functions.append("Water Resistance: Sealed enclosure protecting against moisture and perspiration.")
        if "usb-c" in all_text or "type c" in all_text:
            detected_specs["Charging / Interface"] = "USB-C Port"

        # Sizing observations
        if "runs small" in all_text:
            detected_specs["Sizing Note"] = "Customer feedback indicates product runs slightly small; consider ordering half size up."
        elif "runs large" in all_text:
            detected_specs["Sizing Note"] = "Customer feedback indicates product runs slightly large."


    inferred_desc = f"Comprehensive product overview and customer intelligence profile for {prod_clean}. Categorized under {inferred_category}. Engineered for high reliability, performance, and everyday consumer satisfaction."
    inferred_img = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80"
    source_link = ""

    if url_info:
        if url_info.get("brand"):
            inferred_brand = url_info["brand"]
        if url_info.get("category"):
            inferred_category = url_info["category"]
        if url_info.get("product_description"):
            inferred_desc = url_info["product_description"]
        if url_info.get("product_image"):
            inferred_img = url_info["product_image"]
        if url_info.get("product_features"):
            detected_functions = url_info["product_features"]
        if url_info.get("product_specs"):
            detected_specs.update(url_info["product_specs"])
        if url_info.get("asin"):
            detected_specs["ASIN"] = url_info["asin"]
        if url_info.get("source_url"):
            source_link = url_info["source_url"]

    if not detected_functions:
        detected_functions = [
            "Primary Operation: Standard functional operation fulfilling core product category requirements.",
            "Everyday Reliability: Engineered for consumer use with integrated controls and user interface.",
        ]

    return {
        "name": prod_clean,
        "brand": inferred_brand,
        "model": detected_specs.get("Identified Model / SKU", prod_clean),
        "asin": (url_info.get("asin") if url_info else None) or detected_specs.get("ASIN", "Extracted via review corpus"),
        "category": inferred_category,
        "price": url_info.get("price") if url_info else None,
        "tagline": f"Comprehensive customer feedback analysis for {prod_clean}.",
        "description": inferred_desc,
        "image": inferred_img,
        "source_url": source_link,
        "functions": detected_functions,
        "specs": detected_specs,
        "target_audience": "General consumers and buyers evaluating product performance and review consensus.",
    }
