# Используем Node.js 20 для генерации токена
FROM node:20-slim AS token-generator

# Установка только необходимых зависимостей
RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
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
        echo "Первые 10 символов: $(grep -o '"poToken":"[^"]*' /po_token.json | cut -d'"' -f4 | head -c 10)..."; \
    else \
        echo "❌ Ошибка генерации PO_TOKEN!" >&2; \
        echo "pytubefix будет генерировать токен автоматически при запуске"; \
        echo '{"error": "token_not_generated"}' > /po_token.json; \
    fi

# Основной образ с Python
FROM python:3.10-slim

# Установка системных зависимостей (только необходимые)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Обновление сертификатов
RUN update-ca-certificates

# Установка Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Копируем сгенерированный токен из первой стадии
COPY --from=token-generator /po_token.json /app/po_token.json

# Проверка токена
RUN \
    echo "Проверка сгенерированного токена..." && \
    if [ -f /app/po_token.json ]; then \
        if grep -q '"poToken"' /app/po_token.json; then \
            echo "✅ Валидный PO_TOKEN обнаружен в /app/po_token.json"; \
            echo "Первые 10 символов: $(grep -o '"poToken":"[^"]*' /app/po_token.json | cut -d'"' -f4 | head -c 10)..."; \
        else \
            echo "⚠️ Токен не сгенерирован при сборке"; \
            echo "pytubefix будет генерировать токен автоматически при запуске"; \
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