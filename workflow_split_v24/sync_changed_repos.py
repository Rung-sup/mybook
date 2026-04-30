import json
from pathlib import Path
from common import load_config, git_commit_push_batched, now_iso, write_json

cfg = load_config()
logs_root = Path(cfg['logs_root'])
library_root = Path(cfg['library_root'])
site_root = cfg['site_root']
changed_rooms = []
ingest_report = logs_root / 'last_ingest_report.json'
if ingest_report.exists():
    changed_rooms = json.loads(ingest_report.read_text(encoding='utf-8')).get('changed_rooms', [])

report = {'started_at': now_iso(), 'git': []}
for room in changed_rooms:
    repo_path = str(library_root / room)
    result = git_commit_push_batched(
        repo_path,
        cfg['git_remote'],
        cfg['github_branch'],
        f'Auto-sync {room} {now_iso()}',
        cfg['git_batch_max_files'],
        cfg['git_batch_max_total_mb'],
        cfg['max_git_file_mb']
    )
    report['git'].append({'repo': repo_path, **result})

site_result = git_commit_push_batched(
    site_root,
    cfg['git_remote'],
    cfg['github_branch'],
    f'Update indexes {now_iso()}',
    cfg['git_batch_max_files'],
    cfg['git_batch_max_total_mb'],
    cfg['max_git_file_mb']
)
report['git'].append({'repo': site_root, **site_result})
report['finished_at'] = now_iso()
write_json(str(logs_root / 'last_sync_report.json'), report)
print(json.dumps(report, ensure_ascii=False, indent=2))
