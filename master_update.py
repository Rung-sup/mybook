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
MAX_FILE_SIZE_MB = 95  # ⚠️ ป้องกันไฟล์เกิน 100MB ของ GitHub

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    normalized_path = unicodedata.normalize('NFC', path_slash)
    fixed_path = normalized_path.replace('\u0e4d\u0e32', '\u0e33') 
    return hashlib.md5(fixed_path.encode('utf-8')).hexdigest()

def main():
    if not os.path.exists(output_root): os.makedirs(output_root)
    all_books, all_music, seen_sizes, valid_cover_ids = [], [], {}, set()
    large_files_warning = []

    print(f"🚀 [System] กำลังสแกนคลังสื่อและตรวจสอบความปลอดภัย...")

    if not os.path.exists(library_path):
        print(f"❌ ไม่พบโฟลเดอร์ Library ที่: {library_path}")
        return

    categories = [d for d in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, d))]
    print(f"DEBUG: พบโฟลเดอร์ใน Library ทั้งหมด: {categories}")
    for cat in categories:
        if cat in ['covers', '.git', '.github', 'metadata', 'scripts']: continue
        cat_path = os.path.join(library_path, cat)
        
        if cat.startswith("7_"):
            # 🎵 หมวดเพลง
            for root, dirs, files in os.walk(cat_path):
                dirs[:] = [d for d in dirs if d not in ['metadata', '.git', '.github', 'scripts']]
                for file_name in files:
                    if file_name.lower().endswith(('.mp3', '.m4a', '.flac', '.wav')):
                        full_path = os.path.join(root, file_name)
                        f_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        
                        if f_size_mb > MAX_FILE_SIZE_MB:
                            large_files_warning.append(f"[MUSIC] {file_name} ({f_size_mb:.2f} MB)")
                            continue

                        rel_path_from_cat = os.path.relpath(full_path, cat_path)
                        url_path = rel_path_from_cat.replace('\\', '/')
                        safe_url_path = urllib.parse.quote(url_path)
                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))
                        valid_cover_ids.add(cover_id)
                        
                        path_parts = rel_path_from_cat.split(os.sep)
                        folder_artist = path_parts[1] if (path_parts[0] == 'audio_files' and len(path_parts) > 1) else (path_parts[0] if len(path_parts) > 1 else "ทั่วไป")

                        all_music.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url_path}",
                            "category": cat, "folder": folder_artist, "cover_id": cover_id, "is_music": True
                        })
        else:
            # 📚 หมวดหนังสือ
            print(f"📂 กำลังสแกนหมวด: {cat}")
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
                        url_path = rel_path_from_cat.replace('\\', '/')
                        safe_url_path = urllib.parse.quote(url_path)
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
                            except: continue

                        all_books.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url_path}",
                            "category": cat, "folder": rel_path_from_cat.split(os.sep)[0] if len(rel_path_from_cat.split(os.sep)) > 1 else "",
                            "cover_id": cover_id, "file_size": f_size_bytes
                        })

    # --- ส่วนแสดงคำเตือน ---
    if large_files_warning:
        print("\n" + "!"*50)
        print("⚠️  พบไฟล์ที่มีขนาดใหญ่เกินกำหนด (95MB) !!!")
        print("ไฟล์เหล่านี้จะไม่ถูกนำลงฐานข้อมูล:")
        for warn in large_files_warning:
            print(f"   - {warn}")
        print("!"*50 + "\n")

    # --- ส่วนบันทึกไฟล์ (ที่หายไป) ---
    final_db = {
        "books": all_books,
        "music": all_music,
        "total_books": len(all_books),
        "total_music": len(all_music)
    }

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(final_db, f, ensure_ascii=False, indent=4)

    print(f"\n✨ [Summary Report]")
    print(f"📖 หนังสือ: {len(all_books)} เล่ม")
    print(f"🎵 เพลง: {len(all_music)} รายการ")
    print(f"✅ อัปเดตข้อมูลลง {db_path} เรียบร้อยแล้ว!")

if __name__ == "__main__":
    main()