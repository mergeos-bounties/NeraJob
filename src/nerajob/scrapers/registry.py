# Add to the existing registry dictionary
from .greenhouse import GreenhouseScraper

SCRAPER_REGISTRY = {
    # ... existing entries ...
    'greenhouse': GreenhouseScraper,
}