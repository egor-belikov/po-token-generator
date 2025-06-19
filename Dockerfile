FROM node:18-slim AS node-base

# Установка youtube-po-token-generator
RUN npm install -g youtube-po-token-generator

# Установка системных зависимостей для Puppeteer
RUN apt-get update && apt-get install -y \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libnss3 \
    lsb-release \
    xdg-utils \
    wget \
    --no-install-recommends

FROM python:3.10-slim

# Копируем Node.js окружение с youtube-po-token-generator
COPY --from=node-base /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-base /usr/local/bin /usr/local/bin
COPY --from=node-base /usr/lib /usr/lib
COPY --from=node-base /lib /lib

# Установка системных зависимостей для Python и FFmpeg
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    ffmpeg \
    --no-install-recommends

WORKDIR /app

# Копируем Python зависимости
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код
COPY bot.py .

# Настройка окружения
ENV PYTHONUNBUFFERED=1
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

CMD ["python", "bot.py"]