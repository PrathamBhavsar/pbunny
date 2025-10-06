import logging
from scraper.page_scraper import PageScraper
from scraper.video_scraper import VideoScraper
from scraper.download_manager import DownloadManager
from scraper.config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    try:
        config_manager = ConfigManager("config.json")
        
        base_url = config_manager.get_base_url()
        downloads_dir = config_manager.get_downloads_dir()
        timeout = config_manager.get_timeout()
        
        logger.info(f"Loaded config - URL: {base_url}, Dir: {downloads_dir}, Timeout: {timeout}s")
        
        page_scraper = PageScraper(base_url=base_url, timeout=timeout)
        video_scraper = VideoScraper(timeout=timeout, output_dir=downloads_dir)
        download_manager = DownloadManager(downloads_dir=downloads_dir)
        
        video_links = page_scraper.scrape()
        
        if not video_links:
            logger.warning("No video links found")
            return
        
        logger.info(f"Found {len(video_links)} links, starting scrape")
        
        success_count = 0
        for idx, link in enumerate(video_links, 1):
            logger.info(f"Processing {idx}/{len(video_links)}: {link}")
            if video_scraper.scrape_video(link):
                success_count += 1
        
        logger.info(f"Scraping complete: {success_count}/{len(video_links)} videos")
        
        logger.info("Starting download queue with IDM")
        stats = download_manager.process_downloads()
        logger.info(f"Download queueing complete: {stats}")
            
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()