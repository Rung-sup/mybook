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
# ⚙️ MASTER CONFIGURATION
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
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd)
        return result.stdout.strip()
    except: return None

def compress_and_split_pdf(f_path):
    try:
        size_mb = os.path.getsize(f_path) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB and os.path.exists(GS_PATH):
            temp_out = f_path.replace(".pdf", "_compressed.pdf")
            gs_cmd = [GS_PATH, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH', f'-sOutputFile={temp_out}', f_path]
            subprocess.run(gs_cmd, capture_output=True)
            if os.path.exists(temp_out):
                os.remove(f_path); os.rename(temp_out, f_path)
        
        if os.path.getsize(f_path) / (1024 * 1024) > MAX_SIZE_MB:
            reader = PdfReader(f_path)
            total_pages = len(reader.pages)
            mid = total_pages // 2
            base_name = os.path.splitext(f_path)[0]
            new_files = []
            for start, end, suffix in [(0, mid, "1.1"), (mid, total_pages, "1.2")]:
                writer = PdfWriter()
                for i in range(start, end): writer.add_page(reader.pages[i])
                out_path = f"{base_name} Part {suffix}.pdf"
                with open(out_path, "wb") as f: writer.write(f)
                new_files.append(out_path)
            os.remove(f_path)
            return new_files
    except: pass
    return [f_path]

def generate_id(rel_path):
    normalized = unicodedata.normalize('NFC', rel_path.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

def main():
    # --- STEP 1: PROCESS ZONE ---
    print("🛠 [1/3] กำลังคัดแยกไฟล์และโฟลเดอร์...")
    for cat in os.listdir(PROCESS_ZONE):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging): continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.exists(target_lib): os.makedirs(target_lib)

        for item in os.listdir(cat_staging):
            f_path = os.path.join(cat_staging, item)
            dest = os.path.join(target_lib, item)
            try:
                if os.path.isdir(f_path):
                    if os.path.exists(dest):
                        for sub_f in os.listdir(f_path):
                            shutil.move(os.path.join(f_path, sub_f), os.path.join(dest, sub_f))
                        shutil.rmtree(f_path)
                    else: shutil.move(f_path, dest)
                else:
                    if os.path.getsize(f_path) == 0: os.remove(f_path); continue
                    ready_files = compress_and_split_pdf(f_path) if item.lower().endswith('.pdf') else [f_path]
                    for r_file in ready_files:
                        final_dest = os.path.join(target_lib, os.path.basename(r_file))
                        if os.path.exists(final_dest): os.remove(r_file)
                        else: shutil.move(r_file, final_dest)
            except: pass

    # --- STEP 2: UPDATE DB & COVERS ---
    print("📊 [2/3] อัปเดตฐานข้อมูลและหน้าปก...")
    all_books, all_music = [], []
    for cat in os.listdir(LIBRARY_ROOT):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']: continue
        for root, _, files in os.walk(cat_path):
            for f in files:
                if f.lower().endswith(('.pdf', '.mp3')):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, LIBRARY_ROOT)
                    cover_id = generate_id(rel_p)
                    
                    if f.lower().endswith('.pdf'):
                        cover_out = os.path.join(LIBRARY_ROOT, 'covers', cat, f"{cover_id}.jpg")
                        os.makedirs(os.path.dirname(cover_out), exist_ok=True)
                        if not os.path.exists(cover_out):
                            try:
                                imgs = convert_from_path(full_p, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
                                if imgs: imgs[0].save(cover_out, 'JPEG', quality=85)
                            except: pass

                    # แก้ไข Syntax Error ตรงนี้ (แยก .replace ออกจาก f-string)
                    path_in_repo = os.path.relpath(full_p, cat_path).replace('\\', '/')
                    safe_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{cat}/main/{urllib.parse.quote(path_in_repo)}"
                    
                    item_data = {"title": os.path.splitext(f)[0], "url": safe_url, "category": cat, "cover_id": cover_id}
                    if cat.startswith("7_"): all_music.append(item_data)
                    else: all_books.append(item_data)

    with open(DB_PATH, 'w', encoding='utf-8') as f: json.dump({"books": all_books}, f, ensure_ascii=False, indent=4)
    with open(MUSIC_DB_PATH, 'w', encoding='utf-8') as f: json.dump({"music": all_music}, f, ensure_ascii=False, indent=4)

    # --- STEP 3: SYNC TO GITHUB ---
    print("☁️ [3/3] ทยอยส่ง GitHub...")
    for folder in os.listdir(LIBRARY_ROOT):
        folder_path = os.path.join(LIBRARY_ROOT, folder)
        if not os.path.exists(os.path.join(folder_path, ".git")): continue
        raw_files = run_git("git ls-files -o -m --exclude-standard", folder_path)
        if raw_files:
            valid_files = [f.strip().strip('"') for f in raw_files.split('\n') if f.strip()]
            for i in range(0, len(valid_files), BATCH_SIZE):
                batch = valid_files[i:i+BATCH_SIZE]
                for b_file in batch: run_git(f'git add "{b_file}"', folder_path)
                run_git(f'git commit -m "Auto-sync library"', folder_path)
                run_git("git push origin main", folder_path)
                # --- [ส่วนสุดท้ายที่ต้องเพิ่ม] ---
    # --- [ส่วนสุดท้าย: ส่งฐานข้อมูลแอปขึ้น GitHub] ---
    # --- [ส่วนสุดท้าย: กวาดทุกอย่างใน MyBook_Test ขึ้น GitHub] ---
    print(f"\n💾 ขั้นตอนสุดท้าย: กำลังล้างไฟล์ค้างใน Repo MyBook (กวาดทั้งหมด)...")
    if os.path.exists(os.path.join(DB_DIR, ".git")):
        # 1. ใช้ "git add ." เพื่อเก็บทุกไฟล์ที่เปลี่ยนแปลง (รวมไฟล์หน้าปกและ HTML)
        run_git("git add .", DB_DIR)
        
        # 2. ตรวจสอบว่ามีอะไรต้อง Commit ไหม
        status = run_git("git status --porcelain", DB_DIR)
        if status:
            run_git('git commit -m "Full auto-sync by Super Master Workflow"', DB_DIR)
            print("   🚀 กำลังส่งข้อมูลทั้งหมดขึ้น Cloud...")
            
            # 3. Push ขึ้น GitHub
            result = run_git("git push origin HEAD", DB_DIR)
            
            if result is not None:
                print("   ✅ อัปเดต Repo MyBook สำเร็จ! (หน้าจอ GHD จะสะอาดกริ๊บ)")
            else:
                print("   ⚠️ Push ไม่สำเร็จ (อาจติดเรื่องสิทธิ์ใน Terminal)")
        else:
            print("   ✅ ไม่มีไฟล์ค้างใน MyBook ทุกอย่างเป็นปัจจุบันแล้ว")
    else:
        print("   ❌ ไม่พบ .git ใน MyBook_Test")
        
if __name__ == "__main__":
    main()
    print("\n✨ เสร็จสิ้นภารกิจ! ข้อมูลอัปเดตเรียบร้อยครับ")