import imgkit
import os
from datetime import datetime

# Настройка пути к движку
PATH_TO_WK = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe'
config = imgkit.config(wkhtmltoimage=PATH_TO_WK)

def run_generator(tournament_name, analysis_text):
    """
    Эта функция вызывается из main.py.
    Принимает название турнира и готовый блок текста.
    """
    output_filename = 'analysis_result.png'
    
    # Подготовка текста для HTML
    formatted_text = analysis_text.replace('\n', '<br>').replace(' ', '&nbsp;')

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{ background-color: #0d1117; color: #c9d1d9; font-family: 'Consolas', monospace; padding: 30px; width: 1000px; }}
        .main-card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 40px; }}
        .header {{ border-bottom: 2px solid #2ea043; padding-bottom: 15px; margin-bottom: 30px; }}
        .title {{ font-size: 26px; font-weight: bold; color: #ffffff; text-transform: uppercase; }}
        .tournament {{ font-size: 18px; color: #56d364; font-weight: bold; }}
        .raw-text {{ font-size: 15px; line-height: 1.6; white-space: pre; color: #c9d1d9; }}
        .cta-text {{ margin-top: 30px; padding: 15px; background: rgba(46,160,67,0.1); border-left: 4px solid #2ea043; color: #fff; text-align: center; font-weight: bold; }}
        .footer {{ margin-top: 25px; font-size: 11px; color: #484f58; text-align: right; border-top: 1px solid #30363d; padding-top: 10px; }}
    </style>
    </head>
    <body>
        <div class="main-card">
            <div class="header">
                <div class="title">CS2 АНАЛИЗ СКРИПТОВ</div>
                <div class="tournament">на {tournament_name}</div>
            </div>
            <div class="raw-text">{formatted_text}</div>
            <div class="cta-text">Полный анализ скриптов доступен в комментариях к посту.</div>
            <div class="footer">GENERATED: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</div>
        </div>
    </body>
    </html>
    """
    
    options = {'format': 'png', 'encoding': "UTF-8", 'quiet': ''}
    
    try:
        imgkit.from_string(html_template, output_filename, options=options, config=config)
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False