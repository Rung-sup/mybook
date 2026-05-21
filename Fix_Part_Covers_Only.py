import os
import sys
import json
import shutil
import hashlib
import unicodedata
import re

# ==========================================
# ⚙️ CONFIGURATION (ตั้งค่าพิกัดหลัก)
# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'

if os.path.exists(POPPLER_PATH):
    from pdf2image import convert_from_path
else:
    print("❌ ไม่พบพิกัด Poppler กรุณาตรวจสอบ CONFIGURATION")
    sys.exit()

# ==========================================
# 🧰 UTILITIES FUNCTIONS
# ==========================================
def normalize_text(text):
    return unicodedata.normalize('NFC', text.strip()).replace('\u0e4d\u0e32', '\u0e33')

def generate_cover_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

# ==========================================
# ⚡ รันระบบซ่อมปกไฟล์พาร์ทแบบถอดรหัส ID แม่นยำ
# ==========================================
def fix_part_covers_precise():
    print("=======================================================")
    print("🎯 เริ่มต้นระบบซ่อมปกไฟล์พาร์ท (จับคู่รหัส ID และแชร์ปกเล่มแรก) 🎯")
    print("=======================================================")
    
    if not os.path.exists(LIBRARY_ROOT):
        print("❌ ไม่พบโฟลเดอร์ MyLibrary")
        return

    covers_root_dir = os.path.join(DB_DIR, 'covers')
    count_generated = 0
    count_copied = 0

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers', '.github']: continue

        print(f"📁 กำลังค้นหาไฟล์พาร์ทในห้อง: {cat_folder}...")
        
        # ดิกสำหรับเก็บรูปปกต้นแบบ: { "ชื่อเรื่อง_lower": "พิกัดไฟล์รูปปกหลัก.jpg" }
        part_one_images = {}
        # รายการรอเคลียร์รูปปกของ Part 2 เป็นต้นไป
        pending_parts = []

        # 🔄 รอบที่ 1: ตามล่าหาเล่มที่เป็น _Part_1 เพื่อเปิดไฟล์เจนปกจริงออกมารอไว้ก่อน
        for root, dirs, files in os.walk(cat_path):
            for f in files:
                if not f.lower().endswith('.pdf'): continue
                
                # ใช้ Regex ตรวจจับรูปแบบไฟล์หั่นพาร์ท
                part_match = re.search(r'^(.*)_part_(\d+)$', os.path.splitext(f)[0], flags=re.IGNORECASE)
                
                if part_match:
                    full_p = os.path.join(root, f)
                    rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                    c_id = generate_cover_id(rel_from_library) # คำนวณรหัส ID แบบเดียวกับสคริปต์หลัก
                    
                    base_story = normalize_text(part_match.group(1)).lower()
                    part_num = int(part_match.group(2))
                    
                    cover_dir = os.path.join(covers_root_dir, cat_folder)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    
                    if part_num == 1:
                        # บังคับเปิด PDF และเจนรูปปกจริงเพื่อเซฟเป็นชื่อรหัส MD5 ให้แอปวิ่งมาเจอ
                        try:
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs:
                                imgs[0].save(cover_out, 'JPEG', quality=85)
                                part_one_images[base_story] = cover_out  # จำพิกัดรูปปกหลักไว้
                                count_generated += 1
                        except Exception as e:
                            print(f"   ❌ ไม่สามารถเจนปกต้นแบบพาร์ท 1 ได้ [{f}]: {e}")
                    else:
                        # ถ้าเป็น Part 2 ขึ้นไป ให้จำข้อมูลและรหัส ID รอไว้ก่อน
                        pending_parts.append({
                            "base_story": base_story,
                            "filename": f,
                            "cover_out": cover_out
                        })

        # 🔄 รอบที่ 2: วนลูปแจกจ่ายรูปปกต้นแบบให้พาร์ทอื่น ๆ (ไม่ต้องเปิดไฟล์ PDF ซ้ำ)
        for part in pending_parts:
            b_story = part["base_story"]
            target_img = part["cover_out"]
            
            if b_story in part_one_images and os.path.exists(part_one_images[b_story]):
                try:
                    # คัดลอกรูปจากพาร์ท 1 ไปเป็นชื่อรหัส ID ของพาร์ทนั้น ๆ ทันที
                    shutil.copy2(part_one_images[b_story], target_img)
                    count_copied += 1
                except Exception as e:
                    print(f"   ⚠️  ก๊อปปี้ปกให้ไฟล์ {part['filename']} พลาด: {e}")
            else:
                # กรณีหา Part_1 ของตัวเองไม่เจอจริง ๆ ให้เจนปกจากหน้าแรกตัวเองเป็นตัวสำรอง
                try:
                    # ค้นหาไฟล์ PDF ของตัวเองเพื่อเปิดทำปก
                    for root, dirs, files in os.walk(cat_path):
                        if part['filename'] in files:
                            full_p = os.path.join(root, part['filename'])
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs:
                                imgs[0].save(target_img, 'JPEG', quality=85)
                                count_generated += 1
                except:
                    pass

    print("\n=======================================================")
    print(f"✨ ซ่อมแซมระบบรูปปกไฟล์พาร์ทเรียบร้อยแล้วครับคุณ Runnara!")
    print(f"📸 สร้างรูปปกต้นแบบ (รหัส ID): {count_generated} รูป")
    print(f"👯 ก๊อปปี้กระจายให้พาร์ทย่อย (รหัส ID): {count_copied} รูป")
    print("=======================================================")

if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    fix_part_covers_precise()