import os
import hashlib
from PyPDF2 import PdfReader

SOURCE_DIR = r'C:\MyLibrary'
REPORT_FILE = r'C:\MyBook_Test\library_report.txt'

def get_file_hash(path):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except: return None

def is_pdf_valid(path):
    try:
        with open(path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF' # เช็คแค่ Header เพื่อความยืดหยุ่นตามที่คุณต้องการ
    except: return False

seen_hashes = {}
large_files = []
corrupt_files = []
duplicate_files = []

print("🔍 กำลังสแกน MyLibrary โปรดรอสักครู่...")

for root, dirs, files in os.walk(SOURCE_DIR):
    for filename in files:
        if not filename.lower().endswith('.pdf'): continue
        file_path = os.path.join(root, filename)
        
        # 1. เช็คขนาด
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > 90:
            large_files.append(f"{filename} ({size_mb:.2f} MB) -> {root}")
            
        # 2. เช็คไฟล์ซ้ำ
        f_hash = get_file_hash(file_path)
        if f_hash in seen_hashes:
            duplicate_files.append(f"{filename} (ซ้ำกับ {seen_hashes[f_hash]}) -> {root}")
        else:
            seen_hashes[f_hash] = filename
            
        # 3. เช็คความถูกต้อง (Header)
        if not is_pdf_valid(file_path):
            corrupt_files.append(f"{filename} -> {root}")

# เขียนรายงานลงไฟล์
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write("=== รายงานการตรวจสอบ MyLibrary ===\n\n")
    f.write(f"⚠️ ไฟล์ใหญ่เกิน 90MB ({len(large_files)} ไฟล์):\n" + "\n".join(large_files) + "\n\n")
    f.write(f"👥 ไฟล์ซ้ำ ({len(duplicate_files)} ไฟล์):\n" + "\n".join(duplicate_files) + "\n\n")
    f.write(f"❌ ไฟล์ที่โครงสร้างไม่ใช่ PDF ({len(corrupt_files)} ไฟล์):\n" + "\n".join(corrupt_files) + "\n")

print(f"✅ สแกนเสร็จสิ้น! ดูผลลัพธ์ได้ที่: {REPORT_FILE}")