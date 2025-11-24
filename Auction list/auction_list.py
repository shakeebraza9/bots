import json, time, sys, os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from google.oauth2.service_account import Credentials

# ===================== SCRAPER =====================
def scrape(date, path, headless=False):
    base_path = os.path.dirname(os.path.abspath(__file__))

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--hide-scrollbars")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(path)
    driver.maximize_window()
    time.sleep(2)

    # ---------- LOGIN ----------
    try:
        provided_u_name = "haider1805@icloud.com"
        provided_pass = "Muhssan7865"

        user_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        user_name.send_keys(provided_u_name)
        driver.find_element(By.ID, "nextButton").click()
        time.sleep(1)

        password = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        password.send_keys(provided_pass)
        driver.find_element(By.ID, "loginBtn").click()
        print("✅ Logged in successfully!")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        driver.quit()
        return

    # ---------- COOKIES ----------
    try:
        cookie_accept = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, './/button[@id="onetrust-accept-btn-handler"]'))
        )
        cookie_accept.click()
        print("🍪 Cookies accepted.")
    except:
        pass

    # ---------- OPEN API ----------
    api_url = f"https://www.bca.co.uk/sales/api/saleprogramme/BCAOffsite?days={date}"
    print(f"🔗 Opening API URL: {api_url}")
    driver.execute_script(f"window.open('{api_url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(5)

    # ---------- GET JSON ----------
    try:
        page_source = driver.find_element(By.TAG_NAME, "pre").text
        data = json.loads(page_source)
        print("✅ JSON fetched successfully!")
    except Exception as e:
        print(f"❌ Failed to extract JSON: {e}")
        driver.quit()
        return

    driver.quit()

    # ---------- PARSE ----------
    all_sales = []
    for day in data.get("dayProgrammes", []):
        for sale in day.get("sales", []):
            all_sales.append({
                "Sale Name": sale.get("publishedSaleName"),
                "Sale Date": sale.get("saleDate"),
                "Lots Available": sale.get("lotsAvailable")
            })

    json_path = os.path.join(base_path, "BCA_Auctions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_sales, f, ensure_ascii=False, indent=4)

    print(f"✅ {len(all_sales)} sales saved to '{json_path}'.")
    return json_path


# ===================== GOOGLE SHEETS UPLOAD =====================
def upload_to_google_sheets(json_file, sheet_id):
    base_path = os.path.dirname(os.path.abspath(__file__))
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds_path = os.path.join(base_path, "bcacouk-6f0e8afe257b.json")
    if not os.path.exists(creds_path):
        print("❌ Google credentials file not found!")
        return

    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(sheet_id).sheet1
        print("✅ Connected to Google Sheet successfully!")
    except Exception as e:
        print("❌ Failed to open Google Sheet:", e)
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for sale in data:
        sale_name = sale.get("Sale Name", "")
        sale_date_raw = sale.get("Sale Date", "")
        lots = sale.get("Lots Available", "")

        try:
            dt = datetime.fromisoformat(sale_date_raw.replace("Z", "+00:00"))
            sale_date = dt.strftime("%d/%m/%Y")
            sale_time = dt.strftime("%H:%M:%S")
        except Exception:
            sale_date, sale_time = sale_date_raw, ""

        sheet.append_row([
            "", "", "BCA",
            sale_name,
            sale_date,
            sale_time,
            "", lots, "", "", "", "", "", ""
        ])

    print(f"✅ Uploaded {len(data)} records to Google Sheets!")


# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) < 2:
        print("❌ Please provide date as argument!")
        sys.exit(1)

    date_arg = sys.argv[1]
    path = "https://login.bca.co.uk/login?signin=1c9b20ed25a32746f9d5d14b3bb2334a"

    # ✅ Google Sheet Details
    sheet_id = "1SigyZCALbmwjFkMv_LKk4q2ku2ej1Z6-J_n5QBX7qEs"
    sheet_url = "https://docs.google.com/spreadsheets/d/1SigyZCALbmwjFkMv_LKk4q2ku2ej1Z6-J_n5QBX7qEs/edit?gid=1586578187#gid=1586578187"

    # ✅ Run scraper
    json_path = scrape(date_arg, path)
    if json_path:
        upload_to_google_sheets(json_path, sheet_id)
        print("✅ Task completed successfully!")
