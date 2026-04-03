import os
import hashlib # ใช้ตัวนี้เพื่อสร้างรหัสสั้นๆ
from pdf2image import convert_from_path

# --- 1. ตั้งค่า Path เหมือนเดิม ---
pdf_parent_folder = r'C:\MyLibrary' # ตรวจสอบให้ชัวร์ว่าชี้ไปที่โฟลเดอร์หนังสือ
output_folder = 'covers' 
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin' # ชี้ไปที่ bin ของ poppler

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

print("--- 🚀 เริ่มเจนรูปปกแบบใช้ MD5 ID (รหัสสั้นพิเศษ) ---")
count = 0

for root, dirs, files in os.walk(pdf_parent_folder):
    for filename in files:
        if filename.lower().endswith(".pdf"):
            # 1. สร้าง Path สัมพัทธ์
            rel_path = os.path.relpath(os.path.join(root, filename), pdf_parent_folder)
            rel_path = rel_path.replace("\\", "/")
            
            # 2. สร้าง ID แบบสั้น (MD5) - จะได้รหัส 32 ตัวอักษรเสมอ ไม่ว่าชื่อไฟล์จะยาวแค่ไหน
            image_id = hashlib.md5(rel_path.encode('utf-8')).hexdigest()
            output_path = os.path.join(output_folder, f"{image_id}.jpg")

            if os.path.exists(output_path): continue

            try:
                pdf_full_path = os.path.join(root, filename)
                images = convert_from_path(pdf_full_path, first_page=1, last_page=1, size=(300, None), poppler_path=poppler_bin_path)
                if images:
                    images[0].save(output_path, 'JPEG', quality=80)
                    count += 1
                    print(f"[{count}] สำเร็จ: {image_id}.jpg (จากไฟล์: {filename})")
            except Exception as e:
                print(f"❌ Error ไฟล์ {filename}: {e}")

print(f"\n--- ✨ เสร็จเรียบร้อย! สร้างปกได้ทั้งหมด {count} เล่ม ---")