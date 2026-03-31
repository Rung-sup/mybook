import os
import json

# ตั้งชื่อหมวดหมู่ให้ตรงกับใน GitHub และ categories.html
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

    # ตรวจสอบว่าในหมวดนั้นมีโฟลเดอร์ย่อยหรือไม่
    subfolders = [f for f in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, f))]

    if not subfolders:
        # กรณีไม่มีโฟลเดอร์ย่อย (แบบ Array รายการยาว)
        files = [f.strip() for f in os.listdir(cat_path) if f.lower().endswith(('.pdf', '.epub'))]
        db_data[cat] = sorted(files)
    else:
        # กรณีมีโฟลเดอร์ย่อย (แบบ Object แยกโฟลเดอร์)
        cat_dict = {}
        for folder in subfolders:
            folder_path = os.path.join(cat_path, folder)
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.epub'))]
            if files:
                cat_dict[folder] = sorted(files)
        
        # กวาดไฟล์ที่อาจจะหลงอยู่นอกโฟลเดอร์ย่อยด้วย
        root_files = [f for f in os.listdir(cat_path) if os.path.isfile(os.path.join(cat_path, f)) and f.lower().endswith(('.pdf', '.epub'))]
        if root_files:
            cat_dict["Other_Files"] = sorted(root_files)
            
        db_data[cat] = cat_dict

# บันทึกเป็นไฟล์ database.json
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, ensure_ascii=False, indent=4)

print("สร้างไฟล์ database.json เรียบร้อยแล้วครับ!")