import telebot
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION
# ==========================================
TOKEN = 'YOUR_BOT_TOKEN_HERE'
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
        
        # Get the latest ID, ignoring non-numeric values
        existing_ids = []
        for r in all_rows:
            if r and r[0].isdigit():
                existing_ids.append(int(r[0]))
        current_id = max(existing_ids) if existing_ids else 0
        
        # Tournament section separator
        sheet.append_row(["", "", f"🏆 {tournament.upper()} 🏆", "", "", "", "", ""])
        
        for date, match, prediction, odds, result in games:
            current_id += 1
            flat = 100
            odds_val = float(odds)
            
            # Profit logic: win = (odds*100)-100, loss = -300
            if result == "WIN":
                profit = round((odds_val * flat) - flat, 2)
                res_text = "✅ win"
            else:
                profit = -300
                res_text = "❌ lose"
            
            # Columns: No(A), Date(B), Tournament(C), Match(D), Prediction(E), Odds(F), Result(G), Profit(H)
            row = [current_id, date, tournament, match, prediction, odds_val, res_text, profit]
            sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Write error: {e}")
        return False

# COMMAND TO CHECK 30-DAY PROFIT
@bot.message_handler(commands=['profit'])
def get_30_days_profit(message):
    try:
        sheet = get_sheet()
        all_data = sheet.get_all_values()
        
        total_30 = 0.0
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        count = 0
        
        for row in all_data[1:]: # Skip header
            try:
                # Skip if row lacks date or profit data
                if len(row) < 8 or not row[1] or not row[7]: continue
                
                # Parse date from column B
                row_date = datetime.strptime(row[1], "%d.%m.%Y")
                
                if row_date >= thirty_days_ago:
                    # Clean profit from spaces and convert to float
                    val = str(row[7]).replace(',', '.').strip()
                    total_30 += float(val)
                    count += 1
            except:
                continue 

        bot.reply_to(message, f"📊 30-Day Statistics:\n\n💰 Net Profit: {round(total_30, 2)} units\n✅ Total Bets: {count}")
    except Exception as e:
        bot.reply_to(message, "❌ Error reading data from spreadsheet.")
        print(f"Error in /profit: {e}")

@bot.message_handler(func=lambda message: "REPORT" in message.text.upper() or "ОТЧЕТ" in message.text.upper())
def handle_report(message):
    lines = [l.strip() for l in message.text.split('\n') if l.strip()]
    tournament = "CS2"
    date_now = datetime.now().strftime("%d.%m.%Y")
    games_list = []

    for i, line in enumerate(lines):
        if ("REPORT" in line.upper() or "ОТЧЕТ" in line.upper()) and ":" in line: continue
        if "🏆" in line:
            tournament = line.replace("🏆", "").strip()
            continue
        
        if "✅" in line or "❌" in line:
            res = "WIN" if "✅" in line else "LOSE"
            m_name = line.replace("✅", "").replace("❌", "").strip()
            
            odds = "1.85"
            prediction = "Total"
            
            # Search for Odds and Prediction in subsequent lines
            for j in range(i + 1, min(i + 3, len(lines))):
                odds_match = re.search(r'(?:Odds|КФ|—)\s*(\d+[\.,]\d+)', lines[j], re.IGNORECASE)
                if odds_match:
                    odds = odds_match.group(1).replace(',', '.')
                if "🎯" in lines[j] or "Bet:" in lines[j] or "Ставка:" in lines[j]:
                    prediction = lines[j].split(":")[-1].split("—")[0].strip()

            games_list.append([date_now, m_name, prediction, odds, res])

    if games_list:
        if add_stats_to_google(tournament, games_list):
            bot.reply_to(message, f"✅ Added: {len(games_list)} matches.\nLoss = -300")
    else:
        bot.reply_to(message, "⚠️ No matches found.")

print("Bot is running. /profit command is active!")
bot.polling(none_stop=True)