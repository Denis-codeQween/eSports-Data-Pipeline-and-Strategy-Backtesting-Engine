import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from generate_image import run_generator

def get_detailed_stats(event_url):
    print("🚀 Starting comprehensive analysis... (Data collection and report generation)")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=154)
    
    target_maps = ["Anubis", "Dust2", "Overpass", "Mirage", "Inferno", "Train", "Ancient", "Nuke", "Vertigo"]
    
    try:
        driver.get(event_url)
        print("\n" + "!"*30)
        print("WAITING: Please complete the Cloudflare verification in the browser.")
        input("Once you see the match list, press ENTER here...")
        print("!"*30 + "\n")

        # Detect tournament name
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
            print("❌ Match links not found.")
            return

        print(f"Found matches: {len(match_urls)}. Analyzing sample of 110 (BO3 only)...")
        
        strategy_data = [] 
        map_pool_data = [] 
        team_map_data = [] 

        # Limit sample to the first 110 matches
        active_urls = match_urls[:110]
        total_to_process = len(active_urls)

        for i, url in enumerate(active_urls):
            try:
                match_name = url.split('/')[-1]
                print(f"[{i+1}/{total_to_process}] Processing: {match_name}")
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
                                    temp_map_results.append({"Map": m_name, "Total": total})
                                    is_over = 1 if total > 21.5 else 0
                                    is_under = 1 if total < 21.5 else 0
                                    temp_teams_results.append({"Team": t1_map, "Map": m_name, "Over": is_over, "Under": is_under, "Total": total})
                                    temp_teams_results.append({"Team": t2_map, "Map": m_name, "Over": is_over, "Under": is_under, "Total": total})
                    except: continue

                if len(match_scores) >= 2:
                    m1, m2 = match_scores[0], match_scores[1]
                    k1_over, k1_under = (1 if m1 > 21.5 else 0), (1 if m1 < 21.5 else 0)
                    k2_over, k2_under = (1 if m2 > 21.5 else 0), (1 if m2 < 21.5 else 0)
                    
                    strategy_data.append({
                        "Team1 Over": k1_over, "Team1 Under": k1_under, "Team2 Over": k2_over, "Team2 Under": k2_under,
                        "TOTAL Over": 1 if (k1_over or k2_over) else 0, "TOTAL Under": 1 if (k1_under or k2_under) else 0
                    })
                    map_pool_data.extend(temp_map_results)
                    team_map_data.extend(temp_teams_results)
            except: continue

        if strategy_data:
            df_strat = pd.DataFrame(strategy_data)
            n = len(df_strat)
            
            # --- BLOCK 1: TEAM ANOMALIES ANALYSIS ---
            team_stats_excel = []
            print("\n🔥 TEAM ANOMALIES ANALYSIS (OVER/UNDER BY MAPS):")
            print(f"{'Team':<20} {'Map':<10} {'Matches':<8} {'Over 21.5 %':<12} {'Under 21.5 %':<12} {'Avg Total'}")
            print("-" * 70)

            if team_map_data:
                df_teams = pd.DataFrame(team_map_data)
                grouped = df_teams.groupby(["Team", "Map"])
                for (team, card), group in grouped:
                    games_count = len(group)
                    over_percent = round((group["Over"].sum() / games_count) * 100, 1)
                    under_percent = round((group["Under"].sum() / games_count) * 100, 1)
                    avg_total = round(group["Total"].mean(), 1)
                    
                    # Anomaly filter: print only strong trends (>=70%) to console to avoid clutter
                    if games_count >= 2 and (over_percent >= 70.0 or under_percent >= 70.0):
                        print(f"{team:<20} {card:<10} {games_count:^8} {str(over_percent)+'%':^12} {str(under_percent)+'%':^12} {avg_total:^8}")
                    
                    # Save everything to Excel without filters for the predictor
                    team_stats_excel.append({
                        "Team": team, "Map": card, "Matches Played": games_count,
                        "Over 21.5 %": f"{over_percent}%", "Under 21.5 %": f"{under_percent}%", "Average Total": avg_total
                    })

            # --- BLOCK 2: TOURNAMENT REPORT GENERATION ---
            res_over1 = f"{round(df_strat['Team1 Over'].sum()/n*100, 1)}%"
            res_under1 = f"{round(df_strat['Team1 Under'].sum()/n*100, 1)}%"
            res_over2 = f"{round(df_strat['Team2 Over'].sum()/n*100, 1)}%"
            res_under2 = f"{round(df_strat['Team2 Under'].sum()/n*100, 1)}%"
            res_total_over = f"{round(df_strat['TOTAL Over'].sum()/n*100, 1)}%"
            res_total_under = f"{round(df_strat['TOTAL Under'].sum()/n*100, 1)}%"

            report_data = "============================================================\n"
            report_data += "ANALYSIS COMPLETED!\n"
            report_data += f"{' ':17} Analysis Parameter {' ':5} Probability %\n"
            report_data += f"{' ':17} Map 1: Over 21.5 {' ':7} {res_over1}\n"
            report_data += f"{' ':17} Map 1: Under 21.5 {' ':6} {res_under1}\n"
            report_data += f"{' ':17} Map 2: Over 21.5 {' ':7} {res_over2}\n"
            report_data += f"{' ':17} Map 2: Under 21.5 {' ':6} {res_under2}\n"
            report_data += f"TOTAL: Over 21.5 (on Map 1 or 2) {' ':3} {res_total_over}\n"
            report_data += f"TOTAL: Under 21.5 (on Map 1 or 2) {' ':2} {res_total_under}\n"
            report_data += "\n" + "-"*30 + "\n"
            report_data += f"{'Map':<10} {'Played':<10} {'Over 21.5 %':<12} {'Under 21.5 %':<12} {'Avg Total'}\n"

            df_maps = pd.DataFrame(map_pool_data)
            map_stats_excel = []
            for m in target_maps:
                m_df = df_maps[df_maps["Map"] == m]
                if not m_df.empty:
                    cnt = len(m_df)
                    over_p = f"{round((m_df['Total'] > 21.5).sum()/cnt*100, 1)}%"
                    under_p = f"{round((m_df['Total'] < 21.5).sum()/cnt*100, 1)}%"
                    avg_t = round(m_df["Total"].mean(), 1)
                    report_data += f"{m:<10} {cnt:^10} {over_p:^12} {under_p:^12} {avg_t:^10}\n"
                    map_stats_excel.append({"Map": m, "Played": cnt, "Over%": over_p, "Under%": under_p, "AVG": avg_t})

            report_data += "============================================================"
            
            # Print tournament report right after team report
            print(report_data)

            # Generate PNG image
            run_generator(tournament_name, report_data)

            # Save Excel database with all sheets
            with pd.ExcelWriter("HLTV_FINAL_REPORT.xlsx") as writer:
                pd.DataFrame(map_stats_excel).to_excel(writer, sheet_name="MapPool", index=False)
                if team_stats_excel:
                    pd.DataFrame(team_stats_excel).to_excel(writer, sheet_name="Teams_Static", index=False)
                    # Duplicate under old name for predictor.py compatibility
                    pd.DataFrame(team_stats_excel).to_excel(writer, sheet_name="Teams_Statistics", index=False)
                df_strat.to_excel(writer, sheet_name="BO3_Details", index=False)
                
            print("\n🎉 Collection complete. All data packaged into Excel successfully!")

    finally:
        try:
            if 'driver' in locals() and driver:
                # Disable the library's problematic destructor before closing
                driver.__class__.__del__ = lambda self: None
                driver.quit()
        except Exception:
            pass
            
        import sys
        sys.exit(0)

if __name__ == "__main__":
    get_detailed_stats("https://www.hltv.org/results?event=8261")