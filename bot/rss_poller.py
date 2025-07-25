import asyncio
import logging
from typing import Optional
import discord
import feedparser
from markdownify import markdownify as md
from discord.ext import tasks
from bot.config import get_poll_interval
from bot import db


logger = logging.getLogger(__name__)


class RSSPoller:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.poll_interval = get_poll_interval()
    
    def start_polling(self):
        self.poll_feeds.start()
    
    def stop_polling(self):
        if self.poll_feeds.is_running():
            self.poll_feeds.cancel()
    
    @tasks.loop(minutes=1)
    async def poll_feeds(self):
        if not hasattr(self, '_actual_interval_set'):
            self.poll_feeds.change_interval(minutes=self.poll_interval)
            self._actual_interval_set = True
            logger.info(f"RSS polling started with {self.poll_interval} minute interval")
            return
        
        try:
            feeds = await db.get_all_feeds()
            for feed_row in feeds:
                await self._process_feed(feed_row)
        except Exception as e:
            logger.error(f"Error during RSS polling: {e}")
    
    async def _process_feed(self, feed_row):
        feed_id = feed_row[0]
        forum_channel_id = feed_row[1]
        url = feed_row[2]
        name = feed_row[3]
        last_entry_id = feed_row[4]
        
        try:
            forum_channel = self.bot.get_channel(forum_channel_id)
            if not forum_channel:
                logger.error(f"Forum channel {forum_channel_id} not found for feed {feed_id}")
                return
            
            if not isinstance(forum_channel, discord.ForumChannel):
                logger.error(f"Channel {forum_channel_id} is not a forum channel for feed {feed_id}")
                return
            
            parsed_feed = await self._fetch_rss_feed(url)
            if not parsed_feed:
                return
            
            entries = parsed_feed.entries
            if not entries:
                logger.debug(f"No entries found in feed {feed_id} ({url})")
                return
            
            new_entries = []
            
            if last_entry_id is None:
                new_entries = entries[:15]
                logger.info(f"First run for feed {feed_id}, posting {len(new_entries)} recent entries")
            else:
                for entry in entries:
                    entry_id = self._get_entry_id(entry)
                    if entry_id == last_entry_id:
                        break
                    new_entries.append(entry)
            
            if new_entries:
                new_entries.reverse()
                
                for entry in new_entries:
                    await self._create_forum_post(forum_channel, entry, feed_id)
                    await asyncio.sleep(1)
                
                latest_entry_id = self._get_entry_id(new_entries[-1])
                await db.update_last_entry_id(feed_id, latest_entry_id)
                
                feed_display_name = name if name else url
                logger.info(f"Posted {len(new_entries)} new entries for feed '{feed_display_name}'")
            else:
                logger.debug(f"No new entries for feed {feed_id}")
                
        except Exception as e:
            feed_display_name = name if name else url
            logger.error(f"Error processing feed '{feed_display_name}': {e}")
    
    async def _fetch_rss_feed(self, url: str):
        try:
            loop = asyncio.get_event_loop()
            parsed_feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            if parsed_feed.bozo:
                logger.warning(f"RSS feed may be malformed: {url}")
            
            return parsed_feed
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {url}: {e}")
            return None
    
    def _get_entry_id(self, entry) -> str:
        if hasattr(entry, 'id') and entry.id:
            return entry.id
        elif hasattr(entry, 'guid') and entry.guid:
            return entry.guid
        elif hasattr(entry, 'link') and entry.link:
            return entry.link
        else:
            return entry.title or "unknown"
    
    async def _create_forum_post(self, forum_channel: discord.ForumChannel, entry, feed_id: int):
        try:
            title = self._clean_title(entry.title if hasattr(entry, 'title') else "Untitled")
            content = self._format_post_content(entry)
            
            thread_with_message = await forum_channel.create_thread(
                name=title,
                content=content
            )
            
            # Record the forum post for cleanup tracking
            # create_thread returns ThreadWithMessage, we need the thread attribute
            await db.record_feed_post(feed_id, thread_with_message.thread.id)
            
            logger.debug(f"Created forum post: {title}")
            
        except Exception as e:
            logger.error(f"Failed to create forum post for entry '{entry.title}': {e}")
    
    def _clean_title(self, title: str) -> str:
        if len(title) > 100:
            title = title[:97] + "..."
        return title.strip()
    
    def _format_post_content(self, entry) -> str:
        content_parts = []
        
        if hasattr(entry, 'link') and entry.link:
            content_parts.append(f"🔗 **Link:** {entry.link}")
            content_parts.append("")
        
        if hasattr(entry, 'summary') and entry.summary:
            content_parts.append(self._html_to_markdown(entry.summary))
        elif hasattr(entry, 'description') and entry.description:
            content_parts.append(self._html_to_markdown(entry.description))
        elif hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list) and len(entry.content) > 0:
                content_parts.append(self._html_to_markdown(entry.content[0].get('value', '')))
            else:
                content_parts.append(self._html_to_markdown(str(entry.content)))
        
        if hasattr(entry, 'published') and entry.published:
            content_parts.append("")
            content_parts.append(f"📅 **Published:** {entry.published}")
        
        return "\n".join(content_parts) if content_parts else "No content available."
    
    def _html_to_markdown(self, html_content: str) -> str:
        if not html_content:
            return ""
        
        try:
            markdown_content = md(
                html_content,
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style']
            ).strip()
            
            return markdown_content if markdown_content else html_content
        except Exception as e:
            logger.warning(f"Failed to convert HTML to markdown: {e}")
            return html_content
    
    @poll_feeds.before_loop
    async def before_poll_feeds(self):
        await self.bot.wait_until_ready()