import re
import os
import logging
import tempfile
from pytubefix import YouTube
from youtube_po_token_generator import generate_po_token
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

# Инициализация PO_TOKEN
try:
    PO_TOKEN = generate_po_token()
    logger.info(f"Successfully generated PO_TOKEN: {PO_TOKEN[:10]}...")
    YouTube._po_token = PO_TOKEN
except Exception as e:
    logger.error(f"PO_TOKEN generation failed: {str(e)}")
    PO_TOKEN = None

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
        yt = YouTube(normalized_url)
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
        
        # Создаем временную директорию
        with tempfile.TemporaryDirectory() as tmp_dir:
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
            
            filepath = os.path.join(tmp_dir, filename)
            stream.download(output_path=tmp_dir, filename=filename)
            filesize = os.path.getsize(filepath) / (1024 * 1024)  # Размер в MB
            
            if filesize > 50:
                await query.edit_message_text("⚠️ Файл слишком большой (>50MB)")
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
        
        await query.delete_message()
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        await query.edit_message_text("❌ Ошибка скачивания. Попробуйте другую ссылку.")

# Инициализация приложения
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_format_selection, pattern=r"^(video|audio)\|"))
    
    logger.info("Бот запущен")
    application.run_polling()

if __name__ == '__main__':
    main()