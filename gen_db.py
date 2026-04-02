import os
import json
import urllib.parse
import re

base_dir = r"C:\MyLibrary"
base_url = "https://Rung-sup.github.io" 
db = []

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

print("🔍 กำลังสำรวจหอสมุดแบบแยกชั้น...")

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith(('.pdf', '.epub')) and not file.startswith(('._', 'ttt')):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            parts = rel_path.split(os.sep)
            
            # parts[0] คือ หมวดใหญ่ (เช่น 2_Thai_Novel)
            # ถ้ามี parts[2] แปลว่าไฟล์นี้อยู่ในโฟลเดอร์ย่อย (เช่น 2_Thai_Novel/ล่องไพร/file.pdf)
            category = parts[0]
            sub_folder = parts[1] if len(parts) > 2 else None # ถ้าอยู่ชั้นนอกจะเป็น None
            
            url_path = urllib.parse.quote(rel_path.replace("\\", "/"))
            
            db.append({
                "title": os.path.splitext(file)[0],
                "url": f"{base_url}/{url_path}",
                "category": category,
                "subFolder": sub_folder
            })

db.sort(key=lambda x: natural_sort_key(x['title']))

with open("database.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=4)

print(f"✨ สำเร็จ! พบทั้งหมด {len(db)} เล่ม")