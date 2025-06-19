# Используем мульти-стадийную сборку
FROM node:18-slim AS nodejs
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
COPY package.json .
RUN npm install puppeteer

FROM python:3.10-slim
WORKDIR /app

# Установка системных зависимостей для Puppeteer и FFmpeg
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
    ffmpeg \
    --no-install-recommends

# Копируем Node.js окружение
COPY --from=nodejs /app/node_modules /app/node_modules
COPY --from=nodejs /usr/bin /usr/bin
COPY --from=nodejs /usr/lib /usr/lib

# Копируем Python зависимости и код
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py .

# Настраиваем окружение для Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]