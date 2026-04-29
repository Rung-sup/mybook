import os
import shutil
import hashlib
import subprocess
from PyPDF2 import PdfReader, PdfWriter

# ==========================================
PROCESS_ZONE = r'C:\Process_Zone'
LIBRARY_ROOT = r'C:\MyLibrary'
DB_PATH = r'C:\MyBook_Test\database.json'
GS_PATH = r'C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe'
MAX_SIZE_MB = 95
# ==========================================

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

def main():
    import json
    existing_hashes = {}
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                old_db = json.load(f)
                for b in old_db.get('books', []):
                    if 'file_hash' in b: existing_hashes[b['file_hash']] = b['title']
        except: pass

    print("🛠 [1/3] กำลังจัดการไฟล์และย้ายเข้าชั้นหนังสือ...")
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

            if item.lower().endswith('.pdf') and os.path.getsize(f_path) / (1024*1024) > MAX_SIZE_MB:
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
    print("✅ จัดการไฟล์เสร็จสิ้น")

if __name__ == "__main__":
    main()