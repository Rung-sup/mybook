import os
import json
import urllib.parse
import re

base_dir = r"C:\MyLibrary"
base_url = "https://Rung-sup.github.io" 
db = []

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

print("📦 กำลังจัดระเบียบหอสมุดดิจิทัล...")

# ดึงรายชื่อโฟลเดอร์หมวดหมู่
categories = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
categories.sort(key=natural_sort_key) # เรียงหมวดหมู่ 1, 2, 3...

for cat in categories:
    cat_path = os.path.join(base_dir, cat)
    file_list = []
    for root, dirs, files in os.walk(cat_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')) and not file.startswith(('a', '._', 'ttt')):
                file_list.append(os.path.join(root, file))
    
    # เรียงไฟล์ในหมวดนั้นๆ ให้เป๊ะ 1, 2, 10
    file_list.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    for full_path in file_list:
        file = os.path.basename(full_path)
        relative_path = os.path.relpath(full_path, base_dir)
        url_path = urllib.parse.quote(relative_path.replace("\\", "/"))
        
        db.append({
            "title": os.path.splitext(file)[0],
            "url": f"{base_url}/{url_path}",
            "category": cat # เก็บชื่อหมวดหมู่ไว้ด้วย
        })

with open("database.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=4)

print(f"✨ เรียงลำดับและจัดหมวดหมู่เสร็จแล้ว {len(db)} เล่ม!")