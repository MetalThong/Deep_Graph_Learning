"""Promote only the validation-selected configuration; retain baseline in optimization/."""
from pathlib import Path
import json, shutil
import numpy as np
import torch

R=Path(__file__).resolve().parent;O=R/'optimization'

def main():
    decision=json.loads((O/'selection.json').read_text(encoding='utf-8'));name=decision['selected_config']
    report=json.loads((O/'report.json').read_text(encoding='utf-8'))
    assert report['selection']==decision and len(report['verified_keys'])==len(decision['evaluate_keys'])
    meta=json.loads((O/'baseline/results/metrics.json').read_text(encoding='utf-8'))
    runs=[r for r in meta['runs'] if r['model'].startswith('rf')]
    for model in ['mlp','gcn']:
        for seed in [0,1,2]:
            key=f'{name}_{model}_{seed}';result=json.loads((O/f'{key}.json').read_text(encoding='utf-8'));result['model']=model
            assert key in decision['evaluate_keys'] and result['config_name']==name
            (R/f'results/{model}_{seed}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            shutil.copy2(O/f'{key}_predictions.npz',R/f'results/{model}_{seed}_predictions.npz')
            ck=torch.load(O/f'{key}.pt',map_location='cpu',weights_only=True);ck['hidden']=ck['config']['hidden']
            torch.save(ck,R/f'models/{model}_{seed}.pt')
            runs.append({k:v for k,v in result.items() if k!='history'})
    summary=[]
    for model in ['rf_local','rf_all','mlp','gcn']:
        rr=[r for r in runs if r['model']==model];out=dict(model=model,n=3,seeds=[0,1,2])
        for k in ['precision','recall','f1','ap','roc_auc']:
            vals=[r['test'][k] for r in rr];out[k]=float(np.mean(vals));out[k+'_std']=float(np.std(vals,ddof=1))
        summary.append(out)
    cfg=next(r['config'] for r in runs if r['model']=='gcn')
    if cfg.get('transform')=='quantile':shutil.copy2(O/'quantile_transform.joblib',R/'models/quantile_transform.joblib')
    meta['summary']=summary;meta['runs']=runs
    meta['environment']['threads']=next(r.get('torch_threads',4) for r in runs if r['model']=='gcn' and r['seed']==0)
    meta['environment']['rf_threads']=4
    meta['environment']['parallel_training_jobs']=2
    meta['protocol']['selection']='Revision 2: candidates and checkpoints selected on validation AP; thresholds maximize validation F1. Original test was already viewed, so these are retrospective test reevaluations, NOT a fresh holdout.'
    meta['protocol']['neural']=f"Selected configuration {name}: {json.dumps(cfg)}. MLP uses identical final hyperparameters and preprocessing with adjacency replaced by identity."
    meta['protocol']['features']=f"93 local numeric features, timestep excluded. Scaler fitted on train nodes only. Neural transform={cfg.get('transform','standard_scaler')}, clip={cfg['clip']} applied before message passing; every fitted transform uses train nodes only. RF features unchanged. RF-all additionally uses 72 provider aggregates."
    meta['optimization']={'selected_config':name,'decision_file':'optimization/selection.json','report_file':'optimization/report.json','baseline':'optimization/baseline/results/metrics.json','test_reuse':True}
    (R/'results/metrics.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
