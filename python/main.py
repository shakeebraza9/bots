import os
import urllib3
import time
from datetime import datetime
from dotenv import load_dotenv
from ExportRecord.ConnectSheet import DataSet 
from ExportRecord.Upload import Upload as Up
LOG_FILE = "auction_error.log"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
API_ENDPOINT = f"{API_BASE_URL}/api/cruds/auctions"
ERROR_LOG_FILE = "error_log.txt"
BASE_FOLDER = os.getenv("BASE_FOLDER", r"D:\python")






if __name__ == "__main__":

    folder_path = os.path.join(BASE_FOLDER, "final_csvs")
    folder_path = folder_path.replace("/", "\\")
    dataset = DataSet()
    dataSet = dataset.data
    auctions = Up.process_csvs_to_json(folder_path, dataSet)
  
    # print(auctions)
    LoginToken = Up.login_and_get_token() 



    for auction in auctions:
        platrfrom_id = Up.getPlatefromID(auction["platform"],LoginToken)
        auction["platform_id"] = platrfrom_id
        Up.post_or_update(auction, LoginToken)
        time.sleep(3)   
