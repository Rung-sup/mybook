import os
import json
import urllib.parse
import hashlib
import unicodedata

# --- ฟังก์ชันดึงข้อมูลเพลงจากภายนอก ---
def get_external_music():
    music_json_path = r"C:\MyLibrary\7_music\metadata\music_db.json"
    if os.path.exists(music_json_path):
        with open(music_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# --- ตั้งค่าพาธ ---
library_path = r'C:\MyLibrary' 
db_path = 'database.json'
base_url = "https://Rung-sup.github.io"

def generate_cover_id(relative_path):
    path_slash = relative_path.replace('\\', '/')
    js_str = unicodedata.normalize('NFC', path_slash).replace('\u0e4d\u0e32', '\u0e33')
    return hashlib.md5(js_str.encode('utf-8')).hexdigest()

def update_database():
    books_list = [] # เปลี่ยนชื่อตัวแปรจาก new_database เป็น books_list เพื่อไม่ให้สับสน
    print("🔄 กำลังสแกนหาหนังสือ PDF...")
    
    for root, dirs, files in os.walk(library_path):
        dirs[:] = [d for d in dirs if d not in ['covers', '.git', '7_music']] # ข้ามโฟลเดอร์เพลงในการสแกนหนังสือ
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, library_path)
                
                parts = rel_path.split(os.sep)
                category = parts[0]
                
                if len(parts) > 2:
                    folder_name = parts[1]
                else:
                    folder_name = ""

                cover_id = generate_cover_id(rel_path)
                final_url = f"{base_url}/{urllib.parse.quote(rel_path.replace('\\', '/'))}"

                books_list.append({
                    "title": os.path.splitext(file_name)[0],
                    "url": final_url,
                    "category": category,
                    "folder": folder_name,
                    "cover_id": cover_id
                })

    # --- ส่วนที่เพิ่มเข้ามา: มัดรวมหนังสือและเพลง ---
    music_list = get_external_music()
    
    all_data = {
        "books": books_list,
        "music": music_list,
        "updated_at": "2026-04-21" # เพิ่มวันที่อัปเดตไว้ดูเล่นๆ ได้ครับ
    }

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ สำเร็จ!")
    print(f"📚 พบหนังสือ: {len(books_list)} เล่ม")
    print(f"🎵 พบเพลง: {len(music_list)} รายการ")
    print(f"💾 บันทึกลง {db_path} เรียบร้อยแล้ว")

if __name__ == "__main__":
    update_database()