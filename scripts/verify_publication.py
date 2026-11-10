"""Verify the public package and replay the unchanged artifact, without network access."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, platform, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_manifest(root, name):
    manifest = json.loads((root / name).read_text(encoding='utf-8'))
    seen = set()
    for row in manifest['files']:
        name = row['path']
        rel = PurePosixPath(name)
        if (rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name
                or name.casefold() in seen):
            raise ValueError('Unsafe or duplicate manifest path: ' + name)
        seen.add(name.casefold())
        path = root / rel
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Path escapes package: ' + name)
        if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('Manifest mismatch: ' + name)
    return len(manifest['files'])

def output_hashes(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Use a new output directory: ' + str(output))
    if output.is_relative_to(ROOT / 'artifact') or output.is_relative_to(ROOT / 'paper'):
        raise ValueError('Output must be outside preserved input directories')
    n = verify_manifest(ROOT, 'PUBLIC_MANIFEST.json')
    n_art = verify_manifest(ROOT / 'artifact', 'MANIFEST.json')
    output.mkdir(parents=True)
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    reports = []
    with tempfile.TemporaryDirectory(prefix='paper25_cwd_') as elsewhere:
        for label, flags in [('ordinary', []), ('isolated', ['-I'])]:
            target = output / label
            command = [sys.executable, *flags, str(ROOT / 'artifact/reproduce.py'), '--output', str(target)]
            proc = subprocess.run(command, cwd=elsewhere, env=environment, capture_output=True,
                                  text=True, encoding='utf-8', errors='replace')
            (output / (label + '.log')).write_text(proc.stdout + proc.stderr, encoding='utf-8')
            if proc.returncode:
                raise RuntimeError(label + ' reconstruction failed; see its log')
            report = json.loads((target / 'reproduction_report.json').read_text())
            if report['status'] != 'PASS' or report['failed']:
                raise ValueError(label + ' reported a numerical discrepancy')
            reports.append(report)
    if reports[0] != reports[1]:
        raise ValueError('Ordinary and isolated scientific reports differ')
    hashes = [output_hashes(output / label) for label in ['ordinary', 'isolated']]
    if hashes[0] != hashes[1]:
        raise ValueError('Ordinary and isolated generated files differ')
    # Recheck original input integrity after execution, not just before it.
    verify_manifest(ROOT, 'PUBLIC_MANIFEST.json')
    result = {'status': 'PASS', 'python': platform.python_version(), 'platform': platform.platform(),
              'public_manifest_files': n, 'artifact_manifest_files': n_art,
              'different_working_directory': True, 'PYTHONPATH_removed': True,
              'ordinary_and_isolated_reports_identical': True,
              'generated_outputs_identical_within_environment': len(hashes[0]),
              'scientific_reproduction': reports[0],
              'scope': 'Offline numerical reproduction and public file integrity; no provider or private HMAC authentication.'}
    (output / 'publication_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'scientific_reproduction'}, indent=2))
    print('Scientific report:', output / 'ordinary/reproduction_report.json')

if __name__ == '__main__':
    main()
