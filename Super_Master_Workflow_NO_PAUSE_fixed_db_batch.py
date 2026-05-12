import os
import sys
import json
import shutil
import hashlib
import subprocess
import time
import unicodedata
import urllib.parse
import re
import shlex

import requests
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

PROCESS_ZONE = r'C:\\Process_Zone'
LIBRARY_ROOT = r'C:\\MyLibrary'
DB_DIR = r'C:\\MyBook_Test'

DB_PATH = os.path.join(DB_DIR, 'database.json')
MUSIC_DB_PATH = os.path.join(DB_DIR, 'music_db.json')
AUDIOBOOK_DB_PATH = os.path.join(DB_DIR, 'audiobook_db.json')
STATE_PATH = os.path.join(DB_DIR, 'workflow_state.json')
REPORT_PATH = os.path.join(DB_DIR, 'workflow_report.txt')

POPPLER_PATH = r'C:\\MyBook_Test\\poppler-25.12.0\\Library\\bin'
GS_PATH = r'C:\\Program Files\\gs\\gs10.07.0\\bin\\gswin64c.exe'

GITHUB_USER = "rung-sup"
MAX_SIZE_MB = 95
PUSH_BATCH_SIZE = 20
PUSH_BATCH_DELAY_SEC = 3
ALLOW_FORCE_PUSH = False
PUSH_DB_ALWAYS = True

def now_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def write_report(lines):
    os.makedirs(DB_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def save_state(step, phase="", current_category="", current_root="", current_file="", status="paused", error="", suggestion=""):
    os.makedirs(DB_DIR, exist_ok=True)
    state = {
        "timestamp": now_text(),
        "step": step,
        "phase": phase,
        "current_category": current_category,
        "current_root": current_root,
        "current_file": current_file,
        "status": status,
        "error": error,
        "suggestion": suggestion
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_state():
    if not os.path.exists(STATE_PATH):
        return {"step": 1, "phase": "", "current_category": "", "current_root": "", "current_file": "", "status": "new", "error": "", "suggestion": ""}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_state():
    if os.path.exists(STATE_PATH):
        os.remove(STATE_PATH)

def pause_workflow(step, phase, title, issue, suggestion, current_category="", current_root="", current_file=""):
    lines = [
        "=" * 72,
        f"WORKFLOW ERROR LOG @ {now_text()}",
        f"STEP      : {step}",
        f"PHASE     : {phase}",
        f"CATEGORY  : {current_category}",
        f"ROOT      : {current_root}",
        f"FILE      : {current_file}",
        "-" * 72,
        f"ISSUE     : {title}",
        f"DETAIL    : {issue}",
        f"SUGGEST   : {suggestion}",
        "=" * 72
    ]
    print(f"⚠️ ตรวจพบข้อผิดพลาด: {title} (บันทึกลง Log แล้ว ข้ามการทำงานส่วนนี้...)")
    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return False

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
            if os.path.getsize(f_path) > 1024 * 1024:
                f.seek(-1024 * 1024, os.SEEK_END)
                hasher.update(f.read())
        return hasher.hexdigest()
    except:
        return None

def safe_json_load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def safe_json_dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(path):
        os.remove(path)
    os.replace(tmp, path)

def ensure_required_paths():
    for p in [PROCESS_ZONE, LIBRARY_ROOT, DB_DIR]:
        if not os.path.exists(p):
            print(f"❌ ไม่พบโฟลเดอร์ที่จำเป็น: {p}")
            return False
    return True

def get_main_category_name(category_name):
    return re.sub(r'_Vol\d+$', '', category_name, flags=re.IGNORECASE)

def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

def compress_pdf_high(f_path):
    if not os.path.exists(GS_PATH):
        return False, "Ghostscript not found"
    temp_out = f_path.replace(".pdf", "_compressed_tmp.pdf")
    gs_cmd = [GS_PATH, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH', f'-sOutputFile={temp_out}', f_path]
    try:
        subprocess.run(gs_cmd, capture_output=True, timeout=300)
        if os.path.exists(temp_out):
            if os.path.getsize(temp_out) < os.path.getsize(f_path):
                os.remove(f_path)
                os.rename(temp_out, f_path)
            else:
                os.remove(temp_out)
            return True, None
        return False, "compressed temp file was not created"
    except Exception as e:
        return False, str(e)

def split_with_cover_injection(f_path):
    try:
        reader = PdfReader(f_path)
        total_pages = len(reader.pages)
        if total_pages < 2:
            return False, "PDF has less than 2 pages"
        base_name = os.path.splitext(f_path)[0]
        mid = total_pages // 2
        w1 = PdfWriter()
        for i in range(0, mid):
            w1.add_page(reader.pages[i])
        path1 = f"{base_name} Part 1.1.pdf"
        with open(path1, "wb") as f:
            w1.write(f)
        w2 = PdfWriter()
        w2.add_page(reader.pages[0])
        for i in range(mid, total_pages):
            w2.add_page(reader.pages[i])
        path2 = f"{base_name} Part 1.2.pdf"
        with open(path2, "wb") as f:
            w2.write(f)
        os.remove(f_path)
        return True, [path1, path2]
    except Exception as e:
        return False, str(e)

def generate_pdf_cover(pdf_path, cover_out):
    try:
        imgs = convert_from_path(pdf_path, first_page=1, last_page=1, size=(None, 400), poppler_path=POPPLER_PATH)
        if imgs:
            imgs[0].save(cover_out, 'JPEG', quality=85)
            return True, None
        return False, "pdf2image returned no image"
    except Exception as e:
        return False, str(e)

def extract_youtube_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0].strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].strip()
    return ""

def get_video_thumbnail(url, save_path):
    if os.path.exists(save_path):
        return True, None
    if "facebook.com" in url.lower() or "fb.watch" in url.lower():
        return False, "Facebook thumbnail auto-fetch not supported. Please use UI default cover."
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return False, "unsupported url format"
    img_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    try:
        r = requests.get(img_url, timeout=15)
        if r.status_code == 200 and r.content:
            with open(save_path, 'wb') as f:
                f.write(r.content)
            return True, None
        return False, f"thumbnail fetch failed with status {r.status_code}"
    except Exception as e:
        return False, str(e)

def parse_links_file(link_path):
    if not os.path.exists(link_path):
        return False, "links.txt not found", None
    try:
        with open(link_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.read().splitlines() if line.strip()]
    except Exception as e:
        return False, str(e), None
    if not lines:
        return False, "links.txt is empty", None
    episodes = []
    current_title = ""
    urls = []
    for line in lines:
        if "http" in line:
            urls.append(line)
            episodes.append({"ep_title": current_title if current_title else "Untitled Episode", "ep_url": line})
        else:
            current_title = line
    if not urls:
        return False, "no URL found in links.txt", None
    invalid = []
    for u in urls:
        is_yt = bool(extract_youtube_video_id(u))
        is_fb = "facebook.com" in u.lower() or "fb.watch" in u.lower()
        if not is_yt and not is_fb:
            invalid.append(u)
    if invalid:
        return False, f"unsupported url(s): {invalid[:3]}", None
    return True, "", {"episodes": episodes, "first_link": urls[0]}

def run_git(command, cwd, timeout=60):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=cwd, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 999, "", str(e)

def is_git_repo(path):
    return os.path.exists(os.path.join(path, ".git"))

def get_current_branch(repo_path):
    code, out, err = run_git("git rev-parse --abbrev-ref HEAD", repo_path)
    if code == 0 and out:
        return out
    return None

def has_remote_origin(repo_path):
    code, out, err = run_git("git remote", repo_path)
    if code != 0:
        return False
    remotes = [x.strip() for x in out.splitlines() if x.strip()]
    return "origin" in remotes

def git_has_changes(repo_path):
    code, out, err = run_git("git status --porcelain", repo_path)
    if code != 0:
        return None, err or out
    return bool(out.strip()), None

def get_changed_files(repo_path):
    code, out, err = run_git("git diff --name-only --cached && git diff --name-only && git ls-files --others --exclude-standard", repo_path, timeout=120)
    if code != 0:
        return None, err or out
    changed_files = []
    for line in out.splitlines():
        p = line.strip()
        if p:
            changed_files.append(p)
    return changed_files, None

def git_push(repo_path, allow_force=False):
    branch = get_current_branch(repo_path)
    if not branch:
        return False, "cannot detect current branch"
    if not has_remote_origin(repo_path):
        return False, "remote origin not found"
    cmd = f"git push origin HEAD{' -f' if allow_force else ''}"
    code, out, err = run_git(cmd, repo_path, timeout=300)
    if code != 0:
        return False, err or out
    return True, ""

def git_commit_and_push_in_batches(repo_path, base_message, allow_force=False, batch_size=PUSH_BATCH_SIZE, delay_sec=PUSH_BATCH_DELAY_SEC):
    changed_files, err = get_changed_files(repo_path)
    if err:
        return False, f"git status failed: {err}"
    if not changed_files:
        return True, "skip:no_change"
    total_batches = (len(changed_files) + batch_size - 1) // batch_size
    for batch_index, batch in enumerate(chunked(changed_files, batch_size), start=1):
        quoted_files = " ".join(shlex.quote(p) for p in batch)
        code, out, err = run_git(f"git add -- {quoted_files}", repo_path, timeout=180)
        if code != 0:
            return False, f"git add batch {batch_index} failed: {err or out}"
        commit_message = f"{base_message} ({batch_index}/{total_batches})"
        code, out, err = run_git(f'git commit -m {shlex.quote(commit_message)}', repo_path, timeout=180)
        if code != 0:
            text = (err or out).lower()
            if "nothing to commit" in text:
                continue
            return False, f"git commit batch {batch_index} failed: {err or out}"
        ok, push_err = git_push(repo_path, allow_force=allow_force)
        if not ok:
            return False, f"git push batch {batch_index} failed: {push_err}"
        if batch_index < total_batches:
            print(f"⏳ พัก {delay_sec} วินาที ก่อน push ชุดถัดไปของ {os.path.basename(repo_path)}...")
            time.sleep(delay_sec)
    return True, f"pushed:{total_batches}_batches"

def load_existing_hashes():
    existing_hashes = {}
    if not os.path.exists(DB_PATH):
        return existing_hashes
    try:
        old_db = safe_json_load(DB_PATH)
        for b in old_db.get('books', []):
            if 'file_hash' in b and b['file_hash']:
                existing_hashes[b['file_hash']] = b.get('title', '')
    except:
        pass
    return existing_hashes

def step1_process_and_move(state):
    print("🚀 [1/3] กำลังตรวจสอบและย้ายไฟล์เข้าระบบ (ลบไฟล์ที่มีปัญหาอัตโนมัติ)...")
    existing_hashes = load_existing_hashes()
    for cat in sorted(os.listdir(PROCESS_ZONE)):
        cat_staging = os.path.join(PROCESS_ZONE, cat)
        if not os.path.isdir(cat_staging):
            continue
        target_lib = os.path.join(LIBRARY_ROOT, cat)
        os.makedirs(target_lib, exist_ok=True)
        for item in sorted(os.listdir(cat_staging)):
            f_path = os.path.join(cat_staging, item)
            save_state(1, "scan_move", cat, cat_staging, item, "running")
            if os.path.isdir(f_path):
                dest = os.path.join(target_lib, item)
                try:
                    if os.path.exists(dest):
                        shutil.rmtree(f_path)
                        print(f"🗑️ ลบโฟลเดอร์ซ้ำ: {item}")
                    else:
                        shutil.move(f_path, dest)
                except Exception:
                    print(f"❌ ย้ายโฟลเดอร์ไม่สำเร็จ ลบทิ้ง: {item}")
                    try:
                        shutil.rmtree(f_path)
                    except:
                        pass
                continue
            f_hash = get_file_hash(f_path)
            if f_hash and f_hash in existing_hashes:
                print(f"🗑️ ลบไฟล์เนื้อหาซ้ำ: {item}")
                try:
                    os.remove(f_path)
                except:
                    pass
                continue
            if item.lower().endswith('.pdf'):
                size_mb = os.path.getsize(f_path) / (1024 * 1024)
                if size_mb > MAX_SIZE_MB:
                    ok, err = compress_pdf_high(f_path)
                    if not ok:
                        print(f"❌ บีบอัดไม่สำเร็จ ลบไฟล์ทิ้ง: {item} ({err})")
                        try:
                            os.remove(f_path)
                        except:
                            pass
                        continue
                    size_mb = os.path.getsize(f_path) / (1024 * 1024)
                    if size_mb > MAX_SIZE_MB:
                        ok, result = split_with_cover_injection(f_path)
                        if not ok:
                            print(f"❌ แบ่งไฟล์ไม่สำเร็จ ลบไฟล์ทิ้ง: {item}")
                            try:
                                os.remove(f_path)
                            except:
                                pass
                            continue
            dest = os.path.join(target_lib, item)
            if os.path.exists(dest):
                print(f"⚠️ ชื่อซ้ำที่ปลายทาง ลบไฟล์ทิ้ง: {item}")
                try:
                    os.remove(f_path)
                except:
                    pass
                continue
            try:
                shutil.move(f_path, dest)
            except Exception:
                print(f"❌ ย้ายไฟล์ไม่สำเร็จ ลบไฟล์ทิ้ง: {item}")
                try:
                    os.remove(f_path)
                except:
                    pass
    save_state(1, "done", status="done")
    return True

def build_file_url(repo_category, full_path, cat_path):
    path_in_repo = os.path.relpath(full_path, cat_path).replace('\\', '/')
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_category}/main/{urllib.parse.quote(path_in_repo)}"

def step2_build_databases(state):
    print("📊 [2/3] อัปเดตฐานข้อมูล (รวมหมวด AudioBooks)...")
    all_books = []
    all_music = []
    all_audiobooks = []
    for cat in sorted(os.listdir(LIBRARY_ROOT)):
        cat_path = os.path.join(LIBRARY_ROOT, cat)
        if not os.path.isdir(cat_path) or cat in ['.git', 'covers']:
            continue
        repo_category = cat
        display_category = get_main_category_name(cat)
        is_audio_cat = display_category.startswith("8_") or "audiobook" in display_category.lower()
        for root, dirs, files in os.walk(cat_path):
            rel_folder = os.path.relpath(root, cat_path)
            display_folder = "ทั่วไป" if rel_folder == "." else rel_folder
            save_state(2, "scan_library", display_category, root, "", "running")
            if is_audio_cat and "links.txt" in files:
                link_path = os.path.join(root, "links.txt")
                ok, err, parsed = parse_links_file(link_path)
                if not ok:
                    print(f"⚠️ ข้ามโฟลเดอร์ {rel_folder} (อ่าน links.txt ไม่สำเร็จ: {err})")
                    dirs.clear()
                    continue
                cover_id = generate_cover_id(rel_folder)
                cover_dir = os.path.join(DB_DIR, 'covers', display_category)
                os.makedirs(cover_dir, exist_ok=True)
                cover_out = os.path.join(cover_dir, f"{cover_id}.jpg")
                ok, err = get_video_thumbnail(parsed["first_link"], cover_out)
                if not ok:
                    print(f"⚠️ ดึงปกอัตโนมัติไม่สำเร็จ (อาจเป็นลิงก์ FB): {rel_folder} ({err})")
                all_audiobooks.append({"title": rel_folder, "cover_id": cover_id, "category": display_category, "source_repo": repo_category, "episodes": parsed["episodes"], "type": "audiobook_playlist"})
                dirs.clear()
                continue
            for f in sorted(files):
                if not f.lower().endswith(('.pdf', '.mp3')):
                    continue
                full_p = os.path.join(root, f)
                save_state(2, "build_item", display_category, root, f, "running")
                f_hash = get_file_hash(full_p)
                rel_from_library = os.path.relpath(full_p, LIBRARY_ROOT)
                cover_id = generate_cover_id(rel_from_library)
                cover_dir = os.path.join(DB_DIR, 'covers', display_category)
                os.makedirs(cover_dir, exist_ok=True)
                cover_out = os.path.join(cover_dir, f"{cover_id}.jpg")
                if f.lower().endswith('.pdf') and not os.path.exists(cover_out):
                    ok, err = generate_pdf_cover(full_p, cover_out)
                    if not ok:
                        print(f"❌ ไฟล์ PDF เสีย สร้างปกไม่ได้ ลบไฟล์ทิ้ง: {f} ({err})")
                        try:
                            os.remove(full_p)
                        except:
                            pass
                        continue
                item_data = {"title": os.path.splitext(f)[0], "url": build_file_url(repo_category, full_p, cat_path), "category": display_category, "source_repo": repo_category, "folder": display_folder, "cover_id": cover_id, "file_hash": f_hash}
                if display_category.startswith("7_") or f.lower().endswith('.mp3'):
                    all_music.append(item_data)
                else:
                    all_books.append(item_data)
    try:
        safe_json_dump(DB_PATH, {"books": all_books})
        safe_json_dump(MUSIC_DB_PATH, {"music": all_music})
        safe_json_dump(AUDIOBOOK_DB_PATH, {"audiobooks": all_audiobooks})
    except Exception as e:
        print(f"❌ เขียนไฟล์ฐานข้อมูลไม่สำเร็จ: {e}")
        return False
    save_state(2, "done", status="done")
    return True

def sync_single_repo(repo_path, commit_message, allow_force_push=False):
    if not is_git_repo(repo_path):
        return True, "skip:not_git_repo"
    ok, err, committed = git_commit_if_needed(repo_path, commit_message)
    if not ok:
        return False, f"commit failed: {err}"
    changed, status_err = git_has_changes(repo_path)
    if status_err:
        return False, f"git status failed: {status_err}"
    if not committed and not changed:
        return True, "skip:no_change"
    ok, err = git_push(repo_path, allow_force=allow_force_push)
    if not ok:
        return False, f"push failed: {err}"
    return True, "pushed"

def step3_sync(state):
    print("☁️ [3/3] กำลังเช็กความเปลี่ยนแปลงและส่งข้อมูลขึ้น Cloud...")
    for folder in sorted(os.listdir(LIBRARY_ROOT)):
        f_p = os.path.join(LIBRARY_ROOT, folder)
        if not os.path.isdir(f_p):
            continue
        save_state(3, "sync_library_repo", folder, f_p, "", "running")
        if not is_git_repo(f_p):
            continue
        ok, msg = sync_single_repo(repo_path=f_p, commit_message="Auto-sync update", allow_force_push=ALLOW_FORCE_PUSH)
        if not ok:
            print(f"⚠️ อัปเดตโฟลเดอร์ {folder} ไม่สำเร็จ: {msg} (ข้ามไปโฟลเดอร์ถัดไป)")
        elif msg == "skip:no_change":
            print(f"⏩ ข้ามห้อง {folder} (ไม่มีการเปลี่ยนแปลง)")
        elif msg.startswith("pushed"):
            print(f"🚀 ส่งห้อง: {folder} สำเร็จ ({msg})")
    if is_git_repo(DB_DIR):
        save_state(3, "sync_db_repo", "DB_DIR", DB_DIR, "", "running")
        if PUSH_DB_ALWAYS:
            ok, msg = git_commit_and_push_in_batches(repo_path=DB_DIR, base_message="Update Audiobook DB", allow_force=False, batch_size=PUSH_BATCH_SIZE, delay_sec=PUSH_BATCH_DELAY_SEC)
            if not ok:
                print(f"⚠️ ส่งฐานข้อมูล (DB_DIR) ไม่สำเร็จ: {msg}")
            elif msg == "skip:no_change":
                print("⏩ ฐานข้อมูลไม่มีการเปลี่ยนแปลง")
            else:
                print(f"💾 ส่งฐานข้อมูลและหน้าปกสำเร็จ! ({msg})")
        else:
            ok, msg = sync_single_repo(DB_DIR, "Update Audiobook DB", allow_force_push=False)
            if not ok:
                print(f"⚠️ ส่งฐานข้อมูล (DB_DIR) ไม่สำเร็จ: {msg}")
    save_state(3, "done", status="done")
    return True

def main():
    if not ensure_required_paths():
        sys.exit(1)
    if os.name == 'nt':
        os.system('chcp 65001 > nul')
    clear_state()
    state = load_state()
    start_step = 1
    print("▶️ เริ่ม Workflow ฉบับลบไฟล์เสียอัตโนมัติ (No Pause)")
    if start_step <= 1:
        step1_process_and_move(state)
    if start_step <= 2:
        step2_build_databases(state)
    if start_step <= 3:
        step3_sync(state)
    clear_state()
    print("\n✨ เสร็จสมบูรณ์ทั้งหมด!")

if __name__ == "__main__":
    main()
