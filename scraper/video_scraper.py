import logging
import json
import re
from pathlib import Path
from typing import Optional, Dict, List
import httpx
from selectolax.parser import HTMLParser

class VideoScraper:
    def __init__(self, timeout: int = 30, output_dir: str = "./downloads"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()
        
    def _ensure_output_dir(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {e}", exc_info=True)
            raise
        
    def fetch_html(self, url: str) -> Optional[str]:
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout fetching {url}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}", exc_info=True)
            return None
    
    def extract_video_data(self, html: str) -> Optional[Dict]:
        try:
            parser = HTMLParser(html)
            script_tags = parser.css('script[type="text/javascript"]')
            
            for script in script_tags:
                script_content = script.text()
                if not script_content or 'video_id:' not in script_content:
                    continue
                
                video_id = self._extract_field(script_content, r"video_id:\s*'([^']+)'")
                if not video_id:
                    continue
                
                title = self._extract_field(script_content, r"video_title:\s*'([^']+)'")
                models = self._extract_field(script_content, r"video_models:\s*'([^']+)'")
                categories_str = self._extract_field(script_content, r"video_categories:\s*'([^']*)'")
                
                categories = [cat.strip() for cat in categories_str.split(',')] if categories_str else []
                categories = [cat for cat in categories if cat]
                
                return {
                    'video_id': video_id,
                    'title': title or '',
                    'model': models or '',
                    'categories': categories
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting video data: {e}", exc_info=True)
            return None
    
    def _extract_field(self, text: str, pattern: str) -> Optional[str]:
        try:
            match = re.search(pattern, text)
            return match.group(1) if match else None
        except Exception:
            return None
        
    def save_json(self, data: Dict) -> bool:
        try:
            video_id = data.get('video_id')
            if not video_id:
                self.logger.error("No video_id in data")
                return False
            
            folder_path = self.output_dir / str(video_id)
            folder_path.mkdir(parents=True, exist_ok=True)  

            filepath = folder_path / f"{video_id}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {video_id}/{video_id}.json")
            return True

        except Exception as e:
            self.logger.error(f"Error saving JSON: {e}", exc_info=True)
            return False

    
    def scrape_video(self, url: str) -> bool:
        try:
            html = self.fetch_html(url)
            if not html:
                return False
            
            data = self.extract_video_data(html)
            if not data:
                self.logger.warning(f"No data extracted from {url}")
                return False
            
            return self.save_json(data)
            
        except Exception as e:
            self.logger.error(f"Failed scraping {url}: {e}", exc_info=True)
            return False