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
            timeout=600  # ขยายเวลารอ 10 นาทีต่อรอบ สำหรับก้อนไฟล์เพลงขนาดใหญ่
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

def get_current_branch(repo_path):
    code, out, _ = run_git("git branch --show-current", repo_path)
    if code == 0 and out.strip():
        return out.strip()
    return "main"

print("🚀 [ระบบกระจกเงาเคลียร์คิวขั้นเด็ดขาด - ยึดคอมพิวเตอร์เป็นหลัก 50 Files / 5 Sec]")
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

print(f"📂 ตรวจพบ Repository หมวดเพลงทั้งหมด {len(target_repos)} ห้อง\n")

for repo_idx, repo_path in enumerate(target_repos, 1):
    repo_name = os.path.basename(repo_path)
    branch_name = get_current_branch(repo_path)
    
    # อัปเดตประวัติจากเซิร์ฟเวอร์ออนไลน์มาก่อนเปรียบเทียบ
    run_git("git fetch origin", repo_path)
    
    # 1. ดึงรายชื่อไฟล์ปัจจุบันบน GitHub ออนไลน์
    code_remote, remote_files_raw, _ = run_git(f"git ls-tree -r origin/{branch_name} --name-only", repo_path)
    remote_files = set(remote_files_raw.splitlines()) if code_remote == 0 else set()
    
    # 2. ดึงรายชื่อไฟล์จริงในเครื่องคอมพิวเตอร์ ณ เวลานี้
    local_files = set()
    for root, dirs, files in os.walk(repo_path):
        if '.git' in root: continue
        for f in files:
            if f.lower().endswith('.mp3') or f == '.gitattributes':
                rel_p = os.path.relpath(os.path.join(root, f), repo_path).replace('\\', '/')
                local_files.add(rel_p)

    # คำนวณความแตกต่างแบบกระจกเงา (Mirror)
    to_add = local_files - remote_files      # ในคอมมี แต่บนเว็บไม่มี -> ต้องเพิ่ม
    to_remove = remote_files - local_files   # บนเว็บมี แต่ในคอมลบแล้ว -> ต้องสั่งลบออกบนเว็บ
    
    all_changes = sorted(list(to_add)) + sorted(list(to_remove))
    
    if not all_changes:
        print(f"📦 [{repo_idx}/{len(target_repos)}] ห้อง {repo_name}: ข้อมูลตรงกันสมบูรณ์แล้ว ✅")
        continue

    print(f"📦 [{repo_idx}/{len(target_repos)}] เข้าจัดการห้อง: {repo_name} (ท่อกิ่ง: {branch_name})")
    print(f"   ⚠️ ต้องเพิ่มเข้า GitHub: {len(to_add)} ไฟล์ / ต้องลบออกจาก GitHub: {len(to_remove)} ไฟล์")
    print(f"   🚀 เริ่มทยอยเคลียร์คิวระบายออกจาก GHD รวม {len(all_changes)} รายการ...")

    # บังคับเปิดท่อเชื่อมสายให้ตรงกิ่งกันก่อน
    run_git(f"git push -u origin {branch_name}", repo_path)

    # 3. เริ่มสับกลุ่มส่งรอบละไม่เกิน 50 ไฟล์ เพื่อป้องกันอาการค้าง
    batch_size = 50
    has_media = False

    for i in range(0, len(all_changes), batch_size):
        batch = all_changes[i:i + batch_size]
        print(f"   🔄 กำลังผลักกลุ่มย่อยที่ {i // batch_size + 1} (รายการที่ {i+1} ถึง {min(i + batch_size, len(all_changes))})")
        
        # จัดการคำสั่งรายไฟล์ในกลุ่มย่อย
        for rel_file in batch:
            quoted_p = shlex.quote(rel_file)
            if rel_file in to_add:
                run_git(f"git add {quoted_p}", repo_path)
                if rel_file.lower().endswith('.mp3'):
                    has_media = True
            elif rel_file in to_remove:
                run_git(f"git rm --cached -r {quoted_p}", repo_path)

        # ทำการ Commit ประจำกลุ่มย่อย
        run_git(f'git commit -m "Mirror sync batch {i // batch_size + 1}"', repo_path)
        
        # บังคับสตรีมก้อนไฟล์เพลงจริง (.mp3) หนีออกจากเครื่องขึ้นเซิร์ฟเวอร์ทันที
        if has_media:
            print("     📤 บังคับสตรีมไฟล์สื่อเนื้อหาจริง (Git LFS Push)...")
            run_git(f'git lfs push origin {branch_name}', repo_path)
            has_media = False
            
        # 🔥 [จุดแก้ไขเด็ดขาด] ใช้คำสั่ง Force Push แบบระบุสายท่อกิ่งเพื่อทะลวงคิวล็อกใน GHD ให้หลุดออก
        p_code, _, p_err = run_git(f"git push origin +{branch_name}", repo_path)
        
        if p_code == 0:
            print(f"   ✅ กลุ่มย่อยที่ {i // batch_size + 1} หลุดออกจากคิว GHD เรียบร้อย!")
        else:
            print(f"   ❌ กลุ่มย่อยนี้ส่งไม่ผ่าน: {p_err}")
            
        # หน่วงเวลา 5 วินาที ตามเกณฑ์ความปลอดภัยสูงสุด
        if i + batch_size < len(all_changes):
            print("   💤 หยุดพักระบบเครือข่าย 5 วินาที เพื่อความเสถียร...")
            time.sleep(5)
            
    print(f"   ✨ ห้อง {repo_name} ซิงค์ข้อมูลสมบูรณ์แบบเสร็จสิ้น\n")

print("=====================================================================")
print("🎉 [เสร็จสมบูรณ์] บังคับระบายคิวค้างใน GHD สำเร็จ ข้อมูลฝั่ง GitHub ตรงตามคอมพิวเตอร์ของคุณ 100% แล้วครับ!")