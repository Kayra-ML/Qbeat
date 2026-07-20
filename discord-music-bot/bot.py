import discord
from discord.ext import commands
import asyncio
import socket

# IPv4 Zorlaması (Railway'in IPv6 hatalarını atlamak için)
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

from config import DISCORD_TOKEN, DISCORD_APPLICATION_ID, TEST_GUILD_ID, WORKER_TOKENS
from utils.logger import logger

class MusicBot(commands.Bot):
    def __init__(self, is_worker=False):
        intents = discord.Intents.default()
        intents.message_content = False
        intents.voice_states = True
        
        self.is_worker = is_worker
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=int(DISCORD_APPLICATION_ID) if (DISCORD_APPLICATION_ID and not is_worker) else None
        )

    async def setup_hook(self):
        if not self.is_worker:
            logger.info("Yüklenen coglar: cogs.music (Main)")
            await self.load_extension("cogs.music")
            
            if TEST_GUILD_ID:
                guild = discord.Object(id=int(TEST_GUILD_ID))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Slash komutları {TEST_GUILD_ID} ID'li test sunucusuna senkronize edildi.")
            else:
                await self.tree.sync()
                logger.info("Slash komutları global olarak senkronize edildi.")
        else:
            logger.info("Yüklenen coglar: cogs.music (Worker)")
            await self.load_extension("cogs.music")

    async def on_ready(self):
        logger.info(f"{self.user} (ID: {self.user.id}) olarak giriş yapıldı. [Worker: {self.is_worker}]")
        if not self.is_worker:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/bot-kontrol"))

async def start_bot_safely(bot_instance, token):
    try:
        await bot_instance.start(token)
    except Exception as e:
        logger.error(f"Bot baslatilamadi (Token hatali olabilir): {e}")

async def start_cluster():
    main_bot = MusicBot(is_worker=False)
    
    workers = []
    for _ in WORKER_TOKENS:
        workers.append(MusicBot(is_worker=True))
        
    main_bot.workers = workers
    
    tasks = [asyncio.create_task(start_bot_safely(main_bot, DISCORD_TOKEN))]
    for i, worker in enumerate(workers):
        tasks.append(asyncio.create_task(start_bot_safely(worker, WORKER_TOKENS[i])))
        
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN bulunamadı. Lütfen çevre değişkenlerini ayarlayın.")
    else:
        asyncio.run(start_cluster())
