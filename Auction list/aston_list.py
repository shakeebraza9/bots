import json
import sys
import os
import time
import re,urllib3,requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
API_ENDPOINT_PLATEFROM = f"{API_BASE_URL}/api/cruds/platform"
AUCTION_UPLOAD_URL = f"{API_BASE_URL}/api/cruds/taskManagement"


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



def filter_aston_json_only_date(date_iso, input_file):
    target_date = date_iso.split("T")[0] 

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered = []
    for item in data:
        date_str = item.get("Date", "")


        if not date_str or date_str == "N/A":
            continue

        try:
    
            dt = datetime.strptime(date_str.split(",")[0], "%A %d %B %Y")
            formatted = dt.strftime("%Y-%m-%d")

            if formatted == target_date:
                filtered.append(item)
        except:
            continue  

    print(f"✅ Filtered {len(filtered)} auctions for {target_date}")


    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=4, ensure_ascii=False)

    return filtered


def login_and_get_token():
    url = f"{API_BASE_URL}/api/auth/login"
    payload = {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    }

    try:
        r = requests.post(url, json=payload, verify=False, timeout=30)
        r.raise_for_status()
        token = r.json().get("data").get("token")

        if not token:
            raise Exception("Token missing in response")

        print("✅ Login successful")
        return token

    except Exception as e:
        print("❌ Login failed:", e)
        exit()

def get_id(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        r = requests.get(API_ENDPOINT_PLATEFROM, headers=headers, verify=False, timeout=30)
        r.raise_for_status()
        platforms = r.json().get("data", [])
        
        for platform in platforms:
            if platform.get("name") == "Aston Barclay":
                return platform.get("id")
        
        return None  
    except requests.RequestException as e:
        print("Error fetching platforms:", e)
        return None

def upload_auctiondata_one_by_one(token ,payload):
 

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(
            AUCTION_UPLOAD_URL,
            json=payload,
            headers=headers,
            verify=False,
            timeout=60
        )

        print("Status:", r.status_code)

        try:
            print("Response:", r.json())
        except Exception:
            print("Response text:", r.text)

    except Exception as e:
        print("❌ Failed:", e)

    time.sleep(1)  
    
    
        
if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    if len(sys.argv) < 2:
        print("❌ Please provide date as argument!")
        sys.exit(1)

    selected_date = sys.argv[1]


    json_file = scrape_aston_live()
    if json_file:
        file_path = os.path.join(base_path, "Aston_Live_Data", "aston_live.json")
        filter_aston_json_only_date(selected_date,file_path)
        token = login_and_get_token()
        if token:
            platefromID = get_id(token)
        
            if platefromID:
                with open(file_path, "r", encoding="utf-8") as f:
                        auctions = json.load(f)

                for i, item in enumerate(auctions, start=1):
                    iso_date_str = item.get("Date", "")
                    if iso_date_str and iso_date_str != "N/A":
                        dt = datetime.strptime(iso_date_str, "%A %d %B %Y, %H:%M")
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")

                    payload = {
                        "auction_type": 2,
                        "platform": platefromID,
                        "auction_name": item.get("Title"),
                        "date": formatted_date,
                        "lots": str(item.get("Vehicles")),
                        "assign_to": "Shakeeb",
                        "status":"Pending"  
                    }

                    res = upload_auctiondata_one_by_one(token,payload)
        
