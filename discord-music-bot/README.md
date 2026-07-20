# Quantum Müzik Botu

Modern, düşük maliyetli ve tamamen etkileşimli (interaktif) bir Discord müzik botu. Şarkıları diske indirmez (no persistent storage), Spotify playlistlerini hızlıca çözümleyerek YouTube üzerinden oynatır ve akıllı otomatik öneri sistemine sahiptir.

## Gereksinimler

- Python 3.12+
- FFmpeg
- Discord Bot Token
- Spotify Client ID ve Secret
- YouTube Data API v3 Key

## Kurulum (Yerel Geliştirme)

1. Depoyu klonlayın ve dizine gidin:
   ```bash
   git clone <repo-url>
   cd discord-music-bot
   ```
2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env.example` dosyasını kopyalayıp `.env` olarak adlandırın ve API anahtarlarınızı doldurun.
4. Botu başlatın:
   ```bash
   python bot.py
   ```

## Railway Üzerinde Dağıtım (Deployment)

Quantum Müzik Botu'nu Railway üzerinde 7/24 çalışacak şekilde ücretsiz/düşük maliyetli bir katmanda barındırabilirsiniz:

1. **Projeyi GitHub’a Yükleme:** Bu projeyi kendi GitHub hesabınızda gizli veya açık bir repository olarak paylaşın.
2. **Railway Projesi Oluşturma:** [Railway.app](https://railway.app/) adresine gidin ve yeni bir "Empty Project" (Boş Proje) veya doğrudan "Deploy from GitHub repo" seçeneğini seçin.
3. **GitHub Repository Bağlama:** GitHub hesabınıza izin verin ve müzik botu reponuzu seçin.
4. **Environment Variable Ekleme:** Railway projenizin `Variables` sekmesine gidin ve `.env.example` içerisindeki tüm değişkenleri (`DISCORD_TOKEN`, `SPOTIFY_CLIENT_ID` vb.) ekleyin.
5. **Deploy Etme:** Değişkenleri ekledikten sonra Railway, Dockerfile'ı kullanarak botu otomatik olarak derleyecek ve başlatacaktır.
6. **Logları Kontrol Etme:** Railway üzerindeki `Deployments` sekmesine tıklayıp son dağıtımın `View Logs` butonuna basarak botun sorunsuz çalıştığından emin olun (örn: "Slash komutları senkronize edildi" mesajını arayın).
7. **Discord Bot İzinlerini Ayarlama:** Botunuzu Discord sunucunuza eklerken **Administrator izni istemeyin.** Sadece aşağıdaki gerekli izinleri vermeniz yeterlidir.
8. **Slash Command Senkronizasyonunu Kontrol Etme:** Discord sunucunuza gidip `/bot-kontrol` yazarak komutun aktif olup olmadığını kontrol edin.

## Gerekli Discord İzinleri

Botu OAuth2 URL'si üzerinden sunucunuza davet ederken şu izinleri (Bot ve application.commands scope'ları ile) işaretleyin:
- View Channels
- Send Messages
- Embed Links
- Read Message History
- Connect
- Speak
- Use Application Commands

*Not: Administrator yetkisine gerek yoktur.*

## Komutlar
Bot **prefix** (örn: `!çal`) kullanmaz. Sadece slash command destekler.
- `/bot-kontrol`: Bulunduğunuz ses kanalında müzik panelini açar. Panel üzerinden şarkı arayabilir, playlist ekleyebilir, karıştırabilir ve geçmişte gezinebilirsiniz.
