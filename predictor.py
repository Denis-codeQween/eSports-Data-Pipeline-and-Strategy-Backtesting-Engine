import os
import pandas as pd
from generate_predictions_image import draw_prediction_report  # Import our image generator

def clean_percent(val):
    if pd.isna(val): return 0.0
    return float(str(val).replace('%', '').strip())

def generate_betting_signals(file_path="HLTV_FINAL_REPORT.xlsx"):
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} not found! Please run the main parser script first.")
        return

    # --- TOURNAMENT NAME PROMPT ---
    print("\n" + "=" * 85)
    user_input = input("🏆 Enter tournament name for the image report (or press Enter for default): ").strip()
    
    if user_input:
        tournament_label = user_input
    else:
        # If nothing entered, try to extract from filename or use default
        base_name = os.path.basename(file_path)
        if base_name != "HLTV_FINAL_REPORT.xlsx":
            tournament_label = os.path.splitext(base_name)[0].replace("_", " ")
        else:
            tournament_label = "MAIN TOURNAMENT"

    print("\n🧠 STARTING ADVANCED ANALYTICAL ADVISOR V2.0...")
    print("=" * 85)
    xls = pd.ExcelFile(file_path)
    
    # String accumulator for the image report text
    image_report_text = ""

    # Load general map trends for cross-analysis
    tournament_maps = {}
    if "MapPool" in xls.sheet_names:
        df_maps = pd.read_excel(xls, sheet_name="MapPool")
        for _, row in df_maps.iterrows():
            tournament_maps[row["Map"]] = {
                "tb": clean_percent(row["Over%"]),
                "tm": clean_percent(row["Under%"]),
                "played": int(row["Played"])
            }

    # 1. TEAM ANOMALIES ANALYSIS
    block1 = "📋 TEAM RECOMMENDATIONS (WITH CROSS-TOURNAMENT FILTER):\n"
    print(block1.strip())
    print("-" * 85)
    image_report_text += block1

    target_sheet = None
    for s_name in ["Teams_Static", "Teams_Statistics", "Starтистика_Команд", "Статистика_Команд"]:
        if s_name in xls.sheet_names:
            target_sheet = s_name
            break

    if target_sheet:
        df_teams = pd.read_excel(xls, sheet_name=target_sheet)
        signals_found = False
        
        for _, row in df_teams.iterrows():
            team = row.get("Team", row.get("Команда", "Unknown"))
            card = row.get("Map", row.get("Карта", "Unknown"))
            games = int(row.get("Matches Played", row.get("Сыграно матчей", 0)))
            tb_p = clean_percent(row.get("Over 21.5 %", row.get("ТБ 21.5 %", 0)))
            tm_p = clean_percent(row.get("Under 21.5 %", row.get("ТМ 21.5 %", 0)))
            avg_t = row.get("Average Total", row.get("Средний Тотал", 0))
            
            if games >= 4:
                t_stats = tournament_maps.get(card, {"tb": 50.0, "tm": 50.0, "played": 0})
                
                # --- OVER ANALYSIS ---
                if tb_p >= 75.0:
                    signals_found = True
                    if t_stats["tb"] >= 55.0:
                        status = "💎 ULTRA (Maximum Confidence!)"
                        note = f"Reinforced by tournament trend (Map Over: {t_stats['tb']}%)"
                    elif t_stats["tm"] >= 60.0:
                        status = "⚠️ WARNING (Trend Conflict)"
                        note = f"Danger! Tournament suppresses this map into Under ({t_stats['tm']}%)"
                    else:
                        status = "🔥 HIGH CHANCE"
                        note = "Standard team trend"
                        
                    if games >= 5: status = "👑 IRON TREND (Large sample distance!)"

                    line1 = f"{status}: Team [{team}] -> Map: {card}\n"
                    line2 = f"    👉 Bet: Total Over 21.5 Rounds\n"
                    line3 = f"    📊 Team Matches: {games} ({tb_p}%) | Avg Total: {avg_t} | {note}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"

                # --- UNDER ANALYSIS ---
                elif tm_p >= 75.0:
                    signals_found = True
                    if t_stats["tm"] >= 55.0:
                        status = "💎 ULTRA (Maximum Confidence!)"
                        note = f"Reinforced by tournament trend (Map Under: {t_stats['tm']}%)"
                    elif t_stats["tb"] >= 60.0:
                        status = "⚠️ WARNING (Trend Conflict)"
                        note = f"Danger! Tournament plays this map over ({t_stats['tb']}%)"
                    else:
                        status = "❄️ HIGH CHANCE"
                        note = "Standard team trend"
                        
                    if games >= 5: status = "👑 IRON TREND (Large sample distance!)"

                    line1 = f"{status}: Team [{team}] -> Map: {card}\n"
                    line2 = f"    👉 Bet: Total Under 21.5 Rounds\n"
                    line3 = f"    📊 Team Matches: {games} ({tm_p}%) | Avg Total: {avg_t} | {note}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"
                    
        if not signals_found: 
            msg = "ℹ️ No team anomalies found.\n"
            print(msg)
            image_report_text += msg
    else:
        print("⚠️ Team data not found in Excel file.")

    # 2. TOURNAMENT MAPPOOL ANALYSIS
    print("-" * 85)
    block2 = "📋 GENERAL MAP TREND RECOMMENDATIONS (Winrate >= 60%):\n"
    print(block2.strip())
    print("-" * 85)
    image_report_text += "\n" + block2

    if tournament_maps:
        map_signals = False
        for card, data in tournament_maps.items():
            played = data["played"]
            tb_p = data["tb"]
            tm_p = data["tm"]
            
            # Strict filter starting from 8 played matches in the tournament
            if played >= 8:
                if tb_p >= 60.0:
                    line1 = f"📈 TOURNAMENT TREND (OVER): Map [{card}] consistently hits high totals.\n"
                    line2 = f"    👉 Recommendation: Good for map progression betting on Over 21.5 (Probability: {tb_p}%)\n"
                    line3 = f"    📊 Total Matches: {played}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"
                    map_signals = True
                elif tm_p >= 60.0:
                    line1 = f"📉 TOURNAMENT TREND (UNDER): Map [{card}] trends towards low totals.\n"
                    line2 = f"    👉 Recommendation: Good for map progression betting on Under 21.5 (Probability: {tm_p}%)\n"
                    line3 = f"    📊 Total Matches: {played}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"
                    map_signals = True
        if not map_signals: 
            msg = "ℹ️ Currently no maps played 8+ times with a pronounced trend.\n"
            print(msg)
            image_report_text += msg

    print("=" * 85)
    print("🎯 Smart analysis completed. Launching PNG generation...")
    
    # Send assembled log and tournament label to generator
    draw_prediction_report(image_report_text, output_filename="PREDICTIONS_REPORT.png", tournament_name=tournament_label)

if __name__ == "__main__":
    generate_betting_signals()