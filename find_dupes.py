import os

# โฟลเดอร์แม่ที่รวมทุกหมวดหนังสือของคุณรันนรา
base_dir = r"C:\MyLibrary"
files_seen = {} # เก็บไฟล์ต้นฉบับ
count = 0

print(f"🚀 กำลังเริ่มทำความสะอาดไฟล์ซ้ำใน {base_dir}...")

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith(('.pdf', '.epub')):
            full_path = os.path.join(root, file)
            file_size = os.path.getsize(full_path)
            
            # ใช้ 'ชื่อไฟล์' และ 'ขนาด' เป็นตัวตัดสินว่าเป็นไฟล์เดียวกันไหม
            file_key = f"{file}_{file_size}"
            
            if file_key in files_seen:
                # เจอไฟล์ซ้ำ! สั่งลบทันที
                try:
                    os.remove(full_path)
                    print(f"❌ ลบไฟล์ซ้ำสำเร็จ: {full_path}")
                    count += 1
                except Exception as e:
                    print(f"⚠️ ลบไม่ได้ (ไฟล์อาจเปิดอยู่): {e}")
            else:
                files_seen[file_key] = full_path

print("-" * 40)
print(f"✨ เรียบร้อย! ลบไฟล์ที่ซ้ำซ้อนออกไปทั้งหมด {count} เล่มครับ")