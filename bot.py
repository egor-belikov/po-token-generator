import re
import subprocess
import logging
import os
import asyncio
from pytubefix import YouTube
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Генерация PO-токена с помощью Node.js
def generate_po_token():
    node_script = """
    const puppeteer = require('puppeteer');
    (async () => {
        const browser = await puppeteer.launch({
            headless: "new",
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--single-process'
            ]
        });
        const page = await browser.newPage();
        await page.goto('https://www.youtube.com', { waitUntil: 'networkidle2', timeout: 60000 });
        const poToken = await page.evaluate(() => localStorage.getItem('PO_TOKEN'));
        console.log(poToken);
        await browser.close();
    })();
    """
    
    with open('po_token.js', 'w') as f:
        f.write(node_script)
    
    try:
        result = subprocess.run(
            ['node', 'po_token.js'],
            capture_output=True,
            text=True,
            timeout=120
        )
        po_token = result.stdout.strip()
        if po_token:
            logger.info(f"PO_TOKEN generated: {po_token}")
            return po_token
        else:
            logger.error("PO_TOKEN generation failed")
            return None
    except Exception as e:
        logger.error(f"PO_TOKEN error: {str(e)}")
        return None

# Инициализация PO_TOKEN
PO_TOKEN = generate_po_token()
if PO_TOKEN:
    YouTube._po_token = PO_TOKEN

# Обработчик ссылок YouTube
def normalize_youtube_url(url: str) -> str:
    """Нормализация YouTube ссылок"""
    # Удаление параметров запроса
    cleaned_url = re.sub(r'\?.*$', '', url)
    
    # Преобразование сокращенных ссылок
    if 'youtu.be' in cleaned_url:
        video_id = cleaned_url.split('/')[-1]
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # Обработка мобильных ссылок
    if 'm.youtube.com' in cleaned_url:
        cleaned_url = cleaned_url.replace('m.youtube.com', 'www.youtube.com')
    
    # Обработка Shorts
    if '/shorts/' in cleaned_url:
        video_id = cleaned_url.split('/shorts/')[-1]
        return f"https://www.youtube.com/watch?v={video_id}"
    
    return cleaned_url

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на YouTube видео, и я скачаю его в видео или аудио формате."
    )

# Обработчик входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    normalized_url = normalize_youtube_url(url)
    
    if 'youtube.com/watch' not in normalized_url and 'youtu.be' not in normalized_url:
        await update.message.reply_text("❌ Неверная YouTube ссылка!")
        return
    
    try:
        yt = YouTube(normalized_url, use_po_token=True)
        title = yt.title
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Видео", callback_data=f"video|{normalized_url}"),
                InlineKeyboardButton("🎵 Аудио", callback_data=f"audio|{normalized_url}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Выберите формат для:\n<b>{title}</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"URL processing error: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка обработки видео. Попробуйте другую ссылку.")

# Обработчик выбора формата
async def handle_format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    format_type, url = data.split('|', 1)
    
    try:
        yt = YouTube(url)
        title = yt.title
        
        await query.edit_message_text(f"⏳ Скачиваю {format_type}...")
        
        if format_type == 'video':
            stream = yt.streams.filter(
                progressive=True,
                file_extension='mp4'
            ).get_highest_resolution()
            filename = f"{yt.video_id}.mp4"
        else:
            stream = yt.streams.filter(
                only_audio=True
            ).get_audio_only()
            filename = f"{yt.video_id}.mp3"
        
        filepath = stream.download(filename=filename)
        filesize = os.path.getsize(filepath) / (1024 * 1024)  # Размер в MB
        
        if filesize > 50:
            await query.edit_message_text("⚠️ Файл слишком большой (>50MB)")
            os.remove(filepath)
            return
        
        await query.edit_message_text("📤 Отправляю файл...")
        
        if format_type == 'video':
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=open(filepath, 'rb'),
                caption=f"🎬 {title}",
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=300
            )
        else:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(filepath, 'rb'),
                caption=f"🎵 {title}",
                title=title[:64],
                performer=yt.author[:64],
                read_timeout=300,
                write_timeout=300,
                connect_timeout=300
            )
        
        os.remove(filepath)
        await query.delete_message()
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        await query.edit_message_text("❌ Ошибка скачивания. Попробуйте другую ссылку.")

# Инициализация приложения
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_format_selection, pattern=r"^(video|audio)\|"))
    
    logger.info("Bot started")
    application.run_polling()

if __name__ == '__main__':
    main()