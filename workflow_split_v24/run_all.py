import subprocess, sys
steps = ['ingest_rooms.py', 'build_indexes.py', 'sync_changed_repos.py']
for step in steps:
    print(f'=== RUN {step} ===')
    r = subprocess.run([sys.executable, step])
    if r.returncode != 0:
        raise SystemExit(r.returncode)
print('ALL DONE')
