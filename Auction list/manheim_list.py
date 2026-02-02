from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.service_account import Credentials
import gspread
import time, json, os, sys,re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import re,urllib3,requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_NAME = "Manheim"
FOLDER_PATH = os.path.join(BASE_DIR, FOLDER_NAME)


load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
API_ENDPOINT_PLATEFROM = f"{API_BASE_URL}/api/cruds/platform"
AUCTION_UPLOAD_URL = f"{API_BASE_URL}/api/cruds/taskManagement"


os.makedirs(FOLDER_PATH, exist_ok=True)

def scrape(url):
    options = ChromeOptions()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = Chrome(service=service, options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 15)

    # ✅ Click "F" tab
    try:
        tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.js-tabs-switcher_item[data-id="tab1"]')))
        tab.click()
        print("✅ Clicked 'F' tab")
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ Could not click tab: {e}")

    # ✅ Click "Load more" twice
    for i in range(2):
        try:
            load_more = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".js-load-more-listing-events")))
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
            time.sleep(1)
            load_more.click()
            print(f"🔄 Clicked 'Load more' ({i+1}/2)")
            time.sleep(3)
        except Exception:
            print("✅ No more 'Load more' button found.")
            break

    # ✅ Extract listings
    listings = driver.find_elements(By.CSS_SELECTOR, ".listing__item.listing__item_events")
    results = []

    for item in listings:
        try:
            day = item.find_element(By.CSS_SELECTOR, '.event_dates__item .day').text.strip()
            date_text = item.find_element(By.CSS_SELECTOR, '.event_dates__item .date').text.strip()
            time_ = item.find_element(By.CSS_SELECTOR, '.event_dates__item .time').text.strip()

            try:
                date_obj = datetime.strptime(f"{date_text} {datetime.now().year}", "%d %b %Y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except:
                formatted_date = date_text

            name = item.find_element(By.CSS_SELECTOR, '.event_title span[itemprop="name"]').text.strip()
            lots_text = item.find_element(By.CSS_SELECTOR, '.event_info__vehicles').text.strip()
            lots = lots_text.split(" ")[0] if lots_text else "0"

            if not time_ or lots == "0" or lots.lower() == "na":
                continue

            results.append({
                "Date": formatted_date,
                "Day": day,
                "Time": time_,
                "Auction name": name,
                "Lots": lots
            })
        except Exception:
            continue

    driver.quit()

    output_file = os.path.join(FOLDER_PATH, "auctions.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"✅ Saved {len(results)} auctions to {output_file}")


def normalize_auction_dates():
    input_file = os.path.join(FOLDER_PATH, "auctions.json")

    if not os.path.exists(input_file):
        print("❌ auctions.json not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_data = []
    for item in data:
        raw = item.get("Date", "").strip()

        # ✅ Already ISO ya proper date ho to skip
        if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", raw):
            fixed_data.append(item)
            continue

        # ✅ Format like "03 Nov" or "3 November"
        try:
            parsed = datetime.strptime(raw, "%d %b")  # 03 Nov
        except:
            try:
                parsed = datetime.strptime(raw, "%d %B")  # 03 November
            except:
                fixed_data.append(item)
                continue

        # ✅ Use current year automatically
        parsed = parsed.replace(year=datetime.now().year)
        item["Date"] = parsed.strftime("%Y/%m/%d")
        fixed_data.append(item)

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=4, ensure_ascii=False)

    print(f"✅ Normalized {len(fixed_data)} auctions in {input_file}")
    
    


def filter_auction_by_iso_date(target_date_iso):
    input_file = os.path.join(FOLDER_PATH, "auctions.json")
    output_file = os.path.join(FOLDER_PATH, "finalList.json")

    if not os.path.exists(input_file):
        print("❌ auctions.json not found.")
        return []

    try:
        target_dt = datetime.strptime(target_date_iso, "%Y-%m-%dT%H:%M:%SZ")
        target_day = target_dt.day
        target_month = target_dt.month
        target_year = target_dt.year
    except Exception as e:
        print(f"❌ Invalid date format: {e}")
        return []

    today = datetime.now()

    # ⚙️ Build normalized auctions with full date
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_data = []
    for item in data:
        raw = item.get("Date", "").strip()

        # Extract only digits (remove st/nd/rd/th)
        match = re.search(r"(\d+)", raw)
        if not match:
            continue

        day_num = int(match.group(1))

        # Determine month/year relative to today
        current_month = today.month
        current_year = today.year

        # if day has already passed in current month -> next month
        if day_num < today.day:
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

        # Create full date
        try:
            full_date = datetime(current_year, current_month, day_num)
        except ValueError:
            continue

        item["Date"] = full_date.strftime("%Y/%m/%d")
        fixed_data.append(item)

    # 🧹 Optional: Overwrite normalized data
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=4, ensure_ascii=False)

    # 🎯 Filter only for given target date
    target_date_str = target_dt.strftime("%Y/%m/%d")
    filtered = [item for item in fixed_data if item["Date"] == target_date_str]

    if not filtered:
        print(f"⚠️ No auctions found for {target_date_str}")
        return []

    # 💾 Save final list
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=4, ensure_ascii=False)

    print(f"✅ Saved {len(filtered)} auctions to {output_file}")

    try:
        os.remove(input_file)
        print("🗑️ Deleted original auctions.json")
    except Exception as e:
        print(f"⚠️ Could not delete auctions.json: {e}")

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
            if platform.get("name") == "Manheim Auction":
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
    if len(sys.argv) < 2:
        print("❌ Please provide a date argument! Example: python manheim.py 2025-11-02T00:00:00Z")
        sys.exit(1)

    selected_date = sys.argv[1]


    path = "https://www.manheim.co.uk/catalogues-and-events"
    scrape(path)
    normalize_auction_dates()
    filtered_data = filter_auction_by_iso_date(selected_date)

    if filtered_data:
        token = login_and_get_token()
        if token:
            platefromID = get_id(token)
        
            if platefromID:
                base_path = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(base_path, "Manheim", "finalList.json")
                with open(file_path, "r", encoding="utf-8") as f:
                        auctions = json.load(f)

                for i, item in enumerate(auctions, start=1):
                    date_str = item.get("Date", "").strip()    
                    time_str = item.get("Time", "").strip()

                    formatted_date = None
                    if date_str and time_str:
                        combined = f"{date_str} {time_str}"
                        dt = datetime.strptime(combined, "%Y/%m/%d %H:%M")

                        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")

                    payload = {
                        "auction_type": 2,
                        "platform": platefromID,
                        "auction_name": item.get("Auction name"),
                        "date": formatted_date,
                        "lots": str(item.get("Lots")),
                        "assign_to": "Shakeeb",
                        "status":"Pending"  
                    }
                    res = upload_auctiondata_one_by_one(token,payload)
