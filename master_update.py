import os

import json

import hashlib

import unicodedata

import urllib.parse

from pdf2image import convert_from_path



# ==========================================

# ⚙️ GLOBAL SETTINGS

# ==========================================

library_path = r'C:\MyLibrary'

db_path = 'database.json'

output_root = 'covers'

poppler_path = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'

github_user = "rung-sup"

MAX_FILE_SIZE_MB = 95



def generate_cover_id(relative_path):

    path_slash = relative_path.replace('\\', '/')

    normalized_path = unicodedata.normalize('NFC', path_slash)

    fixed_path = normalized_path.replace('\u0e4d\u0e32', '\u0e33')

    return hashlib.md5(fixed_path.encode('utf-8')).hexdigest()



def main():

    if not os.path.exists(output_root): os.makedirs(output_root)

    all_books, all_music, seen_sizes, valid_cover_ids = [], [], {}, set()

    large_files_warning = []



    print(f"🚀 [System] กำลังสแกนคลังสื่อแบบเจาะลึก (Deep Scan)...")



    if not os.path.exists(library_path):

        print(f"❌ ไม่พบโฟลเดอร์ Library ที่: {library_path}"); return



    categories = [d for d in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, d))]

   

    for cat in categories:

        if cat in ['covers', '.git', '.github', 'metadata', 'scripts']: continue

        cat_path = os.path.join(library_path, cat)

       

        # 🎵 หมวดเพลง (7_)

        if cat.startswith("7_"):

            for root, dirs, files in os.walk(cat_path):

                dirs[:] = [d for d in dirs if d not in ['metadata', '.git', '.github']]

                for file_name in files:

                    if file_name.lower().endswith(('.mp3', '.m4a', '.flac', '.wav')):

                        full_path = os.path.join(root, file_name)

                        f_size_mb = os.path.getsize(full_path) / (1024 * 1024)

                        if f_size_mb > MAX_FILE_SIZE_MB:

                            large_files_warning.append(f"[MUSIC] {file_name} ({f_size_mb:.2f} MB)")

                            continue

                       

                        rel_path_from_cat = os.path.relpath(full_path, cat_path)

                        # ✅ แก้ไข: แยกการจัดการ Path ออกจาก f-string

                        clean_path = rel_path_from_cat.replace('\\', '/')

                        safe_url = urllib.parse.quote(clean_path)

                       

                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))

                        valid_cover_ids.add(cover_id)

                       

                        all_music.append({

                            "title": os.path.splitext(file_name)[0],

                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}",

                            "category": cat, "cover_id": cover_id, "is_music": True

                        })



        # 📚 หมวดหนังสือ (สแกนลึกถึงโฟลเดอร์ย่อย)

        else:

            print(f"📂 กำลังสแกนหมวดหนังสือ: {cat}")

            for root, dirs, files in os.walk(cat_path):

                dirs[:] = [d for d in dirs if d not in ['.git', '.github', 'covers']]

                for file_name in files:

                    if file_name.lower().endswith('.pdf'):

                        full_path = os.path.join(root, file_name)

                        f_size_bytes = os.path.getsize(full_path)

                        f_size_mb = f_size_bytes / (1024 * 1024)



                        if f_size_mb > MAX_FILE_SIZE_MB:

                            large_files_warning.append(f"[BOOK] {file_name} ({f_size_mb:.2f} MB)")

                            continue



                        if f_size_bytes in seen_sizes: continue

                        seen_sizes[f_size_bytes] = file_name



                        rel_path_from_cat = os.path.relpath(full_path, cat_path)

                        # ✅ แก้ไข: แยกการจัดการ Path ออกจาก f-string

                        clean_path = rel_path_from_cat.replace('\\', '/')

                        safe_url = urllib.parse.quote(clean_path)

                       

                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))

                        valid_cover_ids.add(cover_id)

                       

                        cat_cover_dir = os.path.join(output_root, cat)

                        os.makedirs(cat_cover_dir, exist_ok=True)

                        cover_file_path = os.path.join(cat_cover_dir, f"{cover_id}.jpg")

                       

                        if not os.path.exists(cover_file_path):

                            try:

                                images = convert_from_path(full_path, first_page=1, last_page=1, size=(None, 400), poppler_path=poppler_path)

                                if images:

                                    images[0].save(cover_file_path, 'JPEG', quality=85)

                                    print(f"   📸 สร้างปกใหม่: {file_name}")

                            except:

                                print(f"   ❌ [ข้ามไฟล์เสีย] {file_name}")

                                continue



                        all_books.append({

                            "title": os.path.splitext(file_name)[0],

                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}",

                            "category": cat,

                            "folder": rel_path_from_cat.split(os.sep)[0] if len(rel_path_from_cat.split(os.sep)) > 1 else "",

                            "cover_id": cover_id,

                            "file_size": f_size_bytes

                        })



    # --- บันทึกผล ---

    if large_files_warning:

        print("\n⚠️ ไฟล์ใหญ่เกิน 95MB (ถูกข้าม):")

        for warn in large_files_warning: print(f"   - {warn}")



    final_db = {"books": all_books, "music": all_music, "total_books": len(all_books), "total_music": len(all_music)}

    with open(db_path, 'w', encoding='utf-8') as f:

        json.dump(final_db, f, ensure_ascii=False, indent=4)



    print(f"\n✨ [Summary] หนังสือ: {len(all_books)} | เพลง: {len(all_music)} | บันทึกสำเร็จ!")



if __name__ == "__main__":

    main()