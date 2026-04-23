import os
import json
import hashlib
import unicodedata
from pdf2image import convert_from_path

# ==========================================
# ⚙️ ตั้งค่า Path (ตรวจสอบให้ตรงกับเครื่องของคุณ)
# ==========================================
library_path = r'C:\MyLibrary' 
db_path = 'database.json'
output_root = 'covers'
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin'

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    js_str = unicodedata.normalize('NFC', path_slash).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(js_str.encode('utf-8')).hexdigest()

def fix_covers():
    if not os.path.exists(db_path):
        print("❌ ไม่พบไฟล์ database.json")
        return

    with open(db_path, 'r', encoding='utf-8') as f:
        books = json.load(f)

    print(f"🔍 เริ่มตรวจสอบปกหนังสือทั้งหมด {len(books)} รายการ...")
    
    # สร้าง Map เพื่อเก็บ "ปกตัวแทน" ของแต่ละโฟลเดอร์ย่อย
    folder_representatives = {} 
    fixed_count = 0

    # รอบที่ 1: ค้นหาว่าแต่ละโฟลเดอร์ย่อย มีปกเล่มไหนที่ใช้งานได้บ้าง (เพื่อเอามาเป็นตัวแทน)
    for book in books:
        folder_key = f"{book['category']}/{book['folder']}" if book['folder'] else None
        if folder_key:
            cover_path = os.path.join(output_root, book['category'], f"{book['cover_id']}.jpg")
            if os.path.exists(cover_path) and folder_key not in folder_representatives:
                folder_representatives[folder_key] = cover_path

    # รอบที่ 2: ซ่อมแซมเล่มที่ปกหาย
    for book in books:
        category = book['category']
        cover_id = book['cover_id']
        folder_key = f"{category}/{book['folder']}" if book['folder'] else None
        
        target_cover_dir = os.path.join(output_root, category)
        target_cover_path = os.path.join(target_cover_dir, f"{cover_id}.jpg")

        # ถ้าไม่พบไฟล์ปก
        if not os.path.exists(target_cover_path):
            print(f"⚠️ พบปกหาย: {book['title']}")
            
            # ทางเลือกที่ 1: ดึงปกจากเล่มแรกในโฟลเดอร์เดียวกันมาแสดงแทน (Copy ไฟล์)
            if folder_key and folder_key in folder_representatives:
                try:
                    import shutil
                    shutil.copy(folder_representatives[folder_key], target_cover_path)
                    print(f"   ✅ ใช้ปกตัวแทนจากโฟลเดอร์ {book['folder']}")
                    fixed_count += 1
                    continue
                except:
                    pass

            # ทางเลือกที่ 2: ถ้าไม่มีตัวแทน ให้สร้างใหม่จากไฟล์ PDF จริงๆ
            # ค้นหาไฟล์ PDF จริงในเครื่อง
            pdf_rel_path = urllib.parse.unquote(book['url'].replace("https://Rung-sup.github.io/", ""))
            pdf_full_path = os.path.join(library_path, pdf_rel_path.replace('/', os.sep))

            if os.path.exists(pdf_full_path):
                try:
                    print(f"   📸 กำลังเจนปกใหม่จาก PDF...")
                    images = convert_from_path(pdf_full_path, first_page=1, last_page=1, size=(300, None), poppler_path=poppler_bin_path)
                    if images:
                        if not os.path.exists(target_cover_dir): os.makedirs(target_cover_dir)
                        images[0].save(target_cover_path, 'JPEG', quality=80)
                        fixed_count += 1
                except Exception as e:
                    print(f"   ❌ ไม่สามารถสร้างปกได้: {e}")
            else:
                print(f"   ❌ ไม่พบไฟล์ PDF ต้นฉบับที่: {pdf_full_path}")

    print("-" * 40)
    print(f"✨ ซ่อมแซมเสร็จสิ้น! แก้ไขปกไปทั้งหมด: {fixed_count} รายการ")

if __name__ == "__main__":
    import urllib.parse
    fix_covers()