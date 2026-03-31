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

    # 1. กวาดรายชื่อโฟลเดอร์ย่อย และใช้ .strip() เพื่อลบช่องว่างที่ชื่อโฟลเดอร์
    subfolders = [f for f in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, f))]

    if not subfolders:
        # กรณีไม่มีโฟลเดอร์ย่อย (แบบ Array) - ลบช่องว่างที่ชื่อไฟล์ด้วย .strip()
        files = [f.strip() for f in os.listdir(cat_path) if f.lower().endswith(('.pdf', '.epub'))]
        db_data[cat] = sorted(files)
    else:
        # กรณีมีโฟลเดอร์ย่อย (แบบ Object)
        cat_dict = {}
        for folder in subfolders:
            folder_path = os.path.join(cat_path, folder)
            # ลบช่องว่างที่ชื่อไฟล์ในโฟลเดอร์ย่อย
            files = [f.strip() for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.epub'))]
            if files:
                # ใช้ชื่อโฟลเดอร์ที่ลบช่องว่างแล้วเป็น Key
                cat_dict[folder.strip()] = sorted(files)
        
        # กวาดไฟล์ที่อยู่นอกโฟลเดอร์ย่อย (ถ้ามี)
        root_files = [f.strip() for f in os.listdir(cat_path) if os.path.isfile(os.path.join(cat_path, f)) and f.lower().endswith(('.pdf', '.epub'))]
        if root_files:
            cat_dict["Other_Files"] = sorted(root_files)
            
        db_data[cat] = cat_dict

# บันทึกเป็นไฟล์ database.json โดยใช้ UTF-8 เพื่อรองรับภาษาไทย
with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, ensure_ascii=False, indent=4)

print("สร้างไฟล์ database.json ฉบับคลีนช่องว่างเรียบร้อยแล้วครับ!")