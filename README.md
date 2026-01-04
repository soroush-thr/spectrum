# Spectrum - AI News Summarizer

Automated AI news agent that monitors RSS feeds, summarizes insights using Perplexity Sonar, and delivers daily digests to Telegram.

## Overview

A Python tool that runs locally on your machine. When executed, it fetches AI news from multiple RSS feeds, generates concise summaries using the Perplexity API, and posts them to a Telegram channel/bot. The tool includes local storage for all fetched articles and summaries, plus a final overview summary that consolidates all news into a single digest.

**Key Features:**
- 📰 Monitors multiple AI news RSS feeds
- 🤖 AI-powered summaries using Perplexity Sonar
- 💾 Local storage of all fetched articles and summaries
- 📊 Daily overview summary with bullet points
- 🔒 Budget management to protect API credits
- 📬 Automated Telegram delivery

**Primary Constraint:** Simple local execution with strict budget management to preserve the $5/month Perplexity API credit.

## Prerequisites

- Python 3.10 or higher
- Perplexity API key (sign up at https://www.perplexity.ai/)
- Telegram Bot Token (create a bot using [@BotFather](https://t.me/BotFather) on Telegram)
- Telegram Chat ID (use [@userinfobot](https://t.me/userinfobot) to get your chat ID, or use a channel ID)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/soroush-thr/spectrum.git
   cd spectrum
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and fill in your API keys:
     ```
     PERPLEXITY_API_KEY=pplx-your-actual-key-here
     TELEGRAM_BOT_TOKEN=your-bot-token-here
     TELEGRAM_CHAT_ID=your-chat-id-here
     ```

## Usage

Run the script:
```bash
python main.py
```

The script will:
1. Fetch articles from configured RSS feeds
2. Filter articles published in the last 48 hours (configurable)
3. Sort by date (newest first)
4. Process up to 5 articles (budget limit)
5. Summarize each article using Perplexity API
6. Post individual summaries to your Telegram channel/bot
7. Generate and send a final overview summary with bullet points
8. Save all fetched articles and summaries locally to `storage/` directory

### Output Format

**Individual Messages:**
```
Source: [Feed Name]

Headline: [Article Title]

Summary: [AI-generated summary]

Link: [Article URL]
```

**Final Overview:**
```
📊 Daily AI News Overview (YYYY-MM-DD)

• [Bullet point summary of all news]
• [Key developments and trends]
• [Consolidated insights]
```

## Configuration

### RSS Feeds

Edit `config.py` to modify the RSS feed sources. The default configuration includes:
- The Verge - AI
- TechCrunch - AI
- Ars Technica - AI
- MIT Technology Review - AI
- Wired - AI

### Budget Management

The script includes built-in budget protection:
- **MAX_ARTICLES**: Maximum number of articles to process per run (default: 5)
- **HOURS_LOOKBACK**: Hours to look back for articles (default: 48)

These can be adjusted in `config.py` to match your budget and needs.

## Local Storage

All fetched articles and generated summaries are automatically saved to the `storage/` directory:

- **Fetched Articles**: `storage/fetched_articles_YYYY-MM-DD_HH-MM-SS.json`
  - Contains all articles found in RSS feeds (before filtering)
  - Includes title, link, description, publication date, and source feed

- **Summaries**: `storage/summaries_YYYY-MM-DD_HH-MM-SS.json`
  - Contains processed articles with AI-generated summaries
  - Includes all article metadata plus the summary and processing timestamp

This allows you to:
- Review what was fetched even if articles were too old to process
- Keep a local archive of all summaries
- Analyze trends over time
- Debug issues with specific articles

## Budget Management Notes

- The script processes a maximum of 5 articles per run, even if more articles are found
- Articles are sorted by date (newest first) before applying the limit
- If an error occurs (e.g., API rate limit), the script will skip that article and continue with the next one
- Each run uses: `(number of articles + 1)` Perplexity API calls (one per article + one for final overview)
- Monitor your Perplexity API usage to stay within the $5/month credit

## Troubleshooting

### "PERPLEXITY_API_KEY not found in .env file"
- Make sure you've created a `.env` file (copy from `.env.example`)
- Verify the key is correctly formatted: `PERPLEXITY_API_KEY=pplx-...`

### "TELEGRAM_BOT_TOKEN not found in .env file"
- Create a bot using [@BotFather](https://t.me/BotFather) on Telegram
- Copy the token and add it to your `.env` file
- See `telegram-bot-setup.md` for detailed bot configuration instructions

### "TELEGRAM_CHAT_ID not found in .env file"
- For personal chats: Use [@userinfobot](https://t.me/userinfobot) to get your chat ID
- For channels: Forward a message from your channel to [@userinfobot](https://t.me/userinfobot) or use the channel's username (e.g., `@yourchannel`)

### "Error fetching feed"
- Check your internet connection
- Verify the RSS feed URL is accessible
- Some feeds may be temporarily unavailable
- The script will continue processing other feeds if one fails

### "Perplexity API error: 429 Too Many Requests"
- You've hit the rate limit or exceeded your credit
- Wait before running the script again
- Check your Perplexity API usage dashboard
- Consider reducing `MAX_ARTICLES` in `config.py`

### No articles found
- The RSS feeds may not have published new articles in the last 48 hours
- Check the feed URLs in `config.py` are correct and accessible
- Review the `storage/fetched_articles_*.json` files to see what was fetched
- Consider increasing `HOURS_LOOKBACK` in `config.py` if needed

## File Structure

```
.
├── .env                  # Your local API keys (ignored by git)
├── .env.example          # Template for .env
├── .gitignore            # Excludes .env, __pycache__, storage/, etc.
├── config.py             # RSS feeds and constants
├── main.py               # Main application logic
├── requirements.txt      # Python dependencies
├── telegram-bot-setup.md # Telegram bot configuration guide
├── logo-prompt.md        # Logo generation prompt for bot profile picture
├── storage/              # Local storage directory (gitignored)
│   ├── fetched_articles_*.json
│   └── summaries_*.json
└── README.md             # This file
```

## Development

This is a local MVP with no database or state management. The script relies on:
- Time-based filtering (last N hours) to avoid processing duplicate articles
- Local JSON files for storage and archival
- Simple error handling that continues processing on failures

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See LICENSE file for details.
