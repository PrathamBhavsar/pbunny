import logging
from typing import List, Optional
import httpx
from selectolax.parser import HTMLParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PageScraper:
    def __init__(self, timeout: int = 30):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout
        self.target_url = "https://pimpbunny.com/videos/1/?videos_per_page=128&sort_by=post_date"
        
    def fetch_html(self) -> Optional[str]:
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(self.target_url)
                response.raise_for_status()
                self.logger.info(f"Fetched {len(response.text)} bytes")
                return response.text
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout fetching URL: {e}")
            return None
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error {e.response.status_code}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching HTML: {e}", exc_info=True)
            return None
    
    def parse_video_links(self, html: str) -> List[str]:
        try:
            parser = HTMLParser(html)
            links = []
            
            nodes = parser.css('a.pb-item-link.pb-item-link-video')
            
            for node in nodes:
                href = node.attributes.get('href', '')
                if href.startswith('https://pimpbunny.com/videos/'):
                    links.append(href)
            
            self.logger.info(f"Parsed {len(links)} video links")
            return links
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}", exc_info=True)
            return []
    
    def scrape(self) -> List[str]:
        try:
            html = self.fetch_html()
            if not html:
                self.logger.error("Failed to fetch HTML")
                return []
            
            links = self.parse_video_links(html)
            return links
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}", exc_info=True)
            return []