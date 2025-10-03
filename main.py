import logging
from scraper.page_scraper import PageScraper
from scraper.video_scraper import VideoScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    try:
        page_scraper = PageScraper(timeout=30)
        video_scraper = VideoScraper(timeout=30, output_dir="./downloads")
        
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
        
        logger.info(f"Completed: {success_count}/{len(video_links)} videos scraped")
            
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()