import os

def is_pdf_valid_safe(file_path):
    """ตรวจสอบแค่โครงสร้างไฟล์เบื้องต้น ไม่เรนเดอร์ภาพ เพื่อป้องกันการลบไฟล์ใหญ่"""
    try:
        if os.path.getsize(file_path) < 100: # ไฟล์ที่เล็กเกินไปมักจะเสีย
            return False
            
        with open(file_path, 'rb') as f:
            header = f.read(4)
            # ตรวจว่าขึ้นต้นด้วย %PDF หรือไม่
            if header != b'%PDF':
                return False
            
            # ตรวจสอบตอนท้ายไฟล์ (EOF)
            f.seek(-1024, os.SEEK_END)
            last_chunk = f.read()
            if b'%%EOF' not in last_chunk:
                return False
                
        return True # ไฟล์โครงสร้างปกติ
    except Exception:
        return False

# ใช้ฟังก์ชันนี้แทนตัวเก่า จะไม่เกิดปัญหาเรนเดอร์ไม่ไหวแล้วสั่งลบครับ