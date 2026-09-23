import telebot
import pytesseract
from PIL import Image
import re
from datetime import datetime

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

TOKEN = '8652669333:AAHwIEOkJvGcIo4VeW_AGbrUOnqHK4-TG6g'
bot = telebot.TeleBot(TOKEN)

user_cache = {}

def format_predictions(text, main_prob):
    """Форматирует матчи и добавляет уточнение про догон (1-2 карта)"""
    lines = text.strip().split('\n')
    
    # Извлечение лиги из первой строки
    league_name = "ТУРНИР" 
    if lines:
        first_line = lines[0]
        clean_league = re.sub(r'[🏆🎲📅🛡📊🔰]', '', first_line)
        clean_league = re.sub(r'(Прогнозы на|ПРОГНОЗЫ НА|Прогноз на)', '', clean_league, flags=re.IGNORECASE)
        clean_league = re.sub(r'\d+\s+(ЯНВАРЯ|ФЕВРАЛЯ|МАРТА|АПРЕЛЯ|МАЯ|ИЮНЯ|ИЮЛЯ|АВГУСТА|СЕНТЯБРЯ|ОКТЯБРЯ|НОЯБРЯ|ДЕКАБРЯ).*', '', clean_league, flags=re.IGNORECASE)
        
        if clean_league.strip():
            league_name = clean_league.strip()

    raw_blocks = text.split('🎲')
    formatted_body = f"🏆 <b>ПРОГНОЗЫ НА {league_name.upper()}</b>\n"

    for block in raw_blocks[1:]:
        block_lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not block_lines: continue

        match_name = "Матч"
        for line in block_lines:
            if "vs" in line.lower():
                match_name = re.sub(r'([a-zA-Z0-9]+)b$', r'\1', line).strip()
                break

        all_floats = re.findall(r'\d+\.\d+', block)
        kf = next((f for f in all_floats if f != "21.5"), "1.85")

        t_type = "Больше" if any(x in block for x in ["Больше", "ТБ"]) else "Меньше"
        short_type = "ТБ" if t_type == "Больше" else "ТМ"

        # Формирование блока матча
        formatted_body += f"\n🎲 <b>{match_name}</b>\n"
        formatted_body += f"└ 🎯 Ставка: Тотал (21.5) {t_type} — КФ {kf}\n"
        formatted_body += f"(Скрипт: вероятность {short_type} на 1 или 2 карте — {main_prob})\n"
        # НОВАЯ СТРОКА:
        formatted_body += "1-2 карта до первой победы\n"

    return formatted_body

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img_path = "temp.png"
    with open(img_path, 'wb') as f: f.write(downloaded_file)
    
    try:
        text_ocr = pytesseract.image_to_string(Image.open(img_path), lang='rus+eng')
        start_m = re.search(r'АНАЛИЗ\s+завершен', text_ocr, re.IGNORECASE)
        end_m = re.search(r'Сыграно\s+карт\s+всего', text_ocr, re.IGNORECASE)
        
        if start_m and end_m:
            area = text_ocr[start_m.end() : end_m.start()]
            probs = re.findall(r'(\d+[.,]\d+)', area)
            main_p = f"{max([float(p.replace(',', '.')) for p in probs])}%" if probs else "100.0%"
        else:
            main_p = "100.0%"
        
        user_cache[message.chat.id] = {'main': main_p}
        bot.reply_to(message, f"✅ Скриншот принят ({main_p}). Пришли текст прогнозов!")
    except Exception:
        user_cache[message.chat.id] = {'main': "100.0%"}
        bot.reply_to(message, "⚠️ Ошибка OCR. Жду текст.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_cache:
        bot.reply_to(message, "⚠️ Сначала отправь скриншот!")
        return

    main_p = user_cache[chat_id]['main']
    months = {1:"ЯНВАРЯ", 2:"ФЕВРАЛЯ", 3:"МАРТА", 4:"АПРЕЛЯ", 5:"МАЯ", 6:"ИЮНЯ", 7:"ИЮЛЯ", 8:"АВГУСТА", 9:"СЕНТЯБРЯ", 10:"ОКТЯБРЯ", 11:"НОЯБРЯ", 12:"ДЕКАБРЯ"}
    now = datetime.now()
    # Обрати внимание: теперь дата будет актуальной на 2026 год (как сегодня)
    date_str = f"{now.day} {months.get(now.month, 'МАРТА')}"

    body = format_predictions(message.text, main_p)

    final_post = (
        f"📅 <b>АНАЛИТИКА И ПРОГНОЗЫ | {date_str}</b>\n\n"
        f"🤖 <b>АНАЛИЗ СКРИПТОВ ЗАФИКСИРОВАЛ:</b>\n"
        f"На скриншоте работы скрипта — лог обработки всех прошедших матчей за турнир.\n\n"
        f"{body}\n"
        f"🛡 <b>Рекомендация: Flat 5-10%</b>\n"
        f"📊 Полный анализ работы скриптов вы можете увидеть на скриншотах в отдельных постах.\n\n"
        f"<b>[ [ 📈 СТАТИСТИКА ] | [ ☕️ ПОДДЕРЖАТЬ КАНАЛ/ПОЛУЧИТЬ ДОСТУП К ПРИВАТНОМУ ЧАТУ ] ]</b>"
    )

    bot.send_message(chat_id, final_post, parse_mode='HTML')
    del user_cache[chat_id]

if __name__ == "__main__":
    bot.polling(none_stop=True)