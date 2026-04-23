import os
import json
import hashlib
import unicodedata
import urllib.parse
import shutil
from pdf2image import convert_from_path

# ==========================================
# ⚙️ SETTINGS
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

# --- 🔄 ฟังก์ชันอัปเกรด: สแกนเพลงจากทุกโกดัง 7_music ---
def scan_all_music():
    """สแกนหาโฟลเดอร์ที่ขึ้นต้นด้วย 7_music ทั้งหมดและดึงเพลงออกมา"""
    all_music_list = []
    # ค้นหาทุกโฟลเดอร์ใน MyLibrary
    for folder_name in os.listdir(library_path):
        # 💡 [แก้ไข]: ถ้าชื่อโฟลเดอร์ขึ้นต้นด้วย 7_music (เช่น 7_music, 7_music_Vol2)
        if folder_name.startswith("7_music"):
            music_dir = os.path.join(library_path, folder_name)
            if not os.path.isdir(music_dir): continue
            
            print(f"🎵 [Music] กำลังสแกนคลังเพลงจาก: {folder_name}...")
            
            for root, dirs, files in os.walk(music_dir):
                dirs[:] = [d for d in dirs if d not in ['metadata', '.git', '.github', 'scripts']]
                for file_name in files:
                    if file_name.lower().endswith(('.mp3', '.m4a', '.flac', '.wav')):
                        full_path = os.path.join(root, file_name)
                        rel_path_from_category = os.path.relpath(full_path, music_dir)
                        
                        # สร้าง ID สำหรับปก
                        rel_path_from_library = os.path.join(folder_name, rel_path_from_category)
                        cover_id = generate_cover_id(rel_path_from_library)
                        
                        # เตรียม URL
                        url_path_fixed = rel_path_from_category.replace('\\', '/')
                        safe_music_path = urllib.parse.quote(url_path_fixed)
                        
                        # แยกชื่อโฟลเดอร์ (ศิลปิน)
                        path_parts = rel_path_from_category.split(os.sep)
                        # ถ้ามี audio_files ให้ข้ามไปเอาโฟลเดอร์ถัดไป
                        if path_parts[0] == 'audio_files' and len(path_parts) > 1:
                            folder_artist = path_parts[1]
                        else:
                            folder_artist = path_parts[0] if len(path_parts) > 1 else "ทั่วไป"

                        all_music_list.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{folder_name}/main/{safe_music_path}",
                            "category": folder_name,
                            "folder": folder_artist,
                            "cover_id": cover_id,
                            "is_music": True
                        })
    
    # บันทึกไฟล์สำรองไว้ในโฟลเดอร์หลักของ 7_music (ถ้ามี)
    main_music_json = os.path.join(library_path, "7_music", "metadata", "music_db.json")
    if os.path.exists(os.path.dirname(main_music_json)):
        with open(main_music_json, 'w', encoding='utf-8') as f:
            json.dump(all_music_list, f, ensure_ascii=False, indent=4)
            
    return all_music_list

def main():
    if not os.path.exists(output_root): os.makedirs(output_root)
    new_db = []
    seen_sizes = {} 
    valid_cover_ids = set()

    print("🚀 [System] เริ่มอัปเดตระบบคลังหนังสือและเพลงข้ามโกดัง...")

    # --- ส่วนการจัดการหนังสือ ---
    for root, dirs, files in os.walk(library_path):
        # 💡 [แก้ไข]: ข้ามทุกโฟลเดอร์ที่เป็นเพลง (ขึ้นต้นด้วย 7_music)
        dirs[:] = [d for d in dirs if d not in ['covers', '.git', '.github'] and not d.startswith('7_music')]
        
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                full_path = os.path.join(root, file_name)
                f_size = os.path.getsize(full_path)
                if f_size in seen_sizes: continue
                seen_sizes[f_size] = file_name

                rel_path = os.path.relpath(full_path, library_path)
                parts = rel_path.split(os.sep)
                category = parts[0]
                folder_name = parts[1] if len(parts) > 2 else ""
                
                file_in_repo_path = os.path.relpath(full_path, os.path.join(library_path, category))
                safe_path = urllib.parse.quote(file_in_repo_path.replace('\\', '/'))
                final_url = f"https://raw.githubusercontent.com/{github_user}/{category}/main/{safe_path}"

                cover_id = generate_cover_id(rel_path)
                valid_cover_ids.add(cover_id)
                
                cat_dir = os.path.join(output_root, category)
                os.makedirs(cat_dir, exist_ok=True)
                cover_file = os.path.join(cat_dir, f"{cover_id}.jpg")
                
                if not os.path.exists(cover_file):
                    try:
                        images = convert_from_path(full_path, first_page=1, last_page=1, 
                                                 size=(None, 400), poppler_path=poppler_path)
                        if images:
                            images[0].save(cover_file, 'JPEG', quality=85)
                            print(f"📸 สร้างปกหนังสือใหม่: {file_name}")
                    except: continue

                new_db.append({
                    "title": os.path.splitext(file_name)[0], "url": final_url,
                    "category": category, "folder": folder_name,
                    "cover_id": cover_id, "file_size": f_size
                })

    # --- ส่วนการจัดการเพลง (ใช้ฟังก์ชันใหม่ที่สแกนทุก Vol) ---
    music_list = scan_all_music()
    for m in music_list:
        valid_cover_ids.add(m['cover_id'])

    # --- ทำความสะอาดรูปปกที่ไม่ได้ใช้ ---
    for root_dir, _, files in os.walk(output_root):
        for f in files:
            if f.endswith('.jpg'):
                if os.path.splitext(f)[0] not in valid_cover_ids:
                    try: os.remove(os.path.join(root_dir, f))
                    except: pass

    # --- บันทึกลงฐานข้อมูลหลัก ---
    final_database = {
        "books": new_db, "music": music_list,
        "total_books": len(new_db), "total_music": len(music_list)
    }

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(final_database, f, ensure_ascii=False, indent=4)

    print(f"\n✨ [Summary]")
    print(f"📚 หนังสือทั้งหมด: {len(new_db)} เล่ม")
    print(f"🎵 เพลงทั้งหมด: {len(music_list)} รายการ (รวมทุก Vol)")
    print(f"✅ อัปเดตข้อมูลลง {db_path} เรียบร้อยแล้ว!")

if __name__ == "__main__":
    main()