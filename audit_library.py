import os
import json

# ==========================================
# ⚙️ ตั้งค่า Path
# ==========================================
library_path = r'C:\MyLibrary'
db_path = 'database.json'

def check_pdf_structure(file_path):
    """ตรวจสอบโครงสร้างไฟล์เบื้องต้น (Header & EOF) แบบปลอดภัย"""
    try:
        if os.path.getsize(file_path) < 500: # ไฟล์ที่เล็กเกินไป (เช่น 0 KB) เสียแน่นอน
            return "Small/Empty File"
            
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return "Invalid PDF Header"
            
            # ตรวจสอบจุดสิ้นสุดไฟล์ (End of File)
            f.seek(-1024, os.sep.replace('\\', '/').count('/') == 0 and os.SEEK_END or os.SEEK_END)
            last_chunk = f.read()
            if b'%%EOF' not in last_chunk:
                return "Incomplete File (No EOF)"
                
        return "OK"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("🔎 เริ่มการตรวจสอบความสมบูรณ์ของไฟล์ในหอสมุด...")
    corrupt_list = []
    total_files = 0

    for root, dirs, files in os.walk(library_path):
        dirs[:] = [d for d in dirs if d not in ['covers', '.git', 'node_modules']]
        for file_name in files:
            if file_name.lower().endswith('.pdf'):
                total_files += 1
                full_path = os.path.join(root, file_name)
                status = check_pdf_structure(full_path)
                
                if status != "OK":
                    print(f"❌ {status}: {file_name}")
                    corrupt_list.append({"file": file_name, "reason": status, "path": full_path})

    print("-" * 40)
    print(f"📊 สรุปผลการสแกน:")
    print(f"📚 ตรวจสอบทั้งหมด: {total_files} เล่ม")
    print(f"⚠️ พบไฟล์ที่มีปัญหา: {len(corrupt_list)} เล่ม")
    
    if corrupt_list:
        print("\nคำแนะนำ: ไฟล์ข้างต้นคือไฟล์ที่เปิดไม่ได้จริง ๆ คุณสามารถเลือกจัดการเป็นรายเล่มได้ครับ")

if __name__ == "__main__":
    main()ย