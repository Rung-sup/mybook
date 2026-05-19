import os
import sys
import json
import shutil
import hashlib
import subprocess
import time
import re
import pypdf # ใช้สำหรับตรวจไฟล์เสียอย่างละเอียด

# ==========================================
# CONFIG
# ==========================================
DRY_RUN = False  # 🟡 True = ทดสอบดูระบบ / False = รันย้ายไฟล์อัปเดตระบบจริงและ Push ทันที

PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'

# โฟลเดอร์ปลายทางสำหรับคัดแยกไฟล์ปัญหา (ในไดรฟ์ F:)
DEST_BAD_FOLDER = r"f:\ไฟล์พัง"
DEST_DUP_FOLDER = r"f:\ไฟล์ซ้ำ"

# ขีดจำกัดความปลอดภัยสำหรับระบบ (ป้องกันชนเพดาน Git/GitHub)
MAX_FILE_SIZE_MB = 90       # ไฟล์เดี่ยวๆ เกินนี้จะถูกบล็อกข้ามไปก่อน
BATCH_PUSH_LIMIT_MB = 90    # รวมไฟล์สะสมครบขนาดเท่านี้ จะทำการ Push ออกไปหนึ่งรอบ

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
# ==========================================

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def get_file_hash(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def move_to_safety(file_path, dest_folder):
    """ฟังก์ชันย้ายไฟล์ไปโฟลเดอร์ปลอดภัยโดยไม่ให้ชื่อซ้ำกัน"""
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(dest_folder, filename)
    
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_folder, f"{base}_{counter}{ext}")
        counter += 1
    
    try:
        shutil.move(file_path, dest_path)
        print(f"   ➡️ ย้ายสำเร็จ -> {os.path.basename(dest_path)}")
        return True
    except Exception as e:
        print(f"   ❌ ย้ายไฟล์ไม่สำเร็จ: {e}")
        return False

def extract_pdf_cover_as_md5(pdf_path, output_dir):
    """ดึงหน้าแรกของ PDF ออกมาเป็นภาพปก และเซฟชื่อไฟล์ด้วยค่า MD5 ของปกนั้น"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            if len(reader.pages) > 0:
                first_page = reader.pages[0]
                if '/Resources' in first_page and '/XObject' in first_page['/Resources']:
                    xobject = first_page['/Resources']['/XObject'].get_object()
                    for obj_name in xobject:
                        obj = xobject[obj_name]
                        if obj['/Subtype'] == '/Image':
                            data = obj.get_data()
                            cover_md5 = hashlib.md5(data).hexdigest()
                            cover_filename = f"{cover_md5}.jpg"
                            cover_path = os.path.join(output_dir, cover_filename)
                            
                            if not os.path.exists(cover_path):
                                with open(cover_path, 'wb') as img_f:
                                    img_f.write(data)
                            return cover_filename
    except Exception as e:
        print(f"   ⚠️ ไม่สามารถสกัดหน้าปกจาก {os.path.basename(pdf_path)} ได้: {e}")
    return None

def execute_git_push(batch_number):
    """ฟังก์ชันรันคำสั่ง Git เพื่อ Commit และ Push ชุดปัจจุบันออกไป"""
    print(f"\n🚀 [Git Sync] ทำการดันไฟล์ขึ้น GitHub - รอบคัดแยกที่ #{batch_number}")
    if DRY_RUN:
        print("   🟡 [DRY RUN] ข้ามขั้นตอนส่งคำสั่ง Git จริง")
        return True
        
    try:
        # สั่งเพิ่มไฟล์ทั้งหมดเข้าสเตจ (รวมฐานข้อมูลและโฟลเดอร์ปก)
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit งานพร้อมระบุช่วงเวลาและ Batch ที่ทำสำเร็จ
        commit_msg = f"Update digital library batch #{batch_number} ({time.strftime('%Y-%m-%d %H:%M')})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # ยิง Push ดันขึ้น GitHub ทันที
        subprocess.run(["git", "push"], check=True)
        print(f"   ✅ Git Push รอบที่ #{batch_number} สำเร็จเสร็จสิ้น!")
        return True
    except subprocess.CalledProcessError as ge:
        print(f"   ❌ Git ทำงานขัดข้อง: {ge}")
        return False

def pre_check_process_zone():
    """🛡️ [สเต็ป 1] ด่านคัดกรองหลัก: ตรวจไฟล์เสีย ไฟล์ซ้ำ และคัดกรองขนาดไฟล์ที่จะอัปโหลดขึ้น GitHub"""
    print("\n🛡️ [สเต็ป 1] เริ่มด่านคัดกรองไฟล์ใน Process_Zone...")
    print("-" * 60)
    
    existing_hashes = set()
    print("🔍 กำลังสแกนแฮชไฟล์เดิมใน MyLibrary...")
    for root, _, files in os.walk(LIBRARY_ROOT):
        for f in files:
            if f.lower().endswith(('.pdf', '.mp3')):
                f_hash = get_file_hash(os.path.join(root, f))
                if f_hash: existing_hashes.add(f_hash)
                    
    bad_count = 0
    dup_count = 0
    oversize_count = 0
    valid_files = []
    
    for root, _, files in os.walk(PROCESS_ZONE):
        for f in files:
            if not f.lower().endswith(('.pdf', '.mp3')): continue
            file_path = os.path.join(root, f)
            
            # 1. เช็กขนาดไฟล์เดี่ยว (ป้องกันหลุดขึ้น GitHub)
            file_size = get_file_size_mb(file_path)
            if file_size > MAX_FILE_SIZE_MB:
                print(f"❌ [⚠️ เตือนไฟล์ยักษ์] {f} มีขนาด {file_size:.2f} MB ซึ่งเกินลิมิต GitHub!")
                print(f"   💡 แนะนำ: กรุณานำไฟล์นี้ไปรันผ่านสคริปต์แยกไฟล์ pdf24_auto_splitter.py ก่อนครับ")
                oversize_count += 1
                continue
            
            # 2. ตรวจไฟล์ PDF เสีย
            if f.lower().endswith('.pdf'):
                is_bad = False
                try:
                    with open(file_path, 'rb') as pdf_f:
                        reader = pypdf.PdfReader(pdf_f)
                        _ = len(reader.pages)
                except Exception:
                    is_bad = True
                
                if is_bad:
                    print(f"❌ พบไฟล์ PDF โครงสร้างเสีย: {f}")
                    if not DRY_RUN:
                        if move_to_safety(file_path, DEST_BAD_FOLDER): bad_count += 1
                    else:
                        print("   🟡 [DRY RUN] ตรวจเจอไฟล์เสีย (จะย้ายไป f:\\ไฟล์พัง)")
                    continue
            
            # 3. ตรวจสอบไฟล์ซ้ำในคลังใหญ่
            f_hash = get_file_hash(file_path)
            if f_hash in existing_hashes:
                print(f"⚠️ พบไฟล์ซ้ำกับในคลังใหญ่: {f}")
                if not DRY_RUN:
                    if move_to_safety(file_path, DEST_DUP_FOLDER): dup_count += 1
                else:
                    print("   🟡 [DRY RUN] ตรวจเจอไฟล์ซ้ำ (จะย้ายไป f:\\ไฟล์ซ้ำ)")
                continue
                
            valid_files.append((file_path, f, f_hash, file_size))
                
    print("-" * 60)
    print(f"✨ คัดกรองเสร็จสิ้น! ย้ายไฟล์เสีย: {bad_count} | ย้ายไฟล์ซ้ำ: {dup_count} | ตกเกณฑ์ไฟล์ใหญ่เกิน: {oversize_count}")
    print(f"📦 มีไฟล์ที่พร้อมส่งเข้าคลังระบบทั้งหมด: {len(valid_files)} ไฟล์")
    print("==========================================================\n")
    return valid_files

def process_and_sync_library(valid_files):
    """🚚 [สเต็ป 2 + 3] ย้ายไฟล์ ดึงปก อัปเดตฐานข้อมูล และทำการทยอย Push ขึ้น Git แบบเป็นชุด"""
    if not valid_files:
        print("💡 ไม่มีไฟล์ใหม่ที่ต้องประมวลผลระบบครับ")
        return
        
    print("🚚 [สเต็ป 2] กำลังลำเลียงย้ายไฟล์และลงทะเบียนฐานข้อมูล...")
    print("-" * 60)
    
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f: books_db = json.load(f)
    else: books_db = []
        
    if os.path.exists(MUSIC_DB_PATH):
        with open(MUSIC_DB_PATH, 'r', encoding='utf-8') as f: music_db = json.load(f)
    else: music_db = []

    books_dict = {b['hash']: b for b in books_db if 'hash' in b}
    music_dict = {m['hash']: m for m in music_db if 'hash' in m}
    covers_dir = os.path.join(DB_DIR, "covers")

    accumulated_size_mb = 0
    batch_counter = 1
    files_in_current_batch = 0

    for file_path, filename, f_hash, file_size in valid_files:
        rel_subfolder = os.path.relpath(os.path.dirname(file_path), PROCESS_ZONE)
        dest_dir = os.path.join(LIBRARY_ROOT, rel_subfolder)
        dest_file_path = os.path.join(dest_dir, filename)
        
        print(f"📦 จัดการ: {filename} ({file_size:.2f} MB)")
        
        if not DRY_RUN:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.move(file_path, dest_file_path)
            
        # แยกบันทึกข้อมูลและดึงหน้าปกหนังสือ
        if filename.lower().endswith('.pdf'):
            cover_file = None
            if not DRY_RUN:
                cover_file = extract_pdf_cover_as_md5(dest_file_path, covers_dir)
            
            books_dict[f_hash] = {
                "title": os.path.splitext(filename)[0],
                "file_name": filename,
                "category": rel_subfolder.replace("\\", "/"),
                "hash": f_hash,
                "cover": cover_file if cover_file else "",
                "added_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        elif filename.lower().endswith('.mp3'):
            music_dict[f_hash] = {
                "title": os.path.splitext(filename)[0],
                "file_name": filename,
                "category": rel_subfolder.replace("\\", "/"),
                "hash": f_hash,
                "added_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }

        # สะสมขนาดและจำนวนไฟล์ใน Batch ปัจจุบัน
        accumulated_size_mb += file_size
        files_in_current_batch += 1
        
        # ── [สเต็ป 3] ตรวจสอบเงื่อนไขการหั่นแบ่งชุดทำ Batch Push ──
        if accumulated_size_mb >= BATCH_PUSH_LIMIT_MB:
            print(f"\n📌 สะสมไฟล์ขนาดรวมได้ {accumulated_size_mb:.2f} MB (ถึงลิมิต {BATCH_PUSH_LIMIT_MB} MBแล้ว)")
            if not DRY_RUN:
                # บันทึกฐานข้อมูลลง JSON ให้เรียบร้อยก่อนยิงขึ้น Git
                with open(DB_PATH, 'w', encoding='utf-8') as f:
                    json.dump(list(books_dict.values()), f, ensure_ascii=False, indent=4)
                with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f:
                    json.dump(list(music_dict.values()), f, ensure_ascii=False, indent=4)
                    
            # ยิงขึ้น GitHub ทันที
            execute_git_push(batch_counter)
            
            # ล้างค่าเซ็ตตัวนับสะสมเพื่อเริ่มรอบใหม่
            accumulated_size_mb = 0
            files_in_current_batch = 0
            batch_counter += 1
            print("-" * 60)

    # เก็บตกไฟล์ก้อนสุดท้ายที่เหลือ (ถ้าขนาดรวมกันในเซ็ตสุดท้ายไม่ถึง 90MB)
    if files_in_current_batch > 0:
        print(f"\n📌 ประมวลผลกลุ่มสุดท้าย ขนาดสะสมรอบเก็บตก: {accumulated_size_mb:.2f} MB")
        if not DRY_RUN:
            with open(DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(list(books_dict.values()), f, ensure_ascii=False, indent=4)
            with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(list(music_dict.values()), f, ensure_ascii=False, indent=4)
        execute_git_push(batch_counter)

    print("\n==========================================================")
    print("💾 บันทึกฐานข้อมูลและทำ Batch Push ขึ้น GitHub ครบทุกส่วนแล้ว!")

if __name__ == "__main__":
    if os.name == 'nt': 
        os.system('chcp 65001 > nul')
    
    print("🎬 === เริ่มระบบออโต้รันประมวลผลและทยอยดันไฟล์ขึ้น GitHub ===")
    
    # 🚀 สเต็ป 1: คัดกรองไฟล์ปัญหาก่อนเริ่มงาน
    ready_files = pre_check_process_zone()
    
    # 🚀 สเต็ป 2 + 3: ลำเลียงย้ายเข้าคลัง ลงทะเบียน และทำระบบ Batch Push แยกก้อนอัตโนมัติ
    process_and_sync_library(ready_files)
    
    print("\n✨ เรียบร้อยครับคุณ Runnara งานประมวลผลและคัดส่งพาร์ทขึ้นคลังสำเร็จสมบูรณ์!")