import os
import json
import urllib.parse

# ข้อมูลของคุณรันนรา
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"

# รายชื่อหมวด (ต้องตรงกับชื่อ Repository บน GitHub)
folders = [
    "1_PetchPraUma", "2_Thai_Novel", "3_English_Translated",
    "4_Chinese_Novel", "5_HowTo_Religion", "6_HowTo_Religion_Science"
]

all_books = []

print("🚀 กำลังเริ่มสร้างฐานข้อมูลใหม่...")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    if not os.path.exists(folder_path): continue

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')):
                title = os.path.splitext(file)[0]
                
                # หาความสัมพันธ์ไฟล์ (แก้ปัญหาโฟลเดอร์ซ้อน)
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")
                
                # สร้าง URL ที่ถูกต้อง (ตัด /mybook/ ออกเพื่อให้ชี้ตรงไปที่กล่องหมวดนั้นๆ)
                final_path = urllib.parse.quote(rel_path_web, safe='/')
                full_url = f"https://{github_username}.github.io/{folder}/{final_path}"

                all_books.append({"title": title, "url": full_url})

# บันทึกลง database.json เป็น Array [ ]
with open("database.json", 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("✅ สำเร็จ! อย่าลืมส่งไฟล์ database.json ขึ้น GitHub กล่อง mybook นะครับ")