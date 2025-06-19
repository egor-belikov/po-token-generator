# Используем Node.js 20 для генерации токена
FROM node:20-slim AS token-generator

# Установка системных зависимостей для headless Chrome
RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \  # Установка корневых сертификатов
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

# Обновление сертификатов
RUN update-ca-certificates

# Клонирование репозитория с временным отключением проверки SSL
RUN git config --global http.sslVerify false && \
    git clone https://github.com/YunzheZJU/youtube-po-token-generator.git /youtube-po-token-generator && \
    git config --global http.sslVerify true

WORKDIR /youtube-po-token-generator

# Установка зависимостей
RUN npm install && npm install commander

# Запуск скрипта и сохранение токена с проверкой
RUN \
    echo "Запуск генерации PO_TOKEN..." && \
    if node examples/one-shot.js > /po_token.json; then \
        echo "✅ PO_TOKEN успешно сгенерирован!"; \
        echo "Первые 10 символов: $(head -c 20 /po_token.json | grep -o '"poToken":"[^"]*' | cut -d'"' -f4 | head -c 10)..."; \
    else \
        echo "❌ Ошибка генерации PO_TOKEN!" >&2; \
        echo "Возможные причины:"; \
        echo "1. Проблемы с доступом к YouTube"; \
        echo "2. Недостаток ресурсов в контейнере"; \
        echo "3. Изменения в API YouTube"; \
        echo "pytubefix будет генерировать токен автоматически при запуске"; \
        echo '{"error": "token_not_generated"}' > /po_token.json; \
    fi

# Основной образ с Python
FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    curl \
    ca-certificates \  
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

# Обновление сертификатов
RUN update-ca-certificates

# Установка Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Копируем сгенерированный токен из первой стадии
COPY --from=token-generator /po_token.json /app/po_token.json

# Проверка токена в основном образе
RUN \
    echo "Проверка сгенерированного токена..." && \
    if [ -f /app/po_token.json ]; then \
        if grep -q '"poToken"' /app/po_token.json; then \
            echo "✅ Валидный PO_TOKEN обнаружен в /app/po_token.json"; \
            echo "Первые 10 символов: $(grep -o '"poToken":"[^"]*' /app/po_token.json | cut -d'"' -f4 | head -c 10)..."; \
        elif grep -q '"error"' /app/po_token.json; then \
            echo "⚠️ Предупреждение: Токен не был сгенерирован на этапе сборки"; \
            echo "pytubefix будет генерировать токен автоматически при запуске"; \
        else \
            echo "⚠️ Неизвестный формат токена в /app/po_token.json"; \
            echo "Содержимое файла:"; \
            cat /app/po_token.json; \
        fi; \
    else \
        echo "❌ Файл токена не найден!"; \
        echo "pytubefix будет генерировать токен автоматически при запуске"; \
    fi

# Установка youtube-po-token-generator как глобального пакета
RUN npm install -g youtube-po-token-generator

# Рабочая директория
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