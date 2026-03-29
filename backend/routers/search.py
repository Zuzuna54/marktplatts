import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query

from models import ListingResponse, ImageResponse, SearchResponse, SyncStatusResponse
from database import get_connection, get_sync_state
from filters import build_query

logger = logging.getLogger(__name__)
router = APIRouter()

DATE_POSTED_MAP = {
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _fetch_images_for_listings(conn, item_ids: list[str]) -> dict[str, list[ImageResponse]]:
    if not item_ids:
        return {}
    placeholders = ",".join("?" for _ in item_ids)
    rows = conn.execute(
        f"SELECT item_id, position, url_medium, url_large FROM listing_images "
        f"WHERE item_id IN ({placeholders}) ORDER BY item_id, position",
        item_ids,
    ).fetchall()
    result: dict[str, list[ImageResponse]] = {}
    for r in rows:
        iid = r["item_id"]
        if iid not in result:
            result[iid] = []
        result[iid].append(ImageResponse(medium=r["url_medium"], large=r["url_large"]))
    return result


def _row_to_response(row: dict, images: list[ImageResponse] | None = None) -> ListingResponse:
    return ListingResponse(
        item_id=row["item_id"],
        title=row["title"],
        description=row["description"],
        price_cents=row["price_cents"],
        price_type=row["price_type"],
        construction_year=row["construction_year"],
        mileage_km=row["mileage_km"],
        engine_cc=row["engine_cc"],
        cylinders=row["cylinders"],
        condition=row["condition"],
        motorcycle_type=row["motorcycle_type"],
        brand=row["brand"],
        engine_power=row["engine_power"],
        advertiser_type=row["advertiser_type"],
        city=row["city"],
        distance_km=row["distance_km"],
        thumbnail_url=row["thumbnail_url"],
        link=row["link"],
        post_date=row["post_date"],
        is_favorite=bool(row["is_favorite"]),
        images=images or [],
        source=row.get("source", "marktplaats"),
        is_auction=bool(row.get("is_auction", 0)),
        current_bid_cents=row.get("current_bid_cents"),
        auction_end_time=row.get("auction_end_time"),
        bid_count=row.get("bid_count"),
    )


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = "",
    price_min: int | None = Query(None),
    price_max: int | None = Query(None),
    mileage_min: int | None = Query(None),
    mileage_max: int | None = Query(None),
    engine_min: int | None = Query(None),
    engine_max: int | None = Query(None),
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    date_posted: str | None = Query(None),
    source: str | None = Query(None),
    sort_by: str = "date",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 100,
):
    date_posted_since = None
    if date_posted and date_posted in DATE_POSTED_MAP:
        cutoff = datetime.now(timezone.utc) - DATE_POSTED_MAP[date_posted]
        date_posted_since = cutoff.strftime("%Y-%m-%d")

    data_sql, count_sql, data_params, count_params = build_query(
        text_query=q.strip() or None,
        price_min=price_min,
        price_max=price_max,
        mileage_min=mileage_min,
        mileage_max=mileage_max,
        engine_min=engine_min,
        engine_max=engine_max,
        year_min=year_min,
        year_max=year_max,
        date_posted_since=date_posted_since,
        source=source,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )

    conn = get_connection()
    try:
        total_row = conn.execute(count_sql, count_params).fetchone()
        total = total_row["total"] if total_row else 0

        rows = conn.execute(data_sql, data_params).fetchall()
        row_dicts = [dict(row) for row in rows]

        item_ids = [r["item_id"] for r in row_dicts]
        images_map = _fetch_images_for_listings(conn, item_ids)

        listings = [_row_to_response(r, images_map.get(r["item_id"])) for r in row_dicts]
    finally:
        conn.close()

    return SearchResponse(
        listings=listings,
        total=total,
        has_more=(offset + limit) < total,
    )


@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status():
    state = get_sync_state()
    progress_pct = None
    if state["status"] == "syncing" and state.get("sync_type") == "full":
        from scrapers.marktplaats import SUBCATEGORIES
        total_subs = len(SUBCATEGORIES) or 1
        current = state.get("current_offset", 0) or 0
        progress_pct = min(100, (current * 100) // total_subs)

    return SyncStatusResponse(
        status=state["status"],
        sync_type=state.get("sync_type"),
        total_in_db=state.get("total_in_db", 0),
        last_completed=state.get("last_completed"),
        progress_pct=progress_pct,
        current_source=state.get("current_source"),
    )
