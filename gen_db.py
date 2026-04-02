import os
import json
import urllib.parse
import re

base_dir = r"C:\MyLibrary"
base_url = "https://Rung-sup.github.io" 
db = []

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

print("🔍 กำลังกู้คืนฐานข้อมูล (ฉบับเสถียร)...")

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith(('.pdf', '.epub')) and not file.startswith(('._', 'ttt')):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            path_parts = rel_path.split(os.sep)
            
            # หมวดหมู่คือโฟลเดอร์ชั้นแรกสุด
            category = path_parts[0] if len(path_parts) > 1 else "ทั่วไป"
            
            url_path = urllib.parse.quote(rel_path.replace("\\", "/"))
            
            db.append({
                "title": os.path.splitext(file)[0],
                "url": f"{base_url}/{url_path}",
                "category": category
            })

# เรียงลำดับชื่อเรื่องให้ 1 มาก่อน 10 ทั่วทั้งระบบ
db.sort(key=lambda x: natural_sort_key(x['title']))

with open("database.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=4)

print(f"✨ คืนค่าสำเร็จ! พบทั้งหมด {len(db)} เล่ม (ตรวจสอบในเครื่องได้เลยครับ)")