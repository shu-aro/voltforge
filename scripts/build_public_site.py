"""Build the public site: the demo video first, then the real app running in the browser."""
from pathlib import Path
import json
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'public_site'
SITE = ROOT/'site'
sys.path.insert(0, str(ROOT/'src'))
from voltforge.studio.copilot import SCHEMA, SYSTEM

links = json.loads((ROOT/'configs/public_site.json').read_text())
# Preserve Vercel's project link when regenerating our own build output.
# Deleting it silently can deploy the same files to a different project.
for folder in ('app', 'api'):
    if (OUT/folder).exists(): shutil.rmtree(OUT/folder)
(OUT/'app').mkdir(parents=True, exist_ok=True); (OUT/'api').mkdir(exist_ok=True)
shutil.copy(SITE/'index.html', OUT/'index.html'); shutil.copy(ROOT/'reports/demo_v1/VOLT-FORGE_demo.mp4', OUT/'demo.mp4')
for file in (ROOT/'web/editor').iterdir():
    if file.name.startswith('studio') or file.name in ('favicon.svg', 'custom-cell-format.md'): shutil.copy(file, OUT/'app'/file.name)
for name in ('backend.js', 'worker.js', 'ai-status.mjs'): shutil.copy(SITE/name, OUT/'app'/name)
page = (ROOT/'web/editor/index.html').read_text().replace('href="/', 'href="./').replace('src="/', 'src="./')
page = page.replace('<script type="module"', '<script src="./backend.js"></script>\n  <script type="module"', 1)
(OUT/'app/index.html').write_text(page)
shutil.copy(SITE/'api/ai.js', OUT/'api/ai.js')
shutil.copy(SITE/'api/context.mjs', OUT/'api/context.mjs')
knowledge = json.loads((SITE/'knowledge/battery.json').read_text())
(OUT/'api/_knowledge.js').write_text('export const KNOWLEDGE = '+json.dumps(knowledge)+';\n')
(OUT/'api/_prompt.js').write_text(f'export const SYSTEM = {json.dumps(SYSTEM)};\nexport const SCHEMA = {json.dumps(SCHEMA)};\n')
(OUT/'package.json').write_text(json.dumps(dict(name='volt-forge-app', private=True, type='module'))+'\n')
(OUT/'vercel.json').write_text(json.dumps(dict(redirects=[dict(source='/appendix', destination=links['appendix_url'], permanent=False)]), indent=1)+'\n')
project = ROOT/sys.argv[1] if len(sys.argv) > 1 else ROOT/'tmp/final/blank/project'
if not project.is_dir(): raise SystemExit('Build a fresh reference project before packaging.')
with zipfile.ZipFile(OUT/'app/engine.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(SITE/'bridge.py', 'bridge.py')
    for folder, name in ((ROOT/'src', 'src'), (ROOT/'configs', 'configs'), (project, 'project')):
        for file in sorted(folder.rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts and not re.search(r'\.lock$', file.name):
                z.write(file, str(Path(name)/file.relative_to(folder)))
print(OUT, sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())//1024, 'KB')
