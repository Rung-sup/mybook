import os
import json
import hashlib
import unicodedata
import urllib.parse
from pdf2image import convert_from_path

# ==========================================
# ⚙️ MASTER SETTINGS (สแกนอย่างเดียว)
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
    all_books, seen_sizes = [], {}

    print(f"🚀 [Master] กำลังสแกนคลังสื่อเพื่ออัปเดต Database...")

    # เจาะจงโฟลเดอร์ที่จะทำ หรือใช้ os.listdir(library_path) เพื่อทำทั้งหมด
    categories = [d for d in os.listdir(library_path) if os.path.isdir(os.path.join(library_path, d))]
    
    for cat in categories:
        if cat in ['covers', '.git', '.github', 'metadata', 'scripts']: continue
        cat_path = os.path.join(library_path, cat)
        
        if not cat.startswith("7_"):
            print(f"📂 สแกนหมวด: {cat}")
            for root, dirs, files in os.walk(cat_path):
                dirs[:] = [d for d in dirs if d not in ['.git', '.github', 'covers']]
                for file_name in files:
                    if file_name.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file_name)
                        f_size_mb = os.path.getsize(full_path) / (1024 * 1024)

                        # ✅ ถ้ายังมีไฟล์ใหญ่หลุดมา Master จะแค่เตือน แต่ไม่ทำอะไร
                        if f_size_mb > MAX_FILE_SIZE_MB:
                            print(f"⚠️  [เตือน!] ไฟล์ใหญ่เกิน 95MB: {file_name} ({f_size_mb:.2f} MB)")
                            continue 

                        f_size_bytes = os.path.getsize(full_path)
                        if f_size_bytes in seen_sizes: continue
                        seen_sizes[f_size_bytes] = file_name

                        rel_path_from_cat = os.path.relpath(full_path, cat_path)
                        clean_path = rel_path_from_cat.replace('\\', '/')
                        safe_url = urllib.parse.quote(clean_path)
                        cover_id = generate_cover_id(os.path.join(cat, rel_path_from_cat))
                        
                        # สร้างหน้าปก
                        cat_cover_dir = os.path.join(output_root, cat)
                        os.makedirs(cat_cover_dir, exist_ok=True)
                        cover_file_path = os.path.join(cat_cover_dir, f"{cover_id}.jpg")
                        
                        if not os.path.exists(cover_file_path):
                            try:
                                images = convert_from_path(full_path, first_page=1, last_page=1, size=(None, 400), poppler_path=poppler_path)
                                if images:
                                    images[0].save(cover_file_path, 'JPEG', quality=85)
                                    print(f"   📸 สร้างปก: {file_name}")
                            except: pass

                        all_books.append({
                            "title": os.path.splitext(file_name)[0],
                            "url": f"https://raw.githubusercontent.com/{github_user}/{cat}/main/{safe_url}",
                            "category": cat,
                            "cover_id": cover_id,
                            "file_size": f_size_bytes
                        })

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump({"books": all_books, "total_books": len(all_books)}, f, ensure_ascii=False, indent=4)
    print(f"\n✨ [Master] อัปเดต Database สำเร็จ! หนังสือทั้งหมด {len(all_books)} เล่ม")

if __name__ == "__main__":
    main()