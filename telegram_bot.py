import telebot
import pytesseract
from PIL import Image
import re
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

user_cache = {}

def format_predictions(text, main_prob):
    """Formats matches and adds progression details (Map 1-2)"""
    lines = text.strip().split('\n')
    
    # Extract league name from the first line
    league_name = "TOURNAMENT" 
    if lines:
        first_line = lines[0]
        clean_league = re.sub(r'[🏆🎲📅🛡📊🔰]', '', first_line)
        clean_league = re.sub(r'(Predictions for|PREDICTIONS FOR|Prediction for|Прогнозы на|ПРОГНОЗЫ НА)', '', clean_league, flags=re.IGNORECASE)
        clean_league = re.sub(r'\d+\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|ЯНВАРЯ|ФЕВРАЛЯ|МАРТА|АПРЕЛЯ|МАЯ|ИЮНЯ|ИЮЛЯ|АВГУСТА|СЕНТЯБРЯ|ОКТЯБРЯ|НОЯБРЯ|ДЕКАБРЯ).*', '', clean_league, flags=re.IGNORECASE)
        
        if clean_league.strip():
            league_name = clean_league.strip()

    raw_blocks = text.split('🎲')
    formatted_body = f"🏆 <b>PREDICTIONS FOR {league_name.upper()}</b>\n"

    for block in raw_blocks[1:]:
        block_lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not block_lines: continue

        match_name = "Match"
        for line in block_lines:
            if "vs" in line.lower():
                match_name = re.sub(r'([a-zA-Z0-9]+)b$', r'\1', line).strip()
                break

        all_floats = re.findall(r'\d+\.\d+', block)
        kf = next((f for f in all_floats if f != "21.5"), "1.85")

        t_type = "Over" if any(x in block for x in ["Больше", "ТБ", "Over"]) else "Under"
        short_type = "OVER" if t_type == "Over" else "UNDER"

        # Format match block
        formatted_body += f"\n🎲 <b>{match_name}</b>\n"
        formatted_body += f"└ 🎯 Bet: Total (21.5) {t_type} — Odds {kf}\n"
        formatted_body += f"(Script: {short_type} probability on Map 1 or 2 — {main_prob})\n"
        formatted_body += "Map 1-2 progression up to the first win\n"

    return formatted_body

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img_path = "temp.png"
    with open(img_path, 'wb') as f: f.write(downloaded_file)
    
    try:
        text_ocr = pytesseract.image_to_string(Image.open(img_path), lang='rus+eng')
        start_m = re.search(r'(ANALYSIS\s+COMPLETED|АНАЛИЗ\s+завершен)', text_ocr, re.IGNORECASE)
        end_m = re.search(r'(Matches\s+played\s+total|Сыграно\s+карт\s+всего)', text_ocr, re.IGNORECASE)
        
        if start_m and end_m:
            area = text_ocr[start_m.end() : end_m.start()]
            probs = re.findall(r'(\d+[.,]\d+)', area)
            main_p = f"{max([float(p.replace(',', '.')) for p in probs])}%" if probs else "100.0%"
        else:
            main_p = "100.0%"
        
        user_cache[message.chat.id] = {'main': main_p}
        bot.reply_to(message, f"✅ Screenshot accepted ({main_p}). Please send the prediction text!")
    except Exception:
        user_cache[message.chat.id] = {'main': "100.0%"}
        bot.reply_to(message, "⚠️ OCR error occurred. Waiting for text.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_cache:
        bot.reply_to(message, "⚠️ Please send the screenshot first!")
        return

    main_p = user_cache[chat_id]['main']
    months = {1:"JANUARY", 2:"FEBRUARY", 3:"MARCH", 4:"APRIL", 5:"MAY", 6:"JUNE", 7:"JULY", 8:"AUGUST", 9:"SEPTEMBER", 10:"OCTOBER", 11:"NOVEMBER", 12:"DECEMBER"}
    now = datetime.now()
    date_str = f"{now.day} {months.get(now.month, 'MARCH')}"

    body = format_predictions(message.text, main_p)

    final_post = (
        f"📅 <b>ANALYTICS & PREDICTIONS | {date_str}</b>\n\n"
        f"🤖 <b>AUTOMATION SCRIPT ANALYSIS RECORDED:</b>\n"
        f"The screenshot shows the processing log for all tournament matches.\n\n"
        f"{body}\n"
        f"🛡 <b>Recommendation: Flat 5-10%</b>\n"
        f"📊 Full script analysis can be viewed on screenshots in separate posts.\n\n"
        f"<b>[ [ 📈 STATISTICS ] | [ ☕️ SUPPORT CHANNEL / PRIVATE CHAT ACCESS ] ]</b>"
    )

    bot.send_message(chat_id, final_post, parse_mode='HTML')
    del user_cache[chat_id]

if __name__ == "__main__":
    bot.polling(none_stop=True)
