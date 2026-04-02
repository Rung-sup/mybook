import os
import json
import urllib.parse

# ข้อมูลของคุณรันนรา
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"

# รายชื่อโฟลเดอร์หนังสือ (ต้องตรงกับชื่อกล่องบน GitHub ของคุณเป๊ะๆ)
folders = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion",
    "6_HowTo_Religion_Science"
]

all_books = [] # สร้างเป็นรายการแบบ Array [ ] ตามที่แอปต้องการ

print(f"🔍 กำลังสร้างสมุดจดรายชื่อหนังสือแบบใหม่...")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    if not os.path.exists(folder_path): continue

    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')):
                title = os.path.splitext(file)[0]
                
                # สร้างที่อยู่เว็บที่ชี้ไปแต่ละกล่องโดยเฉพาะ
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")
                # เปลี่ยนบรรทัดเดิม เป็นบรรทัดนี้ครับ (เพิ่ม safe='/')
full_url = f"https://{github_username}.github.io/{folder}/{urllib.parse.quote(rel_path_web, safe='/')}"
                
                # บันทึกข้อมูลแบบมีที่อยู่เว็บ (URL)
                all_books.append({
                    "title": title,
                    "url": full_url
                })
                count += 1
    print(f"✅ บันทึกจากกล่อง [{folder}] เสร็จแล้ว: {count} เล่ม")

# บันทึกลง database.json ในเครื่องคุณ
with open("database.json", 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! ตอนนี้ database.json เริ่มต้นด้วย [ เรียบร้อยแล้วครับ")