import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from collections import Counter

def get_full_fails_report_bo3_only(event_url):
    print("🚀 Запуск main4.py: Глобальный анализ осечек (ТОЛЬКО BO3 матчи)...")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=151)
    
    try:
        driver.get(event_url)
        print("\n" + "!"*20 + " ВНИМАНИЕ " + "!"*20)
        input("Пройдите Cloudflare и нажмите ENTER в консоли...")

        match_urls = []
        sections = driver.find_elements(By.CLASS_NAME, 'results-sublist') or \
                   driver.find_elements(By.CLASS_NAME, 'results-all')

        for section in sections:
            links = section.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and '/matches/' in href and '/stats/' not in href:
                    if href not in match_urls: match_urls.append(href)
        
        if not match_urls: 
            print("Матчи не найдены.")
            return

        total_matches = 0
        fails_tm_count = 0
        fails_tb_count = 0
        tm_fail_teams, tb_fail_teams, all_played_teams = [], [], []

        limit = 110 
        selected_urls = match_urls[:limit]

        for i, url in enumerate(selected_urls):
            try:
                driver.get(url)
                time.sleep(3.5)
                
                # Извлекаем названия команд из URL
                url_part = url.split('/')[-1]
                match_info = url_part.split('-vs-')
                if len(match_info) >= 2:
                    t1 = match_info[0].replace('-', ' ').title()
                    t2 = match_info[1].split('-')[0].title()
                else: continue
                
                map_holders = driver.find_elements(By.CLASS_NAME, 'mapholder')
                totals = []
                for holder in map_holders:
                    if 'defwin' in holder.text.lower(): continue
                    scores = holder.find_elements(By.CLASS_NAME, 'results-team-score')
                    if len(scores) >= 2:
                        s1, s2 = scores[0].text.strip(), scores[1].text.strip()
                        if s1.isdigit() and s2.isdigit():
                            totals.append(int(s1) + int(s2))

                # --- ФИЛЬТР ТОЛЬКО BO3 ---
                # Если сыграно меньше 2-х карт, это BO1 или отмена — пропускаем
                if len(totals) >= 2:
                    total_matches += 1
                    all_played_teams.extend([t1, t2]) # Учитываем команды только в BO3
                    
                    m1 = totals[0]
                    m2 = totals[1]
                    
                    # Осечка ТМ 21.5 (Обе карты > 21.5) - Длинные игры
                    if (m1 > 21.5) and (m2 > 21.5):
                        fails_tm_count += 1
                        tm_fail_teams.extend([t1, t2])

                    # Осечка ТБ 21.5 (Обе карты <= 21.5) - Короткие игры
                    if (m1 <= 21.5) and (m2 <= 21.5):
                        fails_tb_count += 1
                        tb_fail_teams.extend([t1, t2])
                    
                    print(f"✅ [{i+1}/{len(selected_urls)}] {t1} vs {t2} (BO3)")
                else:
                    print(f"ℹ️ [{i+1}/{len(selected_urls)}] Пропуск BO1: {t1} vs {t2}")

            except Exception as e: 
                print(f"⚠️ Ошибка в матче {i+1}: {e}")
                continue

        # --- ГЕНЕРАЦИЯ СТАТИСТИКИ ---
        total_team_games = Counter(all_played_teams)
        
        def build_full_df(fail_list):
            f_counts = Counter(fail_list)
            data = []
            for team, count in f_counts.items():
                total = total_team_games[team]
                data.append({
                    "Команда": team,
                    "Осечек": count,
                    "Игр на турнире": total,
                    "% Риска": f"{round((count/total)*100, 1)}%"
                })
            if not data: return pd.DataFrame()
            return pd.DataFrame(data).sort_values("Осечек", ascending=False)

        df_tm_all = build_full_df(tm_fail_teams)
        df_tb_all = build_full_df(tb_fail_teams)

        # --- ВЫВОД В КОНСОЛЬ ---
        print("\n" + "="*70)
        print(f"📊 ОТЧЕТ ПО BO3 МАТЧАМ (Проанализировано встреч: {total_matches})")
        print("="*70)
        
        tm_perc = round((fails_tm_count/total_matches)*100, 2) if total_matches > 0 else 0
        tb_perc = round((fails_tb_count/total_matches)*100, 2) if total_matches > 0 else 0
        
        print(f"❌ Провалы ТМ 21.5 (обе длинные): {tm_perc}%")
        print(f"❌ Провалы ТБ 21.5 (обе короткие): {tb_perc}%")
        print("-" * 70)

        print("\n⚠️  КОМАНДЫ, СКЛОННЫЕ К ДЛИННЫМ ИГРАМ (Портят ТМ):")
        print(df_tm_all.to_string(index=False) if not df_tm_all.empty else "Осечек не найдено.")

        print("\n⚠️  КОМАНДЫ, СКЛОННЫЕ К КОРОТКИМ ИГРАМ (Портят ТБ):")
        print(df_tb_all.to_string(index=False) if not df_tb_all.empty else "Осечек не найдено.")
        print("="*70)

        # Сохранение в Excel
        with pd.ExcelWriter("BO3_STRATEGY_REPORT.xlsx") as writer:
            df_tm_all.to_excel(writer, sheet_name="Осечки_ТМ_Длинные", index=False)
            df_tb_all.to_excel(writer, sheet_name="Осечки_ТБ_Короткие", index=False)
            
    finally:
        driver.quit()
        print("\nГотово! Данные сохранены в BO3_STRATEGY_REPORT.xlsx")

if __name__ == "__main__":
    # Укажите нужный ID турнира
    get_full_fails_report_bo3_only("https://www.hltv.org/results?event=8261")