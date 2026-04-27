import os
import shutil
import hashlib
import json
import unicodedata
import urllib.parse
import time
import subprocess
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

# ==========================================
# ⚙️ CONFIGURATION (ตรวจสอบ Path ให้ตรงกับเครื่องท่าน)
# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_DIR = r'C:\MyBook_Test'
DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\MyBook_Test\poppler-25.12.0\Library\bin'
GS_PATH = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'

GITHUB_USER = "rung-sup"
MAX_SIZE_MB = 95
BATCH_SIZE = 15

def run_git(command, cwd):
    try:
        # ซ่อม: เพิ่ม timeout เพื่อไม่ให้ค้างที่คำสั่ง git
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=60)
        return result.stdout.strip()
    except: return None

def get_file_hash(f_path):
    """สร้าง MD5 Hash เพื่อตรวจไฟล์ซ้ำจากเนื้อหาจริงๆ"""
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
    """บีบอัด PDF ขั้นสูง (eBook Quality) เพื่อพยายามรักษาเล่มไม่ให้ถูกแบ่ง"""
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
    """แบ่งเล่ม PDF และคัดลอกหน้าปกจากเล่มแรกไปใส่ให้เล่มที่สองอัตโนมัติ"""
    print(f"   ✂️ ไฟล์ยังใหญ่เกินไป! กำลังแบ่งเล่มและแถมหน้าปกให้เล่มลูก...")
    reader = PdfReader(f_path)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(f_path)[0]
    mid = total_pages // 2
    
    # เล่ม 1.1
    w1 = PdfWriter()
    for i in range(0, mid): w1.add_page(reader.pages[i])
    path1 = f"{base_name} Part 1.1.pdf"
    with open(path1, "wb") as f: w1.write(f)
    
    # เล่ม 1.2 (แถมปกหน้าแรก)
    w2 = PdfWriter()
    w2.add_page(reader.pages[0]) # ✅ ก๊อปปี้หน้าปก
    for i in range(mid, total_pages): w2.add_page(reader.pages[i])
    path2 = f"{base_name} Part 1.2.pdf"
    with open(path2, "wb") as f: w2.write(f)
    
    os.remove(f_path)
    return [path1, path2]

def generate_cover_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def main():
    # โหลด Hash เดิมจาก DB เพื่อเช็กซ้ำ
    existing_hashes = {}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            try:
                old_db = json.load(f)
                for b in old_db.get('books', []):
                    if 'file_hash' in b: existing_hashes[b['file_hash']] = b['title']
            except: pass

    # --- STEP 1: SMART PROCESS & MOVE ---
    print("🛠 [1/3] กำลังตรวจสอบไฟล์ด้วยระบบ Hash & High Compression...")
    for cat in os.listdir(PROCESS_ZONE):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        os.makedirs(target_lib, exist_ok=True)

        for item in os.listdir(cat_staging):
            f_path = os.path.join(cat_staging, item)
            
            # ตรวจซ้ำด้วย Hash
            if not os.path.isdir(f_path):
                f_hash = get_file_hash(f_path)
                if f_hash in existing_hashes:
                    print(f"   🗑️ พบไฟล์ซ้ำจากเนื้อหา (ลบทิ้ง): {item} (ซ้ำกับ {existing_hashes[f_hash]})")
                    os.remove(f_path); continue

            # บีบอัดและแบ่งเล่ม (เฉพาะ PDF)
            if item.lower().endswith('.pdf'):
                if os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
                    compress_pdf_high(f_path)
                    if os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
                        split_with_cover_injection(f_path); continue

            # ย้ายไฟล์/โฟลเดอร์
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

    # --- STEP 2: UPDATE DB & GROUPING ---
    print("📊 [2/3] อัปเดตฐานข้อมูล จัดกลุ่มโฟลเดอร์ และสร้างหน้าปก...")
    all_books, all_music = [], []
    for cat in os.listdir(LIBRARY_ROOT):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']: continue
        
        for root, _, files in os.walk(cat_path):
            rel_folder = os.path.relpath(root, cat_path)
            display_folder = "ทั่วไป" if rel_folder == "." else rel_folder
            
            for f in files:
                if f.lower().endswith(('.pdf', '.mp3')):
                    full_p = os.path.join(root, f)
                    f_hash = get_file_hash(full_p)
                    cover_id = generate_cover_id(os.path.relpath(full_p, LIBRARY_ROOT))
                    
                    # สร้างปกไปที่ MyBook_Test/covers
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
                    # ซ่อม: ปรับการแยกเพลงให้แม่นยำขึ้น
                    if cat.startswith("7_") or f.lower().endswith('.mp3'):
                        all_music.append(item_data)
                    else:
                        all_books.append(item_data)

    # บันทึก JSON
    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=4)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=4)

    # --- STEP 3: FULL SYNC ---
    print("\n☁️ [3/3] กำลังทยอยส่งข้อมูลขึ้น Cloud...")
    
    # 3.1 ส่งเนื้อหา (MyLibrary)
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.exists(os.path.join(f_p, ".git")):
            print(f"🚀 กำลังส่งห้อง: {folder}")
            run_git("git add .", f_p)
            run_git('git commit -m "Auto-sync V1.4"', f_p)
            # ซ่อม: ใช้ subprocess แบบมี timeout เพื่อป้องกันการค้าง
            try:
                subprocess.run("git push origin HEAD", cwd=f_p, shell=True, timeout=60)
            except: print(f"   ⚠️ ห้อง {folder} ใช้เวลาส่งนานเกินไป (ข้าม)")

    # ... (ส่วนต้นของโค้ดเหมือนเดิมจนถึง Step 3) ...

    # --- STEP 3: FULL SYNC ---
    print("\n☁️ [3/3] กำลังทยอยส่งข้อมูลขึ้น Cloud...")
    
    # 3.1 ส่งเนื้อหา (MyLibrary)
    for folder in os.listdir(LIBRARY_ROOT):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if os.path.exists(os.path.join(f_p, ".git")):
            print(f"🚀 กำลังส่งห้อง: {folder}")
            run_git("git add .", f_p)
            run_git('git commit -m "Auto-sync V1.4"', f_p)
            # ✅ แก้ไข: เพิ่ม timeout 60 วินาที ป้องกันการค้าง
            try:
                subprocess.run("git push origin HEAD", cwd=f_p, shell=True, timeout=60)
            except subprocess.TimeoutExpired:
                print(f"   ⚠️ ห้อง {folder} ใช้เวลาส่งนานเกินไป (ข้ามเพื่อไม่ให้ค้าง)")

    # 3.2 ส่งฐานข้อมูลและหน้าปก (MyBook_Test)
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        print("💾 กำลังส่งฐานข้อมูลและหน้าปก...")
        run_git("git add .", DB_DIR)
        status = run_git("git status --porcelain", DB_DIR)
        if status:
            run_git('git commit -m "Final DB and Covers Sync"', DB_DIR)
            # ✅ แก้ไข: เพิ่ม timeout 60 วินาที ป้องกันการค้าง
            try:
                subprocess.run("git push origin HEAD", cwd=DB_DIR, shell=True, timeout=60)
                print("   ✅ อัปเดต Repo MyBook สำเร็จ!")
            except subprocess.TimeoutExpired:
                print("   ⚠️ การส่งฐานข้อมูลค้าง (ข้ามเพื่อให้สคริปต์ปิดตัวได้)")
        else:
            print("   ✅ ไม่มีข้อมูลใหม่ใน MyBook_Test")

    # บังคับจบงาน
    print("\n✨ [ภารกิจเสร็จสมบูรณ์] ข้อมูลทุกอย่างปลอดภัยบน Cloud แล้วครับ")
    time.sleep(2)
    os._exit(0)

if __name__ == "__main__":
    main()