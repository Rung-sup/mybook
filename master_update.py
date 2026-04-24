import os
import json
import hashlib
import unicodedata
import urllib.parse

# --- Settings ---
library_path = r'C:\MyLibrary'
db_path = 'database.json'
music_db_path = r'C:\MyLibrary\7_music\metadata\music_db.json'
github_user = "rung-sup"
MAX_FILE_SIZE_MB = 95

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    normalized_path = unicodedata.normalize('NFC', path_slash)
    fixed_path = normalized_path.replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(fixed_path.encode('utf-8')).hexdigest()

def main():
    all_books, all_music = [], []
    large_files_warning = []

    print(f"🚀 [System] กำลังอัปเดตฐานข้อมูล (รองรับ .wma)...")

    if not os.path.exists(library_path):
        print(f"❌ ไม่พบ Library: {library_path}"); return

    categories = [d for d in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, d))]
    
    for cat in categories:
        if cat in ['covers', '.git', '.github', 'metadata', 'scripts']: continue
        cat_path = os.path.join(library_path, cat)
        
        # 🎵 หมวดเพลง (รองรับ 7_ ทุกรูปแบบ)
        if cat.startswith("7"):
            print(f"🔗 สแกนห้องเพลง: {cat}")
            for root, dirs, files in os.walk(cat_path):
                for file_name in files:
                    allowed_ext = ('.mp3', '.m4a', '.flac', '.wav', '.aac', '.wma')
                    if file_name.lower().endswith(allowed_ext):
                        full_path = os.path.join(root, file_name)
                        f_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        
                        if f_size_mb > MAX_FILE_SIZE_MB:
                            continue
                        
                        rel_path = os.path.relpath(full_path, cat_path)
                        clean_path = rel_path.replace('\\', '/')
                        safe_url = urllib.parse.quote(clean_path)
                        cover_id = generate_cover_id(os.path.join(cat, rel_path))
                        
                        # ✅ แก้ไขจุดนี้: ดึงชื่อโฟลเดอร์ย่อยมาเป็นชื่อ "Album" หรือ "Folder"
                        # ถ้าเพลงอยู่ใน 7_music_Vol2/audio_files/สามก๊ก/01.mp3
                        # path_parts จะช่วยแยกชื่อ "สามก๊ก" ออกมาครับ
                        path_parts = rel_path.split(os.sep)
                        folder_name = path_parts[-2] if len(path_parts) > 1 else "ทั่วไป"

                        all_music.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}",
                            "category": cat,
                            "folder": folder_name, # ✅ ส่งชื่อโฟลเดอร์ (เช่น สามก๊ก) ไปให้แอป
                            "cover_id": cover_id, 
                            "is_music": True
                        })

        # 📚 หมวดหนังสือ
        else:
            print(f"📂 กำลังสแกนหมวดหนังสือ: {cat}")
            for root, dirs, files in os.walk(cat_path):
                for file_name in files:
                    if file_name.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file_name)
                        f_size_bytes = os.path.getsize(full_path)
                        if (f_size_bytes / (1024*1024)) > MAX_FILE_SIZE_MB: continue
                        
                        rel_path = os.path.relpath(full_path, cat_path)
                        clean_path = rel_path.replace('\\', '/')
                        safe_url = urllib.parse.quote(clean_path)
                        cover_id = generate_cover_id(os.path.join(cat, rel_path))
                        
                        all_books.append({
                            "title": os.path.splitext(file_name)[0], 
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}", 
                            "category": cat, 
                            "cover_id": cover_id, 
                            "file_size": f_size_bytes
                        })

    # --- บันทึกทั้ง 2 ไฟล์ ---
    db_content = {"books": all_books, "music": all_music, "total_books": len(all_books), "total_music": len(all_music)}
    music_content = {"music": all_music, "total_music": len(all_music)}

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db_content, f, ensure_ascii=False, indent=4)
    
    with open(music_db_path, 'w', encoding='utf-8') as f:
        json.dump(music_content, f, ensure_ascii=False, indent=4)

    if large_files_warning:
        print(f"\n⚠️ ไฟล์เพลงใหญ่เกิน 95MB และถูกข้ามไป {len(large_files_warning)} ไฟล์")

    print(f"\n✨ [Summary] อัปเดตเสร็จสิ้น!")
    print(f"📊 รวมหนังสือ: {len(all_books)} | รวมเพลง: {len(all_music)}")

if __name__ == "__main__":
    main()