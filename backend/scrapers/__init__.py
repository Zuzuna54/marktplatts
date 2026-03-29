from scrapers.marktplaats import MarktplaatsScraper
from scrapers.autoscout24 import AutoScout24Scraper

# Registry of all active scrapers — sync.py iterates this list
SOURCES = [
    MarktplaatsScraper(),
    AutoScout24Scraper(),
    # TweedehandsScraper(),    # Phase 3
    # MotoroccasionScraper(),  # Phase 4
    # BVAAuctionsScraper(),    # Phase 5
    # CatawikiScraper(),       # Phase 6
]
