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
MAX_SIZE_MB = 90 

# ==========================================
# UTILS (คงเดิมและเพิ่มฟังก์ชัน Split)
# ==========================================
def normalize_rel_path(path_text):
    return unicodedata.normalize('NFC', path_text.replace('\\', '/'))

def run_git(cmd, cwd):
    try:
        res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
        return res.returncode == 0, res.stdout, res.stderr
    except:
        return False, "", "Execution error"

def git_push(repo_path):
    for i in range(3): # Try 3 times
        ok, out, err = run_git("git push origin main", repo_path)
        if ok: return True, ""
        time.sleep(5)
    return False, err

def is_pdf_valid(filepath):
    try:
        with open(filepath, 'rb') as f:
            reader = PdfReader(f)
            _ = len(reader.pages)
        return True
    except:
        return False

def get_md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# --- ฟังก์ชันใหม่: แบ่งไฟล์ PDF ---
def split_large_pdf(filepath, max_size_mb=90):
    """แบ่งไฟล์ PDF เป็นส่วนๆ และจัดใส่โฟลเดอร์ชื่อเดียวกับไฟล์"""
    file_size = os.path.getsize(filepath) / (1024 * 1024)
    if file_size <= max_size_mb:
        return [filepath]

    print(f"✂️  พบไฟล์ใหญ่ ({file_size:.2f} MB) กำลังแบ่ง: {os.path.basename(filepath)}")
    
    try:
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        # สร้างโฟลเดอร์สำหรับเก็บเล่มย่อย
        folder_path = os.path.join(os.path.dirname(filepath), base_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        new_files = []
        current_part = 1
        writer = PdfWriter()
        
        for page_num in range(total_pages):
            writer.add_page(reader.pages[page_num])
            
            # ตรวจสอบขนาดทุกๆ 10 หน้า
            if page_num % 10 == 0 or page_num == total_pages - 1:
                temp_output = os.path.join(folder_path, f"{base_name}_Part_{current_part}.pdf")
                with open(temp_output, "wb") as f:
                    writer.write(f)
                
                # ถ้าไฟล์ย่อยเริ่มใหญ่เกิน 85MB ให้ตัดขึ้นเล่มใหม่
                if os.path.getsize(temp_output) / (1024 * 1024) > (max_size_mb - 5):
                    new_files.append(temp_output)
                    writer = PdfWriter()
                    current_part += 1
                elif page_num == total_pages - 1:
                    new_files.append(temp_output)
        
        # ย้ายไฟล์ต้นฉบับออกไปที่ Backup เพื่อไม่ให้ถูก Sync ซ้ำ
        backup_dir = os.path.join(PROCESS_ZONE, "Split_Backup")
        if not os.path.exists(backup_dir): os.makedirs(backup_dir)
        shutil.move(filepath, os.path.join(backup_dir, os.path.basename(filepath)))
        
        return new_files
    except Exception as e:
        print(f"❌ ไม่สามารถแบ่งไฟล์ได้: {e}")
        return [filepath]

def extract_cover_from_pdf(pdf_path, category, cover_id):
    cover_dir = os.path.join(DB_DIR, 'covers', category)
    if not os.path.exists(cover_dir): os.makedirs(cover_dir)
    out_path = os.path.join(cover_dir, f"{cover_id}.jpg")
    if os.path.exists(out_path): return
    
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, poppler_path=POPPLER_PATH)
        if images:
            images[0].save(out_path, 'JPEG', quality=80)
    except:
        pass

# ==========================================
# STEP 1: CLEAN & PREPARE
# ==========================================
def step1_clean_and_prepare():
    print("🚀 [1/3] ตรวจสอบไฟล์และเตรียมความพร้อม...")
    seen_hashes = {}
    
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if not os.path.isdir(f_p): continue
        
        for root, _, files in os.walk(f_p):
            for file in files:
                if not file.lower().endswith('.pdf'): continue
                path = os.path.join(root, file)
                
                # 1. เช็คไฟล์เสีย (เพิ่ม Try-Except ครอบไว้กัน Error หยุดสคริปต์)
                try:
                    if not is_pdf_valid(path):
                        print(f"⚠️ ตรวจพบปัญหาไฟล์: {file} (ข้ามเพื่อความปลอดภัย)")
                        continue # เปลี่ยนจากลบเป็นข้ามก่อน เพื่อให้คุณไปเช็คเอง
                except Exception as e:
                    print(f"⏩ ไม่สามารถเข้าถึงไฟล์ได้ (ข้าม): {file}")
                    continue

                # 2. เช็คไฟล์ซ้ำ (Global MD5)
                try:
                    h = get_md5(path)
                    if h in seen_hashes:
                        print(f"🗑️ พบไฟล์ซ้ำ: {file} (กำลังพยายามลบ...)")
                        os.remove(path)
                        continue
                    seen_hashes[h] = path
                except PermissionError:
                    print(f"⏩ ไฟล์ซ้ำแต่ลบไม่ได้ (ถูกเปิดค้างไว้): {file}")
                    continue
                
                # 3. เช็คขนาดและแบ่งไฟล์
                try:
                    split_large_pdf(path, MAX_SIZE_MB)
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดขณะแบ่งไฟล์ {file}: {e}")

# ==========================================
# STEP 2: GENERATE DB (Logic เดิม)
# ==========================================
def step2_gen_db():
    print("📊 [2/3] อัปเดตฐานข้อมูล...")
    books = []
    for folder in sorted(os.listdir(LIBRARY_ROOT)):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if not os.path.isdir(f_p): continue
        
        for root, _, files in os.walk(f_p):
            for file in sorted(files):
                if not file.lower().endswith('.pdf'): continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, LIBRARY_ROOT)
                
                # คำนวณหมวดหมู่และโฟลเดอร์สำหรับ UI
                parts = rel_path.split(os.sep)
                cat = parts[0]
                # ถ้าอยู่ในโฟลเดอร์ย่อย (ที่เกิดจากการแบ่งเล่ม) ให้ใช้ชื่อโฟลเดอร์เป็นกลุ่ม
                sub_folder = parts[1] if len(parts) > 2 else ""
                
                cid = hashlib.md5(rel_path.encode('utf-8')).hexdigest()
                extract_cover_from_pdf(full_path, cat, cid)
                
                books.append({
                    "title": os.path.splitext(file)[0],
                    "url": f"https://raw.githubusercontent.com/{GITHUB_USER}/MyLibrary/main/{normalize_rel_path(rel_path)}",
                    "category": cat,
                    "folder": sub_folder,
                    "cover_id": cid
                })
    
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"✅ รวมไฟล์ทั้งหมดสำเร็จ: หนังสือ {len(books)} รายการ")

# ==========================================
# STEP 3: SMART BATCH SYNC (ระบบใหม่)
# ==========================================
def git_push_batch(repo_path, batch_size=15):
    _, out, _ = run_git("git ls-files --others --modified --exclude-standard", repo_path)
    files = out.splitlines()
    
    _, status_out, _ = run_git("git status", repo_path)
    if not files:
        if "ahead of" in status_out:
            print(f"⬆️ Push Commit ค้างใน {os.path.basename(repo_path)}...")
            git_push(repo_path)
        return

    print(f"📦 {os.path.basename(repo_path)}: ทยอยส่ง {len(files)} รายการ (Smart Batch)...")
    
    idx = 0
    current_batch_limit = batch_size
    
    while idx < len(files):
        current_batch = []
        total_size_mb = 0
        
        # รวมไฟล์เข้า Batch โดยจำกัดจำนวน และขนาดรวมไม่เกิน 180MB (เพื่อความเสถียร)
        for i in range(idx, min(idx + current_batch_limit, len(files))):
            f_p = os.path.join(repo_path, files[i])
            f_size = os.path.getsize(f_p) / (1024 * 1024) if os.path.exists(f_p) else 0
            
            if total_size_mb + f_size > 180 and len(current_batch) > 0:
                break
            
            current_batch.append(files[i])
            total_size_mb += f_size
        
        if not current_batch: break
        
        for f in current_batch: run_git(f'git add "{f}"', repo_path)
        run_git(f'git commit -m "Auto-sync batch {idx//batch_size + 1} ({total_size_mb:.1f}MB)"', repo_path)
        
        ok, err = git_push(repo_path)
        if ok:
            print(f"✅ สำเร็จ: {idx + len(current_batch)}/{len(files)} (Batch Size: {total_size_mb:.1f}MB)")
            idx += len(current_batch)
            time.sleep(2)
        else:
            print(f"⚠️ Push ไม่ผ่าน ลดขนาด Batch และลองใหม่...")
            run_git("git reset --soft HEAD~1", repo_path)
            current_batch_limit = max(1, current_batch_limit // 2)
            time.sleep(5)

def step3_sync():
    print("☁️ [3/3] เริ่มการส่งข้อมูล (Batch Sync)...")
    # 1. Sync ฐานข้อมูลก่อน
    git_push_batch(DB_DIR, batch_size=5)
    # 2. Sync แต่ละ Repo ใน Library
    for folder in sorted(os.listdir(LIBRARY_ROOT)):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.isdir(f_p) and os.path.exists(os.path.join(f_p, ".git")):
            git_push_batch(f_p)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    step1_clean_and_prepare()
    step2_gen_db()
    step3_sync()
    print("🏁 ทุกอย่างเสร็จสิ้น!")