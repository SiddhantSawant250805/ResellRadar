"""
ResellRadar High-Throughput Synthetic Listing Generator
Generates realistic second-hand marketplace listings (50,000+ items target)
for Mobile Phones & Furniture categories with natural price & spatial distributions.
"""

import datetime
import json
import os
import random
import time
from typing import Dict, List, Any


PHONE_MODELS = [
    ("Apple", "iPhone 15 Pro Max", ["128GB", "256GB", "512GB", "1TB"], ["Natural Titanium", "Blue Titanium", "Black Titanium", "White Titanium"], (850, 1399), "Apple iPhone"),
    ("Apple", "iPhone 15 Pro", ["128GB", "256GB", "512GB"], ["Natural Titanium", "Black Titanium", "White Titanium"], (750, 1150), "Apple iPhone"),
    ("Apple", "iPhone 14 Pro", ["128GB", "256GB", "512GB"], ["Space Black", "Deep Purple", "Gold", "Silver"], (600, 950), "Apple iPhone"),
    ("Apple", "iPhone 13", ["128GB", "256GB"], ["Midnight", "Starlight", "Blue", "Pink"], (420, 680), "Apple iPhone"),
    ("Samsung", "Galaxy S24 Ultra", ["256GB", "512GB", "1TB"], ["Titanium Black", "Titanium Gray", "Titanium Violet"], (890, 1350), "Samsung Galaxy"),
    ("Samsung", "Galaxy S23 Ultra", ["256GB", "512GB"], ["Phantom Black", "Green", "Cream", "Lavender"], (620, 920), "Samsung Galaxy"),
    ("Samsung", "Galaxy Z Fold 5", ["256GB", "512GB"], ["Icy Blue", "Phantom Black", "Cream"], (950, 1500), "Samsung Galaxy"),
    ("Google", "Pixel 8 Pro", ["128GB", "256GB", "512GB"], ["Bay Blue", "Obsidian", "Porcelain"], (580, 890), "Google Pixel"),
    ("Google", "Pixel 7a", ["128GB"], ["Charcoal", "Sea", "Snow"], (280, 420), "Google Pixel"),
    ("OnePlus", "OnePlus 12", ["256GB", "512GB"], ["Silky Black", "Emerald Green"], (520, 780), "Android Smartphones"),
]

FURNITURE_MODELS = [
    ("Herman Miller", "Aeron Chair Remastered", "Size B / Fully Loaded", (650, 1250), "Seating & Office"),
    ("Herman Miller", "Embody Ergonomic Chair", "Sync Fabric Black / Cyan Base", (850, 1550), "Seating & Office"),
    ("Steelcase", "Gesture Desk Chair", "Graphite Frame / 3D Knit", (550, 950), "Seating & Office"),
    ("IKEA", "KALLAX Shelf Unit", "4x4 White / Insert Drawers", (45, 120), "Storage & Shelving"),
    ("IKEA", "MARKUS Executive Chair", "Vissle Dark Gray", (80, 160), "Seating & Office"),
    ("West Elm", "Mid-Century Pop-Up Coffee Table", "Acorn Wood Finish", (250, 480), "Tables & Desks"),
    ("West Elm", "Hamilton Leather Sofa", "78\" Tan Top-Grain Leather", (950, 2100), "Seating & Sofas"),
    ("Article", "Sven Charme Sofa", "Tan Leather 3-Seater", (800, 1650), "Seating & Sofas"),
    ("CB2", "Drommen Acacia Bed Frame", "Queen Size / Upholstered Headboard", (450, 920), "Bedroom Furniture"),
    ("Pottery Barn", "Farmhouse Extending Dining Table", "Rustic Mahogany 86\"", (750, 1850), "Tables & Desks"),
]

LOCATIONS = [
    ("Austin", "TX"), ("Seattle", "WA"), ("Miami", "FL"), ("Chicago", "IL"),
    ("New York", "NY"), ("San Francisco", "CA"), ("Boston", "MA"),
    ("Atlanta", "GA"), ("Denver", "CO"), ("Dallas", "TX"), ("Los Angeles", "CA"),
    ("Portland", "OR"), ("Phoenix", "AZ"), ("Nashville", "TN")
]

SELLER_TYPES = ["Individual", "Individual", "Individual", "Verified PowerSeller", "Liquidation Depot", "Refurbisher"]
SOURCES = ["Craigslist", "Facebook Marketplace", "OfferUp", "eBay Refurbished"]
CONDITIONS = ["Like New - Unlocked with Box", "Excellent Condition - Minor Scuffs", "Good Condition - Fully Functional", "Fair - Battery Health 84%", "Mint Condition in Original Box"]

def _new_run_id() -> str:
    """Generate a unique run id so listing IDs never collide across batches.

    Multiple generate_batch() calls in the same second (or across machines)
    must not reuse primary keys in the raw zone.
    """
    return f"{int(time.time() * 1000) % 100000000:08d}{random.randint(100, 999)}"


def generate_listing(item_id: int, category_filter: str = "all", run_id: str = None) -> Dict[str, Any]:
    """Generate a single realistic raw listing payload."""
    if run_id is None:
        run_id = _new_run_id()
    if category_filter == "phones":
        chosen_cat = "Phones & Mobile"
    elif category_filter == "furniture":
        chosen_cat = "Furniture & Decor"
    else:
        chosen_cat = random.choice(["Phones & Mobile", "Furniture & Decor"])

    city, region = random.choice(LOCATIONS)
    seller = random.choice(SELLER_TYPES)
    source = random.choice(SOURCES)
    
    # Posted timestamp within last 30 days
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    posted_dt = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    posted_str = posted_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 35% chance of being delisted/sold
    delisted_str = None
    if random.random() < 0.35:
        delisted_dt = posted_dt + datetime.timedelta(days=random.randint(1, 12), hours=random.randint(1, 10))
        if delisted_dt <= datetime.datetime.utcnow():
            delisted_str = delisted_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if chosen_cat == "Phones & Mobile":
        brand, model, storage_list, colors, price_range, sub_cat = random.choice(PHONE_MODELS)
        storage = random.choice(storage_list)
        color = random.choice(colors)
        condition = random.choice(CONDITIONS)
        title = f"{brand} {model} {storage} {color} - {condition}"
        base_price = random.uniform(price_range[0], price_range[1])
        # Add random discount / variance for used condition
        price = round(base_price * random.uniform(0.85, 1.05), 2)
        desc = (
            f"Selling my {brand} {model} ({storage}, {color}). {condition}. "
            f"Unlocked for all carriers (AT&T, T-Mobile, Verizon). Battery health is at {random.randint(86, 99)}%. "
            f"Comes with original USB-C charging cable. Pickup near {city} or local delivery available."
        )
    else:
        brand, model, spec, price_range, sub_cat = random.choice(FURNITURE_MODELS)
        title = f"{brand} {model} ({spec}) - Great Condition"
        base_price = random.uniform(price_range[0], price_range[1])
        price = round(base_price * random.uniform(0.80, 1.08), 2)
        desc = (
            f"{brand} {model} in {spec}. Purchased 1 year ago, moving to new apartment so need to sell ASAP. "
            f"Clean, smoke-free, pet-free home. Dimensions: standard {spec}. Must bring truck/van for pickup in {city}, {region}."
        )

    return {
        "listing_id": f"RR-{chosen_cat[:1].upper()}-{item_id:07d}-{run_id}",
        "title": title,
        "description": desc,
        "price": price,
        "currency": "USD",
        "category": chosen_cat,
        "sub_category": sub_cat,
        "location_city": city,
        "location_region": region,
        "posted_date": posted_str,
        "delisted_date": delisted_str,
        "seller_type": seller,
        "source_platform": source,
        "scraped_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def generate_batch(count: int = 500, category: str = "all", output_dir: str = "data/raw") -> str:
    """
    Generate a batch of raw listings and save to data/raw/raw_YYYY_MM_DD_HHMMSS.json
    Returns the generated file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.datetime.utcnow().strftime("%Y_%m_%d_%H%M%S")
    run_id = _new_run_id()
    filename = f"raw_{category}_{timestamp_str}_{run_id}.json"
    filepath = os.path.join(output_dir, filename)

    items = [generate_listing(i + 1, category_filter=category, run_id=run_id) for i in range(count)]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    return filepath


if __name__ == "__main__":
    print("Testing Synthetic Listing Generator (Generating 500 sample items)...")
    path = generate_batch(count=500, category="all")
    print(f"Sample batch generated successfully at: {path}")
