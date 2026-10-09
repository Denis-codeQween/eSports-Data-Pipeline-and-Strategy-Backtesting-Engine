import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from collections import Counter

def get_full_fails_report_bo3_only(event_url):
    print("🚀 Starting analysis script: Global failure analysis (BO3 matches only)...")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=154)
    
    try:
        driver.get(event_url)
        print("\n" + "!"*20 + " ATTENTION " + "!"*20)
        input("Please complete Cloudflare verification and press ENTER in the console...")

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
            print("No matches found.")
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
                
                # Extract team names from URL
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

                # --- BO3 ONLY FILTER ---
                # If less than 2 maps played, it's a BO1 or default win/cancellation — skip
                if len(totals) >= 2:
                    total_matches += 1
                    all_played_teams.extend([t1, t2]) # Track teams in BO3 matches only
                    
                    m1 = totals[0]
                    m2 = totals[1]
                    
                    # Under 21.5 Fail (Both maps > 21.5) - Long games
                    if (m1 > 21.5) and (m2 > 21.5):
                        fails_tm_count += 1
                        tm_fail_teams.extend([t1, t2])

                    # Over 21.5 Fail (Both maps <= 21.5) - Short games
                    if (m1 <= 21.5) and (m2 <= 21.5):
                        fails_tb_count += 1
                        tb_fail_teams.extend([t1, t2])
                    
                    print(f"✅ [{i+1}/{len(selected_urls)}] {t1} vs {t2} (BO3)")
                else:
                    print(f"ℹ️ [{i+1}/{len(selected_urls)}] Skipping BO1: {t1} vs {t2}")

            except Exception as e: 
                print(f"⚠️ Error in match {i+1}: {e}")
                continue

        # --- GENERATE STATISTICS ---
        total_team_games = Counter(all_played_teams)
        
        def build_full_df(fail_list):
            f_counts = Counter(fail_list)
            data = []
            for team, count in f_counts.items():
                total = total_team_games[team]
                data.append({
                    "Team": team,
                    "Fails": count,
                    "Tournament Games": total,
                    "Risk %": f"{round((count/total)*100, 1)}%"
                })
            if not data: return pd.DataFrame()
            return pd.DataFrame(data).sort_values("Fails", ascending=False)

        df_tm_all = build_full_df(tm_fail_teams)
        df_tb_all = build_full_df(tb_fail_teams)

        # --- CONSOLE OUTPUT ---
        print("\n" + "="*70)
        print(f"📊 BO3 MATCHES REPORT (Analyzed meetings: {total_matches})")
        print("="*70)
        
        tm_perc = round((fails_tm_count/total_matches)*100, 2) if total_matches > 0 else 0
        tb_perc = round((fails_tb_count/total_matches)*100, 2) if total_matches > 0 else 0
        
        print(f"❌ Under 21.5 Fails (both long): {tm_perc}%")
        print(f"❌ Over 21.5 Fails (both short): {tb_perc}%")
        print("-" * 70)

        print("\n⚠️ TEAMS PRONE TO LONG GAMES (Ruining Under bets):")
        print(df_tm_all.to_string(index=False) if not df_tm_all.empty else "No fails found.")

        print("\n⚠️ TEAMS PRONE TO SHORT GAMES (Ruining Over bets):")
        print(df_tb_all.to_string(index=False) if not df_tb_all.empty else "No fails found.")
        print("="*70)

        # Save to Excel
        with pd.ExcelWriter("BO3_STRATEGY_REPORT.xlsx") as writer:
            df_tm_all.to_excel(writer, sheet_name="Under_Fails_Long", index=False)
            df_tb_all.to_excel(writer, sheet_name="Over_Fails_Short", index=False)
            
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        print("\nDone! Data successfully saved to BO3_STRATEGY_REPORT.xlsx")
        import sys
        sys.exit(0)

if __name__ == "__main__":
    # Specify the target tournament ID URL
    get_full_fails_report_bo3_only("https://www.hltv.org/results?event=8261")