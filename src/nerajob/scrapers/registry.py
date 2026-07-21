from .base_scraper import BaseScraper
from .indeed_scraper import IndeedScraper
from .linkedin_scraper import LinkedInScraper
from .muse_scraper import MuseScraper

SCRAPERS: dict[str, BaseScraper] = {
    "indeed": IndeedScraper(),
    "linkedin": LinkedInScraper(),
    "muse": MuseScraper()
}