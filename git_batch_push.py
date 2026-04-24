import os
import subprocess

def run_git_command(command):
    try:
        # ใช้ encoding utf-8 เพื่อรองรับชื่อไฟล์ภาษาไทย
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout
    except subprocess.CalledProcessError as e:
        # ถ้าไม่มีอะไรให้ commit หรือ push git อาจจะ return error code มา เราจะดึงข้อความมาเช็ก
        return None

def batch_push_all(batch_size=10):
    print("🔍 กำลังสแกนหาไฟล์ที่มีการเปลี่ยนแปลงในทุกโฟลเดอร์...")
    
    # ดึงไฟล์ที่แก้ไข (Modified) และ ไฟล์ใหม่ (Untracked) ทั้งหมด
    # -o คือ others (ไฟล์ใหม่), -m คือ modified (ไฟล์แก้ไข), --exclude-standard คือข้ามไฟล์ใน .gitignore
    cmd = ['git', 'ls-files', '-o', '-m', '--exclude-standard']
    raw_files = run_git_command(cmd)
    
    if not raw_files:
        print("✅ ทุกอย่างเป็นปัจจุบันแล้ว ไม่พบไฟล์ที่ต้อง Push ครับ")
        return

    # จัดการรายชื่อไฟล์: ตัดช่องว่าง และลบเครื่องหมาย " ออก (สำคัญสำหรับไฟล์ภาษาไทย/มีเว้นวรรค)
    files = [line.strip().strip('"').strip("'") for line in raw_files.split('\n') if line.strip()]
    
    total_files = len(files)
    print(f"📦 พบไฟล์ที่ต้องดำเนินการทั้งหมด: {total_files} ไฟล์")

    for i in range(0, total_files, batch_size):
        current_batch = files[i:i + batch_size]
        print(f"\n🚀 [กลุ่มที่ {i//batch_size + 1}] เริ่มจัดการไฟล์ที่ {i+1} ถึง {min(i+batch_size, total_files)}...")
        
        # 1. Add ไฟล์ใน Batch
        for file in current_batch:
            run_git_command(['git', 'add', file])
        
        # 2. Commit
        commit_msg = f"Auto-sync: Batch {i//batch_size + 1} ({len(current_batch)} files)"
        run_git_command(['git', 'commit', '-m', commit_msg])
        
        # 3. Push
        print(f"📤 กำลัง Push ขึ้น GitHub...")
        push_status = run_git_command(['git', 'push'])
        
        if push_status is not None:
            print(f"✅ สำเร็จ!")
        else:
            # ถ้า Push ไม่ผ่าน อาจเกิดจากเน็ตหลุด หรือไฟล์ใหญ่เกินไป ให้หยุดเช็กก่อน
            print(f"❌ การ Push ขัดข้อง (อาจจะติดที่ไฟล์ขนาดใหญ่หรือสัญญาณเน็ต)")
            print("สคริปต์จะหยุดทำงานเพื่อความปลอดภัย โปรดตรวจสอบ Error ใน Terminal ครับ")
            break

    print("\n✨ --- ดำเนินการเสร็จสิ้นทุกรายการ --- ✨")

if __name__ == "__main__":
    batch_push_all(batch_size=10)