import os
from pdf2image import convert_from_path

# --- 1. ตั้งค่าโฟลเดอร์หลักที่คุมทุกหมวดหนังสือไว้ ---
# ก๊อปปี้ที่อยู่โฟลเดอร์ใหญ่สุดที่มีหมวดหนังสือย่อยๆ อยู่ข้างในมาวางครับ
pdf_parent_folder = r'C:\MyLibrary'   

# โฟลเดอร์ปลายทางสำหรับเก็บรูปปกทั้งหมด
output_folder = 'covers' 

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# --- 2. ระบุทางไปหา Poppler (bin) เหมือนเดิมครับ ---
poppler_bin_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin' 

print("--- 🚀 เริ่มปฏิบัติการ 'มุด' ดึงหน้าปก 1,200 เล่ม ---")
count = 0

# ใช้ os.walk เพื่อ "มุด" ลงไปในทุกโฟลเดอร์ย่อย
for root, dirs, files in os.walk(pdf_parent_folder):
    for filename in files:
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(root, filename)
            # ตั้งชื่อรูปภาพตามชื่อไฟล์ PDF
            image_name = filename.replace(".pdf", ".jpg").replace(".PDF", ".jpg")
            output_path = os.path.join(output_folder, image_name)

            # เช็คก่อนว่าเคยทำไปหรือยัง (กันพลาดถ้าต้องรันซ้ำ)
            if os.path.exists(output_path):
                continue

            try:
                # สั่งแปลงหน้าแรกเป็นภาพจิ๋ว (300px) เพื่อความลื่นไหลของแอป
                images = convert_from_path(
                    pdf_path, 
                    first_page=1, 
                    last_page=1, 
                    size=(300, None), 
                    poppler_path=poppler_bin_path
                )
                
                if images:
                    images[0].save(output_path, 'JPEG', quality=80)
                    count += 1
                    print(f"[{count}] สำเร็จ: {image_name}")
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดกับไฟล์ {filename}: {e}")

print(f"\n--- ✨ เสร็จเรียบร้อย! ดึงหน้าปกได้ทั้งหมด {count} เล่ม ---")
print(f"รูปทั้งหมดอยู่ที่: {os.path.abspath(output_folder)}")