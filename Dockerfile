FROM python:3.11-slim

# Ishchi katalog
WORKDIR /app

# Tizim talablarini o'rnatish (ffmpeg video bilan ishlash uchun kerak bo'ladi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "bot.py"]
