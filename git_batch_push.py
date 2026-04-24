import os
import subprocess

def run_git_command(command):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def batch_push(batch_size=10):
    # 1. ตรวจสอบสถานะไฟล์ที่เปลี่ยนแปลง
    # s = short format, --untracked-files=all เพื่อหาไฟล์ใหม่ในโฟลเดอร์ย่อยด้วย
    status = run_git_command(['git', 'status', '-s', '--untracked-files=all'])
    
    if not status:
        print("ไม่มีไฟล์ที่เปลี่ยนแปลงครับ ทุกอย่างเป็นปัจจุบันแล้ว")
        return

    # แยกรายชื่อไฟล์ (เอาเฉพาะชื่อไฟล์ ตัดสถานะ M, A, ?? ออก)
    files = [line[3:].strip() for line in status.split('\n') if line.strip()]
    total_files = len(files)
    print(f"พบไฟล์ที่เปลี่ยนแปลงทั้งหมด: {total_files} ไฟล์")

    # 2. แบ่งกลุ่มไฟล์ละ 10 ไฟล์ (Batching)
    for i in range(0, total_files, batch_size):
        current_batch = files[i:i + batch_size]
        print(f"\nกำลังดำเนินการกลุ่มที่ {i//batch_size + 1} (ไฟล์ที่ {i+1} ถึง {min(i+batch_size, total_files)})...")
        
        # Add เฉพาะไฟล์ใน Batch นี้
        for file in current_batch:
            run_git_command(['git', 'add', file])
        
        # Commit
        commit_message = f"Auto-batch push: group {i//batch_size + 1}"
        run_git_command(['git', 'commit', '-m', commit_message])
        
        # Push
        print(f"กำลัง Push กลุ่มที่ {i//batch_size + 1} ขึ้น GitHub...")
        push_result = run_git_command(['git', 'push'])
        
        if push_result is not None:
            print(f"สำเร็จ! กลุ่มที่ {i//batch_size + 1} ถูกอัปโหลดแล้ว")
        else:
            print(f"เกิดข้อผิดพลาดในการ Push กลุ่มที่ {i//batch_size + 1}")
            break

    print("\n--- ดำเนินการเสร็จสิ้นทุกไฟล์แล้วครับ ---")

if __name__ == "__main__":
    batch_push(10)