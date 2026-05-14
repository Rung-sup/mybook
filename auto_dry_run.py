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

import requests
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

# ==========================================
# CONFIG
# ==========================================
DRY_RUN = False  # *** ตั้งเป็น True เพื่อทดสอบ (จะไม่ส่งไฟล์จริง) / ตั้งเป็น False เพื่อเริ่มส่งจริง ***

PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
AUDIOBOOK_DB_PATH = os.path.join(DB_DIR, 'audiobook_db.json')
STATE_PATH = os.path.join(DB_DIR, 'workflow_state.json')

POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GS_PATH = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'

GITHUB_USER = "rung-sup"
MAX_SIZE_MB = 90 # ขนาดไฟล์สูงสุดต่อ 1 ไฟล์ PDF
BATCH_SIZE_LIMIT_MB = 200 # ขนาดรวมสูงสุดต่อการ Push 1 ครั้ง (ไม่เกิน 200MB เพื่อความเสถียร)
FILES_PER_BATCH = 15 # จำนวนไฟล์สูงสุดต่อการ Push 1 ครั้ง

# ==========================================
# UTILS (คงเดิม)
# ==========================================
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
            if os.path.getsize(f_path) > 1024 * 1024:
                f.seek(-1024 * 1024, os.SEEK_END)
                hasher.update(f.read())
        return hasher.hexdigest()
    except: return None

def safe_json_dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(path): os.remove(path)
    os.replace(tmp, path)

def run_git(command, cwd):
    if DRY_RUN and any(x in command for x in ["git add", "git commit", "git push"]):
        return 0, f"[DRY RUN] Executed: {command}", ""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=300)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except: return 999, "", ""

def is_git_repo(path):
    return os.path.exists(os.path.join(path, ".git"))

def git_push(repo_path):
    if DRY_RUN:
        print(f"   ☁️ [DRY RUN] แกล้งทำเป็น Push สำเร็จใน {os.path.basename(repo_path)}")
        return True, ""
    code, out, err = run_git("git push origin HEAD", repo_path)
    return (code == 0, err or out)

# ==========================================
# STEP 1: DEEP SCAN & PROCESS (คงเดิม)
# ==========================================
def step1_process_and_move():
    print("🚀 [1/3] ตรวจสอบไฟล์ใหม่และลบไฟล์ซ้ำ (Deep Scan)...")
    if DRY_RUN: print("🧪 [MODE: DRY RUN] จะไม่มีการย้ายหรือลบไฟล์จริง")
    
    for cat in sorted(os.listdir(PROCESS_ZONE)):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        if not DRY_RUN: os.makedirs(target_lib, exist_ok=True)

        for item in sorted(os.listdir(cat_staging)):
            f_path = os.path.join(cat_staging, item)
            if os.path.isdir(f_path): continue
            
            curr_size = os.path.getsize(f_path)
            curr_ext = os.path.splitext(item)[1].lower()
            
            is_duplicate = False
            for root, _, files in os.walk(LIBRARY_ROOT):
                for f in files:
                    if os.path.splitext(f)[1].lower() == curr_ext:
                        f_full = os.path.join(root, f)
                        if os.path.getsize(f_full) == curr_size:
                            if get_file_hash(f_path) == get_file_hash(f_full):
                                is_duplicate = True; break
                if is_duplicate: break

            if is_duplicate:
                print(f"🗑️ ตรวจพบไฟล์ซ้ำ: {item}")
                if not DRY_RUN: os.remove(f_path)
                continue

            if not DRY_RUN:
                dest = os.path.join(target_lib, item)
                shutil.move(f_path, dest)
            else:
                print(f"📦 [จำลอง] ย้าย {item} ไปยัง {cat}")

# ==========================================
# STEP 2: BUILD DB (คงเดิม)
# ==========================================
def get_clean_category(folder_name):
    return re.sub(r'_Vol\d+$', '', folder_name, flags=re.IGNORECASE)

def build_file_url(repo_name, full_path, cat_root_path):
    path_in_repo = os.path.relpath(full_path, cat_root_path).replace('\\', '/')
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_name}/main/{urllib.parse.quote(path_in_repo)}"

def step2_build_databases():
    print("📊 [2/3] อัปเดตฐานข้อมูล...")
    all_books, all_music = [], []

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder == '.git': continue
        display_category = get_clean_category(cat_folder)

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = "ทั่วไป" if rel_f == "." else rel_f
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')): continue
                full_p = os.path.join(root, f)
                c_id = generate_cover_id(os.path.relpath(full_p, LIBRARY_ROOT))
                item_data = {
                    "title": os.path.splitext(f)[0],
                    "url": build_file_url(cat_folder, full_p, cat_path),
                    "category": display_category,
                    "folder": folder_disp,
                    "cover_id": c_id,
                    "file_hash": get_file_hash(full_p)
                }
                if cat_folder.startswith("7_") or f.lower().endswith('.mp3'): all_music.append(item_data)
                else: all_books.append(item_data)

    if not DRY_RUN:
        safe_json_dump(DB_PATH, {"books": all_books})
        safe_json_dump(MUSIC_DB_PATH, {"music": all_music})
    print(f"✅ สแกนเสร็จสิ้น: พบ {len(all_books)} รายการ")

# ==========================================
# STEP 3: BATCH SYNC (จำกัดขนาดรวมตามกลยุทธ์ใหม่)
# ==========================================
def step3_sync_batched(repo_path, pause_time=3):
    if not is_git_repo(repo_path): return
    _, out, _ = run_git("git ls-files --others --modified --exclude-standard", repo_path)
    files = out.splitlines()
    
    _, status_out, _ = run_git("git status", repo_path)
    if not files:
        if "ahead of" in status_out:
            print(f"⬆️ Push Commit ค้างใน {os.path.basename(repo_path)}...")
            git_push(repo_path)
        return

    print(f"📦 {os.path.basename(repo_path)}: วิเคราะห์ขนาดและทยอยส่ง...")
    
    idx = 0
    while idx < len(files):
        current_batch = []
        current_batch_size_mb = 0
        
        # คัดเลือกไฟล์เข้า Batch โดยจำกัดทั้งจำนวน (15) และขนาดรวม (200MB)
        for i in range(idx, min(idx + FILES_PER_BATCH, len(files))):
            f_p = os.path.join(repo_path, files[i])
            f_size_mb = os.path.getsize(f_p) / (1024 * 1024) if os.path.exists(f_p) else 0
            
            # ถ้าเพิ่มไฟล์นี้แล้วเกิน 200MB และใน Batch มีไฟล์อื่นอยู่แล้ว ให้ตัดรอบทันที
            if current_batch_size_mb + f_size_mb > BATCH_SIZE_LIMIT_MB and len(current_batch) > 0:
                break
                
            current_batch.append(files[i])
            current_batch_size_mb += f_size_mb
            
        if not current_batch: break

        # ดำเนินการส่งข้อมูล
        for f in current_batch:
            run_git(f'git add "{f}"', repo_path)
            
        commit_msg = f"Auto-sync batch (Files: {len(current_batch)}, Size: {current_batch_size_mb:.2f}MB)"
        run_git(f'git commit -m "{commit_msg}"', repo_path)
        
        print(f"   📤 กำลัง Push: {len(current_batch)} ไฟล์ ({current_batch_size_mb:.2f} MB)...")
        ok, err = git_push(repo_path)
        
        if ok:
            idx += len(current_batch)
            print(f"   ✅ สำเร็จ! (สะสม {idx}/{len(files)})")
            if idx < len(files): time.sleep(pause_time)
        else:
            print(f"   ❌ Push ล้มเหลว: {err}")
            if not DRY_RUN:
                run_git("git reset --soft HEAD~1", repo_path) # ถอยกลับเพื่อไม่ให้ค้าง
            break # หยุดส่งใน Repo นี้ก่อนเพื่อตรวจสอบอินเทอร์เน็ต

def step3_sync():
    print("☁️ [3/3] เริ่มการส่งข้อมูล (Smart Batch Sync)...")
    for folder in sorted(os.listdir(LIBRARY_ROOT)):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.isdir(f_p): step3_sync_batched(f_p)
    if is_git_repo(DB_DIR): step3_sync_batched(DB_DIR)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    print("▶️ เริ่มระบบจัดการหอสมุด (Safe Multi-Repo Sync)")
    if DRY_RUN:
        print("🚩 [MODE: DRY RUN] อยู่ในโหมดทดสอบ ระบบจะจำลองการทำงานทั้งหมด")
    
    step1_process_and_move()
    step2_build_databases()
    step3_sync()
    
    print("\n✨ ทำงานเสร็จสมบูรณ์!")
    if DRY_RUN:
        print("💡 หากพอใจในผลลัพธ์ ให้เปลี่ยนค่า DRY_RUN = False ในโค้ดเพื่อเริ่มทำงานจริงครับ")