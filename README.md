# 📸 Instagram & YouTube Video Downloader Bot (@mrsaver12bot)

Ushbu bot **Instagram** (Reels, post) va **YouTube** (Shorts, video) dan videolarni yuqori sifatda yuklab beruvchi, videoning audio/musiqasini ajratib oluvchi hamda to'liq **Admin Panel** bilan jihozlangan Telegram botdir.

---

## ✨ Asosiy Imkoniyatlar

1. **Instagram Video & Reels** yuklash.
2. **YouTube Video & Shorts** yuklash.
3. **🎵 Musiqasini yuklash tugmasi**: Har bir yuborilgan video ostida musiqani (MP3/Audio) alohida yuklab olish uchun qulay tugma bo'ladi.
4. **📊 Admin Panel (`/admin`)**:
   - Bot statistikasi (Jami a'zolar, bugungi yangi foydalanuvchilar, jami yuklab olishlar).
   - Foydalanuvchilarga ommaviy xabar yuborish (Broadcast / Reklama).
5. **🗄 SQLite Ma'lumotlar Bazasi**: Barcha foydalanuvchilar va statistikalar avtomatik saqlanadi.
6. **☁️ 24/7 Render & UptimeRobot**: Bot uxlab qolmasligi uchun maxsus HTTP server integratsiya qilingan.

---

## 📁 Loyiha Tuzilishi

```
instagram_bot/
├── bot.py             # Asosiy Telegram bot logikasi va web-server
├── admin.py           # Admin panel, statistika va xabar tarqatish
├── database.py        # SQLite ma'lumotlar bazasi (aiosqlite)
├── downloader.py      # Instagram & YouTube yuklovchi vosita (yt-dlp)
├── config.py          # Sozlamalar va muhit o'zgaruvchilari
├── requirements.txt   # Kerakli Python kutubxonalari
├── Dockerfile         # 24/7 serverlar uchun Docker sozlamasi
├── Procfile           # Render / Railway worker sozlamasi
├── render.yaml        # Render.com avtomatik sozlamasi
├── .gitignore         # .env, bazalar va vaqtinchalik fayllar filtri
├── .env               # Bot tokeni va Admin ID
├── .env.example       # Namunaviy .env fayli
└── downloads/         # Vaqtinchalik yuklab olingan fayllar
```

---

## 👑 Admin Panelni Sozlash

1. O'zingizning Telegram ID raqamingizni bilish uchun Telegramda [@userinfobot](https://t.me/userinfobot) ga kiring va `/start` bosing. U sizga `Id: 12345678` ko'rinishida raqam beradi.
2. `.env` faylini oching va `ADMIN_ID` ga o'z ID raqamingizni yozing:
   ```env
   BOT_TOKEN=8801105760:AAEZ1Bekvm5BuVmNe5JPuyouTZBzAkhBCaY
   ADMIN_ID=12345678
   ```
   *(Agar bir nechta admin bo'lsa, vergul bilan yozing: `ADMIN_ID=12345678,87654321`)*
3. Botga kirib `/admin` komandasini yuboring.

---

## 🚀 Ishga Tushirish

### Kompyuterda sinab ko'rish:
```powershell
pip install -r requirements.txt
python bot.py
```

### 24/7 Render.com da ishlatish:
Render Web Service dagi **Environment Variables** ga quyidagilarni kiritasiz:
- `BOT_TOKEN`: `8801105760:AAEZ1Bekvm5BuVmNe5JPuyouTZBzAkhBCaY`
- `ADMIN_ID`: Sizning Telegram ID raqamingiz
- `PORT`: `10000`
