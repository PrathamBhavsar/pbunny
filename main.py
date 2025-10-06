import logging
from scraper.page_scraper import PageScraper
from scraper.video_scraper import VideoScraper
from scraper.download_manager import DownloadManager
from scraper.config_manager import ConfigManager
from scraper.progress_manager import ProgressManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    try:
        # Load configuration
        config_manager = ConfigManager("config.json")
        
        base_url = config_manager.get_base_url()
        downloads_dir = config_manager.get_downloads_dir()
        timeout = config_manager.get_timeout()
        pages_per_parse = config_manager.get_pages_per_parse()
        
        logger.info(f"Loaded config - URL: {base_url}, Dir: {downloads_dir}, Timeout: {timeout}s, Pages: {pages_per_parse}")
        
        # Load progress
        progress_manager = ProgressManager("progress.json")
        last_parsed_page = progress_manager.get_last_parsed_page()
        total_videos = progress_manager.get_total_videos_parsed()
        
        logger.info(f"Previous progress - Last page: {last_parsed_page}, Total videos: {total_videos}")
        
        # Initialize scrapers
        page_scraper = PageScraper(base_url=base_url, timeout=timeout, pages_per_parse=pages_per_parse)
        video_scraper = VideoScraper(timeout=timeout, output_dir=downloads_dir)
        download_manager = DownloadManager(downloads_dir=downloads_dir)
        
        # Determine starting page
        if last_parsed_page is not None and last_parsed_page > 1:
            start_page = last_parsed_page - 1
            logger.info(f"Resuming from page {start_page} (previous: {last_parsed_page})")
        else:
            start_page = None  # Will use default starting page
            logger.info("Starting fresh scrape")
        
        # Scrape video links
        video_links, last_successful_page = page_scraper.scrape(start_page)
        
        if not video_links:
            logger.warning("No video links found")
            if last_successful_page:
                progress_manager.save_progress(last_successful_page, total_videos)
            return
        
        logger.info(f"Found {len(video_links)} links, starting scrape")
        
        # Scrape individual videos
        success_count = 0
        for idx, link in enumerate(video_links, 1):
            logger.info(f"Processing {idx}/{len(video_links)}: {link}")
            if video_scraper.scrape_video(link):
                success_count += 1
        
        logger.info(f"Scraping complete: {success_count}/{len(video_links)} videos")
        
        # Update progress with new totals
        new_total_videos = total_videos + success_count
        progress_manager.save_progress(last_successful_page, new_total_videos)
        logger.info(f"Progress saved - Last page: {last_successful_page}, Total videos: {new_total_videos}")
        
        # Queue downloads with IDM
        logger.info("Starting download queue with IDM")
        stats = download_manager.process_downloads()
        logger.info(f"Download queueing complete: {stats}")
            
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()