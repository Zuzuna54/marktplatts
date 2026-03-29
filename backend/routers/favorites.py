import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models import ListingResponse, ImageResponse
from database import get_connection

router = APIRouter()


@router.get("/favorites", response_model=list[ListingResponse])
async def list_favorites():
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT l.*, 1 as is_favorite
            FROM favorites f
            JOIN listings l ON f.item_id = l.item_id
            ORDER BY f.added_at DESC"""
        ).fetchall()
        row_dicts = [dict(r) for r in rows]
        # Fetch images
        item_ids = [r["item_id"] for r in row_dicts]
        images_map: dict[str, list[ImageResponse]] = {}
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            img_rows = conn.execute(
                f"SELECT item_id, position, url_medium, url_large FROM listing_images "
                f"WHERE item_id IN ({placeholders}) ORDER BY item_id, position",
                item_ids,
            ).fetchall()
            for ir in img_rows:
                iid = ir["item_id"]
                if iid not in images_map:
                    images_map[iid] = []
                images_map[iid].append(ImageResponse(medium=ir["url_medium"], large=ir["url_large"]))
        return [
            ListingResponse(
                item_id=r["item_id"],
                title=r["title"],
                description=r["description"],
                price_cents=r["price_cents"],
                price_type=r["price_type"],
                construction_year=r["construction_year"],
                mileage_km=r["mileage_km"],
                engine_cc=r["engine_cc"],
                cylinders=r["cylinders"],
                condition=r["condition"],
                motorcycle_type=r["motorcycle_type"],
                brand=r["brand"],
                engine_power=r["engine_power"],
                advertiser_type=r["advertiser_type"],
                city=r["city"],
                distance_km=r["distance_km"],
                thumbnail_url=r["thumbnail_url"],
                link=r["link"],
                post_date=r["post_date"],
                is_favorite=True,
                images=images_map.get(r["item_id"], []),
            )
            for r in row_dicts
        ]
    finally:
        conn.close()


@router.post("/favorites/{item_id}")
async def add_favorite(item_id: str):
    conn = get_connection()
    try:
        listing = conn.execute(
            "SELECT 1 FROM listings WHERE item_id = ?", (item_id,)
        ).fetchone()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        try:
            conn.execute(
                "INSERT OR IGNORE INTO favorites (item_id, added_at) VALUES (?, ?)",
                (item_id, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=404, detail="Listing not found")
        return {"status": "ok"}
    finally:
        conn.close()


@router.delete("/favorites/{item_id}")
async def remove_favorite(item_id: str):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM favorites WHERE item_id = ?", (item_id,))
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()
