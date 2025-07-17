#!/usr/bin/env python3
"""
Enhanced Video Scraper
A robust, configurable web scraper for video platforms with comprehensive error handling,
logging, rate limiting, and data validation.
"""

import json
import time
import logging
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests


@dataclass
class VideoData:
    """Data structure for video information."""
    url: str
    title: Optional[str] = None
    views: Optional[str] = None
    subscribers: Optional[str] = None
    likes: Optional[str] = None
    tags: Optional[List[str]] = None
    comments: Optional[List[Dict[str, str]]] = None
    duration: Optional[str] = None
    upload_date: Optional[str] = None
    author: Optional[str] = None
    scrape_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.comments is None:
            self.comments = []
        if self.scrape_timestamp is None:
            self.scrape_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")


class VideoScraper:
    """Enhanced video scraper with robust error handling and configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = None
        self.setup_logging()
        self.session_stats = {
            'total_videos': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'start_time': time.time()
        }
    
    def setup_logging(self) -> None:
        """Configure logging with appropriate level and format."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self) -> None:
        """Initialize Chrome WebDriver with optimized options."""
        options = Options()
        
        # Add headless mode if specified
        if self.config.get('headless', True):
            options.add_argument('--headless=new')
        
        # Performance and stability options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Custom binary location if specified
        if self.config.get('chrome_binary'):
            options.binary_location = self.config['chrome_binary']
        
        # Experimental options for better performance
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(self.config.get('implicit_wait', 10))
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def safe_extract_text(self, soup: BeautifulSoup, selector: str, default: str = None) -> Optional[str]:
        """Safely extract text from HTML element."""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else default
        except Exception as e:
            self.logger.debug(f"Failed to extract text with selector '{selector}': {e}")
            return default
    
    def safe_extract_attribute(self, soup: BeautifulSoup, selector: str, attr: str, default: str = None) -> Optional[str]:
        """Safely extract attribute from HTML element."""
        try:
            element = soup.select_one(selector)
            return element.get(attr) if element else default
        except Exception as e:
            self.logger.debug(f"Failed to extract attribute '{attr}' with selector '{selector}': {e}")
            return default
    
    def extract_video_links(self, homepage_url: str) -> List[str]:
        """Extract video URLs from homepage/category page."""
        self.logger.info(f"Extracting video links from: {homepage_url}")
        
        try:
            self.driver.get(homepage_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(self.config.get('page_load_delay', 3))
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            video_links = []
            
            # Multiple selectors for different video link patterns
            selectors = [
                'a.video-thumb__image-container',
                'a[href*="/videos/"]',
                '.video-item a',
                '.thumb-container a'
            ]
            
            base_url = f"{urlparse(homepage_url).scheme}://{urlparse(homepage_url).netloc}"
            
            for selector in selectors:
                for link in soup.select(selector):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url not in video_links and '/videos/' in full_url:
                            video_links.append(full_url)
            
            self.logger.info(f"Extracted {len(video_links)} video URLs")
            return video_links
            
        except TimeoutException:
            self.logger.error("Timeout waiting for page to load")
            return []
        except Exception as e:
            self.logger.error(f"Error extracting video links: {e}")
            return []
    
    def extract_video_data(self, video_url: str) -> Optional[VideoData]:
        """Extract comprehensive data from a single video page."""
        try:
            self.logger.debug(f"Scraping video: {video_url}")
            self.driver.get(video_url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(self.config.get('video_load_delay', 2))
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Extract video metadata with multiple fallback selectors
            video_data = VideoData(url=video_url)
            
            # Title extraction with fallbacks
            title_selectors = [
                'span.body-bold-8643e.label-5984a.label-96c3e',
                'h1.video-title',
                '.video-details h1',
                'title'
            ]
            for selector in title_selectors:
                video_data.title = self.safe_extract_text(soup, selector)
                if video_data.title:
                    break
            
            # Views extraction
            views_selectors = [
                'span.primary-8643e',
                '.view-count',
                '.stats .views'
            ]
            for selector in views_selectors:
                video_data.views = self.safe_extract_text(soup, selector)
                if video_data.views:
                    break
            
            # Subscribers/Channel info
            sub_selectors = [
                'span.sub-button__counter',
                '.channel-subscribers',
                '.author-info .subscribers'
            ]
            for selector in sub_selectors:
                video_data.subscribers = self.safe_extract_text(soup, selector)
                if video_data.subscribers:
                    break
            
            # Likes extraction
            likes_selectors = [
                'div.rb-new__info',
                '.like-count',
                '.rating-count'
            ]
            for selector in likes_selectors:
                video_data.likes = self.safe_extract_text(soup, selector)
                if video_data.likes:
                    break
            
            # Tags extraction
            tag_selectors = [
                'span.body-8643e.label-5984a.label-96c3e',
                '.video-tags a',
                '.tags .tag'
            ]
            for selector in tag_selectors:
                tags = soup.select(selector)
                if tags:
                    video_data.tags = list(set(tag.get_text(strip=True) for tag in tags if tag.get_text(strip=True)))
                    break
            
            # Comments extraction
            self.extract_comments(soup, video_data)
            
            # Additional metadata
            video_data.duration = self.safe_extract_text(soup, '.duration, .video-duration')
            video_data.author = self.safe_extract_text(soup, '.uploader, .author-name, .channel-name')
            video_data.upload_date = self.safe_extract_text(soup, '.upload-date, .date-added')
            
            self.session_stats['successful_scrapes'] += 1
            return video_data
            
        except TimeoutException:
            self.logger.warning(f"Timeout loading video: {video_url}")
            self.session_stats['failed_scrapes'] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error scraping video {video_url}: {e}")
            self.session_stats['failed_scrapes'] += 1
            return None
    
    def extract_comments(self, soup: BeautifulSoup, video_data: VideoData) -> None:
        """Extract comments from video page."""
        try:
            comment_selectors = [
                'div.comment',
                '.comment-item',
                '.user-comment'
            ]
            
            for selector in comment_selectors:
                comment_blocks = soup.select(selector)
                if comment_blocks:
                    break
            
            max_comments = self.config.get('max_comments', 50)
            
            for comment in comment_blocks[:max_comments]:
                try:
                    username_selectors = [
                        'span.primary-8643e.username-a2e4b',
                        '.comment-author',
                        '.username'
                    ]
                    
                    text_selectors = [
                        'span.commentText-ea690',
                        '.comment-text',
                        '.comment-content'
                    ]
                    
                    username = None
                    comment_text = None
                    
                    for selector in username_selectors:
                        username = self.safe_extract_text(comment, selector)
                        if username:
                            break
                    
                    for selector in text_selectors:
                        comment_text = self.safe_extract_text(comment, selector)
                        if comment_text:
                            break
                    
                    if username and comment_text:
                        video_data.comments.append({
                            'user': username,
                            'comment': comment_text,
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                
                except Exception as e:
                    self.logger.debug(f"Error extracting comment: {e}")
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error extracting comments: {e}")
    
    def scrape_videos(self, homepage_url: str, max_videos: Optional[int] = None) -> List[VideoData]:
        """Main scraping method."""
        self.setup_driver()
        
        try:
            # Extract video URLs
            video_links = self.extract_video_links(homepage_url)
            
            if not video_links:
                self.logger.warning("No video links found")
                return []
            
            # Limit number of videos if specified
            if max_videos:
                video_links = video_links[:max_videos]
            
            self.session_stats['total_videos'] = len(video_links)
            video_data_list = []
            
            # Rate limiting
            delay_between_requests = self.config.get('delay_between_requests', 2)
            
            for idx, url in enumerate(video_links, 1):
                self.logger.info(f"Processing video {idx}/{len(video_links)}: {url}")
                
                video_data = self.extract_video_data(url)
                if video_data:
                    video_data_list.append(video_data)
                
                # Rate limiting
                if idx < len(video_links):
                    time.sleep(delay_between_requests)
                
                # Progress reporting
                if idx % 10 == 0:
                    success_rate = (self.session_stats['successful_scrapes'] / idx) * 100
                    self.logger.info(f"Progress: {idx}/{len(video_links)} ({success_rate:.1f}% success rate)")
            
            return video_data_list
            
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed")
    
    def save_data(self, video_data_list: List[VideoData], output_format: str = 'json') -> None:
        """Save scraped data in specified format."""
        if not video_data_list:
            self.logger.warning("No data to save")
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if output_format.lower() == 'json':
            filename = f"video_data_{timestamp}.json"
            data_dict = [asdict(video) for video in video_data_list]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data saved to {filename}")
            
        elif output_format.lower() == 'csv':
            filename = f"video_data_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if video_data_list:
                    # Flatten data for CSV
                    flattened_data = []
                    for video in video_data_list:
                        flat_video = asdict(video)
                        flat_video['tags'] = '; '.join(flat_video['tags']) if flat_video['tags'] else ''
                        flat_video['comments_count'] = len(flat_video['comments']) if flat_video['comments'] else 0
                        flat_video.pop('comments')  # Remove complex nested data for CSV
                        flattened_data.append(flat_video)
                    
                    writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_data)
            
            self.logger.info(f"Data saved to {filename}")
    
    def print_session_stats(self) -> None:
        """Print session statistics."""
        duration = time.time() - self.session_stats['start_time']
        success_rate = (self.session_stats['successful_scrapes'] / max(self.session_stats['total_videos'], 1)) * 100
        
        print("\n" + "="*50)
        print("SCRAPING SESSION SUMMARY")
        print("="*50)
        print(f"Total videos processed: {self.session_stats['total_videos']}")
        print(f"Successful scrapes: {self.session_stats['successful_scrapes']}")
        print(f"Failed scrapes: {self.session_stats['failed_scrapes']}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total duration: {duration:.1f} seconds")
        print(f"Average time per video: {duration/max(self.session_stats['total_videos'], 1):.1f} seconds")
        print("="*50)


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or return defaults."""
    default_config = {
        'headless': True,
        'log_level': 'INFO',
        'implicit_wait': 10,
        'page_load_delay': 3,
        'video_load_delay': 2,
        'delay_between_requests': 2,
        'max_comments': 50,
        'chrome_binary': None,
        'output_format': 'json'
    }
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
            default_config.update(user_config)
        except Exception as e:
            logging.warning(f"Failed to load config file: {e}. Using defaults.")
    
    return default_config


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(description="Enhanced Video Scraper")
    parser.add_argument('url', help='Homepage/category URL to scrape')
    parser.add_argument('--max-videos', type=int, help='Maximum number of videos to scrape')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--output-format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.headless:
        config['headless'] = True
    config['log_level'] = args.log_level
    config['output_format'] = args.output_format
    
    # Create scraper and run
    scraper = VideoScraper(config)
    
    try:
        video_data = scraper.scrape_videos(args.url, args.max_videos)
        scraper.save_data(video_data, config['output_format'])
        scraper.print_session_stats()
        
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()