"""
AI News Summarizer - Local MVP
Fetches AI news from RSS feeds, summarizes using Perplexity API, and posts to Telegram
"""

import os
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
import feedparser
import requests

import config


def load_env():
    """Load environment variables from .env file"""
    load_dotenv()
    
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not perplexity_key:
        raise ValueError("PERPLEXITY_API_KEY not found in .env file")
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")
    if not telegram_chat_id:
        raise ValueError("TELEGRAM_CHAT_ID not found in .env file")
    
    return perplexity_key, telegram_token, telegram_chat_id


def fetch_rss_feeds():
    """
    Parse all RSS feeds and return entries with feed information
    Returns list of dicts with: feed_name, title, link, published_parsed
    """
    all_articles = []
    
    print("Loading configuration...")
    print(f"Checking {len(config.RSS_FEEDS)} RSS feeds...\n")
    
    for feed_config in config.RSS_FEEDS:
        feed_name = feed_config["name"]
        feed_url = feed_config["url"]
        
        print(f"Checking feed: {feed_name}...")
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and feed.bozo_exception:
                print(f"  Warning: Feed parsing issue - {feed.bozo_exception}\n")
                continue
            
            for entry in feed.entries:
                # Extract article information
                article = {
                    "feed_name": feed_name,
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published_parsed": entry.get("published_parsed"),
                    "published": entry.get("published", ""),
                    "description": entry.get("description", "")
                }
                
                if article["published_parsed"]:
                    all_articles.append(article)
            
            print(f"  Found {len(feed.entries)} articles\n")
            
        except Exception as e:
            print(f"  Error fetching feed: {e}\n")
            continue
    
    return all_articles


def filter_recent_articles(articles):
    """
    Filter articles from last 24 hours, sort by date (newest first), limit to MAX_ARTICLES
    Returns filtered and sorted list
    """
    if not articles:
        return []
    
    # Calculate cutoff time (24 hours ago)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=config.HOURS_LOOKBACK)
    current_time = datetime.now(timezone.utc)
    
    print(f"Current time (UTC): {current_time}")
    print(f"Cutoff time (UTC): {cutoff_time} (last {config.HOURS_LOOKBACK} hours)\n")
    
    recent_articles = []
    skipped_count = 0
    
    for article in articles:
        if not article["published_parsed"]:
            skipped_count += 1
            continue
        
        # Convert published_parsed (time.struct_time) to datetime
        try:
            # published_parsed is a time.struct_time, convert to datetime
            pub_time = datetime(*article["published_parsed"][:6], tzinfo=timezone.utc)
            article["published_datetime"] = pub_time
            article["published_datetime_str"] = pub_time.isoformat()
            
            # Check if article is within the last 24 hours
            if pub_time >= cutoff_time:
                recent_articles.append(article)
            else:
                skipped_count += 1
                # Debug: show a few skipped articles
                if skipped_count <= 3:
                    hours_ago = (current_time - pub_time).total_seconds() / 3600
                    print(f"  Skipped (too old): '{article['title'][:50]}...' - {hours_ago:.1f} hours ago")
        except (ValueError, TypeError) as e:
            # Skip articles with invalid dates
            skipped_count += 1
            continue
    
    # Sort by publication date (newest first)
    recent_articles.sort(key=lambda x: x["published_datetime"], reverse=True)
    
    # Limit to MAX_ARTICLES
    limited_articles = recent_articles[:config.MAX_ARTICLES]
    
    print(f"\nFound {len(recent_articles)} articles in the last {config.HOURS_LOOKBACK} hours")
    print(f"Skipped {skipped_count} articles (too old or invalid date)")
    print(f"Processing top {len(limited_articles)} articles (budget limit: {config.MAX_ARTICLES})\n")
    
    return limited_articles


def summarize_with_perplexity(api_key, title, url):
    """
    Send article title + URL to Perplexity API (sonar model), return summary
    """
    endpoint = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Summarize the key updates in this article in 2 sentences. Title: {title}, URL: {url}"
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 250
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        summary = result["choices"][0]["message"]["content"].strip()
        
        return summary
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Perplexity API error: {e}")


def send_to_telegram(telegram_token, chat_id, feed_name, title, summary, url):
    """
    Format and send message to Telegram
    """
    endpoint = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    
    message = f"""Source: {feed_name}

Headline: {title}

Summary: {summary}

Link: {url}"""
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        raise Exception(f"Telegram API error: {e}")


def generate_final_summary(api_key, summaries):
    """
    Generate a final overview summary from all article summaries using Perplexity
    """
    endpoint = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Combine all summaries into one text
    combined_summaries = "\n\n".join([f"• {summary}" for summary in summaries])
    
    prompt = f"""Create a concise bullet-point overview summarizing the key AI and tech news from these summaries. 
Format as clean bullet points without titles or links. Focus on the main developments and trends:

{combined_summaries}

Provide a brief, unified overview in bullet points."""
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 300
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        overview = result["choices"][0]["message"]["content"].strip()
        
        return overview
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Perplexity API error: {e}")


def send_final_summary(telegram_token, chat_id, summary_text):
    """
    Send final summary message to Telegram
    """
    endpoint = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    
    message = f"""📊 **Daily AI News Overview** ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})

{summary_text}"""
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        raise Exception(f"Telegram API error: {e}")


def save_fetched_articles(articles):
    """
    Save all fetched articles to a local JSON file
    """
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = storage_dir / f"fetched_articles_{timestamp}.json"
    
    # Prepare articles for JSON serialization
    serializable_articles = []
    for article in articles:
        article_copy = article.copy()
        # Convert published_parsed to string if it exists
        if "published_parsed" in article_copy and article_copy["published_parsed"]:
            try:
                pub_time = datetime(*article_copy["published_parsed"][:6], tzinfo=timezone.utc)
                article_copy["published_datetime"] = pub_time.isoformat()
            except:
                pass
            # Remove non-serializable published_parsed
            article_copy.pop("published_parsed", None)
        serializable_articles.append(article_copy)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_articles": len(serializable_articles),
            "articles": serializable_articles
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(serializable_articles)} fetched articles to {filename}")
    return filename


def save_summaries(processed_articles):
    """
    Save processed articles with summaries to a local JSON file
    """
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = storage_dir / f"summaries_{timestamp}.json"
    
    # Prepare articles for JSON serialization
    serializable_articles = []
    for article in processed_articles:
        article_copy = article.copy()
        # Convert datetime to string if it exists
        if "published_datetime" in article_copy:
            if isinstance(article_copy["published_datetime"], datetime):
                article_copy["published_datetime"] = article_copy["published_datetime"].isoformat()
        # Remove non-serializable published_parsed
        article_copy.pop("published_parsed", None)
        serializable_articles.append(article_copy)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_summaries": len(serializable_articles),
            "articles": serializable_articles
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(serializable_articles)} summaries to {filename}")
    return filename


def main():
    """Main workflow orchestration"""
    try:
        # Load environment variables
        perplexity_key, telegram_token, telegram_chat_id = load_env()
        
        # Fetch RSS feeds
        all_articles = fetch_rss_feeds()
        
        if not all_articles:
            print("No articles found in any RSS feeds.")
            return
        
        # Save all fetched articles locally
        save_fetched_articles(all_articles)
        print()
        
        # Filter recent articles
        articles_to_process = filter_recent_articles(all_articles)
        
        if not articles_to_process:
            print(f"No articles found in the last {config.HOURS_LOOKBACK} hours.")
            print("Note: All fetched articles have been saved to storage/ directory.")
            return
        
        # Process each article
        successful_count = 0
        processed_articles = []
        successful_summaries = []  # Collect summaries for final overview
        
        for i, article in enumerate(articles_to_process, 1):
            print(f"[{i}/{len(articles_to_process)}] Processing article: {article['title']}")
            print("Summarizing...")
            
            try:
                # Get summary from Perplexity
                summary = summarize_with_perplexity(
                    perplexity_key,
                    article["title"],
                    article["link"]
                )
                
                # Add summary to article data
                article["summary"] = summary
                article["processed_at"] = datetime.now(timezone.utc).isoformat()
                processed_articles.append(article)
                
                # Send to Telegram
                send_to_telegram(
                    telegram_token,
                    telegram_chat_id,
                    article["feed_name"],
                    article["title"],
                    summary,
                    article["link"]
                )
                
                print(f"Sent: {article['title']}\n")
                successful_count += 1
                successful_summaries.append(summary)  # Collect for final summary
                
            except Exception as e:
                print(f"Error processing '{article['title']}': {e}\n")
                # Still save the article even if processing failed
                article["error"] = str(e)
                article["processed_at"] = datetime.now(timezone.utc).isoformat()
                processed_articles.append(article)
                continue
        
        # Save all processed articles with summaries locally
        if processed_articles:
            save_summaries(processed_articles)
            print()
        
        # Send final overview summary if we have successful summaries
        if successful_summaries and successful_count > 0:
            print("Generating final overview summary...")
            try:
                final_summary = generate_final_summary(perplexity_key, successful_summaries)
                send_final_summary(telegram_token, telegram_chat_id, final_summary)
                print("Sent final overview summary to Telegram.\n")
            except Exception as e:
                print(f"Error generating/sending final summary: {e}\n")
        
        print(f"Done. Processed {successful_count} articles successfully.")
        print(f"All data saved to storage/ directory.")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        return


if __name__ == "__main__":
    main()

