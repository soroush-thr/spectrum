"""
Configuration file for AI News Summarizer
Contains RSS feed URLs and tunable constants
"""

# Maximum number of articles to process per run (budget protection)
MAX_ARTICLES = 5

# Hours to look back for articles
HOURS_LOOKBACK = 48

# RSS Feed URLs for AI news sources
RSS_FEEDS = [
    {
        "name": "The Verge - AI",
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"
    },
    {
        "name": "TechCrunch - AI",
        "url": "https://techcrunch.com/tag/artificial-intelligence/feed/"
    },
    {
        "name": "Ars Technica - AI",
        "url": "https://feeds.arstechnica.com/arstechnica/index"
    },
    {
        "name": "MIT Technology Review - AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
    },
    {
        "name": "Wired - AI",
        "url": "https://www.wired.com/feed/tag/artificial-intelligence/latest/rss"
    }
]

