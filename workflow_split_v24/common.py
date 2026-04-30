import os, json, hashlib, shutil, subprocess
from pathlib import Path
from datetime import datetime

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

BOOK_EXTS = {'.pdf'}
MUSIC_EXTS = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
TEXT_LINKS = {'.txt'}
ALLOWED_EXTS = BOOK_EXTS | MUSIC_EXTS | TEXT_LINKS


def load_config(config_path='workflow_config.json'):
    return json.loads(Path(config_path).read_text(encoding='utf-8'))


def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def sha256_file(path, chunk_size=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(path, root):
    return str(Path(path).resolve().relative_to(Path(root).resolve())).replace('\\', '/')


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def read_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return default


def state_paths(state_root):
    root = Path(state_root)
    ensure_dir(root)
    return {
        'root': root,
        'manifest': root / 'library_manifest.json',
        'index': root / 'library_file_index.json',
        'history': root / 'ingest_history.json'
    }


def load_state(state_root):
    sp = state_paths(state_root)
    manifest = read_json(sp['manifest'], {'files': {}, 'updated_at': None})
    index = read_json(sp['index'], {})
    history = read_json(sp['history'], {'runs': []})
    return sp, manifest, index, history


def save_state(sp, manifest, index, history):
    manifest['updated_at'] = now_iso()
    write_json(sp['manifest'], manifest)
    write_json(sp['index'], index)
    write_json(sp['history'], history)


def validate_pdf(path):
    if PdfReader is None:
        return True, 'pypdf_unavailable'
    try:
        reader = PdfReader(path)
        _ = len(reader.pages)
        return True, 'ok'
    except Exception as e:
        return False, f'pdf_invalid: {e}'


def validate_audio(path):
    try:
        size = os.path.getsize(path)
        if size < 1024:
            return False, 'audio_too_small'
        with open(path, 'rb') as f:
            head = f.read(16)
        if not head:
            return False, 'audio_empty'
        return True, 'ok'
    except Exception as e:
        return False, f'audio_invalid: {e}'


def compress_pdf_if_needed(src_path, max_pdf_mb):
    src = Path(src_path)
    max_bytes = int(max_pdf_mb * 1024 * 1024)
    size = src.stat().st_size
    if size <= max_bytes:
        return str(src), False, 'within_limit'
    gs = shutil.which('gswin64c') or shutil.which('gswin32c') or shutil.which('gs')
    if not gs:
        return str(src), False, 'ghostscript_not_found'
    tmp = src.with_suffix('.compressed.tmp.pdf')
    cmd = [
        gs, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        '-dDetectDuplicateImages=true', '-dDownsampleColorImages=true', '-dColorImageResolution=150',
        '-dDownsampleGrayImages=true', '-dGrayImageResolution=150', '-dDownsampleMonoImages=true',
        '-dMonoImageResolution=300', f'-sOutputFile={str(tmp)}', str(src)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0 or not tmp.exists():
        return str(src), False, 'compress_failed'
    valid, _ = validate_pdf(tmp)
    if not valid:
        tmp.unlink(missing_ok=True)
        return str(src), False, 'compress_invalid_pdf'
    if tmp.stat().st_size >= size:
        tmp.unlink(missing_ok=True)
        return str(src), False, 'compress_not_smaller'
    final = src.with_suffix('.optimized.pdf')
    if final.exists():
        final.unlink()
    tmp.replace(final)
    return str(final), True, 'compressed'


def cover_id_for_file(rel_path, sha256):
    return hashlib.md5(f'{rel_path}|{sha256}'.encode('utf-8')).hexdigest()


def build_item(room, rel_room_path, sha256, github_account, branch):
    title = Path(rel_room_path).stem
    folder = str(Path(rel_room_path).parent).replace('\\', '/')
    folder = '' if folder == '.' else folder
    return {
        'title': title,
        'category': room,
        'folder': folder,
        'cover_id': cover_id_for_file(rel_room_path, sha256),
        'file_hash': sha256,
        'source_relpath': rel_room_path,
        'url': f'https://raw.githubusercontent.com/{github_account}/{room}/{branch}/{rel_room_path}'
    }


def build_audiobook_items(room_path):
    out = []
    for txt in Path(room_path).rglob('*.txt'):
        try:
            lines = [x.strip() for x in txt.read_text(encoding='utf-8', errors='ignore').splitlines() if x.strip()]
        except Exception:
            continue
        eps = []
        for i, line in enumerate(lines, start=1):
            if 'youtube.com' in line or 'youtu.be' in line:
                eps.append({'ep_title': f'ตอนที่ {i}', 'ep_url': line})
        if eps:
            rel = safe_rel(txt, room_path)
            out.append({
                'title': txt.stem,
                'category': '8_AudioBooks',
                'folder': str(Path(rel).parent).replace('\\', '/'),
                'cover_id': hashlib.md5(rel.encode('utf-8')).hexdigest(),
                'episodes': eps,
                'file_hash': sha256_file(txt),
                'source_relpath': rel
            })
    return out


def build_global_library_index(library_root, rooms):
    index = {}
    for room, meta in rooms.items():
        room_path = Path(library_root) / room
        if not room_path.exists():
            continue
        for f in room_path.rglob('*'):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in ALLOWED_EXTS:
                continue
            size = f.stat().st_size
            key = f'{ext}|{size}'
            rec = {
                'room': room,
                'relpath': safe_rel(f, room_path),
                'size': size,
                'ext': ext,
                'sha256': sha256_file(f)
            }
            index.setdefault(key, []).append(rec)
    return index


def find_duplicate_in_library(global_index, ext, size, sha256=None):
    key = f'{ext}|{size}'
    matches = global_index.get(key, [])
    if not matches:
        return None, 'no_match'
    if sha256 is None:
        return matches[0], 'same_ext_same_size'
    for m in matches:
        if m.get('sha256') == sha256:
            return m, 'same_ext_same_size_same_hash'
    return matches[0], 'same_ext_same_size_diff_hash'


def git_changed_files(repo_path):
    r = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return []
    files = []
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path:
            files.append(path)
    return files


def chunk_files_by_policy(repo_path, rel_files, max_files, max_total_mb, max_file_mb):
    max_total_bytes = int(max_total_mb * 1024 * 1024)
    max_file_bytes = int(max_file_mb * 1024 * 1024)
    batches, skipped = [], []
    current, current_size = [], 0
    for rel in rel_files:
        abs_p = Path(repo_path) / rel
        if not abs_p.exists():
            continue
        size = abs_p.stat().st_size
        if size > max_file_bytes:
            skipped.append({'file': rel, 'reason': 'file_too_large_for_github', 'size_bytes': size})
            continue
        if current and (len(current) >= max_files or current_size + size > max_total_bytes):
            batches.append(current)
            current, current_size = [], 0
        current.append(rel)
        current_size += size
    if current:
        batches.append(current)
    return batches, skipped


def git_commit_push_batched(repo_path, remote, branch, message_prefix, max_files, max_total_mb, max_file_mb):
    if not (Path(repo_path) / '.git').exists():
        return {'success': False, 'result': 'no_git_repo', 'batches': [], 'skipped': []}
    rel_files = git_changed_files(repo_path)
    if not rel_files:
        return {'success': False, 'result': 'no_changes', 'batches': [], 'skipped': []}
    batches, skipped = chunk_files_by_policy(repo_path, rel_files, max_files, max_total_mb, max_file_mb)
    results = []
    for i, batch in enumerate(batches, start=1):
        subprocess.run(['git', 'reset'], cwd=repo_path, check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')
        add = subprocess.run(['git', 'add', '--'] + batch, cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if add.returncode != 0:
            results.append({'batch': i, 'success': False, 'result': (add.stdout + add.stderr)[-500:], 'files': batch})
            continue
        commit = subprocess.run(['git', 'commit', '-m', f'{message_prefix} [batch {i}/{len(batches)}]'], cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if commit.returncode != 0 and 'nothing to commit' not in (commit.stdout + commit.stderr).lower():
            results.append({'batch': i, 'success': False, 'result': (commit.stdout + commit.stderr)[-500:], 'files': batch})
            continue
        push = subprocess.run(['git', 'push', remote, branch], cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
        results.append({'batch': i, 'success': push.returncode == 0, 'result': ((push.stdout + push.stderr)[-500:] if push.returncode != 0 else 'pushed'), 'files': batch})
        if push.returncode != 0:
            break
    overall = all(x['success'] for x in results) if results else False
    return {'success': overall, 'result': 'batched_push_complete' if overall else 'batched_push_partial_or_failed', 'batches': results, 'skipped': skipped}
