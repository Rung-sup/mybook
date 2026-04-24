import os
import subprocess
import time

def run_git_command(command):
    try:
        # ใช้ shell=True และระบุ encoding เพื่อดึงชื่อไฟล์ภาษาไทยที่ GHD อ่านอยู่
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout
    except Exception as e:
        return None

def push_from_ghd_list(batch_size=10):
    print("🔍 กำลังดึงรายการไฟล์ที่ค้างอยู่ใน GitHub Desktop...")
    
    # ดึงรายชื่อไฟล์ที่ GHD เห็นว่ามีการเปลี่ยนแปลง (ทั้ง Untracked และ Modified)
    # คำสั่งนี้จะลิสต์ไฟล์เหมือนที่ปรากฏในหน้า Changes ของ GHD
    raw_untracked = run_git_command("git ls-files --others --exclude-standard")
    raw_modified = run_git_command("git ls-files -m")
    
    all_files = []
    if raw_untracked: all_files.extend(raw_untracked.splitlines())
    if raw_modified: all_files.extend(raw_modified.splitlines())
    
    # ลบช่องว่างและเครื่องหมายอัญประกาศ
    files = [f.strip().strip('"') for f in all_files if f.strip()]
    total_files = len(files)
    
    if total_files == 0:
        print("✅ ไม่พบไฟล์ค้างในรายการ (หรืออาจจะต้องลองกด Refresh ใน GHD อีกครั้ง)")
        return

    print(f"📦 พบไฟล์ที่ยังไม่ได้ Push ทั้งหมด {total_files} ไฟล์")
    print(f"🚀 จะเริ่มทยอยส่งทีละ {batch_size} ไฟล์...")

    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        print(f"\n[กลุ่มที่ {i//batch_size + 1}] กำลังเตรียม {len(batch)} ไฟล์...")
        
        # Add ไฟล์ในกลุ่มนี้
        for file in batch:
            # ใช้เครื่องหมายคำพูดครอบชื่อไฟล์เผื่อมีเว้นวรรค
            run_git_command(f'git add "{file}"')
        
        # Commit
        commit_msg = f"Batch push from GHD list: group {i//batch_size + 1}"
        run_git_command(f'git commit -m "{commit_msg}"')
        
        # Push
        print(f"📤 กำลัง Push ขึ้น GitHub...")
        push_output = run_git_command("git push")
        
        if push_output is not None:
            print(f"✅ กลุ่มที่ {i//batch_size + 1} สำเร็จ!")
        else:
            print(f"❌ กลุ่มนี้ติดปัญหา (อาจเพราะไฟล์ใหญ่เกินไป)")
            break
            
        # พักสั้นๆ เพื่อให้ Git เคลียร์ Buffer
        time.sleep(0.5)

    print("\n✨ --- จัดการไฟล์ที่ค้างอยู่เสร็จสิ้นครับ! ---")

if __name__ == "__main__":
    push_from_ghd_list(10)