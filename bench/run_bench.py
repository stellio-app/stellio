"""Benchmarks reproductibles (1.2.1) : modèles générés (graine fixe), mesures médianes, résultat JSON comparable.
  python bench/run_bench.py                         → bench/results/<date>.json
  python bench/run_bench.py --compare ancien.json   → signale les régressions > 25 %
Les scénarios dont une dépendance manque sont ignorés et signalés."""
import argparse, json, os, platform, sqlite3, statistics, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
REPEAT = 3


def timed(fn, repeat=REPEAT):
    runs = []
    for _ in range(repeat):
        t = time.perf_counter(); r = fn(); runs.append(time.perf_counter() - t)
        if hasattr(r, 'status_code') and r.status_code != 200:       # une mesure sur une erreur ne vaut rien
            raise RuntimeError(f"scénario en erreur ({r.status_code}) : {r.get_data(as_text=True)[:200]}")
    return {'median_s': round(statistics.median(runs), 4), 'min_s': round(min(runs), 4), 'runs': repeat}


def bench_sqlite(tmp):
    c = sqlite3.connect(os.path.join(tmp, 'b.db'))
    c.executescript("CREATE TABLE file_tags (file_path TEXT NOT NULL, tag_id INTEGER NOT NULL, PRIMARY KEY (file_path, tag_id));")
    c.executemany("INSERT INTO file_tags VALUES (?,?)", ((f'/lib/{i}.stl', i % 50) for i in range(200000)))
    c.commit()
    q = lambda: [c.execute("SELECT file_path FROM file_tags WHERE tag_id=?", (t,)).fetchall() for t in range(10)]
    sans = timed(q)
    c.execute("CREATE INDEX idx_file_tags_tag ON file_tags(tag_id)"); c.commit()
    return {'sqlite_tags_200k_sans_index': sans, 'sqlite_tags_200k_avec_index': timed(q)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--compare'); ap.add_argument('--out'); a = ap.parse_args()
    res = {'meta': {'date': time.strftime('%Y-%m-%d %H:%M:%S'), 'python': platform.python_version(), 'machine': platform.machine(), 'cpu_count': os.cpu_count()}, 'results': {}, 'skipped': {}}
    with tempfile.TemporaryDirectory() as tmp:
        for name, fn in (('sqlite', bench_sqlite),):
            try:
                res['results'].update(fn(tmp))
            except ImportError as e:
                res['skipped'][name] = str(e)
    out = a.out or os.path.join(ROOT, 'bench', 'results', time.strftime('%Y%m%d-%H%M%S') + '.json')
    os.makedirs(os.path.dirname(out), exist_ok=True); json.dump(res, open(out, 'w'), indent=1, ensure_ascii=False)
    for k, v in res['results'].items():
        print(f"{k:42s} {v['median_s']:8.3f} s")
    for k, v in res['skipped'].items():
        print('ignoré', k, v)
    if a.compare:
        old = json.load(open(a.compare))['results']; bad = 0
        for k, v in res['results'].items():
            if k in old and v['median_s'] > old[k]['median_s'] * 1.25 and v['median_s'] - old[k]['median_s'] > 0.05:
                bad += 1; print(f"RÉGRESSION {k}: {old[k]['median_s']:.3f} → {v['median_s']:.3f} s")
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
