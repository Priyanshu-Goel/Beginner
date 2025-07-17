# Enhanced Video Scraper

A robust, configurable web scraper for video platforms with comprehensive error handling, logging, rate limiting, and data validation.

## Features

### 🚀 **Core Functionality**
- **Automated Video Discovery**: Extracts video URLs from category/homepage pages
- **Comprehensive Data Extraction**: Collects title, views, likes, tags, comments, and metadata
- **Multiple Output Formats**: Supports JSON and CSV export
- **Robust Error Handling**: Graceful failure recovery and detailed logging

### 🛡️ **Reliability & Performance**
- **Smart Rate Limiting**: Configurable delays to respect server resources
- **Multiple Selector Fallbacks**: Adapts to different page structures
- **Session Statistics**: Tracks success rates and performance metrics
- **WebDriver Management**: Automatic driver installation and cleanup

### ⚙️ **Configuration & Customization**
- **Flexible Configuration**: JSON-based config file or command-line options
- **Headless Operation**: Optional GUI-less browsing
- **Custom Chrome Binary**: Support for different Chrome installations
- **Adjustable Timeouts**: Fine-tune waiting periods for different networks

### 📊 **Data Quality**
- **Structured Data Models**: Type-safe data structures using dataclasses
- **Timestamp Tracking**: Records when data was scraped
- **Comment Limiting**: Configurable maximum comments per video
- **Data Validation**: Ensures data integrity and consistency

## Installation

1. **Clone or download the scraper files**
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure Chrome/Chromium is installed** (or provide custom binary path)

## Usage

### Command Line Interface

#### Basic Usage
```bash
python video_scraper.py "https://example.com/videos"
```

#### Advanced Usage
```bash
# Limit to 50 videos, save as CSV, run in headless mode
python video_scraper.py "https://example.com/videos" \
    --max-videos 50 \
    --output-format csv \
    --headless \
    --log-level DEBUG

# Use custom configuration file
python video_scraper.py "https://example.com/videos" \
    --config my_config.json \
    --max-videos 100
```

### Python Script Usage
```python
from video_scraper import VideoScraper, load_config

# Load configuration
config = load_config('config.json')

# Create scraper instance
scraper = VideoScraper(config)

# Scrape videos
video_data = scraper.scrape_videos('https://example.com/videos', max_videos=20)

# Save data
scraper.save_data(video_data, 'json')

# Print statistics
scraper.print_session_stats()
```

## Configuration

### Configuration File (`config.json`)
```json
{
  "headless": true,
  "log_level": "INFO",
  "implicit_wait": 10,
  "page_load_delay": 3,
  "video_load_delay": 2,
  "delay_between_requests": 2,
  "max_comments": 50,
  "chrome_binary": null,
  "output_format": "json"
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `headless` | boolean | `true` | Run browser without GUI |
| `log_level` | string | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `implicit_wait` | integer | `10` | WebDriver implicit wait timeout (seconds) |
| `page_load_delay` | integer | `3` | Delay after loading homepage (seconds) |
| `video_load_delay` | integer | `2` | Delay after loading video page (seconds) |
| `delay_between_requests` | integer | `2` | Delay between video requests (seconds) |
| `max_comments` | integer | `50` | Maximum comments to extract per video |
| `chrome_binary` | string | `null` | Path to custom Chrome binary |
| `output_format` | string | `"json"` | Output format (json, csv) |

## Command Line Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `url` | string | **Required** - Homepage/category URL to scrape |
| `--max-videos` | integer | Maximum number of videos to scrape |
| `--config` | string | Path to configuration file |
| `--output-format` | string | Output format: json or csv |
| `--headless` | flag | Enable headless mode |
| `--log-level` | string | Set logging level |

## Output Data Structure

### JSON Output
```json
[
  {
    "url": "https://example.com/video/123",
    "title": "Video Title",
    "views": "1.2K views",
    "subscribers": "50K subscribers",
    "likes": "95%",
    "tags": ["tag1", "tag2"],
    "comments": [
      {
        "user": "username",
        "comment": "Great video!",
        "timestamp": "2024-01-15 14:30:00"
      }
    ],
    "duration": "10:30",
    "upload_date": "2024-01-10",
    "author": "Channel Name",
    "scrape_timestamp": "2024-01-15 14:30:00"
  }
]
```

### CSV Output
CSV format includes all fields except nested comments (comments_count provided instead).

## Error Handling

The scraper includes comprehensive error handling:

- **Network Timeouts**: Automatic retry with exponential backoff
- **Missing Elements**: Graceful degradation with null values
- **WebDriver Issues**: Automatic cleanup and error reporting
- **Invalid URLs**: Skip and continue with next video
- **Rate Limiting**: Respect server response times

## Logging

Logs are written to both console and `scraper.log` file:

```
2024-01-15 14:30:00 - INFO - Chrome WebDriver initialized successfully
2024-01-15 14:30:05 - INFO - Extracting video links from: https://example.com/videos
2024-01-15 14:30:08 - INFO - Extracted 25 video URLs
2024-01-15 14:30:10 - INFO - Processing video 1/25: https://example.com/video/123
```

## Session Statistics

After completion, the scraper provides detailed statistics:

```
==================================================
SCRAPING SESSION SUMMARY
==================================================
Total videos processed: 25
Successful scrapes: 23
Failed scrapes: 2
Success rate: 92.0%
Total duration: 120.5 seconds
Average time per video: 4.8 seconds
==================================================
```

## Best Practices

1. **Respect Rate Limits**: Use appropriate delays between requests
2. **Monitor Logs**: Check `scraper.log` for issues and performance
3. **Test Small Batches**: Start with `--max-videos 5` to test selectors
4. **Use Configuration Files**: Maintain consistent settings across runs
5. **Check robots.txt**: Ensure compliance with website policies
6. **Regular Updates**: Update dependencies and Chrome driver periodically

## Troubleshooting

### Common Issues

1. **Chrome Binary Not Found**
   ```bash
   # Solution: Install Chrome or specify custom binary
   --chrome-binary /path/to/chrome
   ```

2. **Timeout Errors**
   ```json
   // Increase timeouts in config.json
   {
     "implicit_wait": 20,
     "page_load_delay": 5
   }
   ```

3. **No Data Extracted**
   ```bash
   # Run with debug logging to see selector issues
   --log-level DEBUG
   ```

4. **Memory Issues**
   ```json
   // Reduce concurrent operations
   {
     "max_comments": 10,
     "delay_between_requests": 5
   }
   ```

## Dependencies

- **selenium**: WebDriver automation
- **webdriver-manager**: Automatic driver management
- **beautifulsoup4**: HTML parsing
- **lxml**: Fast XML/HTML parsing
- **requests**: HTTP requests (future enhancements)

## Legal Considerations

⚠️ **Important**: Always ensure compliance with:
- Website Terms of Service
- robots.txt files
- Rate limiting requirements
- Data protection laws (GDPR, CCPA, etc.)
- Copyright and fair use policies

This tool is for educational and research purposes. Users are responsible for ensuring legal and ethical use.

## License

This project is provided as-is for educational purposes. Please use responsibly and in accordance with applicable laws and website terms of service.