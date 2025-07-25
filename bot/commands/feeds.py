from discord.ext import commands
import discord
import asyncio
from bot import db


def setup_feeds(bot: commands.Bot):
    @bot.hybrid_command(
        name="addfeed", description="Add a new RSS feed to a forum channel"
    )
    @commands.has_permissions(administrator=True)
    async def addfeed(
        ctx: commands.Context[commands.Bot],
        forum_channel: discord.ForumChannel,
        url: str,
        *,
        name: str | None = None,
    ):
        if ctx.guild is None:
            return

        await db.add_feed(ctx.guild.id, forum_channel.id, url, name)
        feed_display = name if name else url
        await ctx.send(f"Feed added: `{feed_display}` → {forum_channel.mention}")

    @bot.hybrid_command(name="removefeed", description="Remove a feed by its ID")
    @commands.has_permissions(administrator=True)
    async def removefeed(ctx: commands.Context[commands.Bot], feed_id: int):
        # Get feed info for confirmation
        feed_info = await db.get_feed_info(feed_id)
        if not feed_info:
            await ctx.send(f"❌ Feed `{feed_id}` not found.")
            return
        
        name, url = feed_info
        feed_display = name if name else url
        
        # Get post count for confirmation
        thread_ids = await db.get_feed_posts(feed_id)
        post_count = len(thread_ids)
        
        # Confirmation message
        if post_count > 0:
            confirmation_msg = (
                f"⚠️ This will delete the feed **{feed_display}** and remove **{post_count}** forum posts.\n"
                f"Type `yes` to confirm or anything else to cancel:"
            )
        else:
            confirmation_msg = (
                f"⚠️ This will delete the feed **{feed_display}**.\n"
                f"Type `yes` to confirm or anything else to cancel:"
            )
        
        await ctx.send(confirmation_msg)
        
        def check(message):
            return (
                message.author == ctx.author 
                and message.channel == ctx.channel
            )
        
        try:
            response = await ctx.bot.wait_for('message', check=check, timeout=30.0)
            
            if response.content.lower() != 'yes':
                await ctx.send("❌ Feed removal cancelled.")
                return
            
            # Start cleanup process
            if post_count > 0:
                cleanup_msg = await ctx.send(f"🧹 Cleaning up forum posts... ({post_count} posts to remove)")
                
                total, success, failed = await db.cleanup_feed_posts(feed_id, ctx.bot)
                
                # Update cleanup message with results
                if failed > 0:
                    result_msg = f"✅ Successfully removed {success} posts, {failed} posts failed to delete"
                else:
                    result_msg = f"✅ Successfully removed all {success} posts"
                
                await cleanup_msg.edit(content=result_msg)
            
            # Remove the feed from database
            await db.remove_feed(feed_id)
            await ctx.send(f"✅ Feed **{feed_display}** removed successfully.")
            
        except asyncio.TimeoutError:
            await ctx.send("❌ Confirmation timeout. Feed removal cancelled.")

    @bot.hybrid_command(
        name="listfeeds", description="List all RSS feeds for this server"
    )
    @commands.has_permissions(administrator=True)
    async def listfeeds(ctx: commands.Context[commands.Bot]):
        if ctx.guild is None:
            return
        feeds = await db.list_feeds(ctx.guild.id)
        if not feeds:
            await ctx.send("No RSS feeds configured for this server.")
            return

        msg = "\n".join(
            f"**[{feed_id}]** {name or url} → <#{forum_channel_id}>"
            for feed_id, forum_channel_id, url, name in feeds
        )

        await ctx.send(f"Configured feeds:\n{msg}")
