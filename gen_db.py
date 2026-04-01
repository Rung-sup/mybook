import os
import json
import urllib.parse

# 1. แผนที่ไปโกดังหนังสือ (ตำแหน่งในคอมพิวเตอร์)
base_dir = r"C:\MyLibrary"

# 2. ชื่อบัญชี GitHub ของคุณปุ๊ก (สำหรับสร้างลิงก์)
github_username = "rung-sup"

# 3. รายชื่อโกดังทั้ง 6 ห้อง (ต้องสะกดให้ตรงกับชื่อโฟลเดอร์เป๊ะๆ)
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
    
    # เช็คว่ามีโฟลเดอร์นี้อยู่ใน C:\MyLibrary จริงๆ ไหม
    if not os.path.exists(folder_path):
        print(f"⚠️ ข้าม: หาโฟลเดอร์ไม่พบ -> {folder_path}")
        continue
        
    # เดินสำรวจทีละโฟลเดอร์
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                # 1. ได้ชื่อหนังสือ
                title = os.path.splitext(file)[0]
                
                # 2. จำลองเส้นทางไฟล์สำหรับเว็บ (เปลี่ยน \ เป็น /)
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                rel_path_web = rel_path.replace("\\", "/")
                
                # 3. เข้ารหัสภาษาไทยให้ URL ไม่พัง
                parts = rel_path_web.split('/')
                encoded_parts = [urllib.parse.quote(p) for p in parts]
                final_path = "/".join(encoded_parts)
                
                # 4. สร้างลิงก์ดึงข้อมูลจาก GitHub Pages โดยตรง
                full_url = f"https://{github_username}.github.io/{folder}/{final_path}"
                
                # 5. จดลงสมุด
                book_data = {
                    "title": title,
                    "url": full_url
                }
                all_books.append(book_data)
                folder_count += 1
                total_count += 1
                
    print(f"✅ โกดัง [{folder}]: กวาดมาได้ {folder_count} เล่ม")

# บันทึกเป็นไฟล์ database.json ลงในโฟลเดอร์ปัจจุบัน
output_file = "database.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"🎉 สำเร็จ! สร้างไฟล์ {output_file} อัปเดตล่าสุดแล้ว")
print(f"📚 ยอดรวมหนังสือทั้งหมดจากทุกโกดัง: {total_count} เล่ม")