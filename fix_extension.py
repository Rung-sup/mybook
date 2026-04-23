import os

# ระบุชื่อโฟลเดอร์หลักที่เก็บรูปหน้าปก
covers_dir = 'covers'

print("🔍 กำลังตรวจสอบและแก้ไขนามสกุลไฟล์ให้เป็นตัวพิมพ์เล็ก (.jpg) ทั้งหมด...")

changed_count = 0
total_files = 0

# วนลูปเข้าไปในทุกโฟลเดอร์ย่อย (เช่น 1_PetchPraUma, 2_Thai_Novel)
for root, dirs, files in os.walk(covers_dir):
    for filename in files:
        total_files += 1
        
        # แยกชื่อไฟล์ และ นามสกุล ออกจากกัน
        name, ext = os.path.splitext(filename)
        
        # ถ้านามสกุลไม่ใช่ .jpg ตัวพิมพ์เล็กเป๊ะๆ (เช่น เป็น .JPG, .jpeg, .PNG)
        if ext != '.jpg':
            old_path = os.path.join(root, filename)
            # บังคับเปลี่ยนเป็น .jpg ตัวเล็ก
            new_path = os.path.join(root, name + '.jpg')
            
            # ทำการเปลี่ยนชื่อไฟล์
            os.rename(old_path, new_path)
            changed_count += 1
            print(f"🔄 เปลี่ยน: {filename} -> {name}.jpg")

print("-" * 40)
print(f"✅ ตรวจสอบไฟล์ทั้งหมด {total_files} ไฟล์")
print(f"✅ ทำการแก้ไขนามสกุลไฟล์ไปทั้งหมด {changed_count} ไฟล์")
print("🎉 ตอนนี้ไฟล์ทั้งหมดเป็น .jpg (ตัวพิมพ์เล็ก) 100% พร้อมทะลวงด่าน iOS แล้วครับ!")