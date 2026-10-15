"""Audit the frozen optimization decision and generate reproducible figures."""
from pathlib import Path
import json,hashlib,joblib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, f1_score, precision_recall_curve
from train import score

R=Path(__file__).resolve().parent;O=R/'optimization'

def main():
    selection=json.loads((O/'selection.json').read_text(encoding='utf-8'))
    config=selection['selected_config'];data=np.load(R/'data/prepared.npz')
    y,s,t=data['y'],data['split'],data['times'];vm=(s==1)&(y>=0);tm=(s==2)&(y>=0)
    rows=[];checks=[]
    for key in selection['evaluate_keys']:
        r=json.loads((O/f'{key}.json').read_text(encoding='utf-8'));p=np.load(O/f'{key}_predictions.npz')['probabilities']
        assert np.isfinite(p).all() and p.min()>=0 and p.max()<=1
        precision,recall,thresholds=precision_recall_curve(y[vm],p[vm]);f=2*precision[:-1]*recall[:-1]/np.maximum(precision[:-1]+recall[:-1],1e-12)
        assert r['threshold']==float(thresholds[np.argmax(f)])
        for mask,part in [(vm,'validation'),(tm,'test')]:
            calculated=score(y[mask],p[mask],r['threshold'])
            for metric in calculated:assert abs(calculated[metric]-r[part][metric])<1e-9,(key,part,metric)
        assert r['best_epoch']==max(r['history'],key=lambda h:h['val_ap'])['epoch'] or abs(max(h['val_ap'] for h in r['history'])-r['history'][r['best_epoch']-1]['val_ap'])<=1e-5
        rows.append({k:v for k,v in r.items() if k!='history'});checks.append(key)
    old=json.loads((O/'baseline/results/metrics.json').read_text(encoding='utf-8'))
    summary=[]
    for name,prefix in [('GCN baseline','baseline'),('GCN optimized',config+'_gcn'),('MLP matched',config+'_mlp')]:
        runs=[r for r in old['runs'] if r['model']=='gcn'] if prefix=='baseline' else [r for r in rows if r['key'].startswith(prefix+'_')]
        assert len(runs)==3,(name,len(runs))
        row=dict(name=name,n=3)
        for metric in ['precision','recall','f1','ap','roc_auc']:
            vals=[r['test'][metric] for r in runs];row[metric]=float(np.mean(vals));row[metric+'_std']=float(np.std(vals,ddof=1))
        summary.append(row)
    summary.extend(dict(name=r['model'],**r) for r in old['summary'] if r['model'].startswith('rf'))
    # Exact first-180-epoch match confirms the budget-only ablation reproduced the baseline.
    long=json.loads((O/'long_gcn_0.json').read_text(encoding='utf-8'));baseline=json.loads((O/'baseline/results/gcn_0.json').read_text(encoding='utf-8'))
    prefix_error=max(abs(a['val_ap']-b['val_ap']) for a,b in zip(long['history'][:180],baseline['history']))
    assert prefix_error<1e-8,prefix_error
    if selection['config'].get('transform')=='quantile':
        qt=joblib.load(O/'quantile_transform.joblib')
        assert qt['train_sha256']==hashlib.sha256(data['x'][s==0,:93].tobytes()).hexdigest()
        assert qt['transformer'].n_features_in_==93 and qt['transformer'].n_quantiles_==1000
    out=dict(selection=selection,summary=summary,ablations=rows,baseline_prefix_max_ap_error=prefix_error,verified_keys=checks,test_reuse_disclosure='The original test had already been viewed. Candidate/epoch/threshold selection used validation only. These are retrospective test results, not a fresh holdout.')
    (O/'report.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(10,5))
    for name in ['long','moderate_weight','paper_inspired','clipped','quantile']:
        r=json.loads((O/f'{name}_gcn_0.json').read_text(encoding='utf-8'));h=r['history'];ax.plot([v['epoch'] for v in h],[v['val_ap'] for v in h],label=name)
    ax.axvline(180,color='gray',ls='--',label='Previous budget: 180');ax.set(xlabel='Epoch',ylabel='Validation AP',title='GCN optimization: validation learning curves (seed 0)');ax.legend(fontsize=9);fig.tight_layout();fig.savefig(O/'validation_learning_curves.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5));labels=[r['name'] for r in summary];vals=[100*r['f1'] for r in summary];err=[100*r['f1_std'] for r in summary]
    bars=ax.bar(labels,vals,yerr=err,color=['#ad7467','#16796f','#83a39b','#6b7d85','#253c42'],capsize=5)
    for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+3,f'{v:.1f}%',ha='center')
    ax.set(ylim=(0,100),ylabel='Illicit F1 (%)',title='Same temporal split; validation-selected thresholds; mean ± seed SD')
    fig.tight_layout();fig.savefig(O/'test_comparison.png',dpi=180);plt.close(fig)
    details=[]
    for tag,path,threshold in [('baseline',O/'baseline/results/gcn_0_predictions.npz',baseline['threshold']),('optimized',O/f'{config}_gcn_0_predictions.npz',next(r['threshold'] for r in rows if r['key']==f'{config}_gcn_0'))]:
        p=np.load(path)['probabilities']
        for step in range(35,50):
            mask=(t==step)&(y>=0)
            details.append(dict(model=tag,step=step,n=int(mask.sum()),illicit=int((y[mask]==1).sum()),**score(y[mask],p[mask],threshold)))
    (O/'by_timestep.json').write_text(json.dumps(details,indent=2))
    print(json.dumps(dict(summary=summary,verified=len(checks),baseline_prefix_error=prefix_error),indent=2))

if __name__=='__main__':main()
