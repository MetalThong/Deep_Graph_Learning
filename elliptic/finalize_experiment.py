"""Repeat the two strongest pilot configurations, freeze selection, evaluate once.

Run after optimize_gcn.py has completed all registered seed-0 pilots. Selection never
reads candidate test metrics, including on a resumable execution.
"""
import datetime,hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import torch
from optimize_gcn import CONFIGS,OUT,ROOT,train_one,evaluate
from report_optimization import main as report

def main():
    torch.set_num_threads(2)
    pilots=[]
    for name in CONFIGS:
        result=json.loads((OUT/f'{name}_gcn_0.json').read_text(encoding='utf-8'))
        pilots.append(result)
    finalists=[r['config_name'] for r in sorted(pilots,key=lambda r:r['validation']['ap'],reverse=True)[:2]]
    print('FINALISTS selected only by pilot validation AP:',finalists,flush=True)
    data=np.load(ROOT/'data/prepared.npz')
    def train_job(job):
        name,seed,mlp=job
        command=[sys.executable,str(ROOT/'optimize_gcn.py'),'--configs',name,'--seeds',str(seed),'--threads','2']
        if mlp:command.append('--mlp')
        subprocess.run(command,cwd=ROOT,check=True)
    vals={};pruned=[]
    for name in finalists:
        observed={seed:json.loads((OUT/f'{name}_gcn_{seed}.json').read_text(encoding='utf-8'))['validation']['ap'] for seed in [0,1,2] if (OUT/f'{name}_gcn_{seed}.json').exists()}
        upper_bound=(sum(observed.values())+3-len(observed))/3
        if vals and max(vals.values())>upper_bound:
            pruned.append(dict(config=name,observed_seeds=list(observed),maximum_possible_mean_ap=upper_bound,incumbent_mean_ap=max(vals.values()),reason='AP <= 1. Even perfect validation AP on every missing seed cannot beat the completed incumbent mean. No test scores used.'))
            print('PROVEN PRUNE',name,upper_bound,'<',max(vals.values()),flush=True)
            continue
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(train_job,[(name,seed,False) for seed in [1,2] if seed not in observed]))
        vals[name]=float(np.mean([json.loads((OUT/f'{name}_gcn_{seed}.json').read_text(encoding='utf-8'))['validation']['ap'] for seed in [0,1,2]]))
    chosen=max(vals,key=vals.get)
    keys=[f'{name}_gcn_0' for name in CONFIGS]+[f'{name}_gcn_{seed}' for name in finalists for seed in [1,2] if (OUT/f'{name}_gcn_{seed}.json').exists()]+[f'{chosen}_mlp_{seed}' for seed in [0,1,2]]
    selection=dict(selected_config=chosen,finalists=finalists,criterion='Mean validation AP across seeds 0,1,2; finalists based on pilot AP; mathematically dominated incomplete candidates may be pruned with AP<=1 upper bound',mean_validation_ap=vals,pruned_finalists=pruned,evaluate_keys=keys,config=CONFIGS[chosen],test_reuse_disclosure='Original test was viewed before this revision. All new candidate selection uses validation only; final test results are retrospective.',selected_gcn_checkpoints_sha256={f'{chosen}_gcn_{seed}':hashlib.sha256((OUT/f'{chosen}_gcn_{seed}.pt').read_bytes()).hexdigest() for seed in [0,1,2]})
    decision_file=OUT/'selection.json'
    if decision_file.exists():
        existing=json.loads(decision_file.read_text(encoding='utf-8'))
        assert all(existing[k]==v for k,v in selection.items()),'Frozen selection differs. Preserve the prior experiment and start a new revision.'
    else:
        selection['frozen_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        decision_file.write_text(json.dumps(selection,indent=2),encoding='utf-8')
    print('FROZEN SELECTION',chosen,vals,flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(train_job,[(chosen,seed,True) for seed in [0,1,2]]))
    for key in keys:evaluate(data,key)
    report()

if __name__=='__main__':main()
