import logging
import json
from pathlib import Path
from typing import Dict, Any

class ProgressManager:
    def __init__(self, progress_path: str = "progress.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.progress_path = Path(progress_path)
        self.progress = self._load_progress()
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load progress from file or create default progress."""
        try:
            if self.progress_path.exists():
                with open(self.progress_path, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                self.logger.info(f"Loaded progress: Last page {progress.get('last_parsed_page', 'N/A')}, Total videos: {progress.get('total_videos_parsed', 0)}")
                return progress
            else:
                self.logger.info("No progress file found, creating new progress")
                return {
                    'last_parsed_page': None,
                    'total_videos_parsed': 0
                }
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in progress file: {e}", exc_info=True)
            return {
                'last_parsed_page': None,
                'total_videos_parsed': 0
            }
        except Exception as e:
            self.logger.error(f"Error loading progress: {e}", exc_info=True)
            return {
                'last_parsed_page': None,
                'total_videos_parsed': 0
            }
    
    def get_last_parsed_page(self) -> int:
        """Get the last successfully parsed page number."""
        return self.progress.get('last_parsed_page')
    
    def get_total_videos_parsed(self) -> int:
        """Get the total number of videos parsed so far."""
        return self.progress.get('total_videos_parsed', 0)
    
    def save_progress(self, last_page: int, total_videos: int):
        """Save the current progress to file."""
        try:
            self.progress['last_parsed_page'] = last_page
            self.progress['total_videos_parsed'] = total_videos
            
            with open(self.progress_path, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Progress saved: Page {last_page}, Total videos: {total_videos}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving progress: {e}", exc_info=True)
            return False
    
    def update_progress(self, last_page: int, videos_count: int):
        """Update progress incrementally."""
        try:
            current_total = self.progress.get('total_videos_parsed', 0)
            new_total = current_total + videos_count
            return self.save_progress(last_page, new_total)
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}", exc_info=True)
            return False