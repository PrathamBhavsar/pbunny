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
        self.base_url = "https://pimpbunny.com/videos/{}/?videos_per_page=32&sort_by=post_date"
        
    def fetch_html(self, page: int) -> Optional[str]:
        try:
            url = self.base_url.format(page)
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                self.logger.info(f"Page {page}: Fetched {len(response.text)} bytes")
                return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.info(f"Page {page}: 404 - No more pages")
                return None
            self.logger.error(f"Page {page}: HTTP error {e.response.status_code}")
            return None
        except httpx.TimeoutException as e:
            self.logger.error(f"Page {page}: Timeout - {e}")
            return None
        except Exception as e:
            self.logger.error(f"Page {page}: Unexpected error - {e}", exc_info=True)
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
            page = 1515
            all_links = []
            
            while True:
                self.logger.info(f"Scraping page {page}")
                html = self.fetch_html(page)
                
                if not html:
                    self.logger.info(f"Stopping at page {page}")
                    break
                
                links = self.parse_video_links(html)
                if not links:
                    self.logger.warning(f"Page {page}: No links found")
                    break
                
                all_links.extend(links)
                self.logger.info(f"Page {page}: Found {len(links)} links (Total: {len(all_links)})")
                page += 1
            
            return all_links
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}", exc_info=True)
            return []