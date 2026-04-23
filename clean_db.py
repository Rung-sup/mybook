import json
import os

# 1. ตั้งค่าชื่อไฟล์และโฟลเดอร์
db_path = 'database.json'
covers_dir = 'covers'
output_path = 'database_cleaned.json'

print("🔍 กำลังตรวจสอบไฟล์รูปหน้าปกเทียบกับ Database...")

# โหลดข้อมูล Database เดิม
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

cleaned_db = []
missing_count = 0
found_count = 0

# 2. วนลูปเช็คหนังสือทีละเล่ม
for book in db:
    cover_id = book.get('cover_id', '')
    category = book.get('category', '')

    # ถ้าใน DB ระบุว่ามีรูปปก ให้ไปเดินหาไฟล์จริง
    if cover_id:
        # ต่อชื่อ Path ให้ตรงกับโครงสร้าง เช่น covers/2_Thai_Novel/12345.jpg
        cover_file_path = os.path.join(covers_dir, category, f"{cover_id}.jpg")
        
        # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        if not os.path.exists(cover_file_path):
            print(f"❌ ไม่พบรูปภาพ: {cover_id}.jpg (ของหนังสือ: {book.get('title')})")
            # ถ้าไม่เจอรูป ให้ล้างค่า cover_id ทิ้ง แอปจะได้ไม่พยายามโหลด
            book['cover_id'] = ""
            missing_count += 1
        else:
            found_count += 1

    cleaned_db.append(book)

# 3. บันทึกเป็น Database ตัวใหม่ที่สะอาดหมดจด
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(cleaned_db, f, ensure_ascii=False, indent=4)

print("-" * 40)
print("✅ ทำความสะอาดเสร็จสิ้น!")
print(f"   - พบรูปหน้าปกที่ถูกต้อง: {found_count} เล่ม")
print(f"   - ลบรายชื่อรูปที่ไม่มีอยู่จริงออกไป: {missing_count} เล่ม")
print(f"🎉 ไฟล์ใหม่ของคุณคือ '{output_path}' ให้นำไปเปลี่ยนชื่อเป็น database.json เพื่อใช้งานได้เลยครับ")