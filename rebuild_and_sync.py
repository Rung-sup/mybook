import os
import json
import hashlib
import unicodedata
import urllib.parse
from pdf2image import convert_from_path

# ==========================================
# ⚙️ ตั้งค่า Path (ตรวจสอบให้ตรงกับเครื่องของคุณ)
# ==========================================
library_path = r'C:\MyLibrary' 
db_path = 'database.json'
output_root = 'covers'
base_url = "https://Rung-sup.github.io"
# ตรวจสอบพาธ Poppler ให้ถูกต้อง
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin'

# ==========================================
# 🔑 ฟังก์ชันสร้าง ID รูปปก (รองรับภาษาไทยมาตรฐานเดียวกับ JS)
# ==========================================
def generate_cover_id(relative_path):
    # เปลี่ยน Path เป็นรูปแบบ URL (ใช้ /)
    path_slash = relative_path.replace('\\', '/')
    # จัดการสระภาษาไทย (NFC) และแก้ปัญหาสระอำ/สระซ้อน
    js_str = unicodedata.normalize('NFC', path_slash).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(js_str.encode('utf-8')).hexdigest()

def main():
    if not os.path.exists(output_root):
        os.makedirs(output_root)

    print("🧹 เริ่มต้นกระบวนการ Deep Clean และ Update ระบบ...")
    
    new_db = []
    valid_cover_ids = set()
    new_covers_count = 0
    
    # 1. สแกนไฟล์ PDF ทั้งหมดในเครื่อง
    for root, dirs, files in os.walk(library_path):
        # ข้ามโฟลเดอร์ที่ไม่เกี่ยวข้อง
        dirs[:] = [d for d in dirs if d not in ['covers', '.git', 'node_modules']]
        
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, library_path)
                
                # แยกหมวดหมู่และโฟลเดอร์ย่อย
                parts = rel_path.split(os.sep)
                category = parts[0]
                folder_name = parts[1] if len(parts) > 2 else ""
                
                # สร้าง ID และ URL (แก้ไข SyntaxError f-string เรียบร้อยแล้ว)
                cover_id = generate_cover_id(rel_path)
                valid_cover_ids.add(cover_id)
                
                # แยกการ replace ออกมาข้างนอกเพื่อป้องกัน SyntaxError ใน Python รุ่นเก่า
                url_path_fixed = rel_path.replace('\\', '/')
                final_url = f"{base_url}/{urllib.parse.quote(url_path_fixed)}"

                # 2. จัดการรูปปก
                cat_cover_dir = os.path.join(output_root, category)
                if not os.path.exists(cat_cover_dir):
                    os.makedirs(cat_cover_dir)
                
                cover_file = os.path.join(cat_cover_dir, f"{cover_id}.jpg")
                
                # ถ้ายังไม่มีรูปปก หรือไฟล์เสีย ให้สร้างใหม่
                if not os.path.exists(cover_file):
                    try:
                        print(f"📸 กำลังสร้างปกใหม่: {file_name}")
                        images = convert_from_path(full_path, first_page=1, last_page=1, size=(300, None), poppler_path=poppler_bin_path)
                        if images:
                            images[0].save(cover_file, 'JPEG', quality=80)
                            new_covers_count += 1
                    except Exception as e:
                        print(f"⚠️ ไม่สามารถสร้างปกได้ {file_name}: {e}")

                # เพิ่มข้อมูลลงใน List ฐานข้อมูล
                new_db.append({
                    "title": os.path.splitext(file_name)[0],
                    "url": final_url,
                    "category": category,
                    "folder": folder_name,
                    "cover_id": cover_id
                })

    # 3. บันทึก database.json (เขียนทับด้วยข้อมูลล่าสุดที่ถูกต้อง)
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, ensure_ascii=False, indent=4)

    # 4. ลบไฟล์รูปปกขยะ (ไฟล์ที่ไม่มีตัวตนในเครื่องแล้ว)
    print("🗑️ กำลังลบรูปปกเก่าที่ไม่ได้ใช้งาน...")
    removed_count = 0
    for root, dirs, files in os.walk(output_root):
        for f_name in files:
            if f_name.lower().endswith('.jpg'):
                cid = os.path.splitext(f_name)[0]
                if cid not in valid_cover_ids:
                    try:
                        os.remove(os.path.join(root, f_name))
                        removed_count += 1
                    except:
                        pass

    print("-" * 40)
    print(f"✨ เสร็จสิ้นการล้างบ้านและอัปเดต!")
    print(f"📚 จำนวนหนังสือทั้งหมดในระบบ: {len(new_db)} เล่ม")
    print(f"🖼️ สร้างปกใหม่เพิ่ม: {new_covers_count} รูป")
    print(f"🗑️ ลบรูปปกขยะทิ้ง: {removed_count} รูป")
    print(f"💾 อัปเดตไฟล์ {db_path} เรียบร้อยแล้ว")
    print("\n👉 ตอนนี้คุณสามารถ Commit และ Push ใน GitHub Desktop ได้เลยครับ")

if __name__ == "__main__":
    main()