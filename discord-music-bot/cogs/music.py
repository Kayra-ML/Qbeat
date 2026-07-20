import discord
from discord import app_commands
from discord.ext import commands
from views.music_panel import MusicPanel
from utils.logger import logger
from models.guild_music_state import GuildMusicState
from services.audio_service import AudioService
from services.spotify_service import SpotifyService
from services.youtube_service import YouTubeService
from services.recommendation_service import RecommendationService
from services.input_parser import InputParser
import asyncio
import random
import collections
import time
from discord.ext import tasks

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.audio_service = AudioService()
        self.spotify_service = SpotifyService()
        self.youtube_service = YouTubeService()
        self.recommendation_service = RecommendationService(self.audio_service)
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        self.idle_timeout = 300 # 5 minutes
        self.idle_check_task.start()

    def cog_unload(self):
        self.idle_check_task.cancel()

    @tasks.loop(seconds=30)
    async def idle_check_task(self):
        current_time = time.time()
        for voice_channel_id, state in list(self.states.items()):
            if state.voice_client and state.voice_client.is_connected():
                if not state.voice_client.is_playing() and not state.voice_client.is_paused():
                    if (current_time - state.last_activity) > self.idle_timeout:
                        logger.info(f"Ses kanalında boşta kalındı, bağlantı kesiliyor: {voice_channel_id}")
                        try:
                            await state.voice_client.disconnect(force=True)
                        except:
                            pass
                        state.voice_client = None
                        state.queue.clear()
                        state.history.clear()
                        state.current_track = None
                        await self.update_panel(state)
                else:
                    state.last_activity = current_time

    def get_state(self, voice_channel_id: int) -> GuildMusicState:
        if voice_channel_id not in self.states:
            self.states[voice_channel_id] = GuildMusicState(voice_channel_id)
        return self.states[voice_channel_id]

    def get_worker_for_channel(self, voice_channel_id: int, guild_id: int):
        main_guild = self.bot.get_guild(guild_id)
        if main_guild and main_guild.voice_client and main_guild.voice_client.channel.id == voice_channel_id:
            return self.bot
            
        if hasattr(self.bot, 'workers'):
            for worker in self.bot.workers:
                g = worker.get_guild(guild_id)
                if g and g.voice_client and g.voice_client.channel.id == voice_channel_id:
                    return worker
                    
        if main_guild and not main_guild.voice_client:
            return self.bot
            
        if hasattr(self.bot, 'workers'):
            for worker in self.bot.workers:
                g = worker.get_guild(guild_id)
                if g and not g.voice_client:
                    return worker
                    
        return None

    @app_commands.command(name="bot-kontrol", description="Müzik kontrol panelini açar.")
    async def music_panel_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("Bu komutu kullanmak için bir ses kanalında olmalısınız.", ephemeral=True)
            return
            
        voice_channel = interaction.user.voice.channel
        state = self.get_state(voice_channel.id)
        
        assigned_bot = self.get_worker_for_channel(voice_channel.id, interaction.guild_id)
        if not assigned_bot:
            await interaction.followup.send("Tüm botlar şu an meşgul! Lütfen boşta bir bot olmasını bekleyin.", ephemeral=True)
            return
            
        if state.panel_message:
            try:
                await state.panel_message.delete()
            except:
                pass

        embed = self.build_panel_embed(state, interaction.user)
        view = MusicPanel(self)
        
        message = await interaction.followup.send(embed=embed, view=view, wait=True)
        state.panel_message = message
        state.panel_channel_id = interaction.channel_id
        
        state.assigned_bot = assigned_bot
        worker_guild = assigned_bot.get_guild(interaction.guild_id)
        worker_channel = worker_guild.get_channel(voice_channel.id)
        
        if not worker_guild.voice_client:
            try:
                state.voice_client = await worker_channel.connect(timeout=60.0, self_deaf=True)
            except Exception as e:
                logger.error(f"Ses kanalina baglanma hatasi: {e}")
                await interaction.followup.send("Ses kanalına bağlanırken bir hata oluştu veya zaman aşımına uğradı.", ephemeral=True)
                return
        else:
            state.voice_client = worker_guild.voice_client
            if not state.voice_client.is_connected():
                try:
                    await state.voice_client.disconnect(force=True)
                except:
                    pass
                try:
                    state.voice_client = await worker_channel.connect(timeout=60.0, self_deaf=True)
                except Exception as e:
                    logger.error(f"Ses kanalina yeniden baglanma hatasi: {e}")
                    await interaction.followup.send("Ses kanalına yeniden bağlanırken hata oluştu.", ephemeral=True)
                    return
            elif state.voice_client.channel != worker_channel:
                if not state.voice_client.is_playing() and not state.voice_client.is_paused():
                    try:
                        await state.voice_client.move_to(worker_channel)
                    except:
                        await interaction.followup.send(f"Bot zaten başka bir kanalda: {state.voice_client.channel.name}", ephemeral=True)
                        return
                else:
                    await interaction.followup.send(f"Bot şu an {state.voice_client.channel.name} kanalında müzik çalıyor.", ephemeral=True)
                    return

    @app_commands.command(name="cal", description="Müzik başlatır (Şarkı ismi veya link girin).")
    @app_commands.describe(sarki="Çalınacak şarkının adı veya YouTube/Spotify linki")
    async def play_cmd(self, interaction: discord.Interaction, sarki: str):
        logger.info(f"/cal komutu cagrildi! User: {interaction.user.name}, Sarki: {sarki}")
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("Bu komutu kullanmak için bir ses kanalında olmalısınız.", ephemeral=True)
            return
            
        voice_channel = interaction.user.voice.channel
        state = self.get_state(voice_channel.id)
        
        assigned_bot = self.get_worker_for_channel(voice_channel.id, interaction.guild_id)
        if not assigned_bot:
            await interaction.followup.send("Tüm botlar şu an meşgul! Lütfen boşta bir bot olmasını bekleyin.", ephemeral=True)
            return
            
        if state.panel_message:
            try:
                await state.panel_message.delete()
            except:
                pass

        embed = self.build_panel_embed(state, interaction.user)
        view = MusicPanel(self)
        
        message = await interaction.followup.send(embed=embed, view=view, wait=True)
        state.panel_message = message
        state.panel_channel_id = interaction.channel_id
        
        state.assigned_bot = assigned_bot
        worker_guild = assigned_bot.get_guild(interaction.guild_id)
        worker_channel = worker_guild.get_channel(voice_channel.id)
        
        if not worker_guild.voice_client:
            try:
                state.voice_client = await worker_channel.connect(timeout=60.0, self_deaf=True)
            except Exception as e:
                logger.error(f"Ses kanalina baglanma hatasi: {e}")
                await interaction.followup.send("Ses kanalına bağlanırken bir hata oluştu veya zaman aşımına uğradı.", ephemeral=True)
                return
        else:
            state.voice_client = worker_guild.voice_client
            if not state.voice_client.is_connected():
                try:
                    await state.voice_client.disconnect(force=True)
                except:
                    pass
                try:
                    state.voice_client = await worker_channel.connect(timeout=60.0, self_deaf=True)
                except Exception as e:
                    logger.error(f"Ses kanalina yeniden baglanma hatasi: {e}")
                    await interaction.followup.send("Ses kanalına yeniden bağlanırken hata oluştu.", ephemeral=True)
                    return
            elif state.voice_client.channel != worker_channel:
                if not state.voice_client.is_playing() and not state.voice_client.is_paused():
                    try:
                        await state.voice_client.move_to(worker_channel)
                    except:
                        await interaction.followup.send(f"Bot zaten başka bir kanalda: {state.voice_client.channel.name}", ephemeral=True)
                        return
                else:
                    await interaction.followup.send(f"Bot şu an {state.voice_client.channel.name} kanalında müzik çalıyor.", ephemeral=True)
                    return

        await self.process_track_input(interaction, sarki)

    def build_panel_embed(self, state: GuildMusicState, user: discord.Member = None):
        embed = discord.Embed(
            title="🎵 Quantum Müzik Paneli",
            color=discord.Color.blurple()
        )
        
        repeat_str = "Kapalı"
        if state.repeat_mode == 1:
            repeat_str = "Tek Şarkı"
        elif state.repeat_mode == 2:
            repeat_str = "Kuyruk"
            
        if state.current_track:
            embed.description = "Şu anda oynatılıyor..."
            track = state.current_track
            embed.add_field(name="Şu Anda Çalan", value=track.title, inline=False)
            embed.add_field(name="Sanatçı", value=track.artist, inline=True)
            
            mins, secs = divmod(int(track.duration), 60)
            embed.add_field(name="Süre", value=f"{mins}:{secs:02d}", inline=True)
            embed.add_field(name="Kuyruk", value=f"{len(state.queue)} şarkı", inline=True)
            embed.add_field(name="Kaynak", value=track.source_type.capitalize() if track.source_type else "-", inline=True)
            
            req_by = track.requested_by if track.requested_by else "Bilinmiyor"
            if track.is_recommendation:
                req_by = "✨ Otomatik öneri"
                
            embed.add_field(name="Ekleyen", value=req_by, inline=True)
            
            embed.add_field(name="Tekrar", value=repeat_str, inline=True)
            embed.add_field(name="Otomatik Öneri", value="Açık" if state.autoplay_enabled else "Kapalı", inline=True)
            if track.thumbnail_url:
                embed.set_thumbnail(url=track.thumbnail_url)
        else:
            embed.description = "Henüz bir şarkı oynatılmıyor."
            embed.add_field(name="Şu Anda Çalan", value="Belirtilmedi", inline=False)
            embed.add_field(name="Sanatçı", value="Belirtilmedi", inline=True)
            embed.add_field(name="Süre", value="00:00", inline=True)
            embed.add_field(name="Kuyruk", value=f"{len(state.queue)} şarkı", inline=True)
            embed.add_field(name="Kaynak", value="-", inline=True)
            embed.add_field(name="Ekleyen", value="-", inline=True)
            embed.add_field(name="Tekrar", value=repeat_str, inline=True)
            embed.add_field(name="Otomatik Öneri", value="Açık" if state.autoplay_enabled else "Kapalı", inline=True)
            
        if user and user.voice:
            embed.add_field(name="Kanal", value=user.voice.channel.name, inline=False)
        elif state.voice_client:
            embed.add_field(name="Kanal", value=state.voice_client.channel.name, inline=False)
            
        return embed

    async def update_panel(self, state: GuildMusicState):
        if state.panel_message:
            try:
                embed = self.build_panel_embed(state)
                view = MusicPanel(self)
                
                if state.current_track:
                    track_name = state.current_track.title
                    if len(track_name) > 80:
                        track_name = track_name[:77] + "..."
                    view.children[1].label = track_name
                else:
                    view.children[1].label = "Henüz bir şarkı oynatılmıyor."
                    
                if state.voice_client and state.voice_client.is_paused():
                    view.children[3].label = "▶ Devam"
                    view.children[3].style = discord.ButtonStyle.success
                else:
                    view.children[3].label = "⏸ Duraklat"
                    view.children[3].style = discord.ButtonStyle.primary
                    
                await state.panel_message.edit(embed=embed, view=view)
            except Exception as e:
                logger.error(f"Panel güncelleme hatası: {e}")

    async def process_track_input(self, interaction: discord.Interaction, query: str):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        if not state.voice_client or not state.voice_client.is_connected():
            await interaction.followup.send("Bot bir ses kanalında değil. Lütfen önce `/bot-kontrol` komutunu kullanın.", ephemeral=True)
            return

        input_type, parsed_query = InputParser.parse_input(query)
        requester = interaction.user.display_name

        if input_type in ["spotify_playlist", "spotify_album", "spotify_artist"]:
            if input_type == "spotify_playlist":
                tracks_info = await self.spotify_service.get_playlist_tracks(parsed_query)
            elif input_type == "spotify_album":
                tracks_info = await self.spotify_service.get_album_tracks(parsed_query)
            else:
                tracks_info = await self.spotify_service.get_artist_top_tracks(parsed_query)
                
            if not tracks_info:
                input_type = "direct_url"
            else:
                await interaction.followup.send(f"{len(tracks_info)} şarkı arka planda eşleştirilip kuyruğa ekleniyor...", ephemeral=True)
                self.bot.loop.create_task(self._process_spotify_tracks(state, tracks_info, requester))
                return
            
        if input_type == "spotify_track":
            track_info = await self.spotify_service.get_track(parsed_query)
            if not track_info:
                input_type = "direct_url"
            else:
                await self._enqueue_spotify_track(state, track_info, requester, interaction)
                return
            
        search_val = parsed_query
        if input_type == "search_query":
            search_val = f"ytsearch:{parsed_query}"
            
        track = await self.audio_service.get_track_info(search_val, requester=requester)
        if not track:
            await interaction.followup.send("Şarkı bulunamadı.", ephemeral=True)
            return
        
        state.queue.append(track)
        await interaction.followup.send(f"Kuyruğa eklendi: **{track.title}**", ephemeral=True)
        if not state.voice_client.is_playing() and not state.voice_client.is_paused() and not state.is_transitioning:
            await self.play_next(state)
        else:
            await self.update_panel(state)

    async def _process_spotify_tracks(self, state: GuildMusicState, tracks_info: list, requester: str):
        success_count = 0
        fail_count = 0
        for info in tracks_info:
            success = await self._enqueue_spotify_track(state, info, requester, interaction=None)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"Spotify playlist import bitirildi: {success_count} eklendi, {fail_count} bulunamadı.")
        if state.panel_channel_id:
            channel = self.bot.get_channel(state.panel_channel_id)
            if channel:
                msg = f"Playlist işlemi tamamlandı: {success_count} eklendi."
                if fail_count > 0:
                    msg += f" ({fail_count} şarkı atlandı)"

    async def _enqueue_spotify_track(self, state: GuildMusicState, info: dict, requester: str, interaction: discord.Interaction = None):
        yt_url = await self.youtube_service.search_and_match(info['title'], info['artist'], info['duration'])
        if not yt_url:
            if interaction:
                await interaction.followup.send(f"Eşleşme bulunamadı: {info['title']}", ephemeral=True)
            return False
            
        track = await self.audio_service.get_track_info(yt_url, requester=requester)
        if not track:
            if interaction:
                await interaction.followup.send(f"Şarkı bilgisi alınamadı: {info['title']}", ephemeral=True)
            return False
            
        track.title = info['title']
        track.artist = info['artist']
        track.spotify_id = info['spotify_id']
        track.source_type = 'spotify/youtube'
        
        state.queue.append(track)
        
        if interaction:
            await interaction.followup.send(f"Kuyruğa eklendi: **{track.title}**", ephemeral=True)
            
        if not state.voice_client.is_playing() and not state.voice_client.is_paused() and not state.is_transitioning:
            await self.play_next(state)
        else:
            await self.update_panel(state)
            
        return True

    async def play_next(self, state: GuildMusicState):
        async with state.lock:
            state.is_transitioning = True
            
            if len(state.queue) == 0:
                if state.autoplay_enabled:
                    recommendation = await self.recommendation_service.get_recommendation(state)
                    if recommendation:
                        state.queue.append(recommendation)
                    else:
                        state.current_track = None
                        state.is_transitioning = False
                        state.last_activity = time.time()
                        await self.update_panel(state)
                        return
                else:
                    state.current_track = None
                    state.is_transitioning = False
                    state.last_activity = time.time()
                    await self.update_panel(state)
                    return

            track = state.queue.popleft()
            state.current_track = track

            stream_url = track.audio_stream_url
            if not stream_url:
                stream_url = await self.audio_service.resolve_stream_url(track)
                
            if not stream_url:
                logger.error("Şarkı stream URL'si çözülemedi, atlanıyor.")
                state.is_transitioning = False
                self.bot.loop.create_task(self.play_next(state))
                return

            try:
                audio_source = discord.FFmpegPCMAudio(stream_url, **self.ffmpeg_options)
                
                def after_playing(error):
                    if error:
                        logger.error(f"Oynatma hatası: {error}")
                    
                    if state.current_track:
                        state.history.append(state.current_track)
                        if state.repeat_mode == 1:
                            state.queue.appendleft(state.current_track)
                        elif state.repeat_mode == 2:
                            state.queue.append(state.current_track)
                            
                        state.current_track = None
                        
                    if state.voice_client and state.voice_client.is_connected():
                        self.bot.loop.create_task(self.play_next(state))

                state.voice_client.play(audio_source, after=after_playing)
            except Exception as e:
                logger.error(f"FFmpeg oynatma hatası: {e}")
                state.is_transitioning = False
                self.bot.loop.create_task(self.play_next(state))
                return
                
            state.is_transitioning = False
            
        await self.update_panel(state)

    async def skip_forward(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        if not state.voice_client or not state.current_track:
            await interaction.response.send_message("Şu anda çalan bir şarkı yok.", ephemeral=True)
            return

        state.history.append(state.current_track)
        state.current_track = None
        state.voice_client.stop()
        await interaction.response.send_message("Sıradaki şarkıya geçiliyor...", ephemeral=True)

    async def skip_backward(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        if not state.voice_client:
            return

        if not state.history:
            await interaction.response.send_message("Daha önce oynatılmış bir şarkı bulunmuyor.", ephemeral=True)
            return

        if state.current_track:
            state.queue.appendleft(state.current_track)
            state.current_track = None

        prev_track = state.history.pop()
        state.queue.appendleft(prev_track)
        
        if state.voice_client.is_playing() or state.voice_client.is_paused():
            state.voice_client.stop()
        else:
            await self.play_next(state)
            
        await interaction.response.send_message("Önceki şarkıya dönülüyor...", ephemeral=True)

    async def pause_resume(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        if not state.voice_client or not state.current_track:
            await interaction.response.send_message("Oynatılan bir şarkı yok.", ephemeral=True)
            return
            
        if state.voice_client.is_playing():
            state.voice_client.pause()
            state.last_activity = time.time()
            await interaction.response.send_message("Müzik duraklatıldı.", ephemeral=True)
        elif state.voice_client.is_paused():
            state.voice_client.resume()
            state.last_activity = time.time()
            await interaction.response.send_message("Müzik devam ediyor.", ephemeral=True)
            
        await self.update_panel(state)

    async def stop_playback(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        state.queue.clear()
        state.history.clear()
        if state.voice_client and (state.voice_client.is_playing() or state.voice_client.is_paused()):
            state.current_track = None
            state.voice_client.stop()
        
        state.current_track = None
        state.last_activity = time.time()
        await self.update_panel(state)
        await interaction.response.send_message("Oynatma durduruldu, kuyruk ve geçmiş temizlendi.", ephemeral=True)

    async def shuffle_queue(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        if len(state.queue) < 2:
            await interaction.response.send_message("Karıştırılacak yeterli şarkı yok.", ephemeral=True)
            return
            
        queue_list = list(state.queue)
        random.shuffle(queue_list)
        state.queue = collections.deque(queue_list)
        await interaction.response.send_message("Kuyruk başarıyla karıştırıldı.", ephemeral=True)
        await self.update_panel(state)

    async def toggle_repeat(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        state.repeat_mode = (state.repeat_mode + 1) % 3
        
        modes = ["Kapalı", "Tek Şarkı", "Kuyruk"]
        await interaction.response.send_message(f"Tekrar modu: **{modes[state.repeat_mode]}**", ephemeral=True)
        await self.update_panel(state)

    async def show_queue(self, interaction: discord.Interaction):
        if not getattr(interaction.user, 'voice', None) or not interaction.user.voice.channel:
            try:
                await interaction.followup.send("Lütfen bir ses kanalına katılın.", ephemeral=True)
            except:
                pass
            return
        state = self.get_state(interaction.user.voice.channel.id)
        if not state.queue:
            await interaction.response.send_message("Kuyruk boş.", ephemeral=True)
            return
            
        embed = discord.Embed(title="📜 Müzik Kuyruğu", color=discord.Color.blurple())
        
        queue_list = list(state.queue)
        display_count = min(10, len(queue_list))
        
        description = ""
        for i in range(display_count):
            track = queue_list[i]
            description += f"**{i+1}.** {track.title} - *{track.artist}*\n"
            
        if len(queue_list) > 10:
            description += f"\n*...ve {len(queue_list) - 10} şarkı daha.*"
            
        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
