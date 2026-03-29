def build_query(
    text_query: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    mileage_min: int | None = None,
    mileage_max: int | None = None,
    engine_min: int | None = None,
    engine_max: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    date_posted_since: str | None = None,
    source: str | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 100,
) -> tuple[str, str, list, list]:
    """Returns (data_sql, count_sql, data_params, count_params).
    Queries the flat listings table directly — no junction table."""
    conditions: list[str] = []
    params: list = []

    if text_query:
        conditions.append("(l.title LIKE ? OR l.description LIKE ?)")
        pattern = f"%{text_query}%"
        params.extend([pattern, pattern])
    if price_min is not None:
        conditions.append("l.price_cents >= ?")
        params.append(price_min * 100)
    if price_max is not None:
        conditions.append("l.price_cents <= ?")
        params.append(price_max * 100)
    if mileage_min is not None:
        conditions.append("l.mileage_km IS NOT NULL AND l.mileage_km >= ?")
        params.append(mileage_min)
    if mileage_max is not None:
        conditions.append("l.mileage_km IS NOT NULL AND l.mileage_km <= ?")
        params.append(mileage_max)
    if engine_min is not None:
        conditions.append("l.engine_cc IS NOT NULL AND l.engine_cc >= ?")
        params.append(engine_min)
    if engine_max is not None:
        conditions.append("l.engine_cc IS NOT NULL AND l.engine_cc <= ?")
        params.append(engine_max)
    if year_min is not None:
        conditions.append("l.construction_year IS NOT NULL AND l.construction_year >= ?")
        params.append(year_min)
    if year_max is not None:
        conditions.append("l.construction_year IS NOT NULL AND l.construction_year <= ?")
        params.append(year_max)
    if date_posted_since is not None:
        conditions.append("l.post_date IS NOT NULL AND l.post_date >= ?")
        params.append(date_posted_since)
    if source is not None:
        conditions.append("l.source = ?")
        params.append(source)

    where = " AND ".join(conditions) if conditions else "1=1"

    sort_map = {
        "price": "l.price_cents",
        "mileage": "l.mileage_km",
        "year": "l.construction_year",
        "date": "l.post_date",
        "engine": "l.engine_cc",
    }
    sort_col = sort_map.get(sort_by, "l.post_date")
    direction = "DESC" if sort_order.lower() == "desc" else "ASC"

    data_sql = (
        f"SELECT l.*, CASE WHEN f.item_id IS NOT NULL THEN 1 ELSE 0 END as is_favorite "
        f"FROM listings l LEFT JOIN favorites f ON l.item_id = f.item_id "
        f"WHERE {where} "
        f"ORDER BY {sort_col} {direction} NULLS LAST "
        f"LIMIT ? OFFSET ?"
    )
    count_sql = f"SELECT COUNT(*) as total FROM listings l WHERE {where}"

    data_params = params + [limit, offset]
    count_params = list(params)

    return data_sql, count_sql, data_params, count_params
