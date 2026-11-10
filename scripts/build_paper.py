"""Compile the supplied preprints offline, without modifying their sources."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Use a new build directory: ' + str(output))
    output.mkdir(parents=True)
    source = output / 'source'
    shutil.copytree(ROOT / 'paper/source', source)
    env = dict(os.environ, SOURCE_DATE_EPOCH='1794268800', FORCE_SOURCE_DATE='1', TZ='UTC')
    version = subprocess.check_output(['pdflatex', '--version'], text=True)
    flags = ['-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error']
    if 'miktex' in version.lower():
        flags.insert(0, '-disable-installer')
    report = {'source_date_epoch_convention': 1794268800,
              'temporal_attestation': False, 'latex_version': version.splitlines()[0], 'documents': []}
    for stem, final in [('main', 'manuscript.pdf'), ('supplement', 'ESM_1.pdf')]:
        log_chunks = []
        commands = [['pdflatex', *flags, stem + '.tex'], ['bibtex', stem],
                    ['pdflatex', *flags, stem + '.tex'], ['pdflatex', *flags, stem + '.tex']]
        for command in commands:
            p = subprocess.run(command, cwd=source, env=env, capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
            log_chunks.append(p.stdout + p.stderr)
            if p.returncode:
                (output / (stem + '_build.txt')).write_text('\n'.join(log_chunks), encoding='utf-8')
                raise RuntimeError(stem + ': compilation failed; see build log')
        (output / (stem + '_build.txt')).write_text('\n'.join(log_chunks), encoding='utf-8')
        log = (source / (stem + '.log')).read_text(errors='replace')
        warnings = [line for line in log.splitlines() if any(t in line for t in
                    ['Overfull', 'undefined', 'LaTeX Warning:', 'Package hyperref Warning:'])]
        shutil.copyfile(source / (stem + '.pdf'), output / final)
        report['documents'].append({'pdf': final, 'warnings': warnings,
            'sha256': hashlib.sha256((output / final).read_bytes()).hexdigest(),
            'source_sha256': hashlib.sha256((ROOT / 'paper/source' / (stem + '.tex')).read_bytes()).hexdigest()})
    (output / 'build_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
