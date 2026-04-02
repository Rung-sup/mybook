import os
import json
import urllib.parse
import re

# ที่อยู่โฟลเดอร์ในเครื่องของคุณรันนรา
base_dir = r"C:\MyLibrary"
base_url = "https://Rung-sup.github.io" 

db = []

# ฟังก์ชันเรียงลำดับแบบธรรมชาติ (Natural Sort) ที่ทำให้เล่ม 1 มาก่อนเล่ม 10
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

print("🔍 กำลังกู้คืนฐานข้อมูลชุดที่ทำงานได้...")

for root, dirs, files in os.walk(base_dir):
    for file in files:
        # เก็บเฉพาะไฟล์ PDF และ EPUB และกรองไฟล์ขยะออก
        if file.lower().endswith(('.pdf', '.epub')) and not file.startswith(('._', 'ttt')):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            
            # แยกหมวดหมู่จากโฟลเดอร์ชั้นแรกสุด
            path_parts = rel_path.split(os.sep)
            category = path_parts[0] if len(path_parts) > 1 else "ทั่วไป"
            
            # เข้ารหัส URL ให้ถูกต้องเพื่อให้อ่านไฟล์ภาษาไทยได้
            url_path = urllib.parse.quote(rel_path.replace("\\", "/"))
            
            db.append({
                "title": os.path.splitext(file)[0],
                "url": f"{base_url}/{url_path}",
                "category": category
            })

# สั่งเรียงลำดับตามชื่อเรื่องให้ถูกต้องก่อนบันทึก
db.sort(key=lambda x: natural_sort_key(x['title']))

with open("database.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=4)

print(f"✨ คืนค่าสำเร็จ! พบหนังสือทั้งหมด {len(db)} เล่ม และเรียงลำดับเรียบร้อยครับ")