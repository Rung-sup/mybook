import os
import sys
import json
import shutil
import hashlib
import subprocess
import time
import unicodedata
import urllib.parse
import shlex
import re
from pdf2image import convert_from_path
import fitz  # PyMuPDF

# ==========================================
# ⚙️ CONFIGURATION (ตั้งค่าพิกัดหลัก)
# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'

MAX_SIZE_MB = 90
PAGES_PER_SPLIT = 150
DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GITHUB_USER = "rung-sup"

# ==========================================
# 🧰 UTILITIES FUNCTIONS
# ==========================================
def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def normalize_text(text):
    return unicodedata.normalize('NFC', text.strip()).replace('\u0e4d\u0e32', '\u0e33')

def generate_cover_id(rel_path):
    normalized = normalize_text(rel_path.replace('\\', '/'))
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

def run_git(command, cwd):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=300)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

def build_file_url(repo_name, full_path, cat_root_path):
    path_in_repo = os.path.relpath(full_path, cat_root_path).replace('\\', '/')
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_name}/main/{urllib.parse.quote(path_in_repo)}"

# ==========================================
# 📑 [ขั้นตอนที่ 1] เตรียมไฟล์ หั่นเล่มใหญ่ และย้ายเข้าระบบ
# ==========================================
def prepare_and_move_files():
    print("\n🚀 [1/3] เริ่มกระบวนการเตรียมไฟล์และจัดสรรโครงสร้าง...")
    if not os.path.exists(PROCESS_ZONE):
        print("❌ ไม่พบโฟลเดอร์ Process_Zone")
        return

    categories = [d for d in os.listdir(PROCESS_ZONE) if os.path.isdir(os.path.join(PROCESS_ZONE, d))]
    
    for cat in categories:
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        target_repo = os.path.join(LIBRARY_ROOT, normalize_text(cat))
        os.makedirs(target_repo, exist_ok=True)

        # 1. สแกนหาไฟล์ PDF เล่มใหญ่ใน Process_Zone เพื่อหั่นก่อนย้าย
        files_in_cat = os.listdir(cat_staging)
        for item in files_in_cat:
            item_path = os.path.join(cat_staging, item)
            if os.path.isdir(item_path): continue
            
            if item.lower().endswith('.pdf') and not "_part_" in item.lower():
                if get_file_size_mb(item_path) > MAX_SIZE_MB:
                    base_name, _ = os.path.splitext(item)
                    base_name = normalize_text(base_name)
                    story_folder = os.path.join(cat_staging, base_name)
                    os.makedirs(story_folder, exist_ok=True)
                    
                    print(f"✂️  พบไฟล์ใหญ่: {item} กำลังหั่นลงโฟลเดอร์ [{base_name}]...")
                    try:
                        doc = fitz.open(item_path)
                        total_pages = len(doc)
                        part_num, start_page = 1, 0
                        while start_page < total_pages:
                            end_page = min(start_page + PAGES_PER_SPLIT, total_pages)
                            out_name = f"{base_name}_Part_{part_num}.pdf"
                            out_path = os.path.join(story_folder, out_name)
                            
                            if not os.path.exists(out_path):
                                new_doc = fitz.open()
                                new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page-1)
                                new_doc.save(out_path, garbage=4, deflate=True, clean=True)
                                new_doc.close()
                            start_page = end_page
                            part_num += 1
                        doc.close()
                        print(f"   ✅ หั่นสำเร็จ! (รักษาไฟล์ต้นฉบับไว้ที่เดิม)")
                    except Exception as e:
                        print(f"   ❌ เกิดข้อผิดพลาดในการหั่น {item}: {e}")

        # 2. ย้ายโฟลเดอร์ย่อยหรือไฟล์ที่พร้อมแล้ว เข้าสู่ MyLibrary
        for item in os.listdir(cat_staging):
            src_path = os.path.join(cat_staging, item)
            dest_path = os.path.join(target_repo, normalize_text(item))
            
            try:
                if os.path.isdir(src_path):
                    if os.path.exists(dest_path):
                        # ถ้าปลายทางมีโฟลเดอร์อยู่แล้ว ให้ย้ายไฟล์พาร์ทข้างในไปเติมแทน
                        for sub_f in os.listdir(src_path):
                            shutil.move(os.path.join(src_path, sub_f), os.path.join(dest_path, sub_f))
                        shutil.rmtree(src_path)
                    else:
                        shutil.move(src_path, dest_path)
                    print(f"📦 [ย้ายโฟลเดอร์เรื่องสำเร็จ] -> {item}")
                else:
                    # สำหรับไฟล์เพลง หรือไฟล์ PDF เล่มเล็กที่ขนาดไม่เกินเกณฑ์ ให้ย้ายตรงๆ
                    if not item.lower().endswith('.pdf') or get_file_size_mb(src_path) <= MAX_SIZE_MB:
                        shutil.move(src_path, dest_path)
                        print(f"📦 [ย้ายไฟล์สำเร็จ] -> {item}")
            except Exception as e:
                print(f"⚠️  ไม่สามารถย้าย {item} ได้เนื่องจากไฟล์ถูกใช้งานอยู่ หรือซ้ำซ้อน: {e}")

# ==========================================
# 📊 [ขั้นตอนที่ 2] อัปเดตฐานข้อมูล สร้างปกไฟล์ + ปกโฟลเดอร์
# ==========================================
def build_databases_and_covers():
    print("\n📊 [2/3] เริ่มกระบวนการสร้างปกและจัดการฐานข้อมูล JSON...")
    all_books, all_music = [], []

    if not os.path.exists(LIBRARY_ROOT): return

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers', '.github']: continue

        # 🛠️ ตรวจจับและยุบรวมห้องย่อยเข้าหมวดหลักสำหรับแอป เช่น 4_Chinese_Novel_Vol4 -> 4_Chinese_Novel อัตโนมัติ
        display_category = re.sub(r'_Vol\d+$', '', cat_folder, flags=re.IGNORECASE)

        folder_info = {}

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = "ทั่วไป" if rel_f == "." else normalize_text(rel_f)
            
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')): continue
                full_p = os.path.join(root, f)
                
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                c_id = generate_cover_id(rel_from_library)
                
                if f.lower().endswith('.pdf'):
                    # 📌 รักษาพิกัดเซฟไฟล์ปกในเครื่องตามโฟลเดอร์คลังจริงบนดิสก์
                    cover_dir = os.path.join(DB_DIR, 'covers', cat_folder)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    
                    if not os.path.exists(cover_out) and os.path.exists(POPPLER_PATH):
                        try:
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                        except:
                            pass
                    
                    if folder_disp != "ทั่วไป":
                        if folder_disp not in folder_info:
                            folder_info[folder_disp] = {"first_pdf": full_p, "count": 0}
                        folder_info[folder_disp]["count"] += 1

                item_data = {
                    "title": normalize_text(os.path.splitext(f)[0]),
                    "url": build_file_url(cat_folder, full_p, cat_path),
                    "category": display_category,                       # รวมหมวดแสดงผลในแอปตามสั่ง
                    "folder": folder_disp,
                    "cover_id": c_id,
                    "file_hash": get_file_hash(full_p),
                    "_raw_cat": cat_folder                               # 📌 แอบเก็บค่าจริงไว้ใช้ตรวจจับและแมปหน้าปกด้านล่างให้แม่นยำ
                }
                
                if cat_folder.startswith("7_") or f.lower().endswith('.mp3'): 
                    all_music.append(item_data)
                else: 
                    all_books.append(item_data)

        # ผูกข้อมูลหน้าปกประจำกลุ่มโฟลเดอร์ และบันทึกจำนวนเล่มส่งไปให้แอปโชว์
        for folder_name, info in folder_info.items():
            try:
                folder_rel_path = os.path.join(cat_folder, folder_name)
                folder_cover_id = generate_cover_id(folder_rel_path)
                
                cover_dir = os.path.join(DB_DIR, 'covers', cat_folder)
                folder_cover_out = os.path.join(cover_dir, f"folder_{folder_cover_id}.jpg")
                
                if not os.path.exists(folder_cover_out) and os.path.exists(POPPLER_PATH):
                    imgs = convert_from_path(info["first_pdf"], first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                    if imgs:
                        imgs[0].save(folder_cover_out, 'JPEG', quality=85)
                        print(f"📸 เจนปกโฟลเดอร์สำเร็จ: [{folder_name}] (มีทั้งหมด {info['count']} เล่ม)")

                for book in all_books:
                    # 🛠️ แก้จุดตาย: เช็คคู่แมปด้วยโฟลเดอร์ต้นทางจริงเพื่อให้เจอหนังสือของห้องย่อยแน่นอน
                    if book["_raw_cat"] == cat_folder and book["folder"] == folder_name:
                        book["folder_cover_id"] = f"folder_{folder_cover_id}"
                        book["folder_book_count"] = info["count"]

            except Exception as e:
                print(f"⚠️  เกิดข้อผิดพลาดกับปกโฟลเดอร์ {folder_name}: {e}")

    # ล้างคีย์ชั่วคราวออกก่อนบันทึกไฟล์ เพื่อคงระเบียบความสะอาดของไฟล์ JSON
    for book in all_books: book.pop("_raw_cat", None)
    for music in all_music: music.pop("_raw_cat", None)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=2)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=2)
    print(f"✅ อัปเดตฐานข้อมูลและสร้างปกเสร็จสิ้น!")

# ==========================================
# ☁️ [ขั้นตอนที่ 3] บังคับคิว Commit และ ทยอยอัปโหลดขึ้น GitHub อัตโนมัติ
# ==========================================
def auto_git_push_all():
    print("\n☁️ [3/3] เริ่มกระบวนการอัปโหลดไฟล์ขึ้น GitHub อัตโนมัติ...")
    
    # วนลูปเช็คทุกโฟลเดอร์ Repo ใน MyLibrary
    for folder in sorted(os.listdir(LIBRARY_ROOT)):
        repo_path = os.path.join(LIBRARY_ROOT, folder)
        if not os.path.isdir(repo_path) or not os.path.exists(os.path.join(repo_path, ".git")): continue
        
        code, out, _ = run_git("git status --porcelain", repo_path)
        if code == 0 and out.strip():
            print(f"📦 [พบไฟล์ใหม่ในคลัง {folder}]: กำลังเตรียมอัปโหลด...")
            run_git("git add .", repo_path)
            run_git(f'git commit -m "Auto-update library content {time.strftime("%Y-%m-%d %H:%M:%S")}"', repo_path)
            
            print(f"   📤 กำลัง Push ข้อมูลขึ้น GitHub (ห้ามปิดโปรแกรม)...")
            p_code, _, p_err = run_git("git push origin HEAD", repo_path)
            if p_code == 0:
                print(f"   ✅ อัปโหลดขึ้นคลัง {folder} สำเร็จแล้ว!")
            else:
                print(f"   ❌ Push ไม่ผ่านชั่วคราวเนื่องจากไฟล์มีขนาดใหญ่: {p_err}")

    # อัปเดตฐานข้อมูลไฟล์เจซอนและรูปปกที่ห้อง MyBook_Test ด้วย
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        code, out, _ = run_git("git status --porcelain", DB_DIR)
        if code == 0 and out.strip():
            print(f"📦 [พบการอัปเดตระบบฐานข้อมูล]: กำลังอัปโหลดข้อมูลหน้าเว็บ...")
            run_git("git add .", DB_DIR)
            run_git(f'git commit -m "Auto-update database and covers"', DB_DIR)
            run_git("git push origin HEAD", DB_DIR)
            print(f"   ✅ อัปโหลดฐานข้อมูลขึ้น GitHub สำเร็จแล้ว!")

# ==========================================
# 🏁 MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    print("=======================================================")
    print("✨ ระบบควบคุมคลังหนังสืออัจฉริยะฉบับเสถียร (All-in-One) ✨")
    print("=======================================================")
    
    prepare_and_move_files()      # จบข้อ 1: เตรียม หั่น ย้าย รักษาต้นฉบับ
    build_databases_and_covers()  # จบข้อ 2: เจนปก นำเข้า JSON นับจำนวนเล่มและยุบรวมหมวดหมู่ _Vol อัตโนมัติ (แก้ไขบั๊กปกหาย)
    auto_git_push_all()           # จบข้อ 3: ทยอยกวาดและผลักขึ้น GitHub
    
    print("\n🎉 [เสร็จสิ้นทุกขั้นตอน] ทุกอย่างถูกจัดการและส่งขึ้น GitHub เรียบร้อยแล้วครับคุณ Runnara!") 