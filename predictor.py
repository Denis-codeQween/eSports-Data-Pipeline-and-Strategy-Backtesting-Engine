import os
import pandas as pd
from generate_predictions_image import draw_prediction_report  # Импортируем наш генератор картинок

def clean_percent(val):
    if pd.isna(val): return 0.0
    return float(str(val).replace('%', '').strip())

def generate_betting_signals(file_path="HLTV_FINAL_REPORT.xlsx"):
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден! Сначала запустите главный парсер/скрипт (main5.py).")
        return

    # --- ЗАПРОС НАЗВАНИЯ ТУРНИРА У ПОЛЬЗОВАТЕЛЯ ---
    print("\n" + "=" * 85)
    user_input = input("🏆 Введите название турнира для картинки (или нажмите Enter для дефолтного): ").strip()
    
    if user_input:
        tournament_label = user_input
    else:
        # Если ничего не ввели, пробуем взять из имени файла или пишем дефолт
        base_name = os.path.basename(file_path)
        if base_name != "HLTV_FINAL_REPORT.xlsx":
            tournament_label = os.path.splitext(base_name)[0].replace("_", " ")
        else:
            tournament_label = "ОСНОВНОЙ ТУРНИР"

    print("\n🧠 ЗАПУСК ПРОКАЧАННОГО АНАЛИТИЧЕСКОГО СОВЕТНИКА V2.0...")
    print("=" * 85)
    xls = pd.ExcelFile(file_path)
    
    # Строка, в которую собираем весь текстовый отчет для картинки
    image_report_text = ""

    # Загружаем общие тренды карт для перекрестного анализа
    tournament_maps = {}
    if "Маппул" in xls.sheet_names:
        df_maps = pd.read_excel(xls, sheet_name="Маппул")
        for _, row in df_maps.iterrows():
            tournament_maps[row["Карта"]] = {
                "tb": clean_percent(row["ТБ%"]),
                "tm": clean_percent(row["ТМ%"]),
                "played": int(row["Сыграно"])
            }

    # 1. АНАЛИЗ КОМАНДНЫХ АНОМАЛИЙ
    block1 = "📋 РЕКОМЕНДАЦИИ ПО КОМАНДАМ (С ПЕРЕКРЕСТНЫМ ФИЛЬТРОМ ТУРНИРА):\n"
    print(block1.strip())
    print("-" * 85)
    image_report_text += block1

    if "Starтистика_Команд" in xls.sheet_names or "Статистика_Команд" in xls.sheet_names:
        sheet_name = "Статистика_Команд" if "Статистика_Команд" in xls.sheet_names else "Starтистика_Команд"
        df_teams = pd.read_excel(xls, sheet_name=sheet_name)
        signals_found = False
        
        for _, row in df_teams.iterrows():
            team = row["Команда"]
            card = row["Карта"]
            games = int(row["Сыграно матчей"])
            tb_p = clean_percent(row["ТБ 21.5 %"])
            tm_p = clean_percent(row["ТМ 21.5 %"])
            avg_t = row["Средний Тотал"]
            
            if games >= 4:
                t_stats = tournament_maps.get(card, {"tb": 50.0, "tm": 50.0, "played": 0})
                
                # --- АНАЛИЗ ДЛЯ ТОТАЛ БОЛЬШЕ ---
                if tb_p >= 75.0:
                    signals_found = True
                    if t_stats["tb"] >= 55.0:
                        status = "💎 УЛЬТРА (Максимальная уверенность!)"
                        note = f"Усиливается трендом турнира (Общий ТБ карты: {t_stats['tb']}%)"
                    elif t_stats["tm"] >= 60.0:
                        status = "⚠️ ВНИМАНИЕ (Конфликт трендов)"
                        note = f"Опасно! Турнир сушит эту карту в ТМ ({t_stats['tm']}%)"
                    else:
                        status = "🔥 ВЫСОКИЙ ШАНС"
                        note = "Обычный командный тренд"
                        
                    if games >= 5: status = "👑 ЖЕЛЕЗНЫЙ ТРЕНД (Большая дистанция!)"

                    line1 = f"{status}: Команда [{team}] -> Карта: {card}\n"
                    line2 = f"   👉 Ставка: Тотал Больше 21.5 раундов\n"
                    line3 = f"   📊 Игры команды: {games} ({tb_p}%) | Ср. Тотал: {avg_t} | {note}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"

                # --- АНАЛИЗ ДЛЯ ТОТАЛ МЕНЬШЕ ---
                elif tm_p >= 75.0:
                    signals_found = True
                    if t_stats["tm"] >= 55.0:
                        status = "💎 УЛЬТРА (Максимальная уверенность!)"
                        note = f"Усиливается трендом турнира (Общий ТМ карты: {t_stats['tm']}%)"
                    elif t_stats["tb"] >= 60.0:
                        status = "⚠️ ВНИМАНИЕ (Конфликт трендов)"
                        note = f"Опасно! Турнир играет эту карту на ТБ ({t_stats['tb']}%)"
                    else:
                        status = "❄️ ВЫСОКИЙ ШАНС"
                        note = "Обычный командный тренд"
                        
                    if games >= 5: status = "👑 ЖЕЛЕЗНЫЙ ТРЕНД (Большая дистанция!)"

                    line1 = f"{status}: Команда [{team}] -> Карта: {card}\n"
                    line2 = f"   👉 Ставка: Тотал Меньше 21.5 раундов\n"
                    line3 = f"   📊 Игры команды: {games} ({tm_p}%) | Ср. Тотал: {avg_t} | {note}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"
                    
        if not signals_found: 
            msg = "ℹ️ Командных аномалий не найдено.\n"
            print(msg)
            image_report_text += msg
    else:
        print("⚠️ Командные данные не найдены в Excel-файле.")

    # 2. АНАЛИЗ ТУРНИРНОГО МАППУЛА
    print("-" * 85)
    block2 = "📋 РЕКОМЕНДАЦИИ ПО ОБЩЕМУ ТРЕНДУ КАРТ (Проходимость >= 60%):\n"
    print(block2.strip())
    print("-" * 85)
    image_report_text += "\n" + block2

    if tournament_maps:
        map_signals = False
        for card, data in tournament_maps.items():
            played = data["played"]
            tb_p = data["tb"]
            tm_p = data["tm"]
            
            # Строгий фильтр от 5 сыгранных матчей на турнире
            if played >= 8:
                if tb_p >= 60.0:
                    line1 = f"📈 ТРЕНД ТУРНИРА (ТБ): Карта [{card}] стабильно пробивает верх.\n"
                    line2 = f"   👉 Рекомендация: Хорошо для догона по картам на ТБ 21.5 (Вероятность: {tb_p}%)\n"
                    line3 = f"   📊 Всего матчей: {played}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"
                    map_signals = True
                elif tm_p >= 60.0:
                    line1 = f"📉 ТРЕНД ТУРНИРА (ТМ): Карта [{card}] идет на низовой тотал.\n"
                    line2 = f"   👉 Рекомендация: Хорошо для догона по картам на ТМ 21.5 (Вероятность: {tm_p}%)\n"
                    line3 = f"   📊 Всего матчей: {played}\n"
                    
                    print(f"{line1}{line2}{line3}")
                    image_report_text += f"{line1}{line2}{line3}\n"
                    map_signals = True
        if not map_signals: 
            msg = "ℹ️ На данный момент нет карт, сыгранных от 6 раз с выраженным трендом.\n"
            print(msg)
            image_report_text += msg

    print("=" * 85)
    print("🎯 Умный анализ завершен. Запуск генерации PNG...")
    
    # Отправляем собранный лог и введенное имя турнира в генератор
    draw_prediction_report(image_report_text, output_filename="PREDICTIONS_REPORT.png", tournament_name=tournament_label)

if __name__ == "__main__":
    generate_betting_signals()