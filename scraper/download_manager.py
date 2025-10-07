import logging
import json
import re
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional

class DownloadManager:
    def __init__(self, downloads_dir: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.downloads_dir = Path(downloads_dir)
        self.idm_path = self._find_idm()
        
    def _find_idm(self) -> Optional[str]:
        try:
            possible_paths = [
                r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe",
                r"C:\Program Files\Internet Download Manager\IDMan.exe",
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    self.logger.info(f"Found IDM at: {path}")
                    return path
            
            self.logger.error("IDM not found in default locations")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding IDM: {e}", exc_info=True)
            return None
    
    def _has_quality_marker(self, url: str) -> bool:
        try:
            pattern = r'_\d+p\.mp4'
            return bool(re.search(pattern, url))
        except Exception:
            return False
    
    def _extract_video_urls(self, json_path: Path) -> List[str]:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video_urls = data.get('video_urls', [])
            filtered_urls = [url for url in video_urls if self._has_quality_marker(url)]
            
            return filtered_urls
            
        except Exception as e:
            self.logger.error(f"Error reading {json_path}: {e}", exc_info=True)
            return []
    
    def _extract_quality_from_url(self, url: str) -> Optional[str]:
        try:
            match = re.search(r'_(\d+p)\.mp4', url)
            return match.group(1) if match else None
        except Exception:
            return None
    
    def _add_to_idm(self, url: str, output_dir: Path, video_id: str) -> bool:
        try:
            if not self.idm_path:
                self.logger.error("IDM path not set")
                return False
            
            quality = self._extract_quality_from_url(url)
            if not quality:
                self.logger.warning(f"Could not extract quality from URL: {url}")
                return False
            
            filename = f"{video_id}_{quality}.mp4"
            
            # Use /d flag to add without prompting, /a to add to queue
            cmd = [
                self.idm_path,
                "/d", url,
                "/p", str(output_dir),
                "/f", filename,
                "/n",
                "/a"
            ]
            
            # Increased timeout and added retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    
                    if result.returncode == 0:
                        self.logger.info(f"Queued: {video_id}_{quality}.mp4")
                        # Small delay to prevent overwhelming IDM
                        time.sleep(0.5)
                        return True
                    else:
                        if attempt < max_retries - 1:
                            self.logger.warning(f"IDM returned {result.returncode}, retrying... ({attempt + 1}/{max_retries})")
                            time.sleep(1)
                        else:
                            self.logger.warning(f"IDM returned {result.returncode} for {url} after {max_retries} attempts")
                            return False
                            
                except subprocess.TimeoutExpired:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Timeout adding {url} to IDM, retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(2)
                    else:
                        self.logger.error(f"Timeout adding {url} to IDM after {max_retries} attempts")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error adding {url} to IDM: {e}", exc_info=True)
            return False
        
        return False
    
    def _start_idm_downloads(self) -> bool:
        """Start IDM downloads without closing the application."""
        try:
            if not self.idm_path:
                return False
            
            # Use /s flag to start queued downloads
            cmd = [self.idm_path, "/s"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            if result.returncode == 0:
                self.logger.info("IDM downloads started successfully")
                return True
            else:
                self.logger.warning(f"IDM start command returned code: {result.returncode}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error starting IDM downloads: {e}", exc_info=True)
            return False
    
    def process_downloads(self) -> Dict[str, int]:
        try:
            if not self.idm_path:
                self.logger.error("Cannot process downloads: IDM not found")
                return {'total': 0, 'queued': 0, 'failed': 0}
            
            json_files = list(self.downloads_dir.rglob("*.json"))
            
            if not json_files:
                self.logger.warning("No JSON files found")
                return {'total': 0, 'queued': 0, 'failed': 0}
            
            self.logger.info(f"Found {len(json_files)} JSON files")
            
            stats = {'total': 0, 'queued': 0, 'failed': 0}
            
            for json_path in json_files:
                video_id = json_path.parent.name
                output_dir = json_path.parent
                
                urls = self._extract_video_urls(json_path)
                
                if not urls:
                    self.logger.info(f"Video {video_id}: No quality-marked URLs")
                    continue
                
                self.logger.info(f"Video {video_id}: Processing {len(urls)} URLs")
                
                for url in urls:
                    stats['total'] += 1
                    if self._add_to_idm(url, output_dir, video_id):
                        stats['queued'] += 1
                    else:
                        stats['failed'] += 1
            
            self.logger.info(
                f"Complete - Total: {stats['total']}, "
                f"Queued: {stats['queued']}, Failed: {stats['failed']}"
            )
            
            # Start downloads if any were queued
            if stats['queued'] > 0:
                self.logger.info("Starting IDM downloads...")
                self._start_idm_downloads()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error processing downloads: {e}", exc_info=True)
            return {'total': 0, 'queued': 0, 'failed': 0}