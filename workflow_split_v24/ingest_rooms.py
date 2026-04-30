import json, shutil
from pathlib import Path
from common import load_config, ensure_dir, sha256_file, safe_rel, validate_pdf, validate_audio, compress_pdf_if_needed, BOOK_EXTS, MUSIC_EXTS, TEXT_LINKS, now_iso, write_json, build_global_library_index, find_duplicate_in_library, load_state, save_state

cfg = load_config()
process_root = Path(cfg['process_root'])
library_root = Path(cfg['library_root'])
logs_root = Path(cfg['logs_root'])
archive_root = Path(cfg['archive_root'])
rooms = cfg['rooms']
ensure_dir(logs_root)
ensure_dir(archive_root)
sp, manifest, global_index, history = load_state(cfg['state_root'])
if not global_index:
    global_index = build_global_library_index(library_root, rooms)
report = {'started_at': now_iso(), 'rooms': [], 'changed_rooms': []}
changed_rooms = []
run_history = {'started_at': report['started_at'], 'rooms': []}

for room, meta in rooms.items():
    process_room = process_root / room
    library_room = library_root / room
    ensure_dir(library_room)
    room_changed = False
    rr = {
        'room': room,
        'ingested': 0,
        'archived_from_process': 0,
        'skipped_unchanged': 0,
        'skipped_invalid': 0,
        'skipped_duplicate_cross_library': 0,
        'compressed': 0,
        'skipped_too_large_after_process': 0,
        'errors': []
    }

    if process_room.exists():
        for src in process_room.rglob('*'):
            if not src.is_file():
                continue
            ext = src.suffix.lower()
            if ext not in BOOK_EXTS | MUSIC_EXTS | TEXT_LINKS:
                continue
            rel_inside_room = safe_rel(src, process_room)
            dest = library_room / rel_inside_room
            ensure_dir(dest.parent)
            try:
                src_sha = sha256_file(src)
            except Exception as e:
                rr['errors'].append(f'hash_fail:{src}:{e}')
                continue

            manifest_key = f'{room}/{rel_inside_room}'
            old = manifest['files'].get(manifest_key)
            if dest.exists() and old and old.get('sha256') == src_sha:
                rr['skipped_unchanged'] += 1
                continue

            valid, reason = True, 'ok'
            if meta['type'] == 'books' and ext == '.pdf':
                valid, reason = validate_pdf(src)
            elif meta['type'] == 'music' and ext in MUSIC_EXTS:
                valid, reason = validate_audio(src)
            elif meta['type'] == 'audiobooks' and ext == '.txt':
                valid = True
            else:
                valid, reason = False, 'unsupported_for_room'

            if not valid:
                rr['skipped_invalid'] += 1
                rr['errors'].append(f'invalid:{src}:{reason}')
                continue

            final_src = src
            if ext == '.pdf':
                out_path, compressed, comp_reason = compress_pdf_if_needed(src, cfg['max_pdf_mb'])
                final_src = Path(out_path)
                if compressed:
                    rr['compressed'] += 1
                rr['errors'].append(f'pdf_process:{src.name}:{comp_reason}')

            final_size = final_src.stat().st_size
            max_git_bytes = int(cfg['max_git_file_mb'] * 1024 * 1024)
            if final_size > max_git_bytes:
                rr['skipped_too_large_after_process'] += 1
                rr['errors'].append(f'skip_github_limit:{final_src}:{final_size}')
                continue

            dup, dup_reason = find_duplicate_in_library(global_index, ext, final_size, src_sha)
            if dup is not None:
                same_dest = (dup['room'] == room and dup['relpath'] == rel_inside_room)
                if not same_dest:
                    rr['skipped_duplicate_cross_library'] += 1
                    rr['errors'].append(f'duplicate:{src}:matched={dup["room"]}/{dup["relpath"]}:reason={dup_reason}')
                    continue

            shutil.copy2(final_src, dest)
            manifest['files'][manifest_key] = {
                'room': room,
                'relpath': rel_inside_room,
                'sha256': src_sha,
                'size': dest.stat().st_size,
                'mtime': int(dest.stat().st_mtime),
                'ext': ext,
                'status': 'ok',
                'last_ingested_at': now_iso()
            }
            global_index.setdefault(f'{ext}|{dest.stat().st_size}', []).append({
                'room': room,
                'relpath': rel_inside_room,
                'size': dest.stat().st_size,
                'ext': ext,
                'sha256': src_sha
            })
            rr['ingested'] += 1
            room_changed = True

            if cfg.get('archive_processed_files', True):
                archive_dest = archive_root / room / rel_inside_room
                ensure_dir(archive_dest.parent)
                if archive_dest.exists():
                    archive_dest.unlink()
                shutil.move(str(src), str(archive_dest))
                rr['archived_from_process'] += 1
                if final_src != src and final_src.exists():
                    try:
                        final_src.unlink()
                    except Exception:
                        pass

    report['rooms'].append(rr)
    run_history['rooms'].append(rr)
    if room_changed:
        changed_rooms.append(room)

report['changed_rooms'] = changed_rooms
history['runs'].append(run_history)
save_state(sp, manifest, global_index, history)
write_json(str(Path(logs_root) / 'last_ingest_report.json'), report)
print(json.dumps(report, ensure_ascii=False, indent=2))
