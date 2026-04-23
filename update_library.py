import os
import json
import urllib.parse
import hashlib
import unicodedata
from pdf2image import convert_from_path

# ==========================================
# ⚙️ ตั้งค่า Path (อ้างอิงจากระบบของคุณ)
# ==========================================
library_path = r'C:\MyLibrary' 
output_root = 'covers'
db_path = 'database.json'
base_url = "https://Rung-sup.github.io"
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin'

# สร้างโฟลเดอร์ covers หลักหากยังไม่มี
if not os.path.exists(output_root):
    os.makedirs(output_root)

# ==========================================
# 🔑 ฟังก์ชันสร้าง ID รูปปก (มาตรฐานเดียว)
# ==========================================
def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    # จัดการสระภาษาไทยให้ออกมาตรงกับฝั่ง JavaScript เพื่อป้องกัน ID เพี้ยน
    js_str = unicodedata.normalize('NFC', path_slash).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(js_str.encode('utf-8')).hexdigest()

# ==========================================
# 🚀 เริ่มการทำงานหลัก
# ==========================================
def main():
    new_database = []
    new_covers_count = 0
    
    print("🚀 เริ่มกระบวนการตรวจสอบ อัปเดตปก และสร้างฐานข้อมูล...")

    for root, dirs, files in os.walk(library_path):
        # ข้ามโฟลเดอร์ที่ไม่ใช่หมวดหมู่หนังสือเพื่อความรวดเร็ว
        dirs[:] = [d for d in dirs if d not in ['covers', '.git']]
        
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, library_path)
                
                # แยกหมวดหมู่และโฟลเดอร์ย่อย
                parts = rel_path.split(os.sep)
                category = parts[0]
                
                # เงื่อนไข Hybrid: มีโฟลเดอร์ย่อยหรือไม่
                folder_name = parts[1] if len(parts) > 2 else ""

                # สร้าง ID ที่ถูกต้องและ URL สำหรับฐานข้อมูล
                cover_id = generate_cover_id(rel_path)
                final_url = f"{base_url}/{urllib.parse.quote(rel_path.replace('\\', '/'))}"

                # --- ส่วนจัดการรูปปก (สร้างเฉพาะไฟล์ PDF ที่เพิ่งเพิ่มเข้ามาใหม่) ---
                category_folder = os.path.join(output_root, category)
                if not os.path.exists(category_folder):
                    os.makedirs(category_folder)
                    
                cover_output_path = os.path.join(category_folder, f"{cover_id}.jpg")
                
                # ถ้ารูปปกนี้ยังไม่มี ค่อยดึงภาพมาสร้างใหม่
                if not os.path.exists(cover_output_path):
                    try:
                        print(f"กำลังสร้างปกใหม่: {file_name}")
                        images = convert_from_path(full_path, first_page=1, last_page=1, size=(300, None), poppler_path=poppler_bin_path)
                        if images:
                            images[0].save(cover_output_path, 'JPEG', quality=80)
                            new_covers_count += 1
                    except Exception as e:
                        print(f"❌ Error สร้างปก {file_name}: {e}")

                # --- ส่วนสร้างฐานข้อมูล ---
                new_database.append({
                    "title": os.path.splitext(file_name)[0],
                    "url": final_url,
                    "category": category,
                    "folder": folder_name,
                    "cover_id": cover_id
                })

    # บันทึกไฟล์ database.json ทับไฟล์เดิม
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(new_database, f, ensure_ascii=False, indent=4)
        
    print("-" * 40)
    print(f"✅ เสร็จสิ้น! สรุปผลการทำงาน:")
    print(f"📚 มีหนังสือในระบบทั้งหมด: {len(new_database)} เล่ม")
    print(f"🖼️ สร้างปกใหม่เพิ่ม: {new_covers_count} รูป")
    print(f"💾 อัปเดตไฟล์ {db_path} เรียบร้อยแล้ว")
    print("📌 ตอนนี้คุณสามารถ Commit และ Push ขึ้น GitHub Desktop ได้เลยครับ")

if __name__ == "__main__":
    main()