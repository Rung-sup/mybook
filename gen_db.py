import os
import json

# 1. รายชื่อหมวดหมู่ (ต้องสะกดให้ตรงกับชื่อโฟลเดอร์จริง)
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

    items = os.listdir(cat_path)
    # คัดกรองเฉพาะโฟลเดอร์ย่อยจริงๆ
    subfolders = [f for f in items if os.path.isdir(os.path.join(cat_path, f))]

    if not subfolders:
        # กรณีไม่มีโฟลเดอร์ย่อย: ลบช่องว่างหน้าหลัง และเรียงลำดับตามตัวอักษร
        files = sorted([f.strip() for f in items if f.lower().endswith(('.pdf', '.epub'))])
        db_data[cat] = files
    else:
        # กรณีมีโฟลเดอร์ย่อย: สร้างพจนานุกรมเก็บไฟล์แยกตามโฟลเดอร์
        cat_dict = {}
        for folder in sorted(subfolders):
            folder_path = os.path.join(cat_path, folder)
            files = sorted([f.strip() for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.epub'))])
            if files:
                cat_dict[folder.strip()] = files
        
        # เก็บไฟล์ที่อยู่นอกโฟลเดอร์ย่อย (ถ้ามี)
        root_files = sorted([f.strip() for f in items if os.path.isfile(os.path.join(cat_path, f)) and f.lower().endswith(('.pdf', '.epub'))])
        if root_files:
            cat_dict["Other_Files"] = root_files
            
        db_data[cat] = cat_dict

# บันทึกไฟล์
try:
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=4)
    print("✅ database.json อัปเดตรายชื่อหนังสือเรียบร้อย!")
except Exception as e:
    print(f"❌ Error: {e}")