import os
import json
import urllib.parse

# ที่อยู่โฟลเดอร์ในเครื่องของคุณรันนรา
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"
repo_name = "mybook"

# รายชื่อหมวดหมู่ที่ยืนยันแล้ว
folders = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion",
    "6_HowTo_Religion_Science"
]

# สร้าง "ตู้เก็บรายชื่อ" แยกตามหมวดหมู่
all_books = {}

print(f"🔍 กำลังเริ่มสำรวจหนังสือใน {base_dir} ...\n")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    all_books[folder] = [] # สร้างลิ้นชักแยกไว้สำหรับแต่ละหมวด
    folder_count = 0

    if not os.path.exists(folder_path):
        print(f"⚠️ ข้าม: หาโฟลเดอร์ไม่พบ -> {folder_path}")
        continue

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # เก็บเฉพาะไฟล์หนังสือ
            if file.lower().endswith(('.pdf', '.epub')):
                # สร้างที่อยู่ไฟล์สำหรับเปิดบนเว็บ (ไม่ต้องแปลงชื่อไฟล์ซ้ำซ้อน)
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")
                
                # เราจะเก็บแค่ชื่อไฟล์ไว้ เดี๋ยวแอปจะไปจัดการที่อยู่เอง
                all_books[folder].append(rel_path_web)
                folder_count += 1

    print(f"✅ หมวด [{folder}]: พบหนังสือ {folder_count} เล่ม")

# บันทึกลงสมุดรายชื่อ database.json
output_file = "database.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! แก้ไขไฟล์ {output_file} เรียบร้อยแล้ว")