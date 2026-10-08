# 📸 Instagram Video Downloader Telegram Bot (@mrsaver12bot)

Ushbu bot Instagram ijtimoiy tarmog'idagi Reels, video va postlarni to'g'ridan-to'g'ri Telegram orqali yuklab beruvchi to'liq asinxron botdir.

---

## 🚀 Texnologiyalar
- **Python 3.11+**
- **aiogram 3.x** (Asinxron va tezkor Telegram Bot freymvorki)
- **yt-dlp** (Tezkor va sifatli media yuklovchi vosita)
- **python-dotenv** (Konfiguratsiya va tokenni xavfsiz boshqarish)
- **Docker / Procfile / render.yaml** (24/7 bulutli serverlarda ishga tushirish uchun tayyor)

---

## 📁 Loyiha tuzilishi

```
instagram_bot/
├── bot.py             # Asosiy Telegram bot logikasi va komandalar
├── downloader.py      # Instagramdan videolarni yuklab olish logikasi
├── config.py          # Sozlamalar va .env fayli bilan ishlash
├── requirements.txt   # Kerakli Python kutubxonalari
├── Dockerfile         # 24/7 bulutli serverlar uchun Docker konteyneri
├── Procfile           # Render / Railway worker sozlamasi
├── render.yaml        # Render.com avtomatik sozlamasi
├── .gitignore         # .env va ortiqcha fayllarni GitHub ga chiqarmaslik uchun
├── .env               # Bot tokeni saqlanadigan maxfiy fayl
├── .env.example       # Namunaviy .env fayli
└── downloads/         # Vaqtinchalik yuklab olingan fayllar (avtomatik tozalanadi)
```

---

## 🐙 1-QADAM: Loyihani GitHub ga yuklash

> [!CAUTION]
> **Muhim eslatma:** `.gitignore` fayli sozlangan bo'lib, sizning maxfiy `.env` faylingiz GitHub ga yuklanmaydi. Tokenni ommaviy repoga hech qachon yuklamang!

1. [GitHub.com](https://github.com) saytiga kiring va yangi repository oching (masalan, `instagram-downloader-bot`).
2. Agar kompyuteringizda Git o'rnatilgan bo'lsa, loyiha papkasida terminalni ochib, quyidagi buyruqlarni bajaring:

```bash
# Repozitoriyni initsializatsiya qilish
git init

# Barcha fayllarni qo'shish (.gitignore tufayli .env qo'shilmaydi)
git add .

# Birinchi commitni amalga oshirish
git commit -m "Initial commit: Instagram downloader bot"

# Asosiy tarmoqni main ga o'zgartirish
git branch -M main

# O'zingizning GitHub repository havolangizni bog'lash:
git remote add origin https://github.com/SIZNING_USERNAME/instagram-downloader-bot.git

# GitHub ga yuklash (push)
git push -u origin main
```

---

## ☁️ 2-QADAM: Botni 24/7 Doimiy Ishlatish (Bepul Cloud Hosting)

Bot kompyuteringiz o'chiq bo'lsa ham 24 soat to'xtovsiz ishlashi uchun uni bepul bulutli serverlarga (cloud hosting) joylashtirish mumkin.

### Variant A: Render.com orqali (Tavsiya etiladi)
1. [Render.com](https://render.com) saytiga GitHub orqali kiring.
2. **New +** tugmasini bosing va **Background Worker** (yoki **Web Service**) ni tanlang.
3. GitHub dagi `instagram-downloader-bot` repozitoriyingizni ulang.
4. Quyidagi parametrlarni tekshiring:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. **Environment Variables** bo'limiga kiring va qo'shing:
   - **Key:** `BOT_TOKEN`
   - **Value:** `8801105760:AAEZ1Bekvm5BuVmNe5JPuyouTZBzAkhBCaY`
6. **Create Background Worker** tugmasini bosing. Bot 24/7 uzluksiz ishga tushadi!

---

### Variant B: Koyeb.com orqali
1. [Koyeb.com](https://www.koyeb.com) ga kiring va GitHub repozitoriyangizni tanlang.
2. Build turi sifatida **Dockerfile** ni tanlang (loyihada `Dockerfile` tayyor holatda mavjud).
3. **Environment variables** qismiga `BOT_TOKEN` ni kiriting.
4. **Deploy** tugmasini bosing.

---

### Variant C: Railway.app orqali
1. [Railway.app](https://railway.app) ga kiring.
2. **New Project** -> **Deploy from GitHub repo** ni tanlang.
3. **Variables** bo'limiga `BOT_TOKEN` ni kiriting.
4. Railway avtomatik tarzda `Procfile` yoki `Dockerfile` ni aniqlab ishga tushiradi.

---

## 💻 Kompyuterda mahalliy ishga tushirish (Local)

Agarda botni o'zingizning kompyuteringizda hoziroq sinab ko'rmoqchi bo'lsangiz:

```powershell
python bot.py
```

Botingiz Telegramda: [@mrsaver12bot](https://t.me/mrsaver12bot)
Unga kirib `/start` bosing va ixtiyoriy Instagram Reels linkini yuborib tekshirib ko'ring!
