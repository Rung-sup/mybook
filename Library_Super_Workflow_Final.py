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
from pdf2image import convert_from_path

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GITHUB_USER = "rung-sup"

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

def build_file_url(repo_name, full_path, cat_root_path):
    path_in_repo = os.path.relpath(full_path, cat_root_path).replace('\\', '/')
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_name}/main/{urllib.parse.quote(path_in_repo)}"

# ==========================================
# 🚀 STEP 1: บังคับย้ายไฟล์และแสดง Log อย่างละเอียด
# ==========================================
def step1_process_and_move():
    print("🚀 [1/3] ตรวจสอบไฟล์ใหม่และย้ายเข้าระบบ (Deep Scan)...")
    if not os.path.exists(PROCESS_ZONE): 
        print("❌ ไม่พบโฟลเดอร์ Process_Zone!")
        return
    
    categories = [d for d in os.listdir(PROCESS_ZONE) if os.path.isdir(os.path.join(PROCESS_ZONE, d))]
    
    for cat in categories:
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        target_lib = os.path.join(LIBRARY_ROOT, cat.strip())
        
        if not os.path.exists(target_lib):
            os.makedirs(target_lib, exist_ok=True)

        # เปลี่ยนมาใช้ os.walk เพื่อค้นหาไฟล์ที่ซ่อนอยู่ลึกในโฟลเดอร์ย่อยด้วย
        all_found_files = []
        for root, dirs, files in os.walk(cat_staging):
            for f in files:
                # บันทึกพาธเต็มของไฟล์ทั้งหมดที่เจอ
                all_found_files.append(os.path.join(root, f))
                
        print(f"📂 โฟลเดอร์ [{cat}] ตรวจพบไฟล์ทั้งหมด (รวมในโฟลเดอร์ย่อย): {len(all_found_files)} ไฟล์")

        for f_path in all_found_files:
            item = os.path.basename(f_path)
            dest = os.path.join(target_lib, item)
            
            # 1. ตรวจสอบขนาดไฟล์เปล่า 0 Bytes
            if os.path.getsize(f_path) == 0:
                print(f"❌ เจอไฟล์เสีย/ไฟล์เปล่า 0 Bytes (จะไม่ย้าย): {item}")
                continue

            # 2. ตรวจสอบไฟล์ซ้ำ
            if os.path.exists(dest):
                print(f"⚠️ ไฟล์ชื่อซ้ำกับคลังปลายทางแล้ว: {item}")
                continue

            try:
                # บังคับย้ายไฟล์จริงออกจากโครงสร้างย่อย ไปวางที่รากของคลังหลัก
                shutil.move(f_path, dest)
                print(f"📦 [ย้ายสำเร็จ] {item} -> คลังหลัก [{cat.strip()}]")
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการย้ายไฟล์ {item}: {e}")
# ==========================================
# 📊 STEP 2: สร้างฐานข้อมูลและดึงปกตรงเข้าห้องย่อย
# ==========================================
def step2_build_databases():
    print("📊 [2/3] อัปเดตฐานข้อมูลและสร้างรูปปก...")
    all_books, all_music = [], []

    if not os.path.exists(LIBRARY_ROOT):
        print("❌ ไม่พบโฟลเดอร์ MyLibrary!")
        return

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers', '.github']: continue

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = "ทั่วไป" if rel_f == "." else rel_f
            
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')): continue
                full_p = os.path.join(root, f)
                
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                c_id = generate_cover_id(rel_from_library)
                
                if f.lower().endswith('.pdf'):
                    cover_dir = os.path.join(DB_DIR, 'covers', cat_folder)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    
                    if not os.path.exists(cover_out) and os.path.exists(POPPLER_PATH):
                        try:
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                        except Exception as e:
                            print(f"⚠️ ไม่สามารถสร้างปกให้ไฟล์ {f} ได้: {e}")

                item_data = {
                    "title": os.path.splitext(f)[0],
                    "url": build_file_url(cat_folder, full_p, cat_path),
                    "category": cat_folder,
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

# ==========================================
# ☁️ STEP 3: BATCH SYNC
# ==========================================
def step3_git_sync_batched(repo_path):
    if not is_git_repo(repo_path): return
    code, out, _ = run_git("git status --porcelain", repo_path)
    if code != 0 or not out.strip(): return

    changed_files = []
    for line in out.splitlines():
        if len(line) > 3: changed_files.append(line[3:].strip('"'))
    if not changed_files: return
    
    print(f"📦 {os.path.basename(repo_path)}: ตรวจพบไฟล์เปลี่ยนแปลง {len(changed_files)} ไฟล์ กำลังทยอยส่ง...")
    batch_size = 15
    for i in range(0, len(changed_files), batch_size):
        batch = changed_files[i:i + batch_size]
        quoted_files = " ".join(shlex.quote(f) for f in batch)
        run_git(f"git add {quoted_files}", repo_path)
        run_git(f'git commit -m "Auto-sync batch {i//batch_size + 1}"', repo_path)
        code, _, err = run_git("git push origin HEAD", repo_path)
        if code == 0:
            print(f"   ✅ ส่งสำเร็จแล้ว {min(i + batch_size, len(changed_files))}/{len(changed_files)}")
        else:
            print(f"   ❌ Batch นี้ส่งไม่สำเร็จ: {err}")
        if i + batch_size < len(changed_files): time.sleep(3)

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