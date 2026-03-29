import re
import logging
from datetime import date, datetime

from marktplaats import SearchQuery, SortBy, SortOrder, category_from_name

logger = logging.getLogger(__name__)

CATEGORY = category_from_name("Motoren")


def _parse_int(value: str | None) -> int | None:
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
    images = []
    for img in listing._images:
        images.append({"medium": img.medium, "large": img.large})
    return images


def parse_listing(listing) -> dict:
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
    }


def fetch_page(offset: int = 0, offered_since: datetime | None = None, category=None) -> list:
    """Fetch a single page of 100 listings from Marktplaats."""
    sq = SearchQuery(
        query="",
        category=category or CATEGORY,
        limit=100,
        offset=offset,
        sort_by=SortBy.DATE,
        sort_order=SortOrder.DESC,
        offered_since=offered_since,
    )
    return sq.get_listings()
