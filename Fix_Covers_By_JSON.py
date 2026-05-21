import os
import json
import shutil
import re

# ==========================================
# ⚙️ CONFIGURATION (ตั้งค่าพิกัดหลัก)
# ==========================================
DB_DIR = r'C:\MyBook_Test'
DB_PATH = os.path.join(DB_DIR, 'database.json')

def fix_covers_by_json_data():
    print("=======================================================")
    print("🎯 เริ่มระบบซ่อมไฟล์ปกพาร์ท โดยอิงรหัส MD5 จากฐานข้อมูล JSON 🎯")
    print("=======================================================")
    
    if not os.path.exists(DB_PATH):
        print("❌ ไม่พบไฟล์ database.json กรุณาตรวจสอบพิกัด DB_DIR")
        return

    # เปิดอ่านฐานข้อมูล JSON ตัวจริงที่แอปใช้งานอยู่
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        db_data = json.load(f)
        
    books = db_data.get("books", [])
    covers_root_dir = os.path.join(DB_DIR, 'covers')
    
    # ดิกชันนารีเก็บรหัสรูปปกจริงของเล่มพาร์ท 1 แยกตามหมวดหมู่ห้องย่อย
    # โครงสร้าง: { "ห้องย่อย/ชื่อเรื่องหลัก": "พิกัดไฟล์รูปปกพาร์ท1.jpg" }
    part_one_images = {}
    pending_parts = []
    
    print("🔄 ขั้นตอนที่ 1: ค้นหารูปปกต้นแบบของไฟล์ Part_1...")
    
    for book in books:
        title = book.get("title", "")
        c_id = book.get("cover_id")
        url = book.get("url", "")
        
        # ถอดชื่อโฟลเดอร์ห้องย่อยจริง (เช่น 4_Chinese_Novel_Vol4) จาก URL บน GitHub
        # ลิงก์ปกติจะเป็น: .../rung-sup/{repo_name}/main/...
        # เราต้องการรู้ว่าในโฟลเดอร์ covers มันนอนอยู่ห้องไหน
        url_parts = url.split('/main/')
        if len(url_parts) > 1:
            # ดึงโครงสร้างโฟลเดอร์ถัดจาก main
            path_after_main = url_parts[1]
            # หากหนังสืออยู่ในโฟลเดอร์ย่อยอีกที ให้แกะเอาชื่อห้องย่อยหลักมา
            sub_folder = path_after_main.split('/')[0]
        else:
            sub_folder = ""
            
        if not c_id or not sub_folder: continue
        
        # ตรวจจับชื่อไฟล์ว่าเป็นตระกูลพาร์ทหรือไม่
        part_match = re.search(r'^(.*)_part_(\d+)$', title, flags=re.IGNORECASE)
        
        if part_match:
            base_story = part_match.group(1).strip().lower()
            part_num = int(part_match.group(2))
            
            # สร้างคีย์อ้างอิงเฉพาะกลุ่ม เช่น "4_Chinese_Novel_Vol4/นิยายเรื่องดัง"
            story_key = f"{sub_folder}/{base_story}"
            
            actual_cover_path = os.path.join(covers_root_dir, sub_folder, f"{c_id}.jpg")
            
            if part_num == 1:
                # ถ้าเป็นพาร์ท 1 และมีไฟล์รูปปกอยู่จริงในเครื่อง ให้บันทึกเก็บไว้เป็นต้นแบบ
                if os.path.exists(actual_cover_path):
                    part_one_images[story_key] = actual_cover_path
                else:
                    # เผื่อว่าชื่อไฟล์รูปภาพพาร์ท 1 บนดิสก์โดนลบหรือหาไม่เจอ
                    print(f"   ⚠️  พบพาร์ท 1 ใน JSON แต่ไม่พบไฟล์รูปปกจริงที่พิกัด: {actual_cover_path}")
            else:
                # ถ้าเป็นพาร์ท 2, 3, 4... ให้เก็บข้อมูลรหัสที่ JSON ต้องการ เพื่อรอคัดลอกรูปมาใส่
                pending_parts.append({
                    "story_key": story_key,
                    "target_path": actual_cover_path,
                    "title": title
                })

    print("\n🔄 ขั้นตอนที่ 2: กำลังสำเนารูปปกจากพาร์ท 1 แจกจ่ายตามรหัส JSON จริง...")
    copied_count = 0
    
    for part in pending_parts:
        s_key = part["story_key"]
        target_file = part["target_path"]
        
        if s_key in part_one_images:
            source_file = part_one_images[s_key]
            try:
                # ตรวจสอบและสร้างโฟลเดอร์ปลายทางถ้ายังไม่มี
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                # คัดลอกรูปปกจากพาร์ท 1 มาสวมให้พาร์ทเสริม โดยใช้ชื่อรหัส MD5 ที่ระบุไว้ใน JSON เป๊ะ ๆ
                shutil.copy2(source_file, target_file)
                copied_count += 1
            except Exception as e:
                print(f"   ❌ ไม่สามารถก๊อปปี้ปกให้ [{part['title']}]: {e}")

    print("\n=======================================================")
    print(f"✅ สำเร็จเสร็จสิ้น! ทำการจับคู่และซ่อมปกตามรหัส JSON เรียบร้อย")
    print(f"👯 สำเนารูปปกให้พาร์ทเสริมสำเร็จทั้งหมด: {copied_count} รูป")
    print("=======================================================")

if __name__ == "__main__":
    if os.name == 'nt': os.system('chcp 65001 > nul')
    fix_covers_by_json_data()