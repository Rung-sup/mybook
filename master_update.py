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
base_domain = "https://rung-sup.github.io"
poppler_path = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'

# --- ฟังก์ชันดึงและอัปเดตข้อมูลเพลงอัตโนมัติ (7_music) ---
def get_external_music():
    """สแกนไฟล์เพลงจริงในโฟลเดอร์ 7_music และอัปเดต music_db.json อัตโนมัติ"""
    music_dir = os.path.join(library_path, "7_music")
    music_json_path = os.path.join(music_dir, "metadata", "music_db.json")
    music_list = []
    
    if not os.path.exists(music_dir):
        print("⚠️ [Music] ไม่พบโฟลเดอร์ 7_music")
        return []

    print("🎵 [Music] กำลังสแกนไฟล์เพลงและอัปเดตฐานข้อมูลเพลง...")
    
    # สแกนหาไฟล์เพลงจริง (.mp3, .m4a, .flac)
    for root, dirs, files in os.walk(music_dir):
        # ข้ามโฟลเดอร์ที่ไม่เกี่ยวข้อง
        dirs[:] = [d for d in dirs if d not in ['metadata', '.git', '.github']]
        
        for file_name in files:
            if file_name.lower().endswith(('.mp3', '.m4a', '.flac')):
                full_path = os.path.join(root, file_name)
                # หา path สัมพัทธ์จาก 7_music
                rel_path_from_music = os.path.relpath(full_path, music_dir)
                
                # สร้าง ID สำหรับปก (ใช้ path สัมพัทธ์จาก MyLibrary เพื่อให้ตรงระบบปก)
                rel_path_from_library = os.path.join("7_music", rel_path_from_music)
                cover_id = generate_cover_id(rel_path_from_library)
                
                # เตรียม URL
                url_path_fixed = rel_path_from_music.replace('\\', '/')
                safe_music_path = urllib.parse.quote(url_path_fixed)
                
                # แยกโฟลเดอร์ (ชื่อนักร้อง/อัลบั้ม)
                path_parts = rel_path_from_music.split(os.sep)
                folder_name = path_parts[0] if len(path_parts) > 1 else "ทั่วไป"

                music_list.append({
                    "title": os.path.splitext(file_name)[0],
                    "url": f"{base_domain}/7_music/{safe_music_path}",
                    "category": "7_music",
                    "folder": folder_name,
                    "cover_id": cover_id,
                    "is_music": True,
                    "path": rel_path_from_music # เก็บไว้ใช้ใน music_db.json เดิม
                })

    # บันทึกอัปเดตลง music_db.json เพื่อให้ Music Room ใช้งานได้
    try:
        os.makedirs(os.path.dirname(music_json_path), exist_ok=True)
        with open(music_json_path, 'w', encoding='utf-8') as f:
            json.dump(music_list, f, ensure_ascii=False, indent=4)
        print(f"✅ [Music] อัปเดต music_db.json สำเร็จ: {len(music_list)} รายการ")
    except Exception as e:
        print(f"⚠️ [Music] ไม่สามารถบันทึก music_db.json: {e}")
        
    return music_list

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    normalized_path = unicodedata.normalize('NFC', path_slash)
    fixed_path = normalized_path.replace('\u0e4d\u0e32', '\u0e33') 
    return hashlib.md5(fixed_path.encode('utf-8')).hexdigest()

def main():
    if not os.path.exists(output_root): os.makedirs(output_root)
    new_db = []
    seen_sizes = {} 
    valid_cover_ids = set()

    print("🚀 [System] เริ่มอัปเดตระบบคลังหนังสือและเพลงของคุณรันนรา...")

    # --- ส่วนการจัดการหนังสือ ---
    for root, dirs, files in os.walk(library_path):
        # ข้ามโฟลเดอร์ที่ไม่เกี่ยวข้อง
        dirs[:] = [d for d in dirs if d not in ['covers', '.git', '.github', '7_music']]
        
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
                url_path_fixed = file_in_repo_path.replace('\\', '/')
                
                normalized_url = unicodedata.normalize('NFC', url_path_fixed).replace('\u0e4d\u0e32', '\u0e33')
                safe_path = urllib.parse.quote(normalized_url)
                final_url = f"{base_domain}/{category}/{safe_path}"

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
                            print(f"📸 สร้างปกใหม่: {file_name}")
                    except:
                        print(f"⚠️ อ่านไม่ได้: {file_name}")
                        continue

                new_db.append({
                    "title": os.path.splitext(file_name)[0],
                    "url": final_url,
                    "category": category,
                    "folder": folder_name,
                    "cover_id": cover_id,
                    "file_size": f_size
                })

    # --- ส่วนการจัดการเพลง (เรียกใช้ฟังก์ชันอัปเดต) ---
    music_list = get_external_music()
    # เก็บ cover_id ของเพลงไว้ด้วยไม่ให้โดนระบบ Clean ลบทิ้ง
    for m in music_list:
        valid_cover_ids.add(m['cover_id'])

    # --- ทำความสะอาดรูปปกที่ไม่ได้ใช้ ---
    for root_dir, _, files in os.walk(output_root):
        for f in files:
            if f.endswith('.jpg'):
                if os.path.splitext(f)[0] not in valid_cover_ids:
                    try: os.remove(os.path.join(root_dir, f))
                    except: pass

    # --- มัดรวมข้อมูลลงฐานข้อมูลหลัก ---
    final_database = {
        "books": new_db,
        "music": music_list,
        "total_books": len(new_db),
        "total_music": len(music_list)
    }

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(final_database, f, ensure_ascii=False, indent=4)

    print(f"\n✨ [Summary]")
    print(f"📚 หนังสือทั้งหมด: {len(new_db)} เล่ม")
    print(f"🎵 เพลงทั้งหมด: {len(music_list)} รายการ")
    print(f"✅ อัปเดตทุกอย่างลง {db_path} และ music_db.json เรียบร้อยแล้ว!")

if __name__ == "__main__":
    main()