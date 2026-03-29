import asyncio
import logging
from datetime import datetime, timezone, timedelta

from scrapers import SOURCES
from database import get_sync_state, update_sync_state, count_listings

logger = logging.getLogger(__name__)

INCREMENTAL_INTERVAL = timedelta(minutes=30)


async def start_sync():
    """Main sync loop. Iterates all registered sources sequentially."""
    source_names = ", ".join(s.source_display for s in SOURCES)
    logger.info(f"Sync engine started with {len(SOURCES)} sources: {source_names}")

    while True:
        try:
            state = get_sync_state()

            if state["last_completed"] is None or state["status"] == "syncing":
                await _full_sync()
            else:
                last = datetime.fromisoformat(state["last_completed"])
                elapsed = datetime.now(timezone.utc) - last

                if elapsed >= INCREMENTAL_INTERVAL:
                    logger.info(f"Starting incremental sync ({elapsed.total_seconds() / 60:.0f} min since last)")
                    await _incremental_sync()
                else:
                    wait = (INCREMENTAL_INTERVAL - elapsed).total_seconds()
                    db_count = count_listings()
                    logger.info(f"Synced ({db_count:,} listings). Next sync in {wait / 60:.0f} min")
                    await asyncio.sleep(wait)
                    continue

        except Exception as e:
            logger.error(f"Sync error: {e}", exc_info=True)
            update_sync_state(status="idle", last_error=str(e))
            await asyncio.sleep(60)
            continue

        await asyncio.sleep(10)


async def _full_sync():
    """Full sync: iterate all sources."""
    state = get_sync_state()

    if state["status"] != "syncing":
        update_sync_state(
            status="syncing", sync_type="full",
            current_offset=0, current_page_offset=0,
            total_fetched=0, current_source=None,
            started_at=datetime.now(timezone.utc).isoformat(), last_error=None,
        )
        logger.info(f"Starting full sync across {len(SOURCES)} sources")

    grand_total = 0

    for source in SOURCES:
        update_sync_state(current_source=source.source_id)
        logger.info(f"[Full] Syncing source: {source.source_display}")

        try:
            count = await source.full_sync()
        except Exception as e:
            logger.error(f"[Full] {source.source_display} failed: {e}", exc_info=True)
            count = 0

        grand_total += count
        db_total = count_listings()
        update_sync_state(total_fetched=grand_total, total_in_db=db_total)
        logger.info(f"[Full] {source.source_display}: {count:,} fetched (DB: {db_total:,})")

    db_total = count_listings()
    update_sync_state(
        status="completed",
        last_completed=datetime.now(timezone.utc).isoformat(),
        total_in_db=db_total,
        current_source=None,
    )
    logger.info(f"Full sync completed: {grand_total:,} fetched, {db_total:,} in DB")


async def _incremental_sync():
    """Incremental sync: fetch new listings from each source."""
    update_sync_state(
        status="syncing", sync_type="incremental",
        current_offset=0, current_page_offset=0,
        total_fetched=0, current_source=None,
        started_at=datetime.now(timezone.utc).isoformat(), last_error=None,
    )

    grand_total = 0

    for source in SOURCES:
        update_sync_state(current_source=source.source_id)

        try:
            count = await source.incremental_sync()
        except Exception as e:
            logger.error(f"[Incremental] {source.source_display} failed: {e}", exc_info=True)
            count = 0

        grand_total += count

        if count > 0:
            logger.info(f"[Incremental] {source.source_display}: {count:,} new/updated")

    db_total = count_listings()
    update_sync_state(
        status="completed",
        last_completed=datetime.now(timezone.utc).isoformat(),
        total_in_db=db_total,
        total_fetched=grand_total,
        current_source=None,
    )
    logger.info(f"Incremental sync completed: {grand_total:,} new/updated, {db_total:,} in DB")
