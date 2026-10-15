"""Recompute reports from existing checkpoints' saved scores, without retraining.
Round scores to six decimals to make threshold ties stable across RF thread ordering.
"""
from pathlib import Path
import json
import numpy as np
from train import score,choose_threshold,MODELS
R=Path(__file__).resolve().parent;d=np.load(R/'data/prepared.npz');y=d['y'];s=d['split'];m=json.loads((R/'results/metrics.json').read_text(encoding='utf-8'));runs=[]
for name in MODELS:
 for seed in [0,1,2]:
  rp=R/f'results/{name}_{seed}.json';r=json.loads(rp.read_text(encoding='utf-8'));pp=R/f'results/{name}_{seed}_predictions.npz';p=np.round(np.load(pp)['probabilities'].astype(np.float64),6);np.savez_compressed(pp,probabilities=p)
  vm=(s==1)&(y>=0);tm=(s==2)&(y>=0);r['threshold']=choose_threshold(y[vm],p[vm]);r['validation']=score(y[vm],p[vm],r['threshold']);r['test']=score(y[tm],p[tm],r['threshold']);r['test_at_half']=score(y[tm],p[tm],.5);rp.write_text(json.dumps(r,indent=2));runs.append({k:v for k,v in r.items() if k!='history'})
m['runs']=runs
for row in m['summary']:
 rr=[r for r in runs if r['model']==row['model']]
 for key in ['precision','recall','f1','ap','roc_auc']:
  vals=[r['test'][key] for r in rr];row[key]=float(np.mean(vals));row[key+'_std']=float(np.std(vals,ddof=1))
m['protocol']['score_precision']='Scores rounded to six decimals before validation threshold selection and reporting to stabilize floating-point ties.'
(R/'results/metrics.json').write_text(json.dumps(m,indent=2));print('Reports refreshed from saved scores; no model retraining or test-based selection.')
