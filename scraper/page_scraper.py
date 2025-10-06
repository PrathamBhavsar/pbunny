import logging
from typing import List, Optional, Tuple
import httpx
from selectolax.parser import HTMLParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PageScraper:
    def __init__(self, base_url: str, timeout: int = 30, pages_per_parse: int = 10):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url_template = base_url.replace('/1/', '/{}/')
        self.timeout = timeout
        self.pages_per_parse = pages_per_parse
        
    def fetch_html(self, page: int) -> Optional[str]:
        try:
            url = self.base_url_template.format(page)
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                self.logger.info(f"Page {page}: Fetched {len(response.text)} bytes")
                return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.info(f"Page {page}: 404 - Page not found")
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
    
    def scrape(self, start_page: Optional[int] = None) -> Tuple[List[str], int]:
        """
        Scrape video links in reverse order (decrementing page numbers).
        Returns: (list of video links, last successfully parsed page)
        """
        try:
            # If start_page is provided, use it; otherwise start from default
            if start_page is None:
                page = 1526
                self.logger.info(f"Starting from default page: {page}")
            else:
                page = start_page
                self.logger.info(f"Resuming from page: {page}")
            
            all_links = []
            pages_parsed = 0
            last_successful_page = page
            
            while page >= 1 and pages_parsed < self.pages_per_parse:
                self.logger.info(f"Scraping page {page} (Progress: {pages_parsed + 1}/{self.pages_per_parse})")
                html = self.fetch_html(page)
                
                if not html:
                    self.logger.warning(f"Page {page}: Failed to fetch, stopping")
                    break
                
                links = self.parse_video_links(html)
                if not links:
                    self.logger.warning(f"Page {page}: No links found, stopping")
                    break
                
                all_links.extend(links)
                last_successful_page = page
                pages_parsed += 1
                
                self.logger.info(f"Page {page}: Found {len(links)} links (Total: {len(all_links)}, Pages: {pages_parsed}/{self.pages_per_parse})")
                
                # Move to previous page
                page -= 1
            
            if page < 1:
                self.logger.info("Reached page 1, scraping complete")
            elif pages_parsed >= self.pages_per_parse:
                self.logger.info(f"Completed {self.pages_per_parse} pages for this parse session")
            
            return all_links, last_successful_page
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}", exc_info=True)
            return [], last_successful_page if 'last_successful_page' in locals() else (start_page or 1526)