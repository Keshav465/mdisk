import asyncio
import logging
from pyrogram import Client, filters, types as t
from bot import Bot
from bot.config import Config
from bot.database.index_db import index_db
from bot.utils import group_wrapper, is_bot_admin, is_int, get_group_admins
from pyrogram.enums import ChatMemberStatus, ChatType

@Client.on_message(filters.command("index") & filters.group)
@group_wrapper
async def index_handler(c: Bot, m: t.Message):
    if len(m.command) < 2:
        return await m.reply("Usage: `/index channel_id` or `/index channel_username`")

    chat = m.command[1]
    sts = await m.reply("`Processing...`")

    try:
        if is_int(chat):
            chat = int(chat)
        
        target_chat = await c.get_chat(chat)
    except Exception as e:
        return await sts.edit(f"Error: {e}")

    if not target_chat.type.CHANNEL:
        return await sts.edit("This is not a channel.")

    # Check if bot is admin
    if not await is_bot_admin(c, target_chat.id):
        return await sts.edit(f"Make me admin in {target_chat.title} first!")

    await sts.edit(f"Starting indexing for **{target_chat.title}**...")
    
    count = 0
    total = 0
    files = []
    
    async for message in c.USER.search_messages(target_chat.id):
        if message.document or message.video or message.audio:
            file = message.document or message.video or message.audio
            file_name = getattr(file, 'file_name', None) or message.caption or ""
            
            if not file_name and message.caption:
                file_name = message.caption.splitlines()[0]
            
            if file_name:
                files.append({
                    'file_name': file_name.lower(),
                    'file_id': file.file_id,
                    'file_size': file.file_size,
                    'message_id': message.id,
                    'chat_id': target_chat.id,
                    'link': message.link
                })
                count += 1
                
                if len(files) >= 100:
                    await index_db.save_files_bulk(files)
                    files = []
                    await sts.edit(f"Indexed {count} files...")
        
        total += 1
        if total % 1000 == 0:
            await asyncio.sleep(1) # Throttling

    if files:
        await index_db.save_files_bulk(files)

    await sts.edit(f"Indexing completed! Total files indexed: **{count}**")

@Client.on_chat_member_updated()
async def auto_index_on_add(c: Bot, m: t.ChatMemberUpdated):
    """Automatically index a channel when the bot is added as an admin."""
    if not m.new_chat_member:
        return
    
    if m.new_chat_member.user.is_self and m.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
        if m.chat.type == ChatType.CHANNEL:
            logging.info(f"Bot added to channel {m.chat.title}. Starting auto-indexing...")
            # We don't have a message to reply to, so we just log it or send a message to log channel
            asyncio.create_task(perform_auto_indexing(c, m.chat.id))

async def perform_auto_indexing(c: Bot, chat_id):
    try:
        count = 0
        files = []
        async for message in c.USER.search_messages(chat_id):
            if message.document or message.video or message.audio:
                file = message.document or message.video or message.audio
                file_name = getattr(file, 'file_name', None) or message.caption or ""
                if not file_name and message.caption:
                    file_name = message.caption.splitlines()[0]
                
                if file_name:
                    files.append({
                        'file_name': file_name.lower(),
                        'file_id': file.file_id,
                        'file_size': file.file_size,
                        'message_id': message.id,
                        'chat_id': chat_id,
                        'link': message.link
                    })
                    count += 1
                    if len(files) >= 100:
                        await index_db.save_files_bulk(files)
                        files = []
        if files:
            await index_db.save_files_bulk(files)
        logging.info(f"Auto-indexing completed for {chat_id}. Total: {count}")
    except Exception as e:
        logging.error(f"Auto-indexing failed for {chat_id}: {e}")

@Client.on_message(filters.command("stats") & filters.user(Config.ADMINS))
async def stats_handler(c: Client, m: t.Message):
    total = await index_db.total_files()
    await m.reply(f"Total files in database: **{total}**")
