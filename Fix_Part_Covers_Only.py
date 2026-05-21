import os
import sys
import json
import shutil
import hashlib
import unicodedata
import re
import urllib.parse
from pdf2image import convert_from_path

# ==========================================
# ⚙️ CONFIGURATION (ตั้งค่าพิกัดหลัก)
# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GITHUB_USER = "rung-sup"

def normalize_text(text):
    return unicodedata.normalize('NFC', text.strip()).replace('\u0e4d\u0e32', '\u0e33')

def generate_cover_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
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

def rebuild_precise_db_and_covers():
    print("=======================================================")
    print("🔄 เริ่มระบบอัปเดตฐานข้อมูล JSON และผูกลิงก์หน้าปกตรงห้องจริง 🔄")
    print("=======================================================")
    
    all_books, all_music = [], []
    covers_root_dir = os.path.join(DB_DIR, 'covers')

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers', '.github']: continue

        # หมวดหมู่สำหรับแสดงผลกลุ่มในแอป (ยุบรวม)
        display_category = re.sub(r'_Vol\d+$', '', cat_folder, flags=re.IGNORECASE)
        folder_info = {}
        part_one_images = {}
        pending_parts = []

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = "ทั่วไป" if rel_f == "." else normalize_text(rel_f)
            
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')): continue
                full_p = os.path.join(root, f)
                
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                c_id = generate_cover_id(rel_from_library)
                
                if f.lower().endswith('.pdf'):
                    cover_dir = os.path.join(covers_root_dir, cat_folder)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    
                    part_match = re.search(r'^(.*)_part_(\d+)$', os.path.splitext(f)[0], flags=re.IGNORECASE)
                    
                    if part_match:
                        base_story = normalize_text(part_match.group(1)).lower()
                        part_num = int(part_match.group(2))
                        
                        if part_num == 1:
                            if not os.path.exists(cover_out) and os.path.exists(POPPLER_PATH):
                                try:
                                    imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                                    if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                                except: pass
                            part_one_images[base_story] = cover_out
                        else:
                            pending_parts.append({"base_story": base_story, "cover_out": cover_out})
                    else:
                        if not os.path.exists(cover_out) and os.path.exists(POPPLER_PATH):
                            try:
                                imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                                if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                            except: pass

                    if folder_disp != "ทั่วไป":
                        if folder_disp not in folder_info:
                            folder_info[folder_disp] = {"first_pdf": full_p, "count": 0}
                        folder_info[folder_disp]["count"] += 1

                # คัดลอกปกพาร์ทหลักให้พาร์ทย่อย
                for part in pending_parts:
                    b_story = part["base_story"]
                    t_img = part["cover_out"]
                    if b_story in part_one_images and os.path.exists(part_one_images[b_story]) and not os.path.exists(t_img):
                        try: shutil.copy2(part_one_images[b_story], t_img)
                        except: pass

                path_in_repo = os.path.relpath(full_p, cat_path).replace('\\', '/')
                file_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{cat_folder}/main/{urllib.parse.quote(path_in_repo)}"

                item_data = {
                    "title": normalize_text(os.path.splitext(f)[0]),
                    "url": file_url,
                    "category": display_category,
                    "folder": folder_disp,
                    "cover_id": c_id,
                    "file_hash": get_file_hash(full_p),
                    "cover_folder_path": cat_folder  # 📌 เพิ่มคีย์พิเศษส่งให้ตัวแอปใช้วิ่งไปดึงรูปจากโฟลเดอร์คลังจริงบน GitHub ได้ถูกต้อง
                }
                
                if cat_folder.startswith("7_") or f.lower().endswith('.mp3'):
                    all_music.append(item_data)
                else:
                    all_books.append(item_data)

    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=2)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=2)
    print("✅ อัปเดตโครงสร้างลิงก์เชื่อมโยงปกในฐานข้อมูล JSON สำเร็จเรียบร้อย!")

if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    rebuild_precise_db_and_covers()