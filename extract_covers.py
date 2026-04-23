import os
import hashlib
from pdf2image import convert_from_path

# --- ตั้งค่า Path ---
pdf_parent_folder = r'C:\MyLibrary' 
output_root = 'covers' 
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin'

if not os.path.exists(output_root):
    os.makedirs(output_root)

print("--- 🚀 เริ่มเจนรูปปกแบบแยกหมวดหมู่ ---")
count = 0

for root, dirs, files in os.walk(pdf_parent_folder):
    for filename in files:
        if filename.lower().endswith(".pdf"):
            full_path = os.path.join(root, filename)
            # หาชื่อหมวด (เช่น 1_PetchPraUma) จากโฟลเดอร์ชั้นแรก
            rel_to_parent = os.path.relpath(full_path, pdf_parent_folder)
            parts = rel_to_parent.split(os.sep)
            category_name = parts[0] # หมวดหลัก
            
            # สร้างโฟลเดอร์หมวดใน covers
            category_folder = os.path.join(output_root, category_name)
            if not os.path.exists(category_folder):
                os.makedirs(category_folder)

            # สร้าง ID จาก Path สัมพัทธ์ (เพื่อใช้เรียกใน JS)
            rel_path_url = rel_to_parent.replace("\\", "/")
            image_id = hashlib.md5(rel_path_url.encode('utf-8')).hexdigest()
            output_path = os.path.join(category_folder, f"{image_id}.jpg")

            if os.path.exists(output_path): continue

            try:
                images = convert_from_path(full_path, first_page=1, last_page=1, size=(300, None), poppler_path=poppler_bin_path)
                if images:
                    images[0].save(output_path, 'JPEG', quality=80)
                    count += 1
                    print(f"[{count}] หมวด {category_name} -> {image_id}.jpg")
            except Exception as e:
                print(f"❌ Error: {filename} -> {e}")

print(f"\n--- ✨ เสร็จสิ้น! แยกหมวดหมู่เรียบร้อยในโฟลเดอร์ covers ---")

