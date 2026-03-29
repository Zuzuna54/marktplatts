import asyncio
import json
import re
import logging
from datetime import datetime, timezone, timedelta

import httpx

from scrapers.base import BaseScraper
from database import (
    upsert_listings_bulk, update_sync_state, count_listings,
    get_source_sync_date, update_source_sync_date_from_listings,
)

logger = logging.getLogger(__name__)

DELAY = 2.0  # Slightly slower than Marktplaats to avoid blocking
BASE_URL = "https://www.autoscout24.nl"
INCREMENTAL_BUFFER = timedelta(hours=1)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}


def _parse_int_from_str(s: str | None) -> int | None:
    if not s:
        return None
    match = re.search(r"(\d[\d.]*)", s.replace(".", ""))
    return int(match.group(1)) if match else None


def _parse_year(vehicle_details: list[dict]) -> int | None:
    """Extract construction year from vehicleDetails (the 'calendar' icon entry)."""
    for detail in vehicle_details:
        if detail.get("iconName") == "calendar":
            # Format: "08/2025" or "2025"
            val = detail.get("data", "")
            match = re.search(r"(\d{4})", val)
            return int(match.group(1)) if match else None
    return None


def _make_image_urls(raw_url: str) -> dict:
    """Convert 250x188 thumbnail to medium (400x300) and large (800x600) URLs."""
    base = raw_url.rsplit("/", 1)[0]
    return {
        "medium": f"{base}/400x300.webp",
        "large": f"{base}/800x600.webp",
    }


def _parse_listing(item: dict) -> dict:
    vehicle = item.get("vehicle", {})
    price_data = item.get("price", {})
    location = item.get("location", {})
    seller = item.get("seller", {})
    vehicle_details = item.get("vehicleDetails", [])
    raw_images = item.get("images", [])

    # Parse price from formatted string "€ 13.999"
    price_str = price_data.get("priceFormatted", "")
    price_cents = None
    if price_str:
        price_match = re.search(r"[\d.]+", price_str.replace(".", ""))
        if price_match:
            price_cents = int(price_match.group()) * 100

    # Parse mileage from "2.483 km"
    mileage_km = _parse_int_from_str(vehicle.get("mileageInKm"))

    # Parse engine cc from "890 cm³"
    engine_cc = _parse_int_from_str(vehicle.get("engineDisplacementInCCM"))

    # Parse year from vehicleDetails
    construction_year = _parse_year(vehicle_details)

    # Build images list
    images = [_make_image_urls(url) for url in raw_images[:20]]  # Cap at 20 images
    thumbnail_url = images[0]["large"] if images else None

    # Build title from make + model + variant
    title_parts = [vehicle.get("make", ""), vehicle.get("model", "")]
    variant = vehicle.get("modelVersionInput") or vehicle.get("variant") or ""
    if variant:
        title_parts.append(variant)
    title = " ".join(p for p in title_parts if p).strip() or item.get("id", "Unknown")

    # Item URL
    url_path = item.get("url", "")
    link = f"{BASE_URL}{url_path}" if url_path.startswith("/") else url_path

    item_id = f"as24_{item.get('crossReferenceId') or item.get('id', '')}"

    seller_type = seller.get("type", "")  # "Dealer" or "Private"

    return {
        "item_id": item_id,
        "title": title,
        "description": vehicle.get("subtitle") or vehicle.get("modelVersionInput") or "",
        "price_cents": price_cents,
        "price_type": "FIXED",
        "construction_year": construction_year,
        "mileage_km": mileage_km,
        "engine_cc": engine_cc,
        "cylinders": None,
        "condition": None,
        "motorcycle_type": vehicle.get("type"),
        "brand": vehicle.get("make"),
        "engine_power": next((d["data"] for d in vehicle_details if d.get("iconName") == "speedometer"), None),
        "advertiser_type": "Bedrijf" if seller_type == "Dealer" else "Particulier",
        "city": location.get("city"),
        "latitude": None,
        "longitude": None,
        "distance_km": None,
        "seller_id": seller.get("id"),
        "seller_name": seller.get("companyName") or seller.get("contactName"),
        "thumbnail_url": thumbnail_url,
        "link": link,
        "post_date": None,  # AutoScout24 doesn't expose post date in listing search
        "images": images,
        "source": "autoscout24",
        "is_auction": 0,
        "current_bid_cents": None,
        "auction_end_time": None,
        "bid_count": None,
    }


def _fetch_page_sync(page: int) -> tuple[list[dict], int]:
    """Fetch a single page. Returns (listings, total_count)."""
    url = f"{BASE_URL}/lst-moto"
    params = {"atype": "B", "cy": "NL", "sort": "standard", "page": str(page)}

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
        r = client.get(url, params=params)

    if r.status_code != 200:
        logger.warning(f"AutoScout24 page {page}: HTTP {r.status_code}")
        return [], 0

    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text)
    if not match:
        logger.warning(f"AutoScout24 page {page}: no __NEXT_DATA__")
        return [], 0

    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    listings = page_props.get("listings", [])
    total = page_props.get("numberOfResults", 0)

    return listings, total


class AutoScout24Scraper(BaseScraper):
    source_id = "autoscout24"
    source_display = "AutoScout24"

    async def full_sync(self) -> int:
        logger.info(f"[{self.source_display}] Starting full sync")
        grand_total = 0
        page = 1
        max_pages = 200

        while page <= max_pages:
            try:
                raw_listings, total_count = await asyncio.to_thread(_fetch_page_sync, page)
            except Exception as e:
                logger.warning(f"[{self.source_display}] Error on page {page}: {e}", exc_info=True)
                break

            if not raw_listings:
                break

            parsed = []
            item_ids = []
            for item in raw_listings:
                try:
                    p = _parse_listing(item)
                    parsed.append(p)
                    item_ids.append(p["item_id"])
                except Exception as e:
                    logger.warning(f"[{self.source_display}] Parse error: {e}")

            if parsed:
                upsert_listings_bulk(parsed)
                update_source_sync_date_from_listings(self.source_id, "__all__", item_ids)

            grand_total += len(parsed)

            if page % 20 == 0:
                db_total = count_listings()
                update_sync_state(total_in_db=db_total, total_fetched=grand_total)
                logger.info(f"  [{self.source_display}] Page {page}/{max_pages}: {grand_total} fetched")

            page += 1
            await asyncio.sleep(DELAY)

        logger.info(f"[{self.source_display}] Full sync done: {grand_total} listings")
        return grand_total

    async def incremental_sync(self) -> int:
        """Fetch first few pages (newest listings) to catch new arrivals."""
        # AutoScout24 doesn't support offered_since — just re-fetch the first ~10 pages
        # which contain the newest listings. Dedup handles overlap.
        grand_total = 0
        max_pages = 10

        for page in range(1, max_pages + 1):
            try:
                raw_listings, _ = await asyncio.to_thread(_fetch_page_sync, page)
            except Exception as e:
                logger.warning(f"[{self.source_display}] Incremental error page {page}: {e}")
                break

            if not raw_listings:
                break

            parsed = []
            for item in raw_listings:
                try:
                    parsed.append(_parse_listing(item))
                except Exception as e:
                    logger.warning(f"[{self.source_display}] Parse error: {e}")

            if parsed:
                upsert_listings_bulk(parsed)

            grand_total += len(parsed)
            await asyncio.sleep(DELAY)

        return grand_total
