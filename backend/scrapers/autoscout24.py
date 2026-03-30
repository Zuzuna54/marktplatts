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

DELAY = 2.0
BASE_URL = "https://www.autoscout24.nl"
MAX_PAGES_PER_BRAND = 200  # AS24 caps at 200 pages per search

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}

# Major brands to shard by — all under 4k each on AS24 NL
BRANDS = [
    "yamaha", "honda", "kawasaki", "bmw", "suzuki", "ducati",
    "harley-davidson", "triumph", "ktm", "aprilia", "moto-guzzi",
    "mv-agusta", "husqvarna", "royal-enfield", "piaggio", "indian",
    "buell", "cfmoto", "benelli",
]


def _parse_int_from_str(s: str | None) -> int | None:
    if not s:
        return None
    match = re.search(r"(\d[\d.]*)", s.replace(".", ""))
    return int(match.group(1)) if match else None


def _parse_year(vehicle_details: list[dict]) -> int | None:
    for detail in vehicle_details:
        if detail.get("iconName") == "calendar":
            val = detail.get("data", "")
            match = re.search(r"(\d{4})", val)
            return int(match.group(1)) if match else None
    return None


def _make_image_urls(raw_url: str) -> dict:
    base = raw_url.rsplit("/", 1)[0]
    return {"medium": f"{base}/400x300.webp", "large": f"{base}/800x600.webp"}


def _parse_listing(item: dict) -> dict:
    vehicle = item.get("vehicle", {})
    price_data = item.get("price", {})
    location = item.get("location", {})
    seller = item.get("seller", {})
    vehicle_details = item.get("vehicleDetails", [])
    raw_images = item.get("images", [])

    price_str = price_data.get("priceFormatted", "")
    price_cents = None
    if price_str:
        price_match = re.search(r"[\d.]+", price_str.replace(".", ""))
        if price_match:
            price_cents = int(price_match.group()) * 100

    mileage_km = _parse_int_from_str(vehicle.get("mileageInKm"))
    engine_cc = _parse_int_from_str(vehicle.get("engineDisplacementInCCM"))
    construction_year = _parse_year(vehicle_details)

    images = [_make_image_urls(url) for url in raw_images[:20]]
    thumbnail_url = images[0]["large"] if images else None

    title_parts = [vehicle.get("make", ""), vehicle.get("model", "")]
    variant = vehicle.get("modelVersionInput") or vehicle.get("variant") or ""
    if variant:
        title_parts.append(variant)
    title = " ".join(p for p in title_parts if p).strip() or item.get("id", "Unknown")

    url_path = item.get("url", "")
    link = f"{BASE_URL}{url_path}" if url_path.startswith("/") else url_path

    item_id = f"as24_{item.get('crossReferenceId') or item.get('id', '')}"
    seller_type = seller.get("type", "")

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
        "post_date": None,
        "images": images,
        "source": "autoscout24",
        "is_auction": 0,
        "current_bid_cents": None,
        "auction_end_time": None,
        "bid_count": None,
    }


def _fetch_page_sync(path: str, page: int) -> tuple[list[dict], int]:
    """Fetch a single page for a given path. Returns (listings, total_count)."""
    url = f"{BASE_URL}{path}"
    params = {"atype": "B", "cy": "NL", "sort": "standard", "page": str(page)}

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
        r = client.get(url, params=params)

    if r.status_code != 200:
        return [], 0

    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text)
    if not match:
        return [], 0

    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    listings = page_props.get("listings", [])
    total = page_props.get("numberOfResults", 0)

    return listings, total


async def _fetch_all_pages(path: str, label: str) -> tuple[int, list[str]]:
    """Paginate through all pages for a given search path. Returns (count, item_ids)."""
    total_fetched = 0
    all_item_ids: list[str] = []

    for page in range(1, MAX_PAGES_PER_BRAND + 1):
        try:
            raw_listings, _ = await asyncio.to_thread(_fetch_page_sync, path, page)
        except Exception as e:
            logger.warning(f"[AutoScout24] Error {label} page {page}: {e}")
            break

        if not raw_listings:
            break

        parsed = []
        for item in raw_listings:
            try:
                p = _parse_listing(item)
                parsed.append(p)
                all_item_ids.append(p["item_id"])
            except Exception as e:
                logger.warning(f"[AutoScout24] Parse error: {e}")

        if parsed:
            upsert_listings_bulk(parsed)

        total_fetched += len(parsed)

        if len(raw_listings) < 20:
            break

        await asyncio.sleep(DELAY)

    return total_fetched, all_item_ids


class AutoScout24Scraper(BaseScraper):
    source_id = "autoscout24"
    source_display = "AutoScout24"

    async def full_sync(self) -> int:
        logger.info(f"[{self.source_display}] Starting full sync ({len(BRANDS)} brands)")
        grand_total = 0

        for i, brand in enumerate(BRANDS):
            path = f"/lst-moto/{brand}"
            logger.info(f"  [{self.source_display}] [{i + 1}/{len(BRANDS)}] {brand}")

            count, item_ids = await _fetch_all_pages(path, brand)

            if item_ids:
                update_source_sync_date_from_listings(self.source_id, brand, item_ids)

            grand_total += count
            db_total = count_listings()
            update_sync_state(total_in_db=db_total)
            logger.info(f"  [{self.source_display}] {brand}: {count} fetched (DB: {db_total:,})")

            await asyncio.sleep(DELAY)

        # Catch remaining brands not in the list via the generic search
        logger.info(f"  [{self.source_display}] Fetching remaining (generic)")
        count, _ = await _fetch_all_pages("/lst-moto", "generic")
        grand_total += count

        logger.info(f"[{self.source_display}] Full sync done: {grand_total:,} listings")
        return grand_total

    async def incremental_sync(self) -> int:
        """Re-fetch first few pages per brand to catch new arrivals."""
        grand_total = 0

        for brand in BRANDS:
            path = f"/lst-moto/{brand}"
            total_fetched = 0

            for page in range(1, 6):  # First 5 pages per brand
                try:
                    raw, _ = await asyncio.to_thread(_fetch_page_sync, path, page)
                except Exception:
                    break
                if not raw:
                    break

                parsed = []
                for item in raw:
                    try:
                        parsed.append(_parse_listing(item))
                    except Exception:
                        pass
                if parsed:
                    upsert_listings_bulk(parsed)
                total_fetched += len(parsed)
                await asyncio.sleep(DELAY)

            grand_total += total_fetched
            if total_fetched > 0:
                logger.info(f"  [{self.source_display}] {brand}: {total_fetched} new/updated")

        return grand_total
