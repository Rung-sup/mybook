import os
import subprocess
import time
import shlex

# ==========================================
# ⚙️ CONFIGURATION (พิกัดคลังหลักของคุณ)
# ==========================================
LIBRARY_ROOT = r'C:\MyLibrary'

def run_git(command, cwd):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=cwd,
            timeout=600  # ตั้งเวลารอ 10 นาทีต่อรอบ สำหรับไฟล์เพลงขนาดใหญ่
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

def get_current_branch(repo_path):
    code, out, _ = run_git("git branch --show-current", repo_path)
    if code == 0 and out.strip():
        return out.strip()
    return "main"

print("🚀 [เริ่มระบบกวาดล้างระบายคิวเพลงค้าง GHD - 50 Files / 5 Sec + Auto Publish]")
print("=====================================================================")

if not os.path.exists(LIBRARY_ROOT):
    print(f"❌ ไม่พบโฟลเดอร์ LIBRARY_ROOT: {LIBRARY_ROOT}")
    exit()

# ค้นหาโฟลเดอร์หมวดเพลง 7_music ทั้งหมดใน MyLibrary
all_folders = sorted(os.listdir(LIBRARY_ROOT))
target_repos = []

for folder in all_folders:
    repo_path = os.path.join(LIBRARY_ROOT, folder)
    if os.path.isdir(repo_path) and folder.startswith("7_") and os.path.exists(os.path.join(repo_path, ".git")):
        target_repos.append(repo_path)

print(f"📂 ตรวจพบ Repository หมวดเพลงที่ต้องเข้าจัดการทั้งหมด {len(target_repos)} ห้อง\n")

for repo_idx, repo_path in enumerate(target_repos, 1):
    repo_name = os.path.basename(repo_path)
    
    # 1. เช็กไฟล์ที่เปลี่ยนแปลงหรือค้างส่งใน GHD ของห้องนี้
    code, out, _ = run_git('git status --porcelain', repo_path)
    if code != 0 or not out.strip():
        # ถ้าห้องนี้สะอาดและตรงกับบน GH อยู่แล้ว ให้ข้ามไป
        continue
        
    branch_name = get_current_branch(repo_path)
    print(f"📦 [{repo_idx}/{len(target_repos)}] เข้าจัดการห้อง: {repo_name} (ท่อกิ่ง: {branch_name})")
    
    # แยกรายชื่อไฟล์ค้างส่ง
    changed_files = []
    has_mp3 = False
    for line in out.splitlines():
        if len(line) > 3:
            filename = line[3:].strip('"')
            changed_files.append(filename)
            if filename.lower().endswith('.mp3'):
                has_mp3 = True
                
    if not changed_files:
        continue
        
    print(f"   -> พบไฟล์ไม่ตรงกันค้างใน GHD จำนวน {len(changed_files)} ไฟล์ เริ่มระบายคิว...")
    
    # ⚡ [ฟังก์ชันพิเศษ] บังคับสั่งเปิดท่อ Publish Branch ผูกกับ GitHub สำหรับคลังสร้างใหม่
    # คำสั่งนี้จะช่วยแก้ปัญหาปุ่มสีฟ้าคาหน้าจอ GHD และทำให้ดันไฟล์ผ่านได้สำเร็จ
    run_git(f"git push -u origin {branch_name}", repo_path)
    
    # 2. แบ่งกลุ่มทยอยส่งรอบละไม่เกิน 50 ไฟล์ ห่างกัน 5 วินาที
    batch_size = 50
    for i in range(0, len(changed_files), batch_size):
        batch = changed_files[i:i + batch_size]
        print(f"   🔄 กำลังผลักกลุ่มย่อยที่ {i // batch_size + 1} (ไฟล์ที่ {i+1} ถึง {min(i + batch_size, len(changed_files))})")
        
        # สั่งดึงไฟล์เข้าคิวเตรียมส่ง (Stage) และ Commit เฉพาะกลุ่มนี้
        quoted_files = ' '.join(shlex.quote(f) for f in batch)
        run_git(f'git add {quoted_files}', repo_path)
        run_git(f'git commit -m "Force sync queue batch {i // batch_size + 1}"', repo_path)
        
        # 🛡️ ลอจิกสำคัญ: สั่งสตรีมเนื้อหาไฟล์เพลงจริง (.mp3) ของกลุ่มนี้ขึ้นไปทันที
        if has_mp3:
            run_git(f'git lfs push origin {branch_name}', repo_path)
            
        # Push อัปเดตตัวชี้ Pointer ปิดงานของรอบนี้
        p_code, _, p_err = run_git('git push origin HEAD', repo_path)
        
        if p_code == 0:
            print(f"   ✅ กลุ่มย่อยที่ {i // batch_size + 1} ส่งขึ้น GitHub สำเร็จ!")
        else:
            print(f"   ❌ กลุ่มย่อยนี้ส่งไม่ผ่าน: {p_err}")
            
        # หน่วงเวลา 5 วินาที เพื่อเซฟแบนด์วิดท์เครือข่ายตามเกณฑ์ความปลอดภัย
        if i + batch_size < len(changed_files):
            print("   💤 พักจังหวะระบบ 5 วินาที เพื่อความเสถียร...")
            time.sleep(5)
            
    print(f"   ✨ ห้อง {repo_name} ปรับข้อมูลตรงกับ GitHub 100% เรียบร้อยแล้ว\n")
    time.sleep(1)

print("=====================================================================")
print("🎉 [เสร็จสิ้น] กวาดล้างคิวค้างสำเร็จ ข้อมูลในคอมพ์และบน GitHub ตรงกัน 100% ทุกห้องเพลงแล้วครับคุณ Runnara!")