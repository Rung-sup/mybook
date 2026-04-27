import os
import shutil
import hashlib
import json
import unicodedata
import urllib.parse
import time
import subprocess
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GS_PATH = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'

GITHUB_USER = "rung-sup"
MAX_SIZE_MB = 95

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=60)
        return result.stdout.strip()
    except: return None

def get_file_hash(f_path):
    hasher = hashlib.md5()
    try:
        with open(f_path, 'rb') as f:
            chunk = f.read(1024 * 1024)
            hasher.update(chunk)
    except: return None
    return hasher.hexdigest()

def compress_pdf_high(f_path):
    if not os.path.exists(GS_PATH): return False
    temp_out = f_path.replace(".pdf", "_tmp_small.pdf")
    gs_cmd = [GS_PATH, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH', f'-sOutputFile={temp_out}', f_path]
    try:
        subprocess.run(gs_cmd, capture_output=True)
        if os.path.exists(temp_out):
            if os.path.getsize(temp_out) < os.path.getsize(f_path):
                os.remove(f_path)
                os.rename(temp_out, f_path)
                return True
            os.remove(temp_out)
    except: pass
    return False

def split_with_cover(f_path):
    print(f"   ✂️ กำลังแบ่งเล่ม: {os.path.basename(f_path)}")
    reader = PdfReader(f_path)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(f_path)[0]
    mid = total_pages // 2
    
    paths = []
    # Part 1
    w1 = PdfWriter()
    for i in range(0, mid): w1.add_page(reader.pages[i])
    p1 = f"{base_name} Part 1.1.pdf"
    with open(p1, "wb") as f: w1.write(f)
    paths.append(p1)
    
    # Part 2 + Cover
    w2 = PdfWriter()
    w2.add_page(reader.pages[0]) 
    for i in range(mid, total_pages): w2.add_page(reader.pages[i])
    p2 = f"{base_name} Part 1.2.pdf"
    with open(p2, "wb") as f: w2.write(f)
    paths.append(p2)
    
    os.remove(f_path)
    return paths

def generate_cover_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def main():
    # --- STEP 1: SAFE MOVE & PROCESS ---
    print("🛠 [1/3] กำลังจัดระเบียบไฟล์ (Safe Move Mode)...")
    for cat in os.listdir(PROCESS_ZONE):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        os.makedirs(target_lib, exist_ok=True)

        for item in os.listdir(cat_staging):
            f_path = os.path.join(cat_staging, item)
            
            # บีบอัด/แบ่งไฟล์ PDF ก่อนย้าย
            if item.lower().endswith('.pdf'):
                if os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
                    compress_pdf_high(f_path)
                    if os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
                        split_with_cover(f_path)
                        # หลังจาก split ไฟล์เดิมหายไปแล้ว ให้ข้ามไปจัดการไฟล์ใหม่ในรอบถัดไป
                        continue

            # ย้ายเข้า LIBRARY_ROOT (ใช้ shutil.move แบบปลอดภัย)
            dest = os.path.join(target_lib, os.path.basename(f_path))
            try:
                if os.path.exists(dest):
                    if os.path.isdir(f_path):
                        for sub in os.listdir(f_path):
                            sub_dest = os.path.join(dest, sub)
                            if not os.path.exists(sub_dest): shutil.move(os.path.join(f_path, sub), sub_dest)
                        shutil.rmtree(f_path)
                    else:
                        os.remove(f_path) # ซ้ำจริงค่อยลบ
                else:
                    shutil.move(f_path, dest)
            except: pass

    # --- STEP 2: RE-GEN DATA & HASH ---
    print("📊 [2/3] อัปเดตฐานข้อมูลหนังสือและเพลง...")
    all_books, all_music = [], []
    for cat in os.listdir(LIBRARY_ROOT):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']: continue
        
        for root, _, files in os.walk(cat_path):
            rel_folder = os.path.relpath(root, cat_path)
            display_folder = "ทั่วไป" if rel_folder == "." else rel_folder
            
            for f in files:
                if f.lower().endswith(('.pdf', '.mp3')):
                    full_p = os.path.join(root, f)
                    f_hash = get_file_hash(full_p)
                    cover_id = generate_cover_id(os.path.relpath(full_p, LIBRARY_ROOT))
                    
                    # จัดการหน้าปก (เฉพาะ PDF)
                    cover_dir = os.path.join(DB_DIR, 'covers', cat)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{cover_id}.jpg")
                    if f.lower().endswith('.pdf') and not os.path.exists(cover_out):
                        try:
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                        except: pass

                    path_in_repo = os.path.relpath(full_p, cat_path).replace('\\', '/')
                    item_data = {
                        "title": os.path.splitext(f)[0],
                        "url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{cat}/main/{urllib.parse.quote(path_in_repo)}",
                        "category": cat, "folder": display_folder, "cover_id": cover_id, "file_hash": f_hash
                    }
                    # ตรวจสอบว่าเป็นเพลงหรือไม่ (เช็กจากโฟลเดอร์หรือนามสกุล)
                    if cat.startswith("7_") or f.lower().endswith('.mp3'):
                        all_music.append(item_data)
                    else:
                        all_books.append(item_data)

    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=4)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=4)

    # --- STEP 3: SYNC ---
    print("\n☁️ [3/3] กำลังส่งข้อมูลขึ้น Cloud...")
    # ส่งเนื้อหา
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.exists(os.path.join(f_p, ".git")):
            run_git("git add .", f_p)
            if run_git("git status --porcelain", f_p):
                run_git('git commit -m "Library Sync"', f_p)
                subprocess.run("git push origin HEAD", cwd=f_p, shell=True, timeout=60)

    # ส่ง DB & Covers
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        run_git("git add .", DB_DIR)
        if run_git("git status --porcelain", DB_DIR):
            run_git('git commit -m "DB Sync"', DB_DIR)
            subprocess.run("git push origin HEAD", cwd=DB_DIR, shell=True, timeout=60)

    print("\n✨ ภารกิจเสร็จสมบูรณ์!")
    os._exit(0)

if __name__ == "__main__":
    main()