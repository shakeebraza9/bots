import os,re
import csv
import json
import time
import requests
import urllib3
from datetime import datetime
from dotenv import load_dotenv
import ExportRecord.function as Fun
from ExportRecord.ConnectSheet import DataSet 

API_BASE_URL = os.getenv("API_BASE_URL")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
LOG_FILE = "auction_error.log"
API_ENDPOINT = f"{API_BASE_URL}/api/cruds/auctions"
API_ENDPOINT_PLATEFROM = f"{API_BASE_URL}/api/cruds/platform"
ERROR_LOG_FILE = "error_log.txt"
class Upload:
    
    def log_error(sheet_id, error_type, response=None):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"Time       : {datetime.now()}\n")
            f.write(f"Sheet ID   : {sheet_id}\n")
            f.write(f"Error Type : {error_type}\n")

            if response is not None:
                try:
                    f.write("API Response:\n")
                    f.write(json.dumps(response, indent=2, ensure_ascii=False))
                except Exception:
                    f.write(str(response))

            f.write("\n\n")

    def normalize(text):
        text = text.lower()
        text = re.sub(r"(auction|auctions|car|cars)", "", text)
        return text.strip()


    def getPlatefromID(auction_house, LoginToken):
        if not auction_house:
            return None
        ALIASES = {
            "protruck": ["protruck", "protruck auction"],
            "cca": ["central car auction", "central car auctions", "cca"],
            "bca": ["bca", "british car auctions"],
            "manheim": ["manheim", "manheim auction"],
            "aston barclay": ["aston barclay", "aston barclay auctions"],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LoginToken}"
        }

        response = requests.get(
            API_ENDPOINT_PLATEFROM,
            headers=headers,
            verify=False,
            timeout=30
        )

        response.raise_for_status()
        data = response.json().get("data", [])

        auction_norm = Upload.normalize(auction_house)

        for item in data:
            item_norm = Upload.normalize(item["name"])
            for key, names in ALIASES.items():
                if auction_norm in names and key in item_norm:
                    return item["id"]
            if auction_norm in item_norm or item_norm in auction_norm:
                return item["id"]

        return None
    
    def process_csvs_to_json(folder_path, dataset: DataSet):
        result = []

        for filename in os.listdir(folder_path):
            if not filename.lower().endswith(".csv"):
                continue

            name = os.path.splitext(filename)[0]
            parts = name.split("_")
            auction_date = parts[0]
            auction_house = parts[1]
            sheet_id, center_name = parts[2].split("-", 1)

            csv_path = os.path.join(folder_path, filename)
            rows = []

            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mapped_row = Fun.DataFields(dataset, row)
                    rows.append(mapped_row)
                    # print(rows)

            result.append({
                "id": sheet_id,
                "name": center_name,
                "auction_date": auction_date,
                "platform": auction_house,
                "auction_type": 2,
                "status": "draft",
                "payload": json.dumps(rows, ensure_ascii=False)
            })
        # print(result)
        return result

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
    
    
    def post_or_update(payload, token):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        sheet_id = payload.get("id")

        try:

            check_url = f"{API_ENDPOINT}?table_id={sheet_id}"
            check = requests.get(
                check_url,
                headers=headers,
                verify=False,
                timeout=30
            )

            check.raise_for_status()
            data = check.json().get("data", [])


            if data:
                auction_db_id = data[0]["id"]
                payload["_method"] = "PUT"

                print(f"🔄 Updating auction sheet {sheet_id}")

                r = requests.post(
                    f"{API_ENDPOINT}/{auction_db_id}",
                    json=payload,
                    headers=headers,
                    verify=False,
                    timeout=60
                )

            else:
                print(f"🆕 Creating auction sheet {sheet_id}")

                r = requests.post(
                    API_ENDPOINT,
                    json=payload,
                    headers=headers,
                    verify=False,
                    timeout=60
                )

            if r.status_code >= 400:
                print(f"❌ API Error {r.status_code} on sheet {sheet_id}")
                Upload.log_error(
                    sheet_id=sheet_id,
                    error_type=f"HTTP {r.status_code}",
                    response=r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
                )
                return r.status_code, r.text

            print("✅ Success:", r.status_code)
            return r.status_code, r.text

        except Exception as e:
            print("❌ Exception:", sheet_id)
            Upload.log_error(sheet_id, "EXCEPTION", str(e))
            return None, None

