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
    all_books, all_music, seen_sizes = [], [], {}
    large_files_warning = []

    print(f"🚀 [System] เริ่มการเชื่อมต่อสายไฟคลังสื่อ...")

    if not os.path.exists(library_path):
        print(f"❌ ไม่พบ Library: {library_path}"); return

    # ดึงรายชื่อโฟลเดอร์ทั้งหมดใน MyLibrary
    categories = [d for d in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, d))]
    
    for cat in categories:
        if cat in ['covers', '.git', '.github', 'metadata', 'scripts']: continue
        cat_path = os.path.join(library_path, cat)
        
        # 🎵 เชื่อมต่อสายไฟหมวดเพลง (รองรับทั้ง 7_ และ 7_vol2)
        if cat.startswith("7"): # ✅ ปรับให้รับทุกโฟลเดอร์ที่ขึ้นต้นด้วย 7
            print(f"🔗 [Connected] กำลังดึงข้อมูลจากห้องเพลง: {cat}")
            music_in_this_cat = 0
            for root, dirs, files in os.walk(cat_path):
                for file_name in files:
                    if file_name.lower().endswith(('.mp3', '.m4a', '.flac', '.wav')):
                        full_path = os.path.join(root, file_name)
                        f_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        
                        if f_size_mb > MAX_FILE_SIZE_MB:
                            large_files_warning.append(f"[MUSIC] {file_name} ({f_size_mb:.2f} MB)")
                            continue
                        
                        rel_path_from_cat = os.path.relpath(full_path, cat_path)
                        clean_path = rel_path_from_cat.replace('\\', '/')
                        safe_url = urllib.parse.quote(clean_path)
                        
                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))
                        
                        all_music.append({
                            "title": os.path.splitext(file_name)[0],
                            # ลิงก์นี้จะชี้ไปที่ Repo ของห้องนั้นๆ โดยตรง (เช่น 7_vol2)
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}",
                            "category": cat, 
                            "cover_id": cover_id, 
                            "is_music": True
                        })
                        music_in_this_cat += 1
            print(f"   💡 พบเพลงใหม่ใน {cat} จำนวน {music_in_this_cat} ไฟล์")

        # 📚 หมวดหนังสือ
        else:
            print(f"📂 สแกนหมวดหนังสือ: {cat}")
            for root, dirs, files in os.walk(cat_path):
                dirs[:] = [d for d in dirs if d not in ['.git', '.github', 'covers']]
                for file_name in files:
                    if file_name.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file_name)
                        f_size_bytes = os.path.getsize(full_path)
                        if (f_size_bytes / (1024*1024)) > MAX_FILE_SIZE_MB:
                            large_files_warning.append(f"[BOOK] {file_name}")
                            continue

                        if f_size_bytes in seen_sizes: continue
                        seen_sizes[f_size_bytes] = file_name
                        
                        rel_path_from_cat = os.path.relpath(full_path, cat_path)
                        clean_path = rel_path_from_cat.replace('\\', '/')
                        safe_url = urllib.parse.quote(clean_path)
                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))
                        
                        all_books.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}",
                            "category": cat,
                            "cover_id": cover_id,
                            "file_size": f_size_bytes
                        })

    # --- บันทึกฐานข้อมูลกลาง ---
    final_db = {
        "books": all_books, 
        "music": all_music, 
        "total_books": len(all_books), 
        "total_music": len(all_music)
    }
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(final_db, f, ensure_ascii=False, indent=4)

    if large_files_warning:
        print(f"\n⚠️ พบไฟล์ใหญ่เกิน {MAX_FILE_SIZE_MB}MB ที่ถูกข้ามไป {len(large_files_warning)} ไฟล์")

    print(f"\n✨ [สำเร็จ] เชื่อมต่อสำเร็จ! รวมหนังสือ {len(all_books)} เล่ม | รวมเพลง {len(all_music)} ไฟล์")

if __name__ == "__main__":
    main()