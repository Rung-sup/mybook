import os
import json
import urllib.parse

# ข้อมูลของคุณรันนรา
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"

# รายชื่อโฟลเดอร์ (ซึ่งตรงกับชื่อกล่องบน GitHub ด้วย)
folders = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion",
    "6_HowTo_Religion_Science"
]

all_books = [] # สร้างเป็นรายการแบบ Array ตามที่แอปต้องการ

print(f"🔍 เริ่มจดบันทึกรายชื่อหนังสือแยกตามกล่องบน GitHub...\n")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    
    if not os.path.exists(folder_path):
        print(f"⚠️ ไม่พบโฟลเดอร์: {folder}")
        continue

    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')):
                title = os.path.splitext(file)[0]
                
                # หาที่อยู่ไฟล์ข้างในโฟลเดอร์
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")
                
                # สร้างที่อยู่ที่ชี้ไปยังกล่อง (Repository) ของหมวดนั้นโดยเฉพาะ
                # ตัวอย่าง: https://rung-sup.github.io/1_PetchPraUma/ชื่อหนังสือ.pdf
                full_url = f"https://{github_username}.github.io/{folder}/{urllib.parse.quote(rel_path_web)}"
                
                all_books.append({
                    "title": title,
                    "url": full_url
                })
                count += 1
    
    print(f"✅ บันทึกจากกล่อง [{folder}] เสร็จแล้ว: {count} เล่ม")

# บันทึกลงสมุดรายชื่อ database.json
with open("database.json", 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! สร้างไฟล์ database.json เป็นแบบ Array เรียบร้อยแล้ว")