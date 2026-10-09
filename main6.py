import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from generate_image import run_generator  # The generate_image.py file must be in the same directory

def get_strategy_analysis(event_url):
    print("🚀 Starting comprehensive strategy analysis... (BO3 matches only)")
    options = uc.ChromeOptions()
    # Using verified driver version (main=152)
    driver = uc.Chrome(options=options, version_main=152)
    
    try:
        driver.get(event_url)
        print("\n" + "!"*30)
        print("WAITING: Please complete Cloudflare verification in the browser.")
        input("Once you see the match list, press ENTER here...")
        print("!"*30 + "\n")

        # --- AUTOMATIC TOURNAMENT DETECTION ---
        try:
            time.sleep(1)
            selectors = [
                (By.CLASS_NAME, 'eventname'), 
                (By.CLASS_NAME, 'event-hub-title'), 
                (By.CSS_SELECTOR, 'h1.event-title'),
                (By.CLASS_NAME, 'event-title')
            ]
            tournament_name = ""
            for s_type, s_val in selectors:
                try:
                    found = driver.find_element(s_type, s_val).text.strip()
                    if found:
                        tournament_name = found
                        break
                except: continue
            
            if not tournament_name:
                tournament_name = driver.title.split('|')[0].replace("Results", "").strip()
            
            if not tournament_name or "Cloudflare" in tournament_name:
                tournament_name = "CS2 Dual Strategy Analysis"

            print(f"✅ Tournament detected: {tournament_name}")
        except:
            tournament_name = "CS2 Strategy Analysis"
            print("⚠️ Failed to detect tournament name, using default.")

        # Collect match links
        match_urls = []
        sections = driver.find_elements(By.CLASS_NAME, 'results-sublist') or driver.find_elements(By.CLASS_NAME, 'results-all')

        for section in sections:
            links = section.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and '/matches/' in href and '/stats/' not in href:
                    if href not in match_urls: match_urls.append(href)
        
        if not match_urls:
            print("❌ ERROR: Match links not found.")
            return

        # On HLTV, new matches are at the TOP. Reverse the list for chronological order
        match_urls.reverse()

        print(f"Found matches: {len(match_urls)}. Collecting chronological map chain (Maximum 110)...")
        
        chronological_chain = [] 

        # Step 1: Collect clean outcomes (Over/Under) for Team 1 and Team 2 of each Bo3 match
        for i, url in enumerate(match_urls[:110]):
            try:
                match_name = url.split('/')[-1]
                print(f"[{i+1}/{min(110, len(match_urls))}] Parsing maps: {match_name}")
                driver.get(url)
                time.sleep(4)
                
                map_holders = driver.find_elements(By.CLASS_NAME, 'mapholder')
                match_scores = []

                for holder in map_holders:
                    if 'defwin' in holder.text.lower(): continue
                    try:
                        scores = holder.find_elements(By.CLASS_NAME, 'results-team-score')
                        if len(scores) >= 2:
                            s1, s2 = int(scores[0].text.strip()), int(scores[1].text.strip())
                            total = s1 + s2
                            if total > 1:
                                match_scores.append(total)
                    except: continue

                if len(match_scores) >= 2:
                    m1, m2 = match_scores[0], match_scores[1]
                    k1_status = "OVER" if m1 > 21.5 else "UNDER"
                    k2_status = "OVER" if m2 > 21.5 else "UNDER"
                    
                    chronological_chain.append({
                        "Match URL": url,
                        "Match Name": match_name,
                        "Team 1": k1_status,
                        "Team 2": k2_status,
                        "Pair": f"{k1_status}-{k2_status}"
                    })
                else:
                    print(f"    ℹ️ Skipping (not BO3 or cancelled): {match_name}")
            except: continue

        # Step 2: Analyze collected chain using two strategies
        if len(chronological_chain) < 2:
            print("❌ ERROR: Not enough BO3 matches for chain analysis.")
            return

        trigger_results = []
        
        # Counters for Rule 1 (OVER-OVER -> UNDER)
        tbb_trig_cnt = 0
        tbb_succ_cnt = 0
        
        # Counters for Rule 2 (UNDER-UNDER -> OVER)
        tmm_trig_cnt = 0
        tmm_succ_cnt = 0

        # Report header matching template structure
        report_data = f"DENIS MILLER STRATEGY ANALYSIS\n"
        report_data += f"Tournament: {tournament_name}\n"
        report_data += "---------------------------------------------------------\n"
        report_data += f"{'Trigger Match':<25} | {'Outcome':<7} | {'Next Match':<25} | {'Result':<10}\n"
        report_data += "---------------------------------------------------------\n"

        for idx in range(len(chronological_chain) - 1):
            current_match = chronological_chain[idx]
            next_match = chronological_chain[idx + 1]
            
            # CHECK RULE 1: OVER-OVER -> at least one UNDER follows
            if current_match["Team 1"] == "OVER" and current_match["Team 2"] == "OVER":
                tbb_trig_cnt += 1
                is_success = "UNDER" in [next_match["Team 1"], next_match["Team 2"]]
                status_text = "WIN" if is_success else "LOSS"
                if is_success: tbb_succ_cnt += 1
                
                report_data += f"{current_match['Match Name'][:25]:<25} | {current_match['Pair']:<7} | {next_match['Match Name'][:25]:<25} | {status_text}\n"
                
                trigger_results.append({
                    "Strategy Type": "OVER-OVER -> UNDER",
                    "Trigger Match": current_match["Match Name"],
                    "Trigger Pair": current_match["Pair"],
                    "Next Match": next_match["Match Name"],
                    "Next Pair": next_match["Pair"],
                    "Status": status_text,
                    "Trigger URL": current_match["Match URL"]
                })

            # CHECK RULE 2: UNDER-UNDER -> at least one OVER follows
            elif current_match["Team 1"] == "UNDER" and current_match["Team 2"] == "UNDER":
                tmm_trig_cnt += 1
                is_success = "OVER" in [next_match["Team 1"], next_match["Team 2"]]
                status_text = "WIN" if is_success else "LOSS"
                if is_success: tmm_succ_cnt += 1
                
                report_data += f"{current_match['Match Name'][:25]:<25} | {current_match['Pair']:<7} | {next_match['Match Name'][:25]:<25} | {status_text}\n"
                
                trigger_results.append({
                    "Strategy Type": "UNDER-UNDER -> OVER",
                    "Trigger Match": current_match["Match Name"],
                    "Trigger Pair": current_match["Pair"],
                    "Next Match": next_match["Match Name"],
                    "Next Pair": next_match["Pair"],
                    "Status": status_text,
                    "Trigger URL": current_match["Match URL"]
                })

        # Calculate winrates
        winrate_tbb = round((tbb_succ_cnt / tbb_trig_cnt * 100), 1) if tbb_trig_cnt > 0 else 0.0
        winrate_tmm = round((tmm_succ_cnt / tmm_trig_cnt * 100), 1) if tmm_trig_cnt > 0 else 0.0

        # Summary statistics block
        report_data += "---------------------------------------------------------\n"
        report_data += "  STATISTICS SUMMARY:\n"
        report_data += f"• Total matches in chain: {len(chronological_chain)}\n"
        report_data += "---------------------------------------------------------\n"
        report_data += "  RULE 1 [OVER-OVER -> UNDER]:\n"
        report_data += f"• Trigger [OVER-OVER] occurred: {tbb_trig_cnt} times\n"
        report_data += f"• Successful outcomes (at least 1 UNDER next): {tbb_succ_cnt}\n"
        report_data += f"• Rule Winrate: {winrate_tbb}%\n"
        report_data += "---------------------------------------------------------\n"
        report_data += "  RULE 2 [UNDER-UNDER -> OVER]:\n"
        report_data += f"• Trigger [UNDER-UNDER] occurred: {tmm_trig_cnt} times\n"
        report_data += f"• Successful outcomes (at least 1 OVER next): {tmm_succ_cnt}\n"
        report_data += f"• Rule Winrate: {winrate_tmm}%\n"

        # Console output
        print("\n" + "="*70)
        print(report_data)
        print(f"Data successfully saved to: DUAL_STRATEGY_REPORT.xlsx")
        print("="*70)

        # Image generation
        run_generator(tournament_name, report_data)

        # Save to Excel
        with pd.ExcelWriter("DUAL_STRATEGY_REPORT.xlsx") as writer:
            pd.DataFrame(chronological_chain).to_excel(writer, sheet_name="Full_Match_Chain", index=False)
            if trigger_results:
                pd.DataFrame(trigger_results).to_excel(writer, sheet_name="Trigger_Performance", index=False)

    finally:
        driver.quit()

if __name__ == "__main__":
    # Run analysis for target HLTV tournament
    get_strategy_analysis("https://www.hltv.org/results?event=8249")
