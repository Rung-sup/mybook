import os
import json

categories = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion_Science",
    "6_Pending_Sort"
]

db_data = {}

for cat in categories:
    cat_path = cat
    if not os.path.exists(cat_path):
        db_data[cat] = []
        continue

    # กวาดชื่อโฟลเดอร์ย่อยและลบช่องว่างทิ้ง
    subfolders = [f for f in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, f))]

    if not subfolders:
        # ลบช่องว่างที่ชื่อไฟล์ในระดับหมวด
        files = [f.strip() for f in os.listdir(cat_path) if f.lower().endswith(('.pdf', '.epub'))]
        db_data[cat] = sorted(list(set(files))) # set ช่วยกำจัดชื่อซ้ำที่เกิดจากช่องว่าง
    else:
        cat_dict = {}
        for folder in subfolders:
            folder_path = os.path.join(cat_path, folder)
            # ลบช่องว่างที่ชื่อไฟล์ในโฟลเดอร์ย่อย
            files = [f.strip() for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.epub'))]
            if files:
                cat_dict[folder.strip()] = sorted(list(set(files)))
        
        # กวาดไฟล์ที่อยู่นอกโฟลเดอร์ย่อย
        root_files = [f.strip() for f in os.listdir(cat_path) if os.path.isfile(os.path.join(cat_path, f)) and f.lower().endswith(('.pdf', '.epub'))]
        if root_files:
            cat_dict["Other_Files"] = sorted(list(set(root_files)))
            
        db_data[cat] = cat_dict

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, ensure_ascii=False, indent=4)

print("ล้างช่องว่างและสร้าง database.json ใหม่เรียบร้อยแล้วครับ!")