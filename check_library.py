import os
import shutil
import hashlib
from PyPDF2 import PdfReader

# --- การตั้งค่าเส้นทาง ---
SOURCE_DIR = r'C:\MyLibrary'
TARGET_LARGE = r'F:\ไฟล์ใหญ่เกิน90mb'
TARGET_DUPLICATE = r'F:\ไฟล์ซ้ำ'
TARGET_CORRUPT = r'F:\ไฟล์เสีย'

# สร้างโฟลเดอร์ปลายทาง
for d in [TARGET_LARGE, TARGET_DUPLICATE, TARGET_CORRUPT]:
    os.makedirs(d, exist_ok=True)

def get_file_hash(path):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except:
        return None

def check_pdf_corrupt(path):
    try:
        with open(path, 'rb') as f:
            reader = PdfReader(f)
            if len(reader.pages) > 0:
                return False
    except:
        return True
    return True

def safe_move(src, dst_dir, filename):
    """ฟังก์ชันย้ายไฟล์ข้าม Drive ที่ปลอดภัยและไม่ทำให้สคริปต์หยุดทำงาน"""
    dst_path = os.path.join(dst_dir, filename)
    try:
        # ใช้ copy2 เพื่อรักษา metadata แล้วค่อยลบ
        shutil.copy2(src, dst_path)
        os.remove(src)
        return True
    except Exception as e:
        print(f"❌ ไม่สามารถย้ายไฟล์ {filename} ได้: {e}")
        return False

seen_hashes = {}
print("🔍 เริ่มตรวจสอบไฟล์ใน MyLibrary (เวอร์ชันแก้ไขการย้ายข้าม Drive)...")

for root, dirs, files in os.walk(SOURCE_DIR):
    for filename in files:
        if not filename.lower().endswith('.pdf'):
            continue
            
        file_path = os.path.join(root, filename)
        
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # 1. ตรวจสอบไฟล์ใหญ่เกิน 90MB
            if file_size_mb > 90:
                print(f"⚠️  ไฟล์ใหญ่ ({file_size_mb:.2f}MB): {filename}")
                safe_move(file_path, TARGET_LARGE, filename)
                continue

            # 2. ตรวจสอบไฟล์ซ้ำ
            f_hash = get_file_hash(file_path)
            if f_hash:
                if f_hash in seen_hashes:
                    print(f"👥 ไฟล์ซ้ำ (ซ้ำกับ {seen_hashes[f_hash]}): {filename}")
                    safe_move(file_path, TARGET_DUPLICATE, filename)
                    continue
                else:
                    seen_hashes[f_hash] = filename

            # 3. ตรวจสอบไฟล์เสีย
            if check_pdf_corrupt(file_path):
                print(f"❌ ไฟล์เสีย: {filename}")
                safe_move(file_path, TARGET_CORRUPT, filename)
                continue
                
        except Exception as e:
            print(f"❗ เกิดข้อผิดพลาดกับไฟล์ {filename}: {e}")

print("\n✅ ตรวจสอบเสร็จสิ้น!")