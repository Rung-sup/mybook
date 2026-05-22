import os
import json
import shutil
import hashlib
import subprocess
import time
import unicodedata
import urllib.parse
import re
import shlex
import sys
from pdf2image import convert_from_path

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
PROCESS_ZONE = r'C:\\Process_Zone'
LIBRARY_ROOT = r'C:\\MyLibrary'
DB_DIR = r'C:\\MyBook_Test'

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
POPPLER_PATH = r'C:\\MyBook_Test\\poppler-25.12.0\\Library\\bin'
GITHUB_USER = "rung-sup"

REPAIR_MISSING_COVERS = True
FORCE_REBUILD_COVERS = False
COVER_MIN_BYTES = 1024
LOG_PATH = os.path.join(DB_DIR, 'cover_repair_log.txt')


def log(msg):
    print(msg)
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception:
        pass


def reset_log():
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            f.write('=== COVER REPAIR LOG ===\n')
    except Exception:
        pass


def normalize_rel_path(path_text):
    return unicodedata.normalize('NFC', path_text.replace('\\', '/')).replace('\u0e4d\u0e32', '\u0e33')


def generate_cover_id(rel_path):
    normalized = normalize_rel_path(rel_path)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def get_file_hash(f_path):
    hasher = hashlib.md5()
    try:
        with open(f_path, 'rb') as f:
            chunk = f.read(1024 * 1024)
            hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def safe_json_dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(path):
        os.remove(path)
    os.replace(tmp, path)


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
            timeout=180
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, '', str(e)


def is_git_repo(path):
    return os.path.exists(os.path.join(path, '.git'))


def build_file_url(repo_name, full_path, cat_root_path):
    path_in_repo = os.path.relpath(full_path, cat_root_path).replace('\\', '/')
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_name}/main/{urllib.parse.quote(path_in_repo)}"


def should_rebuild_cover(cover_out):
    if FORCE_REBUILD_COVERS:
        return True
    if not REPAIR_MISSING_COVERS:
        return not os.path.exists(cover_out)
    if not os.path.exists(cover_out):
        return True
    try:
        if os.path.getsize(cover_out) < COVER_MIN_BYTES:
            return True
    except Exception:
        return True
    return False


def render_cover_with_poppler(pdf_path, cover_out, use_retry=False):
    kwargs = {
        'pdf_path': pdf_path,
        'first_page': 1,
        'last_page': 1,
        'poppler_path': POPPLER_PATH,
    }
    if use_retry:
        kwargs['dpi'] = 100
        kwargs['use_cropbox'] = True
    else:
        kwargs['size'] = (None, 400)

    imgs = convert_from_path(**kwargs)
    if not imgs:
        return False
    img = imgs[0]
    img.thumbnail((300, 400))
    img.save(cover_out, 'JPEG', quality=85)
    return os.path.exists(cover_out) and os.path.getsize(cover_out) >= COVER_MIN_BYTES


def ensure_pdf_cover(pdf_path, cover_out, context_label='PDF'):
    os.makedirs(os.path.dirname(cover_out), exist_ok=True)

    if not should_rebuild_cover(cover_out):
        return False, 'skip'

    if not os.path.exists(POPPLER_PATH):
        log(f"❌ [{context_label}] ไม่พบ POPPLER_PATH: {POPPLER_PATH}")
        return False, 'missing-poppler'

    try:
        ok = render_cover_with_poppler(pdf_path, cover_out, use_retry=False)
        if ok:
            log(f"✅ [{context_label}] สร้างปกสำเร็จ: {pdf_path}")
            return True, 'ok-main'
        log(f"⚠️ [{context_label}] Poppler รอบหลักไม่คืนภาพ: {pdf_path}")
    except Exception as e:
        log(f"⚠️ [{context_label}] Poppler รอบหลักล้มเหลว: {pdf_path} | {e}")

    try:
        ok = render_cover_with_poppler(pdf_path, cover_out, use_retry=True)
        if ok:
            log(f"✅ [{context_label}] สร้างปกสำเร็จด้วย retry mode: {pdf_path}")
            return True, 'ok-retry'
        log(f"⚠️ [{context_label}] Retry mode ยังไม่คืนภาพ: {pdf_path}")
    except Exception as e:
        log(f"❌ [{context_label}] Retry mode ล้มเหลว: {pdf_path} | {e}")

    return False, 'failed'


# ==========================================
# 🚀 STEP 1: ย้ายโฟลเดอร์ย่อยโดยรักษาโครงสร้างเดิม 100%
# ==========================================
def step1_process_and_move():
    log("🚀 [1/3] ตรวจสอบไฟล์ใหม่และย้ายเข้าระบบ (Deep Scan)...")
    if not os.path.exists(PROCESS_ZONE):
        log(f"ℹ️ ไม่พบ PROCESS_ZONE: {PROCESS_ZONE} — ข้ามขั้นตอนนี้")
        return

    categories = [d for d in os.listdir(PROCESS_ZONE) if os.path.isdir(os.path.join(PROCESS_ZONE, d))]

    for cat in categories:
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        target_lib = os.path.join(LIBRARY_ROOT, cat.strip())

        if not os.path.exists(target_lib):
            os.makedirs(target_lib, exist_ok=True)

        for item in os.listdir(cat_staging):
            src_path = os.path.join(cat_staging, item)
            dest_path = os.path.join(target_lib, item)

            if os.path.exists(dest_path):
                log(f"⚠️ พบรายการซ้ำที่ปลายทางแล้ว ข้ามการย้าย: {item}")
                continue

            try:
                shutil.move(src_path, dest_path)
                log(f"📦 [ย้ายสำเร็จ] {item} -> คลังหลัก [{cat.strip()}] (คงโครงสร้างโฟลเดอร์)")
            except Exception as e:
                log(f"❌ เกิดข้อผิดพลาดในการย้าย {item}: {e}")


# ==========================================
# 📊 STEP 2: สร้าง DB + ปกรายไฟล์ + ปกโฟลเดอร์
# ==========================================
def step2_build_databases():
    log("📊 [2/3] อัปเดตฐานข้อมูลและสร้าง/ซ่อมรูปปก...")
    all_books, all_music = [], []

    if not os.path.exists(LIBRARY_ROOT):
        log(f"❌ ไม่พบ LIBRARY_ROOT: {LIBRARY_ROOT}")
        return

    repaired_count = 0
    failed_count = 0

    for cat_folder in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat_folder)
        if not os.path.isdir(cat_path) or cat_folder in ['.git', 'covers', '.github']:
            continue

        folder_info = {}

        for root, dirs, files in os.walk(cat_path):
            rel_f = os.path.relpath(root, cat_path)
            folder_disp = 'ทั่วไป' if rel_f == '.' else rel_f

            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')):
                    continue

                full_p = os.path.join(root, f)
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                c_id = generate_cover_id(rel_from_library)

                if f.lower().endswith('.pdf'):
                    cover_dir = os.path.join(DB_DIR, 'covers', cat_folder)
                    cover_out = os.path.join(cover_dir, f"{c_id}.jpg")
                    changed, status = ensure_pdf_cover(full_p, cover_out, context_label='BOOK')
                    if changed:
                        repaired_count += 1
                    elif status == 'failed':
                        failed_count += 1

                    if folder_disp != 'ทั่วไป':
                        if folder_disp not in folder_info:
                            folder_info[folder_disp] = {'first_pdf': full_p, 'count': 0}
                        folder_info[folder_disp]['count'] += 1

                item_data = {
                    'title': os.path.splitext(f)[0],
                    'url': build_file_url(cat_folder, full_p, cat_path),
                    'category': cat_folder,
                    'folder': folder_disp,
                    'cover_id': c_id,
                    'file_hash': get_file_hash(full_p)
                }

                if cat_folder.startswith('7_') or f.lower().endswith('.mp3'):
                    all_music.append(item_data)
                else:
                    all_books.append(item_data)

        for folder_name, info in folder_info.items():
            try:
                folder_rel_path = os.path.join(cat_folder, folder_name)
                folder_cover_id = generate_cover_id(folder_rel_path)
                cover_dir = os.path.join(DB_DIR, 'covers', cat_folder)
                folder_cover_out = os.path.join(cover_dir, f"folder_{folder_cover_id}.jpg")

                changed, status = ensure_pdf_cover(info['first_pdf'], folder_cover_out, context_label=f'FOLDER:{folder_name}')
                if changed:
                    repaired_count += 1
                elif status == 'failed':
                    failed_count += 1

                for book in all_books:
                    if book['category'] == cat_folder and book['folder'] == folder_name:
                        book['folder_cover_id'] = f"folder_{folder_cover_id}"
                        book['folder_book_count'] = info['count']

            except Exception as e:
                log(f"⚠️ เกิดข้อผิดพลาดกับปกโฟลเดอร์ {folder_name}: {e}")

    safe_json_dump(DB_PATH, {'books': all_books})
    safe_json_dump(MUSIC_DB_PATH, {'music': all_music})
    log(f"✅ อัปเดตฐานข้อมูลเสร็จสิ้น! หนังสือ {len(all_books)} รายการ, เพลง {len(all_music)} รายการ")
    log(f"🛠️ สรุปการซ่อมปก: สร้าง/ซ่อม {repaired_count} รายการ | ล้มเหลว {failed_count} รายการ")


# ==========================================
# ☁️ STEP 3: BATCH SYNC TO GITHUB
# ==========================================
def step3_git_sync_batched(repo_path):
    if not is_git_repo(repo_path):
        return

    code, out, _ = run_git('git status --porcelain', repo_path)
    if code != 0 or not out.strip():
        return

    changed_files = []
    for line in out.splitlines():
        if len(line) > 3:
            changed_files.append(line[3:].strip('"'))
    if not changed_files:
        return

    log(f"📦 {os.path.basename(repo_path)}: ตรวจพบไฟล์เปลี่ยนแปลง {len(changed_files)} ไฟล์ กำลังทยอยส่ง...")
    batch_size = 15

    for i in range(0, len(changed_files), batch_size):
        batch = changed_files[i:i + batch_size]
        quoted_files = ' '.join(shlex.quote(f) for f in batch)
        run_git(f'git add {quoted_files}', repo_path)
        run_git(f'git commit -m "Auto-sync batch {i // batch_size + 1}"', repo_path)
        code, _, err = run_git('git push origin HEAD', repo_path)
        if code == 0:
            log(f" ✅ ส่งสำเร็จแล้ว {min(i + batch_size, len(changed_files))}/{len(changed_files)}")
        else:
            log(f" ❌ Batch นี้ส่งไม่สำเร็จ: {err}")
        if i + batch_size < len(changed_files):
            time.sleep(3)


def sync_all_repositories():
    log("☁️ [3/3] เริ่มกระบวนการ Batch Sync ไปยัง GitHub...")
    if os.path.exists(LIBRARY_ROOT):
        for folder in sorted(os.listdir(LIBRARY_ROOT)):
            f_p = os.path.join(LIBRARY_ROOT, folder)
            if os.path.isdir(f_p):
                step3_git_sync_batched(f_p)
    if is_git_repo(DB_DIR):
        step3_git_sync_batched(DB_DIR)


if __name__ == '__main__':
    if os.name == 'nt':
        os.system('chcp 65001 > nul')

    reset_log()
    log('▶️ เริ่มระบบจัดการคลังหนังสือรันนารา (Repair Cover Edition)')
    log(f'ℹ️ REPAIR_MISSING_COVERS = {REPAIR_MISSING_COVERS}')
    log(f'ℹ️ FORCE_REBUILD_COVERS = {FORCE_REBUILD_COVERS}')

    step1_process_and_move()
    step2_build_databases()
    sync_all_repositories()

    log('\n✨ ทำงานเสร็จสมบูรณ์ ทุกอย่างอัปเดตเป็นปัจจุบันแล้วครับ!')
