# CS2 Automated Data Analysis & Betting Strategy Toolkit

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Selenium](https://img.shields.io/badge/Selenium-Undetected%20Chromedriver-green)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-orange)
![Telegram](https://img.shields.io/badge/Telegram-BotAPI-blueviolet)

A professional suite of Python scripts designed for automated web scraping, data processing, statistical strategy evaluation, visual report generation, and Telegram/Google Sheets integration. Built to minimize manual effort and handle complex web interactions (including Cloudflare bypass) for sports/Esports analytics.

---

## 🛠️ Project Structure & Modules

1. **`main4.py` — BO3 Global Failure Analysis**
   * Scrapes match results from HLTV events using `undetected-chromedriver`.
   * Filters matches strictly to BO3 format, calculates Under/Over 21.5 round thresholds, and identifies teams prone to long or short games.
   * Exports structured datasets into Excel (`BO3_STRATEGY_REPORT.xlsx`).

2. **`main5.py` — Comprehensive Statistics & MapPool Analysis**
   * Performs deep analysis of map pools and team anomalies across specific maps (Anubis, Mirage, Inferno, etc.).
   * Generates detailed tournament reports and packages data into multi-sheet workbooks (`HLTV_FINAL_REPORT.xlsx`).

3. **`main6.py` — Dual Strategy Chain Analysis (Denis Miller Method)**
   * Analyzes chronological map chains in BO3 matches to evaluate consecutive strategy triggers (e.g., Over-Over ➔ Under transitions or Under-Under ➔ Over transitions).
   * Calculates winrates and outputs structured logs (`DUAL_STRATEGY_REPORT.xlsx`).

4. **`generate_image.py` & `generate_predictions_image.py` — Visual Report Renderers**
   * Converts raw text analytical logs and strategy outputs into polished, dark-themed PNG preview cards (`analysis_result.png`, `PREDICTIONS_REPORT.png`) using `imgkit` and `wkhtmltoimage`.

5. **`telegram_bot.py` — OCR & Prediction Formatter Bot**
   * A Telegram bot that parses screenshot data using `pytesseract` (OCR), extracts success probabilities, formats match predictions, and generates ready-to-publish channel posts.

6. **`google_sheets_bot.py` — Automated Google Sheets Sync Bot**
   * Automatically records match outcomes, calculates profit/loss based on custom flat/odds logic, and tracks 30-day performance metrics via Google Sheets API.
---

## ⚙️ Prerequisites & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **External Dependencies:**
   * **Google Chrome** (compatible version with `undetected-chromedriver`).
     > 💡 **Note on Chrome Driver Compatibility:** In scripts utilizing `undetected-chromedriver` (such as `main4.py`), the browser version is explicitly specified (e.g., `version_main=151`). If you experience driver launch errors, make sure to update this parameter to match your currently installed Google Chrome major version, or remove it to let the library detect it automatically.
   * **wkhtmltopdf / wkhtmltoimage** (required for image generation scripts). Make sure the path in the code matches your installation directory (e.g., `C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe`).
   * **Tesseract-OCR** (required for the Telegram OCR bot). Download and install binaries for Windows/Linux.

---

## 🔒 Security & Configuration

* **API Tokens & Credentials:** 
  * Real Telegram bot tokens and Google Cloud service account keys (`credentials.json`) are **strictly excluded** from this repository for security reasons.
  * To run the Google Sheets bot, create your own project in Google Cloud Console, generate a service account key, and save it as `credentials.json` in the root folder.
  * Always ensure `credentials.json` and `.env` files are listed in your `.gitignore`.

---

## 🚀 Usage Example

Run the main scraping and analysis script:
```bash
python main5.py
```
Run the Telegram prediction bot locally:
```bash
python telegram_bot.py
```