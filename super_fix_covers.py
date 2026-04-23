import os
import json
import hashlib
import unicodedata
import shutil
from pdf2image import convert_from_path

# ==========================================
# ⚙️ ตั้งค่า Path (ตรวจสอบให้ตรงกับเครื่องของคุณ)
# ==========================================
library_path = r'C:\MyLibrary' 
db_path = 'database.json'
output_root = 'covers'
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin'

def generate_cover_id(relative_path):
    # สูตรมาตรฐานรองรับภาษาไทย (NFC + แก้สระอำ)
    path_slash = relative_path.replace('\\', '/')
    js_str = unicodedata.normalize('NFC', path_slash).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(js_str.encode('utf-8')).hexdigest()

def super_fix():
    if not os.path.exists(db_path):
        print("❌ ไม่พบไฟล์ database.json")
        return

    with open(db_path, 'r', encoding='utf-8') as f:
        books = json.load(f)

    print(f"🔍 เริ่มการตรวจสอบระดับลึก {len(books)} รายการ...")
    
    # สร้างคลังเก็บ "ปกตัวอย่าง" ของแต่ละโฟลเดอร์ย่อยไว้ล่วงหน้า
    folder_samples = {}
    
    # สแกนหาปกที่มีอยู่แล้วจริงๆ ในโฟลเดอร์ covers ทั้งหมด
    print("📁 สแกนไฟล์รูปภาพที่มีอยู่แล้ว...")
    actual_files = {}
    for root, dirs, files in os.walk(output_root):
        for f in files:
            if f.endswith('.jpg'):
                actual_files[os.path.splitext(f)[0]] = os.path.join(root, f)

    fixed_by_copy = 0
    fixed_by_gen = 0
    
    for book in books:
        category = book['category']
        folder = book['folder']
        cover_id = book['cover_id']
        title = book['title']
        
        target_dir = os.path.join(output_root, category)
        target_path = os.path.join(target_dir, f"{cover_id}.jpg")

        # ถ้าในโฟลเดอร์ปลายทางไม่มีรูปปกที่ชื่อตรงกับ ID
        if not os.path.exists(target_path):
            print(f"❌ ปกหาย: [{category}] {title}")
            
            # ขั้นตอนที่ 1: ลองหาว่ามีไฟล์รูปปกนี้ "หลง" อยู่โฟลเดอร์อื่นไหม (ถ้ามีให้ย้ายมา)
            if cover_id in actual_files:
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy(actual_files[cover_id], target_path)
                print(f"   ✅ แก้ไข: พบไฟล์เดิมแต่ผิดที่ จึงคัดลอกมาวางให้ถูกหมวด")
                fixed_by_copy += 1
                continue

            # ขั้นตอนที่ 2: ถ้าไม่มีจริงๆ ลองดูว่ามี "เพื่อน" ในโฟลเดอร์เดียวกันที่มีปกไหม
            folder_key = f"{category}/{folder}" if folder else None
            sample_cover = None
            if folder_key:
                # ค้นหาตัวแทนใน Folder เดียวกัน
                for b in books:
                    if f"{b['category']}/{b['folder']}" == folder_key:
                        p = os.path.join(output_root, b['category'], f"{b['cover_id']}.jpg")
                        if os.path.exists(p):
                            sample_cover = p
                            break
            
            if sample_cover:
                shutil.copy(sample_cover, target_path)
                print(f"   ✅ แก้ไข: ใช้ปกตัวแทนจากเพื่อนในโฟลเดอร์ [{folder}]")
                fixed_by_copy += 1
            else:
                # ขั้นตอนที่ 3: ถ้าสิ้นหวังจริงๆ ให้เจนใหม่จาก PDF
                try:
                    # พยายามหาไฟล์ PDF จาก URL ใน Database
                    import urllib.parse
                    # ตัดส่วน URL ออกให้เหลือแต่ Path ในเครื่อง
                    rel_pdf = urllib.parse.unquote(book['url'].replace("https://Rung-sup.github.io/", ""))
                    full_pdf = os.path.join(library_path, rel_pdf.replace('/', os.sep))

                    if os.path.exists(full_pdf):
                        print(f"   📸 แก้ไข: กำลังเจนปกใหม่จากไฟล์ PDF...")
                        images = convert_from_path(full_pdf, first_page=1, last_page=1, size=(300, None), poppler_path=poppler_bin_path)
                        if images:
                            os.makedirs(target_dir, exist_ok=True)
                            images[0].save(target_path, 'JPEG', quality=80)
                            fixed_by_gen += 1
                    else:
                        print(f"   ⚠️ ข้าม: ไม่พบไฟล์ PDF ต้นฉบับเพื่อสร้างปก")
                except Exception as e:
                    print(f"   ❌ ข้าม: เกิดข้อผิดพลาดในการสร้างปก ({e})")

    print("-" * 40)
    print(f"🚀 ผลการซ่อมแซม:")
    print(f"📦 ย้าย/คัดลอกปกที่สับสน: {fixed_by_copy} รายการ")
    print(f"🎨 เจนปกใหม่จาก PDF: {fixed_by_gen} รายการ")
    print(f"✨ ตอนนี้ไฟล์รูปในเครื่องควรจะตรงกับแอป 100% แล้วครับ")

if __name__ == "__main__":
    super_fix()
    