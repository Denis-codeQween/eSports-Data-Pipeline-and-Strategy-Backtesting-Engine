import telebot
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# === КОНФИГУРАЦИЯ ===
TOKEN = '8089303391:AAFbSDUaTk7wq8h8G3EVUaTg000jv0_d7zA'
SHEET_NAME = "CS2 STATS"
bot = telebot.TeleBot(TOKEN)

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def add_stats_to_google(tournament, games):
    try:
        sheet = get_sheet()
        all_rows = sheet.get_all_values()
        
        # Получаем последний ID, игнорируя нечисловые значения
        existing_ids = []
        for r in all_rows:
            if r and r[0].isdigit():
                existing_ids.append(int(r[0]))
        current_id = max(existing_ids) if existing_ids else 0
        
        # Разделитель турнира
        sheet.append_row(["", "", f"🏆 {tournament.upper()} 🏆", "", "", "", "", ""])
        
        for date, match, prediction, odds, result in games:
            current_id += 1
            flat = 100
            odds_val = float(odds)
            
            # Логика профита: вин = (кф*100)-100, луз = -300
            if result == "WIN":
                profit = round((odds_val * flat) - flat, 2)
                res_text = "✅ win"
            else:
                profit = -300
                res_text = "❌ lose"
            
            # Колонки: №(A), Дата(B), Турнир(C), Матч(D), Прогноз(E), КФ(F), Результат(G), Профит(H)
            row = [current_id, date, tournament, match, prediction, odds_val, res_text, profit]
            sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Ошибка записи: {e}")
        return False

# КОМАНДА ДЛЯ ПРОВЕРКИ ПРОФИТА ЗА 30 ДНЕЙ
@bot.message_handler(commands=['profit'])
def get_30_days_profit(message):
    try:
        sheet = get_sheet()
        all_data = sheet.get_all_values()
        
        total_30 = 0.0
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        count = 0
        
        for row in all_data[1:]: # Пропускаем шапку
            try:
                # Если в строке нет даты или профита — пропускаем
                if len(row) < 8 or not row[1] or not row[7]: continue
                
                # Парсим дату из колонки B
                row_date = datetime.strptime(row[1], "%d.%m.%Y")
                
                if row_date >= thirty_days_ago:
                    # Чистим профит от возможных пробелов и превращаем в число
                    val = str(row[7]).replace(',', '.').strip()
                    total_30 += float(val)
                    count += 1
            except:
                continue 

        bot.reply_to(message, f"📊 Статистика за 30 дней:\n\n💰 Чистый профит: {round(total_30, 2)} ед.\n✅ Всего ставок: {count}")
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при чтении данных из таблицы.")
        print(f"Ошибка в /profit: {e}")

@bot.message_handler(func=lambda message: "ОТЧЕТ" in message.text.upper())
def handle_report(message):
    lines = [l.strip() for l in message.text.split('\n') if l.strip()]
    tournament = "CS2"
    date_now = datetime.now().strftime("%d.%m.%Y")
    games_list = []

    for i, line in enumerate(lines):
        if "ОТЧЕТ" in line.upper() and ":" in line: continue
        if "🏆" in line:
            tournament = line.replace("🏆", "").strip()
            continue
        
        if "✅" in line or "❌" in line:
            res = "WIN" if "✅" in line else "LOSE"
            m_name = line.replace("✅", "").replace("❌", "").strip()
            
            odds = "1.85"
            prediction = "Тотал"
            
            # Поиск КФ и Прогноза в строках ниже
            for j in range(i + 1, min(i + 3, len(lines))):
                odds_match = re.search(r'(?:КФ|—)\s*(\d+[\.,]\d+)', lines[j])
                if odds_match:
                    odds = odds_match.group(1).replace(',', '.')
                if "🎯" in lines[j] or "Ставка:" in lines[j]:
                    prediction = lines[j].split("Ставка:")[-1].split("—")[0].strip()

            games_list.append([date_now, m_name, prediction, odds, res])

    if games_list:
        if add_stats_to_google(tournament, games_list):
            bot.reply_to(message, f"✅ Добавлено: {len(games_list)} матчей.\nЛуз = -300")
    else:
        bot.reply_to(message, "⚠️ Матчи не найдены.")

print("Бот запущен. Команда /profit активна!")
bot.polling(none_stop=True)