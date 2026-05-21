import os
import sys
import json
import shutil
import hashlib
import unicodedata
import re
import time
import urllib.parse
from pdf2image import convert_from_path
import fitz  # PyMuPDF

# ==========================================
# ⚙️ CONFIGURATION (ดึงตามพิกัดหลักของคุณ)
# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GITHUB_USER = "rung-sup"

# ==========================================
# 🧰 UTILITIES FUNCTIONS
# ==========================================
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

# ==========================================
# ⚡ MAIN REGENERATE PROCESS
# ==========================================
def force_regenerate_covers_and_db():
    print("=========================================================================")
    print("🔄 เริ่มต้นระบบล้างและเจนรูปปกใหม่ทั้งหมด 100% (แชร์รูปปกพาร์ทแรกให้พาร์ทถัดไป) 🔄")
    print("=========================================================================")
    
    # 🚨 1. เคลียร์โฟลเดอร์เก็บปกเดิมทิ้งทั้งหมด เพื่อความสะอาดของระบบ
    target_covers_dir = os.path.join(DB_DIR, 'covers')
    if os.path.exists(target_covers_dir):
        print("🗑️  กำลังลบโฟลเดอร์ปกเก่าทั้งหมดเพื่อป้องกันข้อมูลตกค้าง...")
        try:
            shutil.rmtree(target_covers_dir)
            time.sleep(1) # หน่วงเวลาให้ Windows คืนทรัพยากรดิสก์
        except Exception as e:
            print(f"⚠️  ไม่สามารถลบโฟลเดอร์ปกบางส่วนได้ (อาจมีไฟล์ถูกเปิดค้างอยู่): {e}")
    
    os.makedirs(target_covers_dir, exist_ok=True)
    
    all_books, all_music = [], []
    if not os.path.exists(LIBRARY_ROOT):
        print("❌ ไม่พบโฟลเดอร์ MyLibrary ปลายทาง")
        return

    # 2. วนลูปสแกนไฟล์ทั้งหมดในคลังใหม่ตั้งแต่ต้น
    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers', '.github']: continue

        print(f"📁 กำลังประมวลผลคลังห้อง: {cat_folder}...")

        # ใช้ Regex ยุบกลุ่ม _Vol เช่น 4_Chinese_Novel_Vol4 -> 4_Chinese_Novel
        display_category = re.sub(r'_Vol\d+$', '', cat_folder, flags=re.IGNORECASE)
        folder_info = {}
        
        # 📌 พจนานุกรมสำหรับจดจำแมปหน้าปกของเล่มแรก: {"ชื่อฐานไฟล์ย่อย_part_1": "เส้นทางรูปปกจริง"}
        part_one_covers = {}

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = "ทั่วไป" if rel_f == "." else normalize_text(rel_f)
            
            # เรียงไฟล์เพื่อให้ Part_1 มาถึงและถูกประมวลผลก่อน Part ถัด ๆ ไปเสมอ
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')): continue
                full_p = os.path.join(root, f)
                
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                c_id = generate_cover_id(rel_from_library)
                
                if f.lower().endswith('.pdf'):
                    cover_dir = os.path.join(target_covers_dir, cat_folder)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    
                    # ตรวจสอบว่าเป็นไฟล์ที่ถูกหั่นแบ่งพาร์ทหรือไม่ด้วย Regex
                    # เช่น "MyStory_Part_2.pdf" จะจับกลุ่มได้ base_story="MyStory" และ part_num="2"
                    part_match = re.search(r'^(.*)_part_(\d+)$', os.path.splitext(f)[0], flags=re.IGNORECASE)
                    
                    if part_match:
                        base_story = normalize_text(part_match.group(1)).lower()
                        part_num = int(part_match.group(2))
                        
                        if part_num == 1:
                            # 🌟 เล่มแรก (Part 1): เจนปกจากหน้าแรกตามปกติ แล้วบันทึกพิกัดเก็บไว้ให้เพื่อนร่วมพาร์ท
                            if os.path.exists(POPPLER_PATH):
                                try:
                                    imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                                    if imgs: 
                                        imgs[0].save(cover_out, 'JPEG', quality=85)
                                        part_one_covers[base_story] = cover_out  # บันทึกพิกัดปกหลักไว้
                                except Exception as e:
                                    print(f"   ❌ ไม่สามารถดึงปกจากพาร์ทแรก {f} ได้: {e}")
                        else:
                            # 🌟 เล่มถัดมา (Part 2, 3, ...): ไม่เจนหน้าแรกของตัวเอง แต่ไปก๊อปปี้ไฟล์ปกจาก Part 1 มาสวมแทน
                            if base_story in part_one_covers and os.path.exists(part_one_covers[base_story]):
                                try:
                                    shutil.copy2(part_one_covers[base_story], cover_out)
                                except Exception as e:
                                    print(f"   ❌ เกิดข้อผิดพลาดในการสำเนารูปปกให้ {f}: {e}")
                            else:
                                # กรณีหลุดคิวหรือหาเล่ม 1 ไม่เจอ ให้เจนปกตัวเองเป็นกรณีสำรอง
                                if os.path.exists(POPPLER_PATH):
                                    try:
                                        imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                                        if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                                    except: pass
                    else:
                        # หนังสือเล่มเดี่ยวปกติ ไม่ได้แบ่งพาร์ท เจนตามปกติ
                        if os.path.exists(POPPLER_PATH):
                            try:
                                imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                                if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                            except Exception as e:
                                print(f"   ❌ ไม่สามารถดึงปกจากไฟล์ {f} ได้: {e}")
                    
                    # 📊 เก็บข้อมูลสำหรับทำปกประจำโฟลเดอร์ย่อย
                    if folder_disp != "ทั่วไป":
                        if folder_disp not in folder_info:
                            folder_info[folder_disp] = {"first_pdf": full_p, "count": 0}
                        folder_info[folder_disp]["count"] += 1

                # คำนวณพิกัด URL สำหรับส่งขึ้น GitHub raw ให้ตรงห้องจริง
                path_in_repo = os.path.relpath(full_p, cat_path).replace('\\', '/')
                file_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{cat_folder}/main/{urllib.parse.quote(path_in_repo)}"

                item_data = {
                    "title": normalize_text(os.path.splitext(f)[0]),
                    "url": file_url,
                    "category": display_category,  # ยุบรวมเข้าหมวดหลักในแอป
                    "folder": folder_disp,
                    "cover_id": c_id,
                    "file_hash": get_file_hash(full_p),
                    "_raw_cat": cat_folder
                }
                
                if cat_folder.startswith("7_") or f.lower().endswith('.mp3'): 
                    all_music.append(item_data)
                else: 
                    all_books.append(item_data)

        # เจนปกประจำกลุ่มโฟลเดอร์ย่อยยึดตามหน้าแรกของหนังสือเล่มแรกในกลุ่ม
        for folder_name, info in folder_info.items():
            try:
                folder_rel_path = os.path.join(cat_folder, folder_name)
                folder_cover_id = generate_cover_id(folder_rel_path)
                
                folder_cover_out = os.path.join(target_covers_dir, cat_folder, f"folder_{folder_cover_id}.jpg")
                
                if os.path.exists(POPPLER_PATH):
                    imgs = convert_from_path(info["first_pdf"], first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                    if imgs:
                        imgs[0].save(folder_cover_out, 'JPEG', quality=85)
                        print(f"   📸 เจนปกโฟลเดอร์ย่อยสำเร็จ: [{folder_name}] (มี {info['count']} เล่ม)")

                for book in all_books:
                    if book["_raw_cat"] == cat_folder and book["folder"] == folder_name:
                        book["folder_cover_id"] = f"folder_{folder_cover_id}"
                        book["folder_book_count"] = info["count"]

            except Exception as e:
                print(f"   ⚠️  เกิดข้อผิดพลาดกับปกโฟลเดอร์ {folder_name}: {e}")

    # ล้างคีย์ชั่วคราวออกก่อนเซฟเข้าระบบ JSON
    for book in all_books: book.pop("_raw_cat", None)
    for music in all_music: music.pop("_raw_cat", None)

    # 3. เขียนทับไฟล์ฐานข้อมูล JSON ใหม่ทั้งหมดเพื่อเคลียร์สารบัญเก่า
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f: 
        json.dump({"books": all_books}, f, ensure_ascii=False, indent=2)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: 
        json.dump({"music": all_music}, f, ensure_ascii=False, indent=2)
        
    print("\n=======================================================")
    print(f"✅ ล้างคลังและเจนปกใหม่เสร็จสิ้น! หนังสือ {len(all_books)} เล่ม, เพลง {len(all_music)} รายการ")
    print("👉 ล็อกหน้าปกให้ไฟล์หั่นพาร์ทเรียบร้อยแล้ว คุณ Runnara สั่งเปิดแอปดูความสวยงามได้เลยครับ!")
    print("=======================================================")

if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    force_regenerate_covers_and_db()