import os
import json
import urllib.parse
import re

base_dir = r"C:\MyLibrary"
base_url = "https://Rung-sup.github.io" 
db = []

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

print("🔍 กำลังจัดกลุ่มหนังสือตามโฟลเดอร์...")

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith(('.pdf', '.epub')) and not file.startswith(('._', 'ttt')):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            path_parts = rel_path.split(os.sep)
            
            # โครงสร้าง: [หมวดหมู่] / [ชื่อชุดหนังสือ(ถ้ามี)] / [ไฟล์]
            category = path_parts[0] if len(path_parts) > 1 else "ทั่วไป"
            # ถ้าอยู่ในโฟลเดอร์ย่อย ให้ถือเป็นชื่อชุด (Series/Folder)
            folder_name = path_parts[1] if len(path_parts) > 2 else ""
            
            url_path = urllib.parse.quote(rel_path.replace("\\", "/"))
            
            db.append({
                "title": os.path.splitext(file)[0],
                "url": f"{base_url}/{url_path}",
                "category": category,
                "folder": folder_name  # เพิ่มฟิลด์โฟลเดอร์
            })

# เรียงลำดับตามธรรมชาติ
db.sort(key=lambda x: natural_sort_key(x['title']))

with open('database.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)

print(f"✅ บันทึกข้อมูลเรียบร้อย! พบทั้งหมด {len(db)} เล่ม")