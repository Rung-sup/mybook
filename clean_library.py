import os
import json
import hashlib
import unicodedata

# ==========================================
# ⚙️ ตั้งค่า Path
# ==========================================
library_path = r'C:\MyLibrary'
output_root = 'covers'
db_path = 'database.json'

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    js_str = unicodedata.normalize('NFC', path_slash).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(js_str.encode('utf-8')).hexdigest()

def clean_system():
    print("🧹 เริ่มต้นการทำความสะอาดระบบ...")
    
    # 1. รวบรวมข้อมูลหนังสือที่มีอยู่จริง ณ ปัจจุบัน
    existing_books_ids = set()
    valid_books_in_db = []
    
    print("🔍 ตรวจสอบไฟล์ในเครื่อง...")
    for root, dirs, files in os.walk(library_path):
        dirs[:] = [d for d in dirs if d not in ['covers', '.git']]
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, library_path)
                cover_id = generate_cover_id(rel_path)
                existing_books_ids.add(cover_id)
                
                # เก็บข้อมูลไว้เตรียมอัปเดต Database
                valid_books_in_db.append(rel_path) # ในที่นี้เราจะเน้นเช็ค ID เป็นหลัก

    # 2. ทำความสะอาดไฟล์รูปปก (Covers)
    print("🖼️ กำลังตรวจสอบโฟลเดอร์รูปปก...")
    removed_covers = 0
    for root, dirs, files in os.walk(output_root):
        for file_name in files:
            if file_name.lower().endswith('.jpg'):
                current_id = os.path.splitext(file_name)[0]
                # ถ้า ID รูปภาพนี้ไม่อยู่ในรายการหนังสือที่มีอยู่จริง = ลบทิ้ง
                if current_id not in existing_books_ids:
                    try:
                        os.remove(os.path.join(root, file_name))
                        removed_covers += 1
                    except:
                        pass

    # 3. ตรวจสอบความถูกต้องของ database.json
    print("📄 กำลังกรองฐานข้อมูลที่ซ้ำซ้อนหรือเสีย...")
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try:
                current_db = json.load(f)
            except:
                current_db = []
        
        # กรองเฉพาะเล่มที่ไฟล์ PDF ยังมีตัวตนอยู่จริงเท่านั้น
        cleaned_db = [book for book in current_db if book.get('cover_id') in existing_books_ids]
        
        # บันทึกกลับ
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_db, f, ensure_ascii=False, indent=4)

    print("-" * 40)
    print(f"✨ ทำความสะอาดเสร็จสิ้น!")
    print(f"🗑️ ลบรูปปกขยะทิ้งไป: {removed_covers} รูป")
    print(f"📚 คงเหลือหนังสือที่ใช้งานได้จริง: {len(existing_books_ids)} เล่ม")
    print("💡 แนะนำ: รันสคริปต์ update_library.py (ตัวที่ผมให้ก่อนหน้า) อีกครั้งเพื่อให้ข้อมูลสมบูรณ์ที่สุด")

if __name__ == "__main__":
    clean_system()ยั