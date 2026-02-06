import json, time, sys, os,re,requests,urllib3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
API_ENDPOINT_PLATEFROM = f"{API_BASE_URL}/api/cruds/platform"
AUCTION_UPLOAD_URL = f"{API_BASE_URL}/api/cruds/taskManagement"



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


    
def get_bca_id(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        r = requests.get(API_ENDPOINT_PLATEFROM, headers=headers, verify=False, timeout=30)
        r.raise_for_status()
        platforms = r.json().get("data", [])
        
        for platform in platforms:
            if platform.get("name") == "BCA":
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

    date_arg = sys.argv[1]
    path = "https://login.bca.co.uk/login?signin=1c9b20ed25a32746f9d5d14b3bb2334a"


    json_path = scrape(date_arg, path)

    Token = login_and_get_token()
    if Token:
        plateformId = get_bca_id(Token)
        with open("BCA_Auctions.json", "r", encoding="utf-8") as f:
            auctions = json.load(f)

        for i, item in enumerate(auctions, start=1):
            iso_date = item.get("Sale Date") 
            dt = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            payload = {
                "auction_type": 2,
                "platform": plateformId,
                "auction_name": item.get("Sale Name"),
                "date": formatted_date,
                "lots": str(item.get("Lots Available")),
                "assign_to": "Mustafa",
                "status":"Pending"  
            }
            res = upload_auctiondata_one_by_one(Token,payload)
            




