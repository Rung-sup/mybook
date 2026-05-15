import os
import shutil

# --- การตั้งค่าเส้นทาง ---
SOURCE_F = r'F:' # ต้นทางที่ไฟล์กระจัดกระจายอยู่
TARGET_C = r'C:\MyLibrary' # ปลายทางที่ต้องการเอากลับไปวาง

# รายชื่อโฟลเดอร์ใน F: ที่เราต้องการดึงไฟล์กลับ
folders_to_restore = [r'F:\ไฟล์เสีย', r'F:\ไฟล์ใหญ่เกิน90mb']

print("🚀 เริ่มกระบวนการกู้คืนไฟล์กลับสู่ MyLibrary...")

for folder in folders_to_restore:
    if not os.path.exists(folder):
        continue
        
    print(f"\n📂 กำลังตรวจสอบ: {folder}")
    for filename in os.listdir(folder):
        src_path = os.path.join(folder, filename)
        
        if os.path.isfile(src_path):
            # พยายามหาว่าไฟล์นี้ควรไปอยู่ที่ไหนใน C:\MyLibrary 
            # (โดยการค้นหาว่าเดิมมันเคยอยู่ในห้องไหน)
            found = False
            for root, dirs, files in os.walk(TARGET_C):
                # ถ้าเราเจอว่ามีโฟลเดอร์ปลายทางที่เหมาะสม (เราจะใช้ชื่อไฟล์เช็คไม่ได้เพราะไฟล์ถูกย้ายออกมาแล้ว)
                # ในที่นี้ เพื่อความปลอดภัย ผมจะย้ายกลับไปที่ 'C:\MyLibrary\Restored_Files' 
                # เพื่อให้คุณรันนาราจัดเข้าหมวดหมู่ได้ง่าย หรือระบุห้องที่แน่นอนได้เลย
                pass
            
            # --- วิธีที่เร็วที่สุด: ย้ายกลับไปที่ห้องกลางก่อนเพื่อให้คุณตรวจสอบ ---
            restore_path = os.path.join(TARGET_C, "0_Waiting_Room") 
            if not os.path.exists(restore_path):
                os.makedirs(restore_path)
                
            dst_path = os.path.join(restore_path, filename)
            
            try:
                # ใช้ move ข้าม drive (copy + delete)
                shutil.move(src_path, dst_path)
                print(f"✅ ย้ายกลับสำเร็จ: {filename}")
            except Exception as e:
                print(f"❌ ไม่สามารถย้าย {filename} กลับได้: {e}")

print("\n✨ เสร็จสิ้น! ไฟล์ทั้งหมดถูกดึงกลับมาไว้ที่ C:\MyLibrary\0_Waiting_Room แล้วครับ")