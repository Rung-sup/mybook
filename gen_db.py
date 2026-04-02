import os
import json
import urllib.parse

# --- ข้อมูลพื้นฐานของคุณรันนรา ---
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"

# รายชื่อโฟลเดอร์หนังสือ (ต้องตรงกับชื่อ Repository บนหน้าเว็บ GitHub เป๊ะๆ)
folders = [
    "1_PetchPraUma",
    "2_Thai_Novel",
    "3_English_Translated",
    "4_Chinese_Novel",
    "5_HowTo_Religion",
    "6_HowTo_Religion_Science"
]

all_books = []
total_count = 0

print(f"🔍 เริ่มสำรวจไฟล์ใน {base_dir} ...\n")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    if not os.path.exists(folder_path):
        print(f"⚠️ ไม่พบโฟลเดอร์ในเครื่อง: {folder}")
        continue

    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.epub')):
                title = os.path.splitext(file)[0]
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                
                # แปลงชื่อไฟล์ให้เป็น URL ที่ถูกต้อง (ไม่มี /mybook/ แทรกลงไป)
                final_path = urllib.parse.quote(rel_path.replace("\\", "/"), safe='/')
                full_url = f"https://{github_username}.github.io/{folder}/{final_path}"

                all_books.append({"title": title, "url": full_url})
                count += 1
                total_count += 1
    print(f"✅ หมวด [{folder}] สำเร็จ: {count} เล่ม")

# บันทึกลง database.json
with open("database.json", 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! สร้าง database.json ใหม่เรียบร้อย (รวม {total_count} เล่ม)")