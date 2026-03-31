import os
import json

# 1. กำหนดรายชื่อหมวดหมู่ให้ตรงกับโฟลเดอร์จริงในเครื่องและบน GitHub
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
    # ถ้าหาโฟลเดอร์หมวดหมู่ไม่เจอ ให้ข้ามไป
    if not os.path.exists(cat_path):
        db_data[cat] = []
        continue

    # 2. เช็กว่าในหมวดนั้นมีโฟลเดอร์ย่อย (Subfolder) หรือไม่
    items = os.listdir(cat_path)
    subfolders = [f for f in items if os.path.isdir(os.path.join(cat_path, f))]

    if not subfolders:
        # --- กรณีเป็นรายการไฟล์ยาวๆ (เช่น เพชรพระอุมา) ---
        # ใช้ .strip() ลบช่องว่างหน้า-หลังชื่อไฟล์ และใช้ set() เพื่อป้องกันชื่อซ้ำ
        files = [f.strip() for f in items if f.lower().endswith(('.pdf', '.epub'))]
        db_data[cat] = sorted(list(set(files)))
    else:
        # --- กรณีมีการแยกโฟลเดอร์ย่อย (เช่น นิยายไทย) ---
        cat_dict = {}
        for folder in subfolders:
            folder_path = os.path.join(cat_path, folder)
            # ลบช่องว่างที่ชื่อไฟล์ในโฟลเดอร์ย่อย
            files = [f.strip() for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.epub'))]
            if files:
                # ใช้ชื่อโฟลเดอร์ที่ลบช่องว่างแล้ว (.strip()) เป็นหัวข้อ
                cat_dict[folder.strip()] = sorted(list(set(files)))
        
        # กวาดไฟล์ที่อาจจะวางอยู่นอกโฟลเดอร์ย่อย (Root ของหมวดนั้น)
        root_files = [f.strip() for f in items if os.path.isfile(os.path.join(cat_path, f)) and f.lower().endswith(('.pdf', '.epub'))]
        if root_files:
            cat_dict["Other_Files"] = sorted(list(set(root_files)))
            
        db_data[cat] = cat_dict

# 3. บันทึกไฟล์เป็น database.json (UTF-8 เพื่อรองรับภาษาไทย)
try:
    with open('database.json', 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=4)
    print("✅ สร้างไฟล์ database.json ฉบับคลีนช่องว่างเรียบร้อยแล้ว!")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดในการบันทึกไฟล์: {e}")