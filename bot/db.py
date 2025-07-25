from collections.abc import Iterable
from sqlite3 import Row
import aiosqlite

DB_PATH = "feeds.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                forum_channel_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                name TEXT DEFAULT NULL,
                last_entry_id TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feed_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                thread_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE
            )
        """)
        await db.commit()
        await migrate_db(db)


async def migrate_db(db: aiosqlite.Connection):
    try:
        await db.execute("ALTER TABLE feeds ADD COLUMN name TEXT DEFAULT NULL")
        await db.commit()
    except Exception:
        pass
    
    # Create feed_posts table if it doesn't exist (for existing installations)
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feed_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                thread_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feed_id) REFERENCES feeds (id) ON DELETE CASCADE
            )
        """)
        await db.commit()
    except Exception:
        pass


async def add_feed(
    guild_id: int, forum_channel_id: int, url: str, name: str | None = None
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO feeds (guild_id, forum_channel_id, url, name) VALUES (?, ?, ?, ?)",
            (guild_id, forum_channel_id, url, name),
        )
        await db.commit()


async def remove_feed(feed_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        await db.commit()


async def list_feeds(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, forum_channel_id, url, name FROM feeds WHERE guild_id = ?",
            (guild_id,),
        )
        return await cursor.fetchall()


async def get_all_feeds() -> Iterable[Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, forum_channel_id, url, name, last_entry_id FROM feeds"
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return rows


async def update_last_entry_id(feed_id: int, new_entry_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE feeds SET last_entry_id = ? WHERE id = ?", (new_entry_id, feed_id)
        )
        await db.commit()


async def record_feed_post(feed_id: int, thread_id: int) -> None:
    """Record a forum post created by a feed for cleanup tracking."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO feed_posts (feed_id, thread_id) VALUES (?, ?)",
            (feed_id, thread_id),
        )
        await db.commit()


async def get_feed_posts(feed_id: int) -> list[int]:
    """Get all thread IDs for posts created by a specific feed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT thread_id FROM feed_posts WHERE feed_id = ?", (feed_id,)
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return [row[0] for row in rows]


async def get_feed_info(feed_id: int) -> tuple[str, str] | None:
    """Get feed name and URL for a specific feed ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name, url FROM feeds WHERE id = ?", (feed_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            return row[0], row[1]  # name, url
        return None


async def cleanup_feed_posts(feed_id: int, bot) -> tuple[int, int, int]:
    """
    Clean up forum posts for a feed and return statistics.
    Returns (total_posts, successfully_deleted, failed_deletions).
    """
    import logging
    import discord
    
    logger = logging.getLogger(__name__)
    
    # Get all thread IDs for this feed
    thread_ids = await get_feed_posts(feed_id)
    total_posts = len(thread_ids)
    successfully_deleted = 0
    failed_deletions = 0
    
    if not thread_ids:
        return 0, 0, 0
    
    for thread_id in thread_ids:
        try:
            # Try to get the thread from Discord
            thread = bot.get_channel(thread_id)
            if thread is None:
                # Try to fetch if not in cache
                try:
                    thread = await bot.fetch_channel(thread_id)
                except discord.NotFound:
                    # Thread was already deleted manually
                    logger.debug(f"Thread {thread_id} already deleted")
                    successfully_deleted += 1
                    continue
                except discord.Forbidden:
                    logger.warning(f"No permission to access thread {thread_id}")
                    failed_deletions += 1
                    continue
                except Exception as e:
                    logger.error(f"Error fetching thread {thread_id}: {e}")
                    failed_deletions += 1
                    continue
            
            # Delete the thread
            if isinstance(thread, discord.Thread):
                await thread.delete()
                successfully_deleted += 1
                logger.debug(f"Deleted thread {thread_id}")
            else:
                logger.warning(f"Channel {thread_id} is not a thread")
                failed_deletions += 1
                
        except discord.NotFound:
            # Thread was already deleted
            successfully_deleted += 1
        except discord.Forbidden:
            logger.warning(f"No permission to delete thread {thread_id}")
            failed_deletions += 1
        except Exception as e:
            logger.error(f"Error deleting thread {thread_id}: {e}")
            failed_deletions += 1
    
    # Clean up database records (this will happen automatically with CASCADE)
    return total_posts, successfully_deleted, failed_deletions
