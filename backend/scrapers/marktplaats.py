import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from marktplaats import SearchQuery, SortBy, SortOrder
from marktplaats.categories import L2Category

from scrapers.base import BaseScraper
from database import (
    upsert_listings_bulk, update_sync_state, count_listings,
    get_source_sync_date, update_source_sync_date_from_listings,
)

logger = logging.getLogger(__name__)

DELAY = 1.5
INCREMENTAL_BUFFER = timedelta(hours=1)

SKIP_PREFIXES = [
    "Accessoires", "Onderdelen", "Kleding", "Handleidingen",
    "Tuning", "Overige Motoren", "Motoren Inkoop",
]

# Load motorcycle-only L2 subcategories
_l2_path = Path(__file__).parents[1] / "venv" / "lib"
_l2_file = next(_l2_path.rglob("l2_categories.json"), None)
SUBCATEGORIES: list[dict] = []
if _l2_file:
    _data = json.loads(_l2_file.read_text())
    SUBCATEGORIES = sorted(
        [
            {"name": v["name"], "id": v["id"]}
            for v in _data.values()
            if v.get("parent") == "Motoren"
            and not any(v["name"].startswith(prefix) for prefix in SKIP_PREFIXES)
        ],
        key=lambda x: x["name"],
    )


def _parse_int(value: str | None) -> int | None:
    import re
    if not value:
        return None
    match = re.search(r"(\d+)", value.replace(".", "").replace(",", ""))
    return int(match.group(1)) if match else None


def _get_attr(listing, key: str) -> str | None:
    for attr in listing.attributes:
        if attr.get("key") == key:
            return attr.get("value")
    for attr in listing.extended_attributes:
        if attr.get("key") == key:
            return attr.get("value")
    return None


def _get_images(listing) -> list[dict]:
    return [{"medium": img.medium, "large": img.large} for img in listing._images]


def _parse_listing(listing) -> dict:
    from datetime import date
    images = _get_images(listing)
    return {
        "item_id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "price_cents": int(listing.price * 100) if listing.price else None,
        "price_type": listing.price_type.value if listing.price_type else None,
        "construction_year": _parse_int(_get_attr(listing, "constructionYear")),
        "mileage_km": _parse_int(_get_attr(listing, "mileage")),
        "engine_cc": _parse_int(_get_attr(listing, "engineDisplacement")),
        "cylinders": _parse_int(_get_attr(listing, "numberOfCilinders")),
        "condition": _get_attr(listing, "condition"),
        "motorcycle_type": _get_attr(listing, "motorcycleType"),
        "brand": _get_attr(listing, "brand"),
        "engine_power": _get_attr(listing, "enginePower"),
        "advertiser_type": _get_attr(listing, "advertiser"),
        "city": listing.location.city if listing.location else None,
        "latitude": listing.location.latitude if listing.location else None,
        "longitude": listing.location.longitude if listing.location else None,
        "distance_km": (
            listing.location.distance / 1000.0
            if listing.location and listing.location.distance
            else None
        ),
        "seller_id": str(listing.seller.id) if listing.seller else None,
        "seller_name": listing.seller.name if listing.seller else None,
        "thumbnail_url": images[0]["large"] if images else None,
        "link": listing.link,
        "post_date": listing.date.isoformat() if isinstance(listing.date, date) else None,
        "images": images,
        "source": "marktplaats",
        "is_auction": 0,
        "current_bid_cents": None,
        "auction_end_time": None,
        "bid_count": None,
    }


def _fetch_page(category: L2Category, offset: int, offered_since: datetime | None = None) -> list:
    sq = SearchQuery(
        query="",
        category=category,
        limit=100,
        offset=offset,
        sort_by=SortBy.DATE,
        sort_order=SortOrder.DESC,
        offered_since=offered_since,
    )
    return sq.get_listings()


async def _fetch_category(
    category: L2Category,
    cat_name: str,
    offered_since: datetime | None = None,
    start_page: int = 0,
) -> tuple[int, list[str]]:
    offset = start_page * 100
    total_fetched = 0
    all_item_ids: list[str] = []

    while True:
        try:
            raw = await asyncio.to_thread(_fetch_page, category, offset, offered_since)
        except Exception as e:
            logger.warning(f"Error fetching {cat_name} offset={offset}: {e}", exc_info=True)
            break

        if not raw:
            break

        parsed = []
        for listing in raw:
            try:
                parsed.append(_parse_listing(listing))
            except Exception as e:
                logger.warning(f"Parse error in {cat_name}: {e}")

        if parsed:
            upsert_listings_bulk(parsed)
            all_item_ids.extend(p["item_id"] for p in parsed)

        total_fetched += len(parsed)
        offset += 100

        update_sync_state(current_page_offset=offset // 100)

        if len(raw) < 100:
            break

        await asyncio.sleep(DELAY)

    return total_fetched, all_item_ids


class MarktplaatsScraper(BaseScraper):
    source_id = "marktplaats"
    source_display = "Marktplaats"

    async def full_sync(self) -> int:
        state_import = __import__("database", fromlist=["get_sync_state"])
        state = state_import.get_sync_state()

        if state["status"] == "syncing" and state.get("current_source") == self.source_id:
            resume_from = state.get("current_offset", 0) or 0
            resume_page = state.get("current_page_offset", 0) or 0
            grand_total = state.get("total_fetched", 0) or 0
            logger.info(f"[{self.source_display}] Resuming from subcategory {resume_from}/{len(SUBCATEGORIES)}, page {resume_page}")
        else:
            resume_from = 0
            resume_page = 0
            grand_total = 0

        for i, sub in enumerate(SUBCATEGORIES):
            if i < resume_from:
                continue

            cat_name = sub["name"]
            try:
                category = L2Category.from_name(cat_name)
            except ValueError:
                logger.warning(f"Could not find category: {cat_name}")
                continue

            start_page = resume_page if i == resume_from else 0
            logger.info(f"  [{self.source_display}] [{i + 1}/{len(SUBCATEGORIES)}] {cat_name}" + (f" (page {start_page})" if start_page > 0 else ""))

            count, item_ids = await _fetch_category(category, cat_name, start_page=start_page)

            if item_ids:
                update_source_sync_date_from_listings(self.source_id, cat_name, item_ids)

            grand_total += count
            db_total = count_listings()
            update_sync_state(
                current_offset=i + 1,
                current_page_offset=0,
                total_fetched=grand_total,
                total_in_db=db_total,
            )
            logger.info(f"  [{self.source_display}] {cat_name}: {count} fetched (DB: {db_total:,})")

            await asyncio.sleep(DELAY)

        return grand_total

    async def incremental_sync(self) -> int:
        grand_total = 0

        for sub in SUBCATEGORIES:
            cat_name = sub["name"]
            try:
                category = L2Category.from_name(cat_name)
            except ValueError:
                continue

            latest_date = get_source_sync_date(self.source_id, cat_name)
            if latest_date:
                since = datetime.fromisoformat(latest_date).replace(tzinfo=timezone.utc) - INCREMENTAL_BUFFER
            else:
                since = datetime.now(timezone.utc) - timedelta(days=1)

            count, item_ids = await _fetch_category(category, cat_name, offered_since=since)

            if item_ids:
                update_source_sync_date_from_listings(self.source_id, cat_name, item_ids)

            grand_total += count

            if count > 0:
                logger.info(f"  [{self.source_display}] {cat_name}: {count} new/updated")

            await asyncio.sleep(0.5)

        return grand_total
