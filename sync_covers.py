import os
import json

# ตั้งค่าพาธ
db_path = 'database.json'
covers_base_dir = 'covers'

with open(db_path, 'r', encoding='utf-8') as f:
    books = json.load(f)

print("🚀 กำลังตรวจสอบและซิงค์ชื่อไฟล์รูปภาพให้ตรงกับ Database...")

count = 0
for book in books:
    title = book.get('title')
    category = book.get('category')
    cover_id = book.get('cover_id')

    if not cover_id or not category:
        continue

    # พาธโฟลเดอร์หมวดหมู่ เช่น covers/2_Thai_Novel
    cat_dir = os.path.join(covers_base_dir, category)
    
    if os.path.exists(cat_dir):
        # ค้นหาไฟล์ภาพที่มีชื่อเรื่องนั้นๆ (ก่อนที่จะเป็น ID)
        # สคริปต์นี้สมมติว่าคุณมีไฟล์รูปที่ชื่อตรงกับ title อยู่ในโฟลเดอร์นั้น
        for filename in os.listdir(cat_dir):
            # ตรวจสอบว่าไฟล์นี้คือรูปของหนังสือเล่มนี้ (โดยเช็คจากชื่อเรื่องในไฟล์)
            if title in filename and not filename.startswith(cover_id):
                old_file = os.path.join(cat_dir, filename)
                new_file = os.path.join(cat_dir, f"{cover_id}.jpg")
                
                try:
                    os.rename(old_file, new_file)
                    print(f"✅ เปลี่ยนชื่อ: {title} -> {cover_id}.jpg")
                    count += 1
                except Exception as e:
                    print(f"❌ พลาด: {title} ({e})")

print("-" * 40)
print(f"🎉 เสร็จสิ้น! แก้ไขชื่อไฟล์ให้ตรงกับ ID ไปทั้งหมด {count} ไฟล์")
print("⚠️ อย่าลืม Commit และ Push ใน GitHub Desktop นะครับ!")