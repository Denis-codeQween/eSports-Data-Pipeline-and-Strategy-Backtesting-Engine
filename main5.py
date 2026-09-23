import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from generate_image import run_generator

def get_detailed_stats(event_url):
    print("🚀 Запуск комплексного анализа... (Сбор данных и вывод отчетов)")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=151)
    
    target_maps = ["Anubis", "Dust2", "Overpass", "Mirage", "Inferno", "Train", "Ancient", "Nuke", "Vertigo"]
    
    try:
        driver.get(event_url)
        print("\n" + "!"*30)
        print("ОЖИДАНИЕ: Пройдите проверку Cloudflare в браузере.")
        input("Когда увидите список матчей, нажмите ENTER здесь...")
        print("!"*30 + "\n")

        # Определение турнира
        try:
            time.sleep(1)
            selectors = [(By.CLASS_NAME, 'eventname'), (By.CLASS_NAME, 'event-hub-title')]
            tournament_name = ""
            for s_type, s_val in selectors:
                try:
                    found = driver.find_element(s_type, s_val).text.strip()
                    if found: tournament_name = found; break
                except: continue
            if not tournament_name:
                tournament_name = driver.title.split('|')[0].replace("Results", "").strip()
        except:
            tournament_name = "CS2 Analysis"

        match_urls = []
        sections = driver.find_elements(By.CLASS_NAME, 'results-sublist') or driver.find_elements(By.CLASS_NAME, 'results-all')
        for section in sections:
            links = section.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and '/matches/' in href and '/stats/' not in href:
                    if href not in match_urls: match_urls.append(href)
        
        if not match_urls:
            print("❌ Ссылки на матчи не найдены.")
            return

        print(f"Найдено матчей: {len(match_urls)}. Анализируем выборку из 65 (Только BO3)...")
        
        strategy_data = [] 
        map_pool_data = [] 
        team_map_data = [] 

        # Ограничиваем выборку до первых 110 матчей
        active_urls = match_urls[:110]
        total_to_process = len(active_urls)

        for i, url in enumerate(active_urls):
            try:
                match_name = url.split('/')[-1]
                print(f"[{i+1}/{total_to_process}] Обработка: {match_name}")
                driver.get(url)
                time.sleep(4)
                
                t1_match_name, t2_match_name = "Team1", "Team2"
                try:
                    t1_match_name = driver.find_elements(By.CLASS_NAME, 'teamName')[0].text.strip()
                    t2_match_name = driver.find_elements(By.CLASS_NAME, 'teamName')[1].text.strip()
                except: pass

                map_holders = driver.find_elements(By.CLASS_NAME, 'mapholder')
                match_scores = []
                temp_map_results = []
                temp_teams_results = []

                for holder in map_holders:
                    if 'defwin' in holder.text.lower(): continue
                    try:
                        m_name = holder.find_element(By.CLASS_NAME, 'mapname').text.strip()
                        scores = holder.find_elements(By.CLASS_NAME, 'results-team-score')
                        map_teams = holder.find_elements(By.CLASS_NAME, 'results-teamname')
                        t1_map = map_teams[0].text.strip() if len(map_teams) >= 1 else t1_match_name
                        t2_map = map_teams[1].text.strip() if len(map_teams) >= 2 else t2_match_name

                        if len(scores) >= 2:
                            s1, s2 = int(scores[0].text.strip()), int(scores[1].text.strip())
                            total = s1 + s2
                            if total > 1:
                                match_scores.append(total)
                                if m_name in target_maps:
                                    temp_map_results.append({"Карта": m_name, "Тотал": total})
                                    is_tb = 1 if total > 21.5 else 0
                                    is_tm = 1 if total < 21.5 else 0
                                    temp_teams_results.append({"Команда": t1_map, "Карта": m_name, "ТБ": is_tb, "ТМ": is_tm, "Тотал": total})
                                    temp_teams_results.append({"Команда": t2_map, "Карта": m_name, "ТБ": is_tb, "ТМ": is_tm, "Тотал": total})
                    except: continue

                if len(match_scores) >= 2:
                    m1, m2 = match_scores[0], match_scores[1]
                    k1_tb, k1_tm = (1 if m1 > 21.5 else 0), (1 if m1 < 21.5 else 0)
                    k2_tb, k2_tm = (1 if m2 > 21.5 else 0), (1 if m2 < 21.5 else 0)
                    
                    strategy_data.append({
                        "К1 ТБ": k1_tb, "К1 ТМ": k1_tm, "К2 ТБ": k2_tb, "К2 ТМ": k2_tm,
                        "ИТОГО ТБ": 1 if (k1_tb or k2_tb) else 0, "ИТОГО ТМ": 1 if (k1_tm or k2_tm) else 0
                    })
                    map_pool_data.extend(temp_map_results)
                    team_map_data.extend(temp_teams_results)
            except: continue

        if strategy_data:
            df_strat = pd.DataFrame(strategy_data)
            n = len(df_strat)
            
            # --- БЛОК 1: ВЫВОД КОМАНДНЫХ АНОМАЛИЙ (КАК НА КАРТИНКЕ 1) ---
            team_stats_excel = []
            print("\n🔥 АНАЛИЗ КОМАНДНЫХ АНОМАЛИЙ (ТБ/ТМ ПО КАРТАМ):")
            print(f"{'Команда':<20} {'Карта':<10} {'Матчей':<8} {'ТБ 21.5 %':<12} {'ТМ 21.5 %':<12} {'Ср.Тотал'}")
            print("-" * 70)

            if team_map_data:
                df_teams = pd.DataFrame(team_map_data)
                grouped = df_teams.groupby(["Команда", "Карта"])
                for (team, card), group in grouped:
                    games_count = len(group)
                    tb_percent = round((group["ТБ"].sum() / games_count) * 100, 1)
                    tm_percent = round((group["ТМ"].sum() / games_count) * 100, 1)
                    avg_total = round(group["Тотал"].mean(), 1)
                    
                    # Фильтр аномалий: в консоль выводим только яркие тренды (>=70%), чтобы не спамить
                    if games_count >= 2 and (tb_percent >= 70.0 or tm_percent >= 70.0):
                        print(f"{team:<20} {card:<10} {games_count:^8} {str(tb_percent)+'%':^12} {str(tm_percent)+'%':^12} {avg_total:^8}")
                    
                    # В Excel при этом сохраняем вообще всё без фильтров для предиктора
                    team_stats_excel.append({
                        "Команда": team, "Карта": card, "Сыграно матчей": games_count,
                        "ТБ 21.5 %": f"{tb_percent}%", "ТМ 21.5 %": f"{tm_percent}%", "Средний Тотал": avg_total
                    })

            # --- БЛОК 2: ФОРМИРОВАНИЕ И ВЫВОД ОТЧЕТА ТУРНИРА (КАК НА КАРТИНКЕ 2) ---
            res_tb1 = f"{round(df_strat['К1 ТБ'].sum()/n*100, 1)}%"
            res_tm1 = f"{round(df_strat['К1 ТМ'].sum()/n*100, 1)}%"
            res_tb2 = f"{round(df_strat['К2 ТБ'].sum()/n*100, 1)}%"
            res_tm2 = f"{round(df_strat['К2 ТМ'].sum()/n*100, 1)}%"
            res_total_tb = f"{round(df_strat['ИТОГО ТБ'].sum()/n*100, 1)}%"
            res_total_tm = f"{round(df_strat['ИТОГО ТМ'].sum()/n*100, 1)}%"

            report_data = "============================================================\n"
            report_data += "АНАЛИЗ ЗАВЕРШЕН!\n"
            report_data += f"{' ':17} Параметр анализа Вероятность %\n"
            report_data += f"{' ':17} Карта 1: ТБ 21.5 {' ':7} {res_tb1}\n"
            report_data += f"{' ':17} Карта 1: ТМ 21.5 {' ':7} {res_tm1}\n"
            report_data += f"{' ':17} Карта 2: ТБ 21.5 {' ':7} {res_tb2}\n"
            report_data += f"{' ':17} Карта 2: ТМ 21.5 {' ':7} {res_tm2}\n"
            report_data += f"ИТОГО: ТБ 21.5 (на 1 или 2 карте) {' ':7} {res_total_tb}\n"
            report_data += f"ИТОГО: ТМ 21.5 (на 1 или 2 карте) {' ':7} {res_total_tm}\n"
            report_data += "\n" + "-"*30 + "\n"
            report_data += f"{'Карта':<10} {'Сыграно':<10} {'ТБ 21.5 %':<12} {'ТМ 21.5 %':<12} {'Ср. Тотал'}\n"

            df_maps = pd.DataFrame(map_pool_data)
            map_stats_excel = []
            for m in target_maps:
                m_df = df_maps[df_maps["Карта"] == m]
                if not m_df.empty:
                    cnt = len(m_df)
                    tb_p = f"{round((m_df['Тотал'] > 21.5).sum()/cnt*100, 1)}%"
                    tm_p = f"{round((m_df['Тотал'] < 21.5).sum()/cnt*100, 1)}%"
                    avg_t = round(m_df["Тотал"].mean(), 1)
                    report_data += f"{m:<10} {cnt:^10} {tb_p:^12} {tm_p:^12} {avg_t:^10}\n"
                    map_stats_excel.append({"Карта": m, "Сыграно": cnt, "ТБ%": tb_p, "ТМ%": tm_p, "AVG": avg_t})

            report_data += "============================================================"
            
            # Печатаем турнирный отчет сразу за командным
            print(report_data)

            # Генерация PNG
            run_generator(tournament_name, report_data)

            # Сохранение Excel базы со всеми вкладками
            with pd.ExcelWriter("HLTV_FINAL_REPORT.xlsx") as writer:
                pd.DataFrame(map_stats_excel).to_excel(writer, sheet_name="Маппул", index=False)
                if team_stats_excel:
                    pd.DataFrame(team_stats_excel).to_excel(writer, sheet_name="Static_Команд", index=False)
                    # Продублируем под старым именем для надежности predictor.py
                    pd.DataFrame(team_stats_excel).to_excel(writer, sheet_name="Статистика_Команд", index=False)
                df_strat.to_excel(writer, sheet_name="Детализация_BO3", index=False)
                
            print("\n🎉 Сбор завершен. Все скрытые данные упакованы в Excel!")

    finally:
        driver.quit()

if __name__ == "__main__":
    get_detailed_stats("https://www.hltv.org/results?event=8261")