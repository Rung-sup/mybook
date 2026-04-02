import os
import json
import urllib.parse

# 1. ข้อมูลพื้นฐานของคุณรันนรา
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"

# 2. รายชื่อโฟลเดอร์หนังสือ (ซึ่งต้องตรงกับชื่อ Repository บน GitHub ของคุณรันนราเป๊ะๆ)
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

print(f"🔍 กำลังเริ่มสำรวจหนังสือใน {base_dir} ...\n")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    folder_count = 0

    if not os.path.exists(folder_path):
        print(f"⚠️ ข้าม: หาโฟลเดอร์ไม่พบ -> {folder_path}")
        continue

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # เก็บเฉพาะไฟล์ PDF และ EPUB
            if file.lower().endswith(('.pdf', '.epub')):
                # ใช้ชื่อไฟล์เป็นชื่อหนังสือ (ตัดนามสกุลออก)
                title = os.path.splitext(file)[0]

                # สร้างที่อยู่ไฟล์สำหรับใช้งานบนเว็บ
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")

                # แปลงชื่อไฟล์ภาษาไทยให้เป็นรหัส URL ที่ถูกต้อง (รองรับเครื่องหมาย / สำหรับโฟลเดอร์ย่อย)
                final_path = urllib.parse.quote(rel_path_web, safe='/')

                # สร้าง URL ที่ชี้ไปยังกล่องหนังสือของแต่ละหมวดโดยตรง
                # ตัวอย่าง: https://rung-sup.github.io/1_PetchPraUma/ชื่อหนังสือ.pdf
                full_url = f"https://{github_username}.github.io/{folder}/{final_path}"

                book_data = {
                    "title": title,
                    "url": full_url
                }

                all_books.append(book_data)
                folder_count += 1
                total_count += 1

    print(f"✅ หมวด [{folder}]: พบหนังสือ {folder_count} เล่ม")

# 3. บันทึกลงสมุดรายชื่อ database.json ในรูปแบบ Array [ ]
output_file = "database.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! สร้างไฟล์ {output_file} เรียบร้อยแล้ว")
print(f"📚 ยอดรวมหนังสือทั้งหมด: {total_count} เล่ม พร้อมอ่านบนเว็บได้ทันที")