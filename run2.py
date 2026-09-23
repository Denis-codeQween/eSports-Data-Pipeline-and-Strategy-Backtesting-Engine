import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from generate_image import run_generator  # Файл generate_image.py должен быть в той же папке

def get_strategy_analysis(event_url):
    print("🚀 Запуск комплексного анализа стратегий... (Только BO3)")
    options = uc.ChromeOptions()
    # Используем проверенную версию драйвера (main=152)
    driver = uc.Chrome(options=options, version_main=152)
    
    try:
        driver.get(event_url)
        print("\n" + "!"*30)
        print("ОЖИДАНИЕ: Пройдите проверку Cloudflare в браузере.")
        input("Когда увидите список матчей, нажмите ENTER здесь...")
        print("!"*30 + "\n")

        # --- АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ТУРНИРА ---
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

            print(f"✅ Турнир определен: {tournament_name}")
        except:
            tournament_name = "CS2 Strategy Analysis"
            print("⚠️ Не удалось определить название, использую стандартное.")

        # Сбор ссылок на матчи
        match_urls = []
        sections = driver.find_elements(By.CLASS_NAME, 'results-sublist') or driver.find_elements(By.CLASS_NAME, 'results-all')

        for section in sections:
            links = section.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and '/matches/' in href and '/stats/' not in href:
                    if href not in match_urls: match_urls.append(href)
        
        if not match_urls:
            print("❌ ОШИБКА: Ссылки на матчи не найдены.")
            return

        # На HLTV новые матчи идут СВЕРХУ. Разворачиваем список для соблюдения хронологии
        match_urls.reverse()

        print(f"Найдено матчей: {len(match_urls)}. Сбор хронологической цепочки карт (Максимум 110)...")
        
        chronological_chain = [] 

        # Шаг 1: Собираем чистые исходы К1 и К2 для каждого Bo3 матча
        for i, url in enumerate(match_urls[:110]):
            try:
                match_name = url.split('/')[-1]
                print(f"[{i+1}/{min(110, len(match_urls))}] Парсинг карт: {match_name}")
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
                    k1_status = "ТБ" if m1 > 21.5 else "ТМ"
                    k2_status = "ТБ" if m2 > 21.5 else "ТМ"
                    
                    chronological_chain.append({
                        "Матч Ссылка": url,
                        "Матч Имя": match_name,
                        "К1": k1_status,
                        "К2": k2_status,
                        "Пара": f"{k1_status}-{k2_status}"
                    })
                else:
                    print(f"    ℹ️ Пропуск (не BO3 или отмена): {match_name}")
            except: continue

        # Шаг 2: Анализ собранной цепочки по двум стратегиям
        if len(chronological_chain) < 2:
            print("❌ ОШИБКА: Недостаточно матчей BO3 для анализа цепочки.")
            return

        trigger_results = []
        
        # Счётчики для Правила 1 (ТБ-ТБ)
        tbb_trig_cnt = 0
        tbb_succ_cnt = 0
        
        # Счётчики для Правила 2 (ТМ-ТМ)
        tmm_trig_cnt = 0
        tmm_succ_cnt = 0

        # Точная разметка шапки таблицы со скриншота
        report_data = f"АНАЛИЗ СТРАТЕГИИ ДЕНИСА МИЛЛЕРА\n"
        report_data += f"Турнир: {tournament_name}\n"
        report_data += "---------------------------------------------------------\n"
        report_data += f"{'Матч Триггер':<25} | {'Исход':<5} | {'Следующий Матч':<25} | {'Результат':<10}\n"
        report_data += "---------------------------------------------------------\n"

        for idx in range(len(chronological_chain) - 1):
            current_match = chronological_chain[idx]
            next_match = chronological_chain[idx + 1]
            
            # ПРОВЕРКА ПРАВИЛА 1: ТБ-ТБ -> минимум один ТМ
            if current_match["К1"] == "ТБ" and current_match["К2"] == "ТБ":
                tbb_trig_cnt += 1
                is_success = "ТМ" in [next_match["К1"], next_match["К2"]]
                status_text = "ЗАХОД" if is_success else "ПРОМАХ"
                if is_success: tbb_succ_cnt += 1
                
                report_data += f"{current_match['Матч Имя'][:25]:<25} | {current_match['Пара']:<5} | {next_match['Матч Имя'][:25]:<25} | {status_text}\n"
                
                trigger_results.append({
                    "Тип Стратегии": "ТБ-ТБ -> ТМ",
                    "Матч Триггер": current_match["Матч Имя"],
                    "Пара Триггер": current_match["Пара"],
                    "Следующий Матч": next_match["Матч Имя"],
                    "Пара След": next_match["Пара"],
                    "Статус": status_text.capitalize(),
                    "Ссылка на Триггер": current_match["Матч Ссылка"]
                })

            # ПРОВЕРКА ПРАВИЛА 2: ТМ-ТМ -> минимум один ТБ
            elif current_match["К1"] == "ТМ" and current_match["К2"] == "ТМ":
                tmm_trig_cnt += 1
                is_success = "ТБ" in [next_match["К1"], next_match["К2"]]
                status_text = "ЗАХОД" if is_success else "ПРОМАХ"
                if is_success: tmm_succ_cnt += 1
                
                report_data += f"{current_match['Матч Имя'][:25]:<25} | {current_match['Пара']:<5} | {next_match['Матч Имя'][:25]:<25} | {status_text}\n"
                
                trigger_results.append({
                    "Тип Стратегии": "ТМ-ТМ -> ТБ",
                    "Матч Триггер": current_match["Матч Имя"],
                    "Пара Триггер": current_match["Пара"],
                    "Следующий Матч": next_match["Матч Имя"],
                    "Пара След": next_match["Пара"],
                    "Статус": status_text.capitalize(),
                    "Ссылка на Триггер": current_match["Матч Ссылка"]
                })

        # Расчет винрейтов
        winrate_tbb = round((tbb_succ_cnt / tbb_trig_cnt * 100), 1) if tbb_trig_cnt > 0 else 0.0
        winrate_tmm = round((tmm_succ_cnt / tmm_trig_cnt * 100), 1) if tmm_trig_cnt > 0 else 0.0

        # Точный блок итогов со скриншота, адаптированный под два правила
        report_data += "---------------------------------------------------------\n"
        report_data += "  ИТОГИ СТАТИСТИКИ:\n"
        report_data += f"• Всего матчей в цепочке: {len(chronological_chain)}\n"
        report_data += "---------------------------------------------------------\n"
        report_data += "  ПРАВИЛО 1 [ТБ-ТБ -> ТМ]:\n"
        report_data += f"• Триггер [ТБ-ТБ] встретился: {tbb_trig_cnt} раз\n"
        report_data += f"• Успешных исходов (минимум 1 ТМ далее): {tbb_succ_cnt}\n"
        report_data += f"• Проходимость правила (Winrate): {winrate_tbb}%\n"
        report_data += "---------------------------------------------------------\n"
        report_data += "  ПРАВИЛО 2 [ТМ-ТМ -> ТБ]:\n"
        report_data += f"• Триггер [ТМ-ТМ] встретился: {tmm_trig_cnt} раз\n"
        report_data += f"• Успешных исходов (минимум 1 ТБ далее): {tmm_succ_cnt}\n"
        report_data += f"• Проходимость правила (Winrate): {winrate_tmm}%\n"

        # Вывод результатов в консоль
        print("\n" + "="*70)
        print(report_data)
        print(f"Данные сохранены в: DUAL_STRATEGY_REPORT.xlsx")
        print("="*70)

        # ГЕНЕРАЦИЯ КАРТИНКИ (report_data теперь полностью повторяет ваш текстовый формат)
        run_generator(tournament_name, report_data)

        # СОХРАНЕНИЕ В EXCEL
        with pd.ExcelWriter("DUAL_STRATEGY_REPORT.xlsx") as writer:
            pd.DataFrame(chronological_chain).to_excel(writer, sheet_name="Общая_Цепочка_Матчей", index=False)
            if trigger_results:
                pd.DataFrame(trigger_results).to_excel(writer, sheet_name="Отработка_Триггеров", index=False)

    finally:
        driver.quit()

if __name__ == "__main__":
    # Запуск на нужный турнир с HLTV
    get_strategy_analysis("https://www.hltv.org/results?event=8249")