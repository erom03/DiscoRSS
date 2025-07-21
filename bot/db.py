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
                last_posted TEXT
            )
        """)
        await db.commit()


async def add_feed(guild_id: int, forum_channel_id: int, url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO feeds (guild_id, forum_channel_id, url, last_posted) VALUES (?, ?, ?, NULL)",
            (guild_id, forum_channel_id, url),
        )
        await db.commit()


async def remove_feed(feed_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        await db.commit()


async def list_feeds(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, forum_channel_id, url FROM feeds WHERE guild_id = ?",
            (guild_id,),
        )
        return await cursor.fetchall()
