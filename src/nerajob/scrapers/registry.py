from .base import BaseScraper
from .himalayas import HimalayasScraper

# Existing imports...

def get_scrapers() -> List[BaseScraper]:
    """Get all available scrapers."""
    return [
        # Existing scrapers...
        HimalayasScraper(),
    ]