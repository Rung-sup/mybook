import os
import json
import urllib.parse

# 1. ข้อมูลพื้นฐานของคุณรันนรา
base_dir = r"C:\MyLibrary"
github_username = "rung-sup"

# 2. รายชื่อโฟลเดอร์หนังสือ (ต้องตรงกับชื่อ Repository บน GitHub ของคุณรันนราเป๊ะๆ)
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

print(f"🔍 เริ่มสำรวจไฟล์ใน {base_dir} เพื่อสร้างฐานข้อมูลแบบแยกกล่อง...\n")

for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    folder_count = 0

    if not os.path.exists(folder_path):
        print(f"⚠️ ไม่พบโฟลเดอร์ในเครื่อง: {folder_path}")
        continue

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # คัดกรองเฉพาะไฟล์หนังสือ
            if file.lower().endswith(('.pdf', '.epub')):
                # ใช้ชื่อไฟล์เป็นชื่อเรื่อง
                title = os.path.splitext(file)[0]

                # สร้างเส้นทางไฟล์ (Path) สำหรับเว็บ
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")

                # แปลงชื่อไฟล์ภาษาไทยให้เป็น URL ที่ถูกต้อง (โดยไม่แปลงเครื่องหมาย /)
                final_path = urllib.parse.quote(rel_path_web, safe='/')

                # สร้างที่อยู่ที่ชี้ตรงไปยัง Repository ของหมวดนั้นๆ 
                # (ตัด /mybook/ ออกเพื่อให้เข้าถึงไฟล์ที่แยกกล่องได้ถูกต้อง)
                full_url = f"https://{github_username}.github.io/{folder}/{final_path}"

                all_books.append({
                    "title": title,
                    "url": full_url
                })
                folder_count += 1
                total_count += 1

    print(f"✅ หมวด [{folder}]: พบหนังสือ {folder_count} เล่ม")

# 3. บันทึกข้อมูลเป็นแบบ Array [ ] ลงในไฟล์ database.json
output_file = "database.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! สร้างไฟล์ {output_file} เรียบร้อยแล้ว")
print(f"📚 รวมหนังสือทั้งหมด: {total_count} เล่ม")