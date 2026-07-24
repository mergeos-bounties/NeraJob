import requests
from bs4 import BeautifulSoup
import time
from typing import List
from src.nerajob.scrapers.base import BaseScraper

class VietnamWorksScraper(BaseScraper):
    def __init__(self):
        self.source_name = 'vietnamworks'
        self.base_url = 'https://www.vietnamworks.com'
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

    def search(self, query: str, location: str, limit: int) -> List[dict]:
        url = f'{self.base_url}/tim-viec-lam/{query}'
        headers = {'User-Agent': self.user_agent}
        response = requests.get(url, headers=headers)
        time.sleep(1)  # rate limiting

        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.find_all('div', class_='job-listing')

        jobs = []
        for job in job_listings:
            title = job.find('h2', class_='job-title').text.strip()
            company = job.find('span', class_='company-name').text.strip()
            link = job.find('a')['href']
            jobs.append({
                'title': title,
                'company': company,
                'link': link
            })

            if len(jobs) >= limit:
                break

        return jobs

def register_scraper():
    from src.nerajob.scrapers.registry import register
    register(VietnamWorksScraper())

register_scraper()