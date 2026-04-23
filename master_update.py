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

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    normalized_path = unicodedata.normalize('NFC', path_slash)
    fixed_path = normalized_path.replace('\u0e4d\u0e32', '\u0e33') 
    return hashlib.md5(fixed_path.encode('utf-8')).hexdigest()

def main():
    if not os.path.exists(output_root): os.makedirs(output_root)
    all_books, all_music, seen_sizes, valid_cover_ids = [], [], {}, set()

    print(f"🚀 [System] กำลังสแกนคลังสื่อใน {library_path}...")
    categories = [d for d in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, d))]
    
    for cat in categories:
        if cat in ['covers', '.git', '.github', 'metadata', 'scripts']: continue
        cat_path = os.path.join(library_path, cat)
        
        # 🎵 กรณีที่ 1: ตรวจพบว่าเป็น "หมวดเพลง"
        if cat.startswith("7_"):
            print(f"🎵 [Scanning Music] -> {cat}")
            for root, dirs, files in os.walk(cat_path):
                dirs[:] = [d for d in dirs if d not in ['metadata', '.git', '.github', 'scripts']]
                for file_name in files:
                    if file_name.lower().endswith(('.mp3', '.m4a', '.flac', '.wav')):
                        full_path = os.path.join(root, file_name)
                        rel_path_from_cat = os.path.relpath(full_path, cat_path)
                        
                        # ✅ แก้ไข SyntaxError: ย้ายการ replace ออกมาข้างนอก f-string
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

        # 📚 กรณีที่ 2: ตรวจพบว่าเป็น "หมวดหนังสือ"
        else:
            print(f"📚 [Scanning Books] -> {cat}")
            for root, dirs, files in os.walk(cat_path):
                dirs[:] = [d for d in dirs if d not in ['.git', '.github', 'covers']]
                for file_name in files:
                    if file_name.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file_name)
                        f_size = os.path.getsize(full_path)
                        if f_size in seen_sizes: continue
                        seen_sizes[f_size] = file_name

                        rel_path_from_cat = os.path.relpath(full_path, cat_path)
                        
                        # ✅ แก้ไข SyntaxError: ย้ายการ replace ออกมาข้างนอก f-string
                        url_path = rel_path_from_cat.replace('\\', '/')
                        safe_url_path = urllib.parse.quote(url_path)

                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))
                        valid_cover_ids.add(cover_id)
                        
                        cat_cover_dir = os.path.join(output_root, cat)
                        os.makedirs(cat_cover_dir, exist_ok=True)
                        if not os.path.exists(os.path.join(cat_cover_dir, f"{cover_id}.jpg")):
                            try:
                                images = convert_from_path(full_path, first_page=1, last_page=1, size=(None, 400), poppler_path=poppler_path)
                                if images: images[0].save(os.path.join(cat_cover_dir, f"{cover_id}.jpg"), 'JPEG', quality=85)
                                print(f"   📸 สร้างปกใหม่: {file_name}")
                            except: continue

                        all_books.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url_path}",
                            "category": cat, "folder": rel_path_from_cat.split(os.sep)[0] if len(rel_path_from_cat.split(os.sep)) > 1 else "",
                            "cover_id": cover_id, "file_size": f_size
                        })

    print("🧹 Cleaning up unused covers...")
    for root_dir, _, files in os.walk(output_root):
        for f in files:
            if f.endswith('.jpg') and os.path.splitext(f)[0] not in valid_cover_ids:
                try: os.remove(os.path.join(root_dir, f))
                except: pass

    final_db = {"books": all_books, "music": all_music, "total_books": len(all_books), "total_music": len(all_music)}
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(final_db, f, ensure_ascii=False, indent=4)

    print(f"\n✨ [Summary Report]\n📖 Books: {len(all_books)} items\n🎵 Music: {len(all_music)} items\n✅ Database updated!")

if __name__ == "__main__":
    main()