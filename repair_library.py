import os
import shutil
from pdf2image import convert_from_path

# --- ตั้งค่าพาธ ---
pdf_root = r'C:\MyLibrary'
damaged_folder = r'C:\MyLibrary\_damaged_files' # โฟลเดอร์เก็บไฟล์ที่เสีย
poppler_path = r'C:\MyWebProjectsmybook\poppler-25.12.0\Library\bin'

if not os.path.exists(damaged_folder):
    os.makedirs(damaged_folder)

print("--- 🛡️ เริ่มต้นสแกนหาไฟล์ PDF ที่เสียทั่วทั้งห้องสมุด ---")
damaged_count = 0
total_checked = 0

for root, dirs, files in os.walk(pdf_root):
    # ข้ามโฟลเดอร์เก็บไฟล์เสียเอง
    if '_damaged_files' in root: continue
    
    for file in files:
        if file.lower().endswith('.pdf'):
            total_checked += 1
            full_path = os.path.join(root, file)
            
            try:
                # ทดลองนับหน้า (วิธีที่เร็วที่สุดในการเช็คว่าไฟล์พังไหม)
                # ถ้าพัง บรรทัดนี้จะเด้งไปที่ except ทันที
                convert_from_path(full_path, first_page=1, last_page=1, poppler_path=poppler_path)
            except Exception:
                damaged_count += 1
                print(f"❌ พบไฟล์เสีย [{damaged_count}]: {file}")
                
                # ย้ายไฟล์ที่เสียออกไปไว้ที่โฟลเดอร์แยก
                target_path = os.path.join(damaged_folder, file)
                try:
                    shutil.move(full_path, target_path)
                except Exception as e:
                    print(f"⚠️ ย้ายไฟล์ไม่ได้ (อาจเพราะชื่อซ้ำ): {e}")

print("-" * 40)
print(f"📊 สรุปการกู้ภัย:")
print(f"   - ตรวจสอบทั้งหมด: {total_checked} เล่ม")
print(f"   - พบไฟล์เสียและแยกออกไปแล้ว: {damaged_count} เล่ม")
print(f"📂 ไฟล์ที่เสียถูกย้ายไปอยู่ที่: {damaged_folder}")
print("✅ ขั้นตอนต่อไป: ให้คุณรัน gen_db.py เพื่ออัปเดตรายชื่อใหม่ครับ")