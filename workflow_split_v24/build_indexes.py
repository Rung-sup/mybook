import json
from pathlib import Path
from common import load_config, ensure_dir, sha256_file, safe_rel, build_item, build_audiobook_items, BOOK_EXTS, MUSIC_EXTS, write_json, now_iso

cfg = load_config()
library_root = Path(cfg['library_root'])
site_root = Path(cfg['site_root'])
logs_root = Path(cfg['logs_root'])
rooms = cfg['rooms']
ensure_dir(site_root)
ensure_dir(logs_root)

changed_rooms_path = Path(logs_root) / 'last_ingest_report.json'
changed_rooms = []
if changed_rooms_path.exists():
    changed_rooms = json.loads(changed_rooms_path.read_text(encoding='utf-8')).get('changed_rooms', [])

books, music, audiobooks = [], [], []
for room, meta in rooms.items():
    room_path = library_root / room
    if not room_path.exists():
        continue
    if meta['type'] == 'audiobooks':
        audiobooks.extend(build_audiobook_items(room_path))
        continue
    for f in room_path.rglob('*'):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if meta['type'] == 'books' and ext not in BOOK_EXTS:
            continue
        if meta['type'] == 'music' and ext not in MUSIC_EXTS:
            continue
        rel_room = safe_rel(f, room_path)
        sha = sha256_file(f)
        item = build_item(room, rel_room, sha, cfg['github_account'], cfg['github_branch'])
        if meta['type'] == 'books':
            books.append(item)
        else:
            music.append(item)

write_json(cfg['database_json'], {'books': books})
write_json(cfg['music_db_json'], {'music': music})
write_json(cfg['audiobook_db_json'], {'audiobooks': audiobooks})
report = {
    'built_at': now_iso(),
    'changed_rooms': changed_rooms,
    'counts': {'books': len(books), 'music': len(music), 'audiobooks': len(audiobooks)}
}
write_json(str(Path(logs_root) / 'last_index_report.json'), report)
print(json.dumps(report, ensure_ascii=False, indent=2))
