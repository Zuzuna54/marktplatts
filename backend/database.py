import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "marktplatts.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    item_id           TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    description       TEXT,
    price_cents       INTEGER,
    price_type        TEXT,
    construction_year INTEGER,
    mileage_km        INTEGER,
    engine_cc         INTEGER,
    cylinders         INTEGER,
    condition         TEXT,
    motorcycle_type   TEXT,
    brand             TEXT,
    engine_power      TEXT,
    advertiser_type   TEXT,
    city              TEXT,
    latitude          REAL,
    longitude         REAL,
    distance_km       REAL,
    seller_id         TEXT,
    seller_name       TEXT,
    thumbnail_url     TEXT,
    link              TEXT NOT NULL,
    post_date         TEXT,
    fetched_at        TEXT NOT NULL,
    source            TEXT NOT NULL DEFAULT 'marktplaats',
    is_auction        INTEGER DEFAULT 0,
    current_bid_cents INTEGER,
    auction_end_time  TEXT,
    bid_count         INTEGER
);

CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price_cents);
CREATE INDEX IF NOT EXISTS idx_listings_year ON listings(construction_year);
CREATE INDEX IF NOT EXISTS idx_listings_mileage ON listings(mileage_km);
CREATE INDEX IF NOT EXISTS idx_listings_engine ON listings(engine_cc);
CREATE INDEX IF NOT EXISTS idx_listings_post_date ON listings(post_date);
CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source);

CREATE TABLE IF NOT EXISTS listing_images (
    item_id    TEXT NOT NULL,
    position   INTEGER NOT NULL,
    url_medium TEXT,
    url_large  TEXT,
    PRIMARY KEY (item_id, position),
    FOREIGN KEY (item_id) REFERENCES listings(item_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorites (
    item_id  TEXT PRIMARY KEY,
    added_at TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES listings(item_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_sync_dates (
    source           TEXT NOT NULL,
    category_name    TEXT NOT NULL,
    latest_post_date TEXT NOT NULL,
    PRIMARY KEY (source, category_name)
);

CREATE TABLE IF NOT EXISTS sync_state (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    status          TEXT NOT NULL DEFAULT 'idle',
    sync_type       TEXT,
    current_offset      INTEGER DEFAULT 0,
    current_page_offset INTEGER DEFAULT 0,
    total_fetched       INTEGER DEFAULT 0,
    total_in_db     INTEGER DEFAULT 0,
    last_completed  TEXT,
    last_error      TEXT,
    started_at      TEXT,
    current_source  TEXT
);
"""

# Migrations for existing databases
MIGRATIONS = [
    ("source", "ALTER TABLE listings ADD COLUMN source TEXT NOT NULL DEFAULT 'marktplaats'"),
    ("is_auction", "ALTER TABLE listings ADD COLUMN is_auction INTEGER DEFAULT 0"),
    ("current_bid_cents", "ALTER TABLE listings ADD COLUMN current_bid_cents INTEGER"),
    ("auction_end_time", "ALTER TABLE listings ADD COLUMN auction_end_time TEXT"),
    ("bid_count", "ALTER TABLE listings ADD COLUMN bid_count INTEGER"),
    ("current_source", "ALTER TABLE sync_state ADD COLUMN current_source TEXT"),
    ("current_page_offset", "ALTER TABLE sync_state ADD COLUMN current_page_offset INTEGER DEFAULT 0"),
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO sync_state (id, status) VALUES (1, 'idle')")
    # Run migrations for existing DBs
    for _name, sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # Column/table already exists
    # Create source index if missing
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source)")
    except sqlite3.OperationalError:
        pass
    # Migrate old category_sync_dates to source_sync_dates
    try:
        rows = conn.execute("SELECT category_name, latest_post_date FROM category_sync_dates").fetchall()
        for r in rows:
            conn.execute(
                "INSERT OR IGNORE INTO source_sync_dates (source, category_name, latest_post_date) VALUES (?, ?, ?)",
                ("marktplaats", r["category_name"], r["latest_post_date"]),
            )
    except sqlite3.OperationalError:
        pass  # Old table doesn't exist
    conn.commit()
    conn.close()


def upsert_listings_bulk(listings: list[dict]):
    """Insert or update listings and their images."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.executemany(
            """INSERT INTO listings
            (item_id, title, description, price_cents, price_type,
             construction_year, mileage_km, engine_cc, cylinders,
             condition, motorcycle_type, brand, engine_power,
             advertiser_type, city, latitude, longitude, distance_km,
             seller_id, seller_name, thumbnail_url, link, post_date,
             fetched_at, source, is_auction, current_bid_cents,
             auction_end_time, bid_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                price_cents = excluded.price_cents,
                price_type = excluded.price_type,
                construction_year = excluded.construction_year,
                mileage_km = excluded.mileage_km,
                engine_cc = excluded.engine_cc,
                cylinders = excluded.cylinders,
                condition = excluded.condition,
                motorcycle_type = excluded.motorcycle_type,
                brand = excluded.brand,
                engine_power = excluded.engine_power,
                advertiser_type = excluded.advertiser_type,
                city = excluded.city,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                distance_km = excluded.distance_km,
                seller_id = excluded.seller_id,
                seller_name = excluded.seller_name,
                thumbnail_url = excluded.thumbnail_url,
                link = excluded.link,
                post_date = excluded.post_date,
                fetched_at = excluded.fetched_at,
                is_auction = excluded.is_auction,
                current_bid_cents = excluded.current_bid_cents,
                auction_end_time = excluded.auction_end_time,
                bid_count = excluded.bid_count""",
            [
                (
                    l["item_id"], l["title"], l["description"],
                    l["price_cents"], l["price_type"],
                    l["construction_year"], l["mileage_km"],
                    l["engine_cc"], l["cylinders"],
                    l["condition"], l["motorcycle_type"], l["brand"],
                    l["engine_power"], l["advertiser_type"],
                    l["city"], l["latitude"], l["longitude"],
                    l["distance_km"], l["seller_id"], l["seller_name"],
                    l["thumbnail_url"], l["link"], l["post_date"],
                    now, l.get("source", "marktplaats"),
                    l.get("is_auction", 0), l.get("current_bid_cents"),
                    l.get("auction_end_time"), l.get("bid_count"),
                )
                for l in listings
            ],
        )
        # Upsert images: delete old then insert new
        item_ids = [l["item_id"] for l in listings]
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            conn.execute(f"DELETE FROM listing_images WHERE item_id IN ({placeholders})", item_ids)
        image_rows = []
        for l in listings:
            for i, img in enumerate(l.get("images", [])):
                image_rows.append((l["item_id"], i, img["medium"], img["large"]))
        if image_rows:
            conn.executemany(
                "INSERT INTO listing_images (item_id, position, url_medium, url_large) VALUES (?, ?, ?, ?)",
                image_rows,
            )
        conn.commit()
    finally:
        conn.close()


def get_sync_state() -> dict:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM sync_state WHERE id = 1").fetchone()
        return dict(row) if row else {"id": 1, "status": "idle"}
    finally:
        conn.close()


def update_sync_state(**kwargs):
    conn = get_connection()
    try:
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values())
        conn.execute(f"UPDATE sync_state SET {sets} WHERE id = 1", vals)
        conn.commit()
    finally:
        conn.close()


def get_source_sync_date(source: str, category_name: str) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT latest_post_date FROM source_sync_dates WHERE source = ? AND category_name = ?",
            (source, category_name),
        ).fetchone()
        return row["latest_post_date"] if row else None
    finally:
        conn.close()


def update_source_sync_date_from_listings(source: str, category_name: str, item_ids: list[str]):
    if not item_ids:
        return
    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in item_ids)
        row = conn.execute(
            f"SELECT MAX(post_date) as latest FROM listings WHERE item_id IN ({placeholders}) AND post_date IS NOT NULL",
            item_ids,
        ).fetchone()
        if row and row["latest"]:
            conn.execute(
                "INSERT OR REPLACE INTO source_sync_dates (source, category_name, latest_post_date) VALUES (?, ?, ?)",
                (source, category_name, row["latest"]),
            )
            conn.commit()
    finally:
        conn.close()


def count_listings() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    finally:
        conn.close()
