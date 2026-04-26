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
# ⚙️ MASTER CONFIGURATION
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
BATCH_SIZE = 15

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd)
        return result.stdout.strip()
    except: return None

def generate_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def main():
    # --- STEP 1: MOVE FILES ---
    print("🛠 [1/3] กำลังจัดระเบียบไฟล์...")
    for cat in os.listdir(PROCESS_ZONE):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        os.makedirs(target_lib, exist_ok=True)

        for item in os.listdir(cat_staging):
            f_path = os.path.join(cat_staging, item)
            dest = os.path.join(target_lib, item)
            try:
                if os.path.isdir(f_path): # หนังสือชุด
                    if os.path.exists(dest):
                        for f in os.listdir(f_path): shutil.move(os.path.join(f_path, f), os.path.join(dest, f))
                        shutil.rmtree(f_path)
                    else: shutil.move(f_path, dest)
                else: # ไฟล์เดี่ยว
                    if os.path.exists(dest): os.remove(f_path)
                    else: shutil.move(f_path, dest)
            except: pass

    # --- STEP 2: UPDATE DB & COVERS (Focused on MyBook_Test) ---
    print("📊 [2/3] อัปเดตฐานข้อมูลและสร้างหน้าปกที่ MyBook_Test...")
    all_books, all_music = [], []
    
    for cat in os.listdir(LIBRARY_ROOT):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']: continue
        
        for root, dirs, files in os.walk(cat_path):
            # จัดการ Folder: ถ้าอยู่ในโฟลเดอร์ย่อย ให้ใช้ชื่อโฟลเดอร์นั้นเป็นชื่อชุด
            rel_folder = os.path.relpath(root, cat_path)
            display_folder = "ทั่วไป" if rel_folder == "." else rel_folder
            
            for f in files:
                if f.lower().endswith(('.pdf', '.mp3')):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, LIBRARY_ROOT)
                    cover_id = generate_id(rel_p)
                    
                    # บังคับสร้างปกไปที่ MyBook_Test/covers
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
                        "category": cat,
                        "folder": display_folder, # ป้องกันหนังสือกระจาย
                        "cover_id": cover_id
                    }
                    if cat.startswith("7_"): all_music.append(item_data)
                    else: all_books.append(item_data)

    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=4)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=4)

    # --- STEP 3: SYNC ALL ---
    print("☁️ [3/3] ทยอยส่งข้อมูลขึ้น GitHub...")
    # 3.1 ส่งไฟล์เนื้อหา (MyLibrary)
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.exists(os.path.join(f_p, ".git")):
            run_git("git add .", f_p)
            run_git('git commit -m "Update Library"', f_p)
            run_git("git push origin HEAD", f_p)

    # 3.2 ส่งฐานข้อมูลและหน้าปก (MyBook_Test)
    print("💾 กำลังล้างไฟล์ค้างใน Repo MyBook (กวาดหน้าปกและ JSON)...")
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        run_git("git add .", DB_DIR)
        run_git('git commit -m "Full sync: Database and Covers"', DB_DIR)
        run_git("git push origin HEAD", DB_DIR)

if __name__ == "__main__":
    main()
    print("\n✨ เรียบร้อยครับ! หน้าปกและโฟลเดอร์ควรกลับมาเป็นปกติแล้วครับ")