import json
import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2.service_account import Credentials
import gspread


# ===================== SCRAPER =====================
def scrape_aston_live():
    base_path = os.path.dirname(os.path.abspath(__file__))
    base_url = "https://www.astonbarclay.net/my-account/live"
    login_url = "https://www.astonbarclay.net/my-account"

    # ✅ Setup Chrome Options
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(login_url)
    print("🌐 Opening Aston Barclay My Account...")

    # ✅ Step 1: Accept Cookies
    try:
        cookie_btn = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_btn.click()
        print("🍪 Cookie consent accepted.")
        time.sleep(2)
    except Exception:
        print("ℹ️ No cookie popup detected.")

    # ✅ Step 2: Login Process
    try:
        login_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        )
        login_btn.click()
        print("🔑 Login form opened...")

        # Wait for username/password fields
        user_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "Username"))
        )
        pass_input = driver.find_element(By.ID, "Password")

        user_input.clear()
        user_input.send_keys("sultanmirza0501@gmail.com")
        pass_input.clear()
        pass_input.send_keys("Muhssan7865")

        # Submit the form
        submit_btn = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
        submit_btn.click()
        print("✅ Credentials submitted, waiting for redirect...")

        # Wait until redirected to account page
        WebDriverWait(driver, 20).until(EC.url_contains("/my-account"))
        print("✅ Logged in successfully!")

    except Exception as e:
        print(f"❌ Login failed: {e}")
        driver.quit()
        return

    # ✅ Step 3: Click “Live” Icon on My Account Page
    try:
        live_icon = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/my-account/live']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", live_icon)
        time.sleep(1)
        live_icon.click()
        print("🎯 'Live' section opened successfully!")

        # Wait for page load
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".azItem.aucItem"))
        )
        print("📦 Live Auctions loaded.")
    except Exception as e:
        print(f"⚠️ Failed to open Live section: {e}")
        driver.quit()
        return

    # ✅ Step 4: Extract auction data
    auctions = []
    auction_elements = driver.find_elements(By.CSS_SELECTOR, ".azItem.aucItem")

    for item in auction_elements:
        try:
            title = item.find_element(By.CSS_SELECTOR, "h2.name").text.strip()
        except:
            title = "N/A"

        try:
            date = item.find_element(By.CSS_SELECTOR, "p.definition").text.strip()
        except:
            date = "N/A"

        try:
            vehicles = item.find_element(By.CSS_SELECTOR, "span.vehicles").text.strip()
        except:
            vehicles = "0"

        try:
            links = item.find_elements(By.CSS_SELECTOR, "ul.linklist li a")
            link_data = {}
            for a in links:
                text = a.text.strip().lower()
                href = a.get_attribute("href")
                link_data[text] = href
        except:
            link_data = {}

        auctions.append({
            "Title": title,
            "Date": date,
            "Vehicles": vehicles,
            "ViewVehicles": link_data.get("view vehicles", ""),
            "PrintCatalogue": link_data.get("print catalogue", ""),
            "OpenLive": link_data.get("open live", "")
        })

    # ✅ Save to JSON inside base_path
    folder = os.path.join(base_path, "Aston_Live_Data")
    os.makedirs(folder, exist_ok=True)
    json_file = os.path.join(folder, "aston_live.json")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(auctions, f, indent=4, ensure_ascii=False)

    print(f"✅ Saved {len(auctions)} auctions to JSON file:")
    print(f"📁 {json_file}")

    driver.quit()
    print("🏁 Done! Browser closed successfully.")
    return json_file


# ===================== FILTER FUNCTION =====================
def filter_aston_json(date_iso, input_file):
    """
    Filters Aston Barclay auctions by a given ISO date (YYYY-MM-DD) and returns the filtered list.
    """
    target_date = date_iso.split("T")[0]  # Example: "2025-11-01"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered = []

    for item in data:
        date_str = item.get("Date", "N/A")
        if date_str == "N/A":
            continue
        try:
            dt = datetime.strptime(date_str.split(",")[0], "%A %d %B %Y")
            formatted = dt.strftime("%Y-%m-%d")
            if formatted == target_date:
                filtered.append(item)
        except:
            continue

    print(f"✅ Filtered {len(filtered)} auctions for {target_date}")
    return filtered


# ===================== GOOGLE SHEETS UPLOAD =====================
def upload_to_google_sheets(data, sheet_id):
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

    for sale in data:
        title = sale.get("Title", "")
        date_raw = sale.get("Date", "")
        lots = sale.get("Vehicles", "")

        try:
            dt = datetime.strptime(date_raw, "%A %d %B %Y, %H:%M")
            sale_date = dt.strftime("%d/%m/%Y")
            sale_time = dt.strftime("%H:%M:%S")
        except Exception:
            sale_date, sale_time = date_raw, ""

        sheet.append_row([
            "", "", "Aston Barclay",
            title,
            sale_date,
            sale_time,
            "",
            lots,
            "", "", "", "", "", ""
        ])

    print(f"✅ Uploaded {len(data)} auctions to Google Sheet!")


# ===================== MAIN EXECUTION =====================
if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) < 2:
        print("❌ Please provide date as argument!")
        sys.exit(1)

    selected_date = sys.argv[1]
    print(f"🗓️ Selected Date: {selected_date}")

    json_file = scrape_aston_live()
    if json_file:
        filtered_data = filter_aston_json(selected_date, json_file)
        sheet_id = "1SigyZCALbmwjFkMv_LKk4q2ku2ej1Z6-J_n5QBX7qEs"
        upload_to_google_sheets(filtered_data, sheet_id)
        print("✅ Task completed successfully!")
