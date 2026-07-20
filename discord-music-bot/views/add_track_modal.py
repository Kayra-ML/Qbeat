import discord
import traceback
from utils.logger import logger

class AddTrackModal(discord.ui.Modal, title='Şarkı veya Çalma Listesi Ekle'):
    track_input = discord.ui.TextInput(
        label='Spotify playlist, YouTube bağlantısı veya ad',
        style=discord.TextStyle.short,
        placeholder='Spotify playlist URL’si, YouTube URL’si veya şarkı adı yapıştırın',
        required=True,
    )

    def __init__(self, music_cog):
        super().__init__()
        self.music_cog = music_cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        query = self.track_input.value
        
        try:
            await self.music_cog.process_track_input(interaction, query)
        except Exception as e:
            logger.error(f"AddTrackModal Error: {traceback.format_exc()}")
            if not interaction.is_expired():
                await interaction.followup.send(f"Bir hata oluştu: {e}", ephemeral=True)
