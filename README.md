# DiscoRSS

A self-hosted Discord bot that transforms RSS feeds into Discord forum discussions. DiscoRSS monitors RSS feeds and automatically creates forum posts for each new article, enabling community discussions around RSS content in a structured way.

## Features

- 🤖 **Automated RSS Monitoring** - Polls RSS feeds at configurable intervals
- 📝 **Forum Integration** - Creates Discord forum posts for each RSS article
- 🏷️ **Custom Feed Names** - Add descriptive names to feeds for easy identification
- 🧹 **Smart Cleanup** - Automatically removes forum posts when feeds are deleted
- 📱 **Slash Commands** - Modern Discord command interface with administrator controls
- 🔄 **Sequential Numbering** - User-friendly feed numbering without gaps
- 📄 **Markdown Support** - Converts HTML content to properly formatted Discord posts

## Quick Start

### Prerequisites

- Python 3.13 or higher
- Discord bot token with forum channel and message content permissions
    - View [Bot Permissions](#bot-permissions)
- Community discord server

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DiscoRSS
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp example.env .env
   # Edit .env with your Discord bot token and user ID
   ```

4. **Run the bot**
   ```bash
   python -m bot.main
   ```

5. **Sync the commands**
   Once the bot is running, do `!sync` to populate the slash commands.
   Note this may take a few minutes.

## Configuration

Create a `.env` file with the following variables:

```env
token=your-discord-bot-token
userid=your-discord-user-id
POLL_INTERVAL_MINUTES=15
```

- `token` - Your Discord bot token from the Discord Developer Portal
- `userid` - Your Discord user ID (for bot owner commands)
- `POLL_INTERVAL_MINUTES` - How often to check feeds for new content (default: 15 minutes)

## Bot Permissions

Your Discord bot needs the following permissions:
- Send Messages
- Use Slash Commands
- Create Public Threads (for forum posts)
- Manage Threads (for cleanup operations)
- Read Message Contents (This is a privileged intent)

## Commands

All commands require administrator permissions and work in servers with forum channels.

### `/addfeed <forum_channel> <url> [name]`
Add a new RSS feed to monitor.

**Examples:**
```
/addfeed #tech-news https://techcrunch.com/feed/ TechCrunch
/addfeed #updates https://example.com/rss.xml
```

### `/removefeed <number>`
Remove a feed by its display number. Includes confirmation prompt and automatic cleanup of forum posts.

**Example:**
```
/removefeed 2
```

### `/listfeeds`
Display all configured RSS feeds with their numbers, names, and target channels.

**Example output:**
```
Configured feeds:
[1] TechCrunch → #tech-news
[2] Science Daily → #science
[3] https://example.com/feed.xml → #updates
```

## How It Works

1. **Feed Addition** - Administrators add RSS feeds to specific forum channels
2. **Automatic Polling** - Bot checks feeds every X minutes for new content
3. **Forum Posts** - New articles become forum posts with title, content, and discussion threads
4. **Content Formatting** - HTML content is converted to Discord-friendly Markdown
5. **Smart Tracking** - Only posts new content since last check to avoid duplicates

## Database Schema

DiscoRSS uses SQLite with automatic migrations:

- **feeds** - Stores RSS feed configurations and tracking data
- **feed_posts** - Maps forum posts to feeds for cleanup operations

## Troubleshooting

### Common Issues

**Bot not responding to commands**
- Verify bot token is correct in `.env`
- Ensure bot has proper permissions in the server
- Check bot is online and invited to your server

**Feeds not updating**
- Verify RSS feed URL is accessible
- Check `POLL_INTERVAL_MINUTES` setting
- Review bot logs for error messages

**Permission errors**
- Ensure bot has forum channel and message content permissions
- Verify you have administrator permissions to use commands

### Logs

The bot logs important events and errors to help with troubleshooting. Check console output for details about:
- Feed polling status
- RSS parsing errors
- Discord API issues
- Database operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the existing code style
4. Test your changes thoroughly
5. Submit a pull request

