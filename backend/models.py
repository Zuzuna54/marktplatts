from pydantic import BaseModel


class ImageResponse(BaseModel):
    medium: str
    large: str


class ListingResponse(BaseModel):
    item_id: str
    title: str
    description: str | None
    price_cents: int | None
    price_type: str | None
    construction_year: int | None
    mileage_km: int | None
    engine_cc: int | None
    cylinders: int | None
    condition: str | None
    motorcycle_type: str | None
    brand: str | None
    engine_power: str | None
    advertiser_type: str | None
    city: str | None
    distance_km: float | None
    thumbnail_url: str | None
    link: str
    post_date: str | None
    is_favorite: bool = False
    images: list[ImageResponse] = []
    source: str = "marktplaats"
    is_auction: bool = False
    current_bid_cents: int | None = None
    auction_end_time: str | None = None
    bid_count: int | None = None


class SearchResponse(BaseModel):
    listings: list[ListingResponse]
    total: int
    has_more: bool


class SyncStatusResponse(BaseModel):
    status: str
    sync_type: str | None
    total_in_db: int
    last_completed: str | None
    progress_pct: int | None = None
    current_source: str | None = None
