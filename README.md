<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:f59e0b,100:ef4444&height=200&section=header&text=Qbeat&fontSize=70&fontColor=ffffff&fontAlignY=38&desc=Discord%20Multi-Instance%20Music%20Bot&descAlignY=58&descAlign=50&animation=fadeIn" />

</div>

> **"Bir bot değil, bir orkestra."**  
> Qbeat, Discord sunucuları için geliştirilmiş, cluster mimarisiyle birden fazla sesli kanalda eş zamanlı müzik çalabilen gelişmiş bir müzik botudur.

---

## 💡 Fikir ve Motivasyon

Mevcut Discord müzik botlarının en büyük sorunu: büyük sunucularda tek bir bot instance'ının tıkanması. Birden fazla kanalda aynı anda müzik çalmak isteyenler için bot takılıyor, gecikmeli yanıt veriyor.

**Çözüm:** Cluster mimarisi. Bir "Main Bot" + N adet "Worker Bot" ile, gelen yükü bölerek çözdüm. Main bot komutları yönetir; worker botlar sesli kanallarda çalar.

---

## 🏗️ Mimari — Cluster Sistemi

```python
class MusicBot(commands.Bot):
    def __init__(self, is_worker=False):
        # Main Bot: Slash komutları, senkronizasyon
        # Worker Bot: Sesli kanal oynatma
        self.is_worker = is_worker

async def start_cluster():
    main_bot = MusicBot(is_worker=False)
    workers = [MusicBot(is_worker=True) for _ in WORKER_TOKENS]
    # Hepsi asyncio.gather ile paralel çalışır
    await asyncio.gather(*[main_bot, *workers])
```

```
Discord Sunucusu
│
├── Main Bot (DISCORD_TOKEN)
│   ├── Slash komutlarını yönetir
│   ├── Guild'e komut senkronize eder
│   └── Worker botlara iş dağıtır
│
├── Worker Bot 1 (WORKER_TOKEN_1)
│   └── Sesli Kanal #1'de çalar
│
└── Worker Bot N (WORKER_TOKEN_N)
    └── Sesli Kanal #N'de çalar
```

---

## ⚙️ Özellikler

- 🎵 **YouTube, Spotify, SoundCloud** desteği
- 🔀 **Sıra yönetimi** — queue, skip, shuffle
- 🔊 **Ses kontrolü** — volume, bass boost
- 🎛️ **Discord Slash Commands** (`/play`, `/skip`, `/queue`...)
- 🐳 **Docker** desteği — production-ready
- ☁️ **Railway** deploy — IPv4 zorlamalı (IPv6 bug'ını çözdüm)
- 📦 **Cog sistemi** — modüler komut yapısı

---

## 🛠️ Tech Stack

| Bileşen | Teknoloji |
|---------|-----------|
| Bot Framework | discord.py |
| Ses Oynatma | yt-dlp + FFmpeg |
| Mimari | Asyncio + Cluster |
| Deployment | Docker + Railway |
| Komut Yapısı | Cogs (modüler) |

---

## 📁 Proje Yapısı

```
discord-music-bot/
├── bot.py          # Ana giriş — Cluster başlatıcı
├── config.py       # Token ve ayar yönetimi
├── cogs/
│   └── music.py    # Tüm müzik komutları (28KB!)
├── services/       # İş mantığı servisleri
├── models/         # Veri modelleri
├── views/          # Discord UI (butonlar, seçiciler)
├── utils/          # Logger ve yardımcılar
└── Dockerfile      # Production container
```

---

## 🚀 Kurulum

### Lokal
```bash
pip install -r requirements.txt
cp .env.example .env
# .env'e DISCORD_TOKEN, WORKER_TOKENS ekle
python bot.py
```

### Docker
```bash
docker build -t qbeat .
docker run --env-file .env qbeat
```

---

## 🐛 Çözdüğüm İlginç Bug

Railway (cloud platform) IPv6 sorunları yaşıyordu. Discord'a bağlanırken IPv6 ile hata alıyordu. Çözüm: `socket.getaddrinfo` fonksiyonunu monkey-patch ederek sadece IPv4 yanıtlarını döndürdüm.

```python
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo
```

---

<div align="center">
<img src="https://img.shields.io/badge/discord.py-Bot-5865F2?style=flat-square&logo=discord" />
<img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker" />
<img src="https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=flat-square" />
<img src="https://img.shields.io/badge/Asyncio-Cluster-3776AB?style=flat-square&logo=python" />

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:ef4444,50:f59e0b,100:0d1117&height=100&section=footer" />
</div>
