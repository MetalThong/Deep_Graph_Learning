"""Package code, trained models, reports, offline demo and learning materials."""
from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parent
out=R/'output/V2/Elliptic_Code_Demo_TaiLieu.zip'
files=[]
for pattern in ['*.py','*.mjs','*.ps1','requirements*.txt','README.md']:
 files.extend(R.glob(pattern))
for folder in ['models','results','site/dist']:
 files.extend(p for p in (R/folder).rglob('*') if p.is_file())
files.extend((R/'output/V2').glob('*.pdf'));files.extend((R/'output/V2').glob('*.pptx'))
for pattern in ['*.json','*.mjs']:
 files.extend((R/'presentation/.build').glob(pattern))
files.extend(p for p in (R/'qa').glob('*.json') if p.name!='package-report.json')
for name in ['workspace.png','false-alarm.png','desktop.png','mobile.png','browser.mjs']:
 files.append(R/'qa'/name)
files.extend(p for p in (R/'optimization').rglob('*') if p.is_file() and not ('baseline/models' in p.as_posix() and p.suffix=='.joblib'))
files=list(dict.fromkeys(p for p in files if p.is_file()))
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,'elliptic/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert 'elliptic/site/dist/index.html' in z.namelist()
 assert not any('/node_modules/' in n or '/.git/' in n for n in z.namelist())
report={'archive':str(out),'files':len(files),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'excluded':'Original raw CSV and prepared.npz; regenerate with prepare_data.py. Git metadata and node_modules excluded.'}
(R/'qa/package-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
