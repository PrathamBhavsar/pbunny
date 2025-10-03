import logging
from scraper.page_scraper import PageScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    try:
        scraper = PageScraper(timeout=30)
        video_links = scraper.scrape()
        
        if video_links:
            logger.info(f"Successfully scraped {len(video_links)} links")
            for link in video_links:
                print(link)
        else:
            logger.warning("No video links found")
            
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main()