
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_SHEET_LINK = os.getenv("GOOGLE_SHEET_LINK")

class DataSet:

    def __init__(self):
        self.data = self.google_sheet_to_json(GOOGLE_SHEET_LINK)
        print("✅ DataSet object created")

    def google_sheet_to_json(self, url):
        data = {}
        df_dict = pd.read_excel(url, sheet_name=None)

        for sheet_name, sheet_df in df_dict.items():
            cleaned = sheet_df.dropna(how="all")
            rows = cleaned.to_dict(orient="records")

            mapping = {}
            for row in rows:
                key = row.get("key")
                value = row.get("value")
                if key and value:
                    mapping[key.lower()] = value
            data[sheet_name] = mapping
        return data

    def printdata(self):
        print(self.data)




# Usage
# car = DataSet()
# cardate = car.printdata()
# print(cardate)