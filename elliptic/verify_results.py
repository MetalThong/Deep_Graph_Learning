"""Independent protocol and metrics integrity checks."""
from pathlib import Path
import json
import numpy as np
from sklearn.metrics import f1_score,average_precision_score,confusion_matrix

R=Path(__file__).resolve().parent;d=np.load(R/'data/prepared.npz');m=json.loads((R/'results/metrics.json').read_text(encoding='utf-8'));y=d['y'];sp=d['split'];t=d['times']
assert np.all(t[d['src']]==t[d['dst']])
assert t[sp==0].max()<t[sp==1].min()<t[sp==2].min()
assert len(m['runs'])==12
checks=[]
for r in m['runs']:
 p=np.load(R/f"results/{r['model']}_{r['seed']}_predictions.npz")['probabilities']; assert np.isfinite(p).all() and p.min()>=0 and p.max()<=1
 for k,name in [(1,'validation'),(2,'test')]:
  mask=(sp==k)&(y>=0);pred=p[mask]>=r['threshold'];v=f1_score(y[mask],pred)
  assert abs(v-r[name]['f1'])<1e-10
  assert abs(average_precision_score(y[mask],p[mask])-r[name]['ap'])<1e-7
 checks.append({'model':r['model'],'seed':r['seed'],'passed':True})
(R/'qa/metrics-integrity.json').write_text(json.dumps({'passed':True,'test_labeled':int(((sp==2)&(y>=0)).sum()),'checks':checks},indent=2))
print('All 12 runs: metrics, chronology, edges and score ranges verified.')
