import os
import shutil
import hashlib
import json
import unicodedata
import urllib.parse
import time
import subprocess
import requests  # เพิ่มสำหรับดึงปกจาก YouTube
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
AUDIOBOOK_DB_PATH = os.path.join(DB_DIR, 'audiobook_db.json') # เพิ่มก้อน DB ใหม่
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GS_PATH = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'

GITHUB_USER = "rung-sup"
MAX_SIZE_MB = 95
BATCH_SIZE = 15

# ✅ ฟีเจอร์ดึงปก YouTube อัตโนมัติ
def get_yt_thumbnail(url, save_path):
    if os.path.exists(save_path): return True 
    video_id = ""
    if "v=" in url: video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: video_id = url.split("youtu.be/")[1]
    
    if video_id:
        # เปลี่ยนจาก maxresdefault เป็น hqdefault (ชัวร์กว่า)
        img_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        try:
            r = requests.get(img_url, timeout=10)
            if r.status_code == 200:
                with open(save_path, 'wb') as f: f.write(r.content)
                print(f"   ✅ ดึงปกสำเร็จ: {save_path}")
                return True
        except Exception as e:
            print(f"   ❌ ดึงปกพลาด: {e}")
    return False

def run_git(command, cwd):
    try:
        # 📍 กฎเหล็ก: Timeout 60 วินาที
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=60)
        return result.stdout.strip()
    except: return None

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

def compress_pdf_high(f_path):
    if not os.path.exists(GS_PATH): return False
    temp_out = f_path.replace(".pdf", "_compressed_tmp.pdf")
    gs_cmd = [
        GS_PATH, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        f'-sOutputFile={temp_out}', f_path
    ]
    try:
        subprocess.run(gs_cmd, capture_output=True)
        if os.path.exists(temp_out):
            if os.path.getsize(temp_out) < os.path.getsize(f_path):
                os.remove(f_path)
                os.rename(temp_out, f_path)
                return True
            os.remove(temp_out)
    except: pass
    return False

def split_with_cover_injection(f_path):
    print(f"   ✂️ ไฟล์ยังใหญ่เกินไป! กำลังแบ่งเล่ม...")
    reader = PdfReader(f_path)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(f_path)[0]
    mid = total_pages // 2
    
    w1 = PdfWriter()
    for i in range(0, mid): w1.add_page(reader.pages[i])
    path1 = f"{base_name} Part 1.1.pdf"
    with open(path1, "wb") as f: w1.write(f)
    
    w2 = PdfWriter()
    w2.add_page(reader.pages[0])
    for i in range(mid, total_pages): w2.add_page(reader.pages[i])
    path2 = f"{base_name} Part 1.2.pdf"
    with open(path2, "wb") as f: w2.write(f)
    
    os.remove(f_path)
    return [path1, path2]

def generate_cover_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def main():
    existing_hashes = {}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            try:
                old_db = json.load(f)
                for b in old_db.get('books', []):
                    if 'file_hash' in b: existing_hashes[b['file_hash']] = b['title']
            except: pass

    # --- STEP 1: SMART PROCESS & MOVE ---
    print("🛠 [1/3] กำลังตรวจสอบไฟล์ระบบ Hash & Compression...")
    for cat in os.listdir(PROCESS_ZONE):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        os.makedirs(target_lib, exist_ok=True)

        for item in os.listdir(cat_staging):
            f_path = os.path.join(cat_staging, item)
            if not os.path.isdir(f_path):
                f_hash = get_file_hash(f_path)
                if f_hash in existing_hashes:
                    print(f"   🗑️ พบไฟล์ซ้ำ: {item}")
                    os.remove(f_path); continue

            # 📍 กฎเหล็ก: คุมขนาด 95MB เฉพาะ PDF
            if item.lower().endswith('.pdf'):
                if os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
                    compress_pdf_high(f_path)
                    if os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
                        split_with_cover_injection(f_path); continue

            dest = os.path.join(target_lib, item)
            if os.path.isdir(f_path):
                if os.path.exists(dest):
                    for sub in os.listdir(f_path):
                        s_src = os.path.join(f_path, sub)
                        s_dst = os.path.join(dest, sub)
                        if not os.path.exists(s_dst): shutil.move(s_src, s_dst)
                    shutil.rmtree(f_path)
                else: shutil.move(f_path, dest)
            else:
                if os.path.exists(dest): os.remove(f_path)
                else: shutil.move(f_path, dest)

    # --- STEP 2: UPDATE DB & AUDIOBOOKS (Optimized & Safe Version) ---
    print("📊 [2/3] อัปเดตฐานข้อมูล (สแกนเฉพาะส่วนที่มีการเปลี่ยนแปลง)...")
    all_books, all_music, all_audiobooks = [], [], []

    # ✅ ดึงข้อมูลเดิมจากไฟล์ JSON มาเก็บไว้ก่อน เพื่อไม่ให้รายการเก่าหายเวลา Skip ห้อง
    try:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r', encoding='utf-8') as f: all_books = json.load(f).get('books', [])
        if os.path.exists(MUSIC_DB_PATH):
            with open(MUSIC_DB_PATH, 'r', encoding='utf-8') as f: all_music = json.load(f).get('music', [])
        if os.path.exists(AUDIOBOOK_DB_PATH):
            with open(AUDIOBOOK_DB_PATH, 'r', encoding='utf-8') as f: all_audiobooks = json.load(f).get('audiobooks', [])
    except: print("   ⚠️ ไม่สามารถโหลดข้อมูลเดิมได้ จะเริ่มสร้างใหม่ทั้งหมด")

    for cat in os.listdir(LIBRARY_ROOT):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']: continue
        
        # 🔍 ตรวจสอบความเปลี่ยนแปลงด้วย Git Status[cite: 1]
        repo_changes = run_git("git status --porcelain", cat_path)
        is_audio_cat = cat.startswith("8_") or "audiobook" in cat.lower()
        
        # ถ้าไม่มีอะไรเปลี่ยน ให้ใช้ข้อมูลเดิม (Skip สแกน)[cite: 1]
        if not repo_changes and not is_audio_cat:
            print(f"   ⏩ ข้ามการสแกนห้อง: {cat} (ใช้ข้อมูลเดิมจาก Database)")
            continue

        # 🧹 ล้างรายการเก่าของเฉพาะ "ห้องที่กำลังจะสแกนใหม่" เพื่อป้องกันข้อมูลซ้ำ
        if is_audio_cat: all_audiobooks = [b for b in all_audiobooks if b['category'] != cat]
        elif cat.startswith("7_"): all_music = [m for m in all_music if m['category'] != cat]
        else: all_books = [b for b in all_books if b['category'] != cat]

        print(f"   🔎 กำลังสแกนความเปลี่ยนแปลงใน: {cat}")
        for root, dirs, files in os.walk(cat_path):
            rel_folder = os.path.relpath(root, cat_path)
            display_folder = "ทั่วไป" if rel_folder == "." else rel_folder

            if is_audio_cat and "links.txt" in files:
                link_path = os.path.join(root, "links.txt")
                with open(link_path, 'r', encoding='utf-8') as f:
                    content = f.read().splitlines()
                
                # 🧼 ล้าง URL ให้สะอาด (ตัดข้อความหลังช่องว่าง/วงเล็บออก)
                valid_links = [line.split()[0].strip() for line in content if "http" in line]
                first_link = valid_links[0] if valid_links else ""
                
                cover_id = generate_cover_id(rel_folder)
                cover_dir = os.path.join(DB_DIR, 'covers', cat)
                os.makedirs(cover_dir, exist_ok=True)
                cover_out = os.path.join(cover_dir, f"{cover_id}.jpg")
                
                if first_link: get_yt_thumbnail(first_link, cover_out) # ดึงปกใหม่[cite: 1]

                episodes = []
                current_title = ""
                for line in content:
                    if not line.strip(): continue
                    if "http" in line:
                        clean_url = line.split()[0].strip() # URL ที่สะอาดสำหรับเล่นเสียง
                        episodes.append({"ep_title": current_title, "ep_url": clean_url})
                    else: current_title = line.strip()

                all_audiobooks.append({
                    "title": rel_folder, "cover_id": cover_id, "category": cat,
                    "episodes": episodes, "type": "audiobook_playlist"
                })
                dirs.clear(); continue 

            # PDF & MP3 ส่วนที่เหลือ
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

            # PDF & MP3 เดิม
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

    # บันทึก JSON
    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=4)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=4)
    with open(AUDIOBOOK_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"audiobooks": all_audiobooks}, f, ensure_ascii=False, indent=4)

   # --- STEP 3: FULL SYNC (Optimized Version) ---
    print("\n☁️ [3/3] กำลังทยอยส่งข้อมูลขึ้น Cloud (เฉพาะห้องที่มีการเปลี่ยนแปลง)...")
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.exists(os.path.join(f_p, ".git")):
            
            # 🔍 ตรวจเช็กว่ามีความเปลี่ยนแปลงในโฟลเดอร์นี้หรือไม่
            status = run_git("git status --porcelain", f_p)
            
            if status: # ถ้ามีไฟล์ใหม่หรือมีการแก้ไขไฟล์
                print(f"🚀 ตรวจพบการเปลี่ยนแปลง กำลังส่งห้อง: {folder}")
                run_git("git add .", f_p)
                # ใช้ commit message ที่ระบุวันที่/เวลา เพื่อความชัดเจนในประวัติการแก้ไข
                run_git(f'git commit -m "Auto-sync update {time.strftime("%Y-%m-%d %H:%M")}"', f_p)
                try:
                    # พยายามส่งข้อมูลขึ้น Cloud
                    subprocess.run("git push origin HEAD -f", cwd=f_p, shell=True, timeout=300)
                except: 
                    print(f"   ⚠️ {folder} Timeout")
            else:
                # ถ้าไม่มีอะไรเปลี่ยน จะข้ามห้องนี้ไปทันที ไม่ต้องเสียเวลาเชื่อมต่อ Git
                print(f"✅ ห้อง {folder} เป็นปัจจุบันแล้ว (Skip)")

    if os.path.exists(os.path.join(DB_DIR, ".git")):
        print("💾 ส่งฐานข้อมูลและปก...")
        run_git("git add .", DB_DIR)
        if run_git("git status --porcelain", DB_DIR):
            run_git('git commit -m "Update Audiobook DB"', DB_DIR)
            try:
                subprocess.run("git push origin HEAD", cwd=DB_DIR, shell=True, timeout=300)
            except: print("   ⚠️ DB Sync Timeout")

    print("\n✨ เสร็จสมบูรณ์! เชิญเช็กที่หน้าแอปได้เลยครับ")
    time.sleep(2)
    os._exit(0)

if __name__ == "__main__":
    main()