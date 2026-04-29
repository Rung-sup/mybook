import os
import hashlib
import json
import unicodedata
import urllib.parse
import requests
from pdf2image import convert_from_path

# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
AUDIOBOOK_DB_PATH = os.path.join(DB_DIR, 'audiobook_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GITHUB_USER = "rung-sup"
# ==========================================

def get_yt_thumbnail(url, save_path):
    if os.path.exists(save_path): return True 
    video_id = ""
    if "v=" in url: video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: video_id = url.split("youtu.be/")[1]
    
    if video_id:
        img_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        try:
            r = requests.get(img_url, timeout=10)
            if r.status_code == 200:
                with open(save_path, 'wb') as f: f.write(r.content)
                print(f"   ✅ ดึงปกสำเร็จ: {save_path}")
                return True
        except Exception as e: print(f"   ❌ ดึงปกพลาด: {e}")
    return False

def get_file_hash(f_path):
    hasher = hashlib.md5()
    try:
        with open(f_path, 'rb') as f:
            chunk = f.read(1024 * 1024)
            hasher.update(chunk)
            if os.path.getsize(f_path) > 1024*1024:
                f.seek(-1024 * 1024, os.SEEK_END)
                hasher.update(f.read())
    except: return None
    return hasher.hexdigest()

def generate_cover_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def main():
    print("📊 [2/3] อัปเดตฐานข้อมูล (สแกนใหม่ทั้งหมดเพื่อความสมบูรณ์ 100%)...")
    all_books, all_music, all_audiobooks = [], [], []
    
    for cat in os.listdir(LIBRARY_ROOT):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']: continue
        
        is_audio_cat = cat.startswith("8_") or "audiobook" in cat.lower()

        for root, dirs, files in os.walk(cat_path):
            rel_folder = os.path.relpath(root, cat_path)
            display_folder = "ทั่วไป" if rel_folder == "." else rel_folder

            if is_audio_cat and "links.txt" in files:
                link_path = os.path.join(root, "links.txt")
                with open(link_path, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                
                # ✅ แก้ปัญหาปก: ตัดข้อความส่วนเกินออกจากลิงก์แรก
                first_link = next((line.split()[0].strip() for line in content if "http" in line), "")
                
                cover_id = generate_cover_id(rel_folder)
                cover_dir = os.path.join(DB_DIR, 'covers', cat)
                os.makedirs(cover_dir, exist_ok=True)
                cover_out = os.path.join(cover_dir, f"{cover_id}.jpg")
                
                if first_link: get_yt_thumbnail(first_link, cover_out)

                episodes = []
                current_title = ""
                for line in content:
                    if not line.strip(): continue
                    if "http" in line:
                        # ✅ แก้ปัญหาเสียง: ตัดข้อความส่วนเกินออกจากทุกลิงก์
                        clean_url = line.split()[0].strip()
                        episodes.append({"ep_title": current_title, "ep_url": clean_url})
                    else: current_title = line.strip()

                all_audiobooks.append({
                    "title": rel_folder, "cover_id": cover_id, "category": cat,
                    "episodes": episodes, "type": "audiobook_playlist"
                })
                dirs.clear(); continue 

            for f in files:
                if f.lower().endswith(('.pdf', '.mp3')):
                    full_p = os.path.join(root, f)
                    f_hash = get_file_hash(full_p)
                    cover_id = generate_cover_id(os.path.relpath(full_p, LIBRARY_ROOT))
                    cover_dir = os.path.join(DB_DIR, 'covers', cat)
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_out = os.path.join(cover_dir, f"{cover_id}.jpg")
                    
                    if f.lower().endswith('.pdf') and not os.path.exists(cover_out):
                        try:
                            imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                            if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                        except: pass

                    path_in_repo = os.path.relpath(full_p, cat_path).replace('\\', '/')
                    item_data = {
                        "title": os.path.splitext(f)[0],
                        "url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{cat}/main/{urllib.parse.quote(path_in_repo)}",
                        "category": cat, "folder": display_folder, "cover_id": cover_id, "file_hash": f_hash
                    }
                    if cat.startswith("7_") or f.lower().endswith('.mp3'): all_music.append(item_data)
                    else: all_books.append(item_data)

    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=4)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=4)
    with open(AUDIOBOOK_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"audiobooks": all_audiobooks}, f, ensure_ascii=False, indent=4)
    print("✅ สร้างฐานข้อมูลเสร็จสิ้น ข้อมูลปลอดภัย 100%")

if __name__ == "__main__":
    main()