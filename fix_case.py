import os
import json

covers_dir = 'covers'
db_path = 'database.json'

print("🔍 กำลังบังคับให้ชื่อไฟล์รูปและฐานข้อมูลเป็นตัวพิมพ์เล็กทั้งหมด...")

# 1. เปลี่ยนชื่อไฟล์รูปภาพทุกรูปให้เป็นตัวพิมพ์เล็ก
changed_files = 0
for root, dirs, files in os.walk(covers_dir):
    for filename in files:
        lower_name = filename.lower()
        if filename != lower_name:
            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, lower_name)
            os.rename(old_path, new_path)
            changed_files += 1

# 2. เปลี่ยนค่า cover_id ใน Database ให้เป็นตัวพิมพ์เล็กด้วย
with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

for book in db:
    if book.get('cover_id'):
        book['cover_id'] = book['cover_id'].lower()

with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False, indent=4)

print("-" * 40)
print(f"✅ เปลี่ยนชื่อไฟล์รูปภาพเป็นตัวเล็กล้วนสำเร็จ: {changed_files} ไฟล์")
print("✅ อัปเดตฐานข้อมูล database.json ให้ตรงกันเรียบร้อย!")
print("🎉 นำไฟล์รูปที่เปลี่ยนชื่อ และ database.json ไปอัปโหลดขึ้น GitHub ได้เลยครับ!")