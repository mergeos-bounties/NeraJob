from .base import BaseScraper
from .lever import LeverScraper

# Existing registry
SCRAPER_REGISTRY = {
    # ... existing scrapers ...
}

# Add Lever scraper to registry
SCRAPER_REGISTRY['lever'] = LeverScraper