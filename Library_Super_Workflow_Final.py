import os
import sys
import json
import shutil
import hashlib
import subprocess
import time
import unicodedata
import urllib.parse
import re
import shlex
import requests
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
AUDIOBOOK_DB_PATH = os.path.join(DB_DIR, 'audiobook_db.json')

POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GS_PATH = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'

GITHUB_USER = "rung-sup"
MAX_SIZE_MB = 90 
PUSH_BATCH_SIZE = 15
PUSH_BATCH_DELAY_SEC = 3

def normalize_rel_path(path_text):
    return unicodedata.normalize('NFC', path_text.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')

def generate_cover_id(rel_path):
    normalized = normalize_rel_path(rel_path)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def get_file_hash(f_path):
    hasher = hashlib.md5()
    try:
        with open(f_path, 'rb') as f:
            chunk = f.read(1024 * 1024)
            hasher.update(chunk)
        return hasher.hexdigest()
    except:
        return None

def safe_json_dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=180)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

def is_git_repo(path):
    return os.path.exists(os.path.join(path, ".git"))

def get_clean_category(folder_name):
    return re.sub(r'_Vol\d+$', '', folder_name, flags=re.IGNORECASE)

def build_file_url(repo_name, full_path, cat_root_path):
    path_in_repo = os.path.relpath(full_path, cat_root_path).replace('\\', '/')
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_name}/main/{urllib.parse.quote(path_in_repo)}"

# ==========================================
# WORKFLOW STEPS
# ==========================================
def step1_process_and_move():
    print("🚀 [1/3] ตรวจสอบไฟล์ใหม่และย้ายเข้าระบบ (Deep Scan)...")
    if not os.path.exists(PROCESS_ZONE): return
    
    for cat in sorted(os.listdir(PROCESS_ZONE)):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        os.makedirs(target_lib, exist_ok=True)

        for item in sorted(os.listdir(cat_staging)):
            f_path = os.path.join(cat_staging, item)
            if os.path.isdir(f_path): continue
            
            # ย้ายไฟล์เข้าหอสมุดโดยตรง (ปลอดภัย ไม่แอบลบไฟล์ทิ้ง)
            dest = os.path.join(target_lib, item)
            if os.path.exists(dest):
                print(f"⚠️ พบไฟล์ชื่อซ้ำที่ปลายทาง ข้ามการย้าย: {item}")
                continue
            try:
                shutil.move(f_path, dest)
                print(f"📦 ย้ายสำเร็จ: {item} -> {cat}")
            except Exception as e:
                print(f"❌ ไม่สามารถย้ายไฟล์ {item} ได้: {e}")

def step2_build_databases():
    print("📊 [2/3] อัปเดตฐานข้อมูลและสร้างรูปปก...")
    all_books, all_music = [], []

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers']: continue
        
        display_category = get_clean_category(cat_folder)

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = "ทั่วไป" if rel_f == "." else rel_f
            
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')): continue
                full_p = os.path.join(root, f)
                
                # มาตรฐานการคำนวณ ID ปก: ใช้พาร์ทสัมพัทธ์จาก LIBRARY_ROOT เพื่อให้ตรงกันทุกสคริปท์
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                c_id = generate_cover_id(rel_from_library)
                
                # เจนปกสำหรับ PDF
                if f.lower().endswith('.pdf'):
                    cover_dir = os.path.join(DB_DIR, 'covers', display_category)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    
                    if not os.path.exists(cover_out) and os.path.exists(POPPLER_PATH):
                        try:
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                        except Exception as e:
                            print(f"⚠️ ไม่สามารถสร้างปกให้ไฟล์ {f} ได้ (ไฟล์อาจจะเข้ารหัสหรือเสีย): {e}")

                item_data = {
                    "title": os.path.splitext(f)[0],
                    "url": build_file_url(cat_folder, full_p, cat_path),
                    "category": display_category,
                    "folder": folder_disp,
                    "cover_id": c_id,
                    "file_hash": get_file_hash(full_p)
                }
                
                if cat_folder.startswith("7_") or f.lower().endswith('.mp3'): 
                    all_music.append(item_data)
                else: 
                    all_books.append(item_data)

    safe_json_dump(DB_PATH, {"books": all_books})
    safe_json_dump(MUSIC_DB_PATH, {"music": all_music})
    print(f"✅ อัปเดตฐานข้อมูลเสร็จสิ้น! หนังสือ {len(all_books)} รายการ, เพลง {len(all_music)} รายการ")

def step3_git_sync_batched(repo_path):
    if not is_git_repo(repo_path): return
    
    # ดึงรายชื่อไฟล์ที่มีการเปลี่ยนแปลงอย่างถูกต้อง
    code, out, _ = run_git("git status --porcelain", repo_path)
    if code != 0 or not out.strip():
        return

    # คัดกรองเอาพาธไฟล์ออกมา
    changed_files = []
    for line in out.splitlines():
        if len(line) > 3:
            # ตัดสถานะ git เช่น 'M ', '?? ' ออกเพื่อเอาเฉพาะพาธไฟล์
            changed_files.append(line[3:].strip('"'))

    if not changed_files: return
    print(f"📦 {os.path.basename(repo_path)}: ตรวจพบไฟล์เปลี่ยนแปลง {len(changed_files)} ไฟล์ กำลังทยอยส่ง...")

    # แบ่งส่งเป็น Batch เพื่อป้องกัน GitHub Desktop/Git ค้าง
    for i in range(0, len(changed_files), PUSH_BATCH_SIZE):
        batch = changed_files[i:i + PUSH_BATCH_SIZE]
        quoted_files = " ".join(shlex.quote(f) for f in batch)
        
        run_git(f"git add {quoted_files}", repo_path)
        run_git(f'git commit -m "Auto-sync batch {i//PUSH_BATCH_SIZE + 1}"', repo_path)
        code, _, err = run_git("git push origin HEAD", repo_path)
        
        if code == 0:
            print(f"   ✅ ส่งสำเร็จแล้ว {min(i + PUSH_BATCH_SIZE, len(changed_files))}/{len(changed_files)}")
        else:
            print(f"   ❌ Batch นี้ส่งไม่สำเร็จ: {err}")
        
        if i + PUSH_BATCH_SIZE < len(changed_files):
            time.sleep(PUSH_BATCH_DELAY_SEC)

def sync_all_repositories():
    print("☁️ [3/3] เริ่มกระบวนการ Batch Sync ไปยัง GitHub...")
    for folder in sorted(os.listdir(LIBRARY_ROOT)):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.isdir(f_p): step3_git_sync_batched(f_p)
    if is_git_repo(DB_DIR): step3_git_sync_batched(DB_DIR)

if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    print("▶️ เริ่มระบบจัดการคลังหนังสือรันนารา (Fixed Version)")
    step1_process_and_move()
    step2_build_databases()
    sync_all_repositories()
    print("\n✨ ทำงานเสร็จสมบูรณ์ ทุกอย่างอัปเดตเป็นปัจจุบันแล้วครับ!")