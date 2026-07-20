import discord
from views.add_track_modal import AddTrackModal

class MusicPanel(discord.ui.View):
    def __init__(self, music_cog):
        super().__init__(timeout=None)
        self.music_cog = music_cog
    
    @discord.ui.button(label="⏮ Geri", style=discord.ButtonStyle.secondary, row=0, custom_id="btn_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.skip_backward(interaction)

    @discord.ui.button(label="Henüz bir şarkı oynatılmıyor.", style=discord.ButtonStyle.secondary, disabled=True, row=0, custom_id="btn_title")
    async def btn_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="İleri ⏭", style=discord.ButtonStyle.secondary, row=0, custom_id="btn_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.skip_forward(interaction)

    @discord.ui.button(label="⏯ Duraklat / Devam", style=discord.ButtonStyle.primary, row=1, custom_id="btn_pause_resume")
    async def btn_pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.pause_resume(interaction)

    @discord.ui.button(label="⏹ Durdur", style=discord.ButtonStyle.danger, row=1, custom_id="btn_stop")
    async def btn_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.stop_playback(interaction)

    @discord.ui.button(label="➕ Şarkı veya Liste Ekle", style=discord.ButtonStyle.success, row=1, custom_id="btn_add")
    async def btn_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddTrackModal(self.music_cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔀 Karıştır", style=discord.ButtonStyle.secondary, row=2, custom_id="btn_shuffle")
    async def btn_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.shuffle_queue(interaction)

    @discord.ui.button(label="🔁 Tekrar", style=discord.ButtonStyle.secondary, row=2, custom_id="btn_repeat")
    async def btn_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.toggle_repeat(interaction)

    @discord.ui.button(label="📜 Kuyruk", style=discord.ButtonStyle.secondary, row=2, custom_id="btn_queue")
    async def btn_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog.show_queue(interaction)
