FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    ffmpeg \
    nodejs \
    npm \
    # Зависимости для headless Chrome
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxtst6 \
    --no-install-recommends

# Установка youtube-po-token-generator через npm
RUN npm install -g youtube-po-token-generator

# Клонирование репозитория для доступа к примерам
RUN git clone https://github.com/YunzheZJU/youtube-po-token-generator.git /youtube-po-token-generator
WORKDIR /youtube-po-token-generator
RUN npm install
RUN node /content/youtube-po-token-generator/examples/one-shot.js

# Возвращаемся в рабочую директорию
WORKDIR /app

# Копируем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код
COPY bot.py .

# Настройка окружения
ENV PYTHONUNBUFFERED=1
ENV NODE_PATH=/usr/local/lib/node_modules

CMD ["python", "bot.py"]