import os
import json
import urllib.parse
import re

# ตรวจสอบที่อยู่โฟลเดอร์ให้ถูกต้อง
base_dir = r"C:\MyLibrary"
base_url = "https://Rung-sup.github.io" 

db = []
seen_files = set() # กันไฟล์ซ้ำซ้อนกรณีเดียวกันเป๊ะ

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

print("🔍 กำลังสำรวจหอสมุดดิจิทัล (ฉบับกู้คืนไฟล์)...")

for root, dirs, files in os.walk(base_dir):
    # ข้ามโฟลเดอร์ที่ไม่เกี่ยวข้อง
    if '.git' in dirs: dirs.remove('.git')
    
    for file in files:
        # เอาเฉพาะ PDF และ EPUB (ไม่สนตัวพิมพ์เล็ก-ใหญ่)
        if file.lower().endswith(('.pdf', '.epub')):
            
            # กรองเฉพาะไฟล์ขยะของระบบจริงๆ เท่านั้น (เช่น ._ หรือไฟล์ชั่วคราว)
            if file.startswith('._') or file.startswith('~$'):
                continue

            full_path = os.path.join(root, file)
            file_size = os.path.getsize(full_path)
            
            # ป้องกันไฟล์ซ้ำ (ใช้ชื่อ+ขนาด)
            file_id = f"{file}_{file_size}"
            if file_id in seen_files:
                continue
            seen_files.add(file_id)

            # แยกหมวดหมู่จากโฟลเดอร์แรกถัดจาก MyLibrary
            relative_path = os.path.relpath(full_path, base_dir)
            path_parts = relative_path.split(os.sep)
            
            if len(path_parts) > 1:
                category = path_parts[0]
            else:
                category = "ทั่วไป" # ไฟล์ที่ไม่ได้อยู่ในโฟลเดอร์ย่อย

            url_path = urllib.parse.quote(relative_path.replace("\\", "/"))
            
            db.append({
                "title": os.path.splitext(file)[0],
                "url": f"{base_url}/{url_path}",
                "category": category
            })
            print(f"✅ เพิ่มแล้ว: [{category}] {file}")

# เรียงลำดับชื่อหนังสือทั้งหมดให้สวยงาม
db.sort(key=lambda x: natural_sort_key(x['title']))

# บันทึกเป็น database.json
with open("database.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=4)

print("-" * 30)
print(f"✨ ภารกิจสำเร็จ! รวมหนังสือทั้งหมดในฐานข้อมูล: {len(db)} เล่ม")
print(f"💡 ตรวจสอบไฟล์ database.json ในเครื่องได้เลยครับ")