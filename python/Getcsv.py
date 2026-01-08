import os
import pandas as pd
from DataFields import DataFields 
from datetime import datetime

base_dir = r"D:\scraper"
output_dir = r"D:\python\final_csvs"
os.makedirs(output_dir, exist_ok=True)

for root, dirs, files in os.walk(base_dir):
    final_csvs = [
        f for f in files
        if f.lower().endswith('.csv') and 'final' in f.lower() and f.lower() != 'final_barclay.csv'
    ]
    
    if final_csvs:
        parts = root.split(os.sep)
        if len(parts) >= 4:
            date_str = parts[-3] 
            current_year = datetime.now().year
            dt = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")
            formatted_date = dt.strftime("%d-%m-%Y")
            auction_house = parts[-2]
            

            folder_desc = parts[-1]
            chunks = folder_desc.split('-')
            if len(chunks) > 2 and chunks[1].isdigit():
                folder_desc = f"{chunks[0]}-" + "-".join(chunks[2:])
            
            folder_name = f"{formatted_date}_{auction_house}_{folder_desc}"
            
            for f in final_csvs:
                src_path = os.path.join(root, f)
                dst_path = os.path.join(output_dir, f"{folder_name}.csv")
                
                
                newData = []
                df = pd.read_csv(src_path)
                data = df.to_dict(orient="records") 
                for key,value in enumerate(data):
                    newitem = DataFields(value)
                    newData.append(newitem)
                
                newcsv = pd.DataFrame(newData)
                newcsv.to_csv(dst_path, index=False)
            
                




