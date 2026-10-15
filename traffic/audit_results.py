"""Post-hoc diagnostics of frozen checkpoints; never changes model selection.

Thresholds are descriptive audit choices, not tuned operational alarm rules.
Neural aggregate MAE/bias averages losses across seeds (not ensemble forecasts).
"""
from pathlib import Path
import json, csv
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'audit_v2'; OUT.mkdir(exist_ok=True)
K=1.609344
d=np.load(ROOT/'data'/'prepared.npz')
p=np.load(ROOT/'results'/'predictions.npz')
r=json.loads((ROOT/'results'/'metrics.json').read_text())
ends=p['ends']; valid=p['valid']; y=p['actual'].astype(np.float64)*K
current=d['filled'][ends].astype(np.float64)*K
pred={'persistence':p['persistence'][None].astype(np.float64)*K,
      **{name:np.stack([p[f'{name}_{seed}'] for seed in [42,43,44]]).astype(np.float64)*K for name in ['gru','gcn_gru']}}
errors={name:a-y[None] for name,a in pred.items()}
absmean={name:np.abs(a).mean(0) for name,a in errors.items()}
def stats(mask):
    n=int(mask.sum())
    return {'n':n,'fraction':n/int(valid.sum()),'models':{
      name:{'mae':float(np.abs(a[:,mask]).mean()),
            'rmse_mean_of_seeds':float(np.sqrt((a[:,mask]**2).mean(1)).mean()),
            'bias':float(a[:,mask].mean()),
            'p90_abs':float(np.quantile(np.abs(a[:,mask]),.90)),
            'p95_abs':float(np.quantile(np.abs(a[:,mask]),.95)),
            'p99_abs':float(np.quantile(np.abs(a[:,mask]),.99)),
            'fraction_error_gt20':float((np.abs(a[:,mask])>20).mean())}
      for name,a in errors.items()}} if n else {'n':0}

history_mask=d['valid'][ends[:,None]+np.arange(-11,1),:]
missing=(~history_mask).mean(1)
current_valid=d['valid'][ends]
delta=y-current
groups={'all':valid,
 'target_0_30':valid&(y<30),'target_30_60':valid&(y>=30)&(y<60),
 'target_60_90':valid&(y>=60)&(y<90),'target_90_plus':valid&(y>=90),
 'current_0_30':valid&current_valid&(current<30),
 'current_30_60':valid&current_valid&(current>=30)&(current<60),
 'current_60_90':valid&current_valid&(current>=60)&(current<90),
 'current_90_plus':valid&current_valid&(current>=90),
 'stable_abs_delta_le5':valid&current_valid&(np.abs(delta)<=5),
 'drop_at_least20':valid&current_valid&(delta<=-20),
 'rise_at_least20':valid&current_valid&(delta>=20),
 'own_window_complete':valid&(missing==0),
 'own_window_any_missing':valid&(missing>0),
 'own_window_at_least_half_missing':valid&(missing>=.5),
 'current_missing':valid&(~current_valid),
 'own_data_age_ge60':valid&(d['age_minutes'][ends]>=60),
 'own_data_age_5_to55':valid&(d['age_minutes'][ends]>0)&(d['age_minutes'][ends]<60)}
out={'run_id':r['run_id'],'protocol':'Six v2 models; all neural losses averaged across seeds, not an ensemble. Target-conditioned subsets are retrospective. Exploratory iteration after v1 test inspection. Audit does not tune/reselect checkpoints.',
 'groups':{name:stats(mask) for name,mask in groups.items()}}
for row in r['summary']:
    assert abs(out['groups']['all']['models'][row['model']]['mae']-row['mae_kmh'])<1e-6
assert ends.shape[0]==6853 and valid.shape==(6853,207)

# Paired differences; all sensors remain together within each sampled calendar day.
dates=np.array([str(t)[:10] for t in d['timestamps'][ends+3]])
days=np.unique(dates)
day_counts=np.array([valid[dates==date].sum() for date in days])
diff=absmean['gcn_gru']-absmean['gru']
day_sums=np.array([diff[dates==date][valid[dates==date]].sum() for date in days])
rng=np.random.default_rng(20261013)
ids=rng.integers(0,len(days),(10000,len(days)))
boot=day_sums[ids].sum(1)/day_counts[ids].sum(1)
# Three-day circular moving blocks retain some between-day dependence.
starts=rng.integers(0,len(days),(10000,int(np.ceil(len(days)/3))))
block_ids=((starts[:,:,None]+np.arange(3))%len(days)).reshape(10000,-1)[:,:len(days)]
boot3=day_sums[block_ids].sum(1)/day_counts[block_ids].sum(1)
out['paired_difference']={'sign':'GCN MAE minus GRU MAE; negative favours graph',
 'mean_kmh':float(diff[valid].mean()),'days':len(days),
 'day_bootstrap_95_percentile':np.quantile(boot,[.025,.975]).tolist(),
 'three_day_circular_block_95_percentile':np.quantile(boot3,[.025,.975]).tolist(),
 'replicates':10000,'seed':20261013,
 'limitation':'Exploratory intervals conditional on these fixed fits and this 24-day test. No new training periods, no hyperparameter-search uncertainty. Day resampling assumes exchangeability; 3-day blocks are sensitivity only.'}
perday=[]
for date in days:
    m=dates==date
    perday.append({'date':date,'valid_targets':int(valid[m].sum()),**{n:float(e[m][valid[m]].mean()) for n,e in absmean.items()}})
out['days_graph_beats_gru']=sum(a['gcn_gru']<a['gru'] for a in perday)
sensor=[]
for j in range(y.shape[1]):
    m=valid[:,j]
    sensor.append({'sensor':str(d['sensor_ids'][j]),'valid_targets':int(m.sum()),
      'target_missing_fraction':float((~m).mean()),'own_history_missing_fraction':float(missing[:,j].mean()),
      **{n:float(e[:,j][m].mean()) for n,e in absmean.items()}})
out['sensors_graph_beats_gru']=sum(a['gcn_gru']<a['gru'] for a in sensor)
out['worst_sensors']=sorted(sensor,key=lambda a:a['gcn_gru'],reverse=True)[:8]
out['best_graph_sensors']=sorted(sensor,key=lambda a:a['gcn_gru']-a['gru'])[:5]
out['worst_graph_sensors']=sorted(sensor,key=lambda a:a['gcn_gru']-a['gru'],reverse=True)[:5]

raw=d['raw']; vm=d['valid']; train_end=int(len(raw)*.7); val_end=int(len(raw)*.8)
out['distribution']={}
for name,sl in [('train',slice(0,train_end)),('val',slice(train_end,val_end)),('test',slice(val_end,None))]:
    z=raw[sl][vm[sl]].astype(np.float64)*K
    out['distribution'][name]={'valid':len(z),'mean_kmh':float(z.mean()),'target_under30_fraction':float((z<30).mean()),
      'target_ge90_fraction':float((z>=90).mean()),'missing_fraction':float((~vm[sl]).mean())}
out['convergence']=[]
for run in r['runs']:
    if run['model']=='persistence':continue
    h=run['history']
    out['convergence'].append({'model':run['model'],'seed':run['seed'],'epochs':len(h),
       'best_epoch':run['best_epoch'],'best_val':run['val_mae_kmh'],
       'first_val':h[0]['val_mae_kmh'],'epoch25_val':h[24]['val_mae_kmh'],
       'last_val':h[-1]['val_mae_kmh'],'last_train_sample':h[-1]['train_sample_mae_kmh'],
       'test_mae':run['mae_kmh'],'stop_reason':run['stop_reason'],
       'last_learning_rate':h[-1]['learning_rate'],
       'lr_reductions':sum(h[k]['learning_rate']<h[k-1]['learning_rate'] for k in range(1,len(h)))})
out['prediction_range']={name:{'min_kmh':float(a[:,valid].min()),'max_kmh':float(a[:,valid].max()),
    'below_zero':int((a[:,valid]<0).sum()),'above_raw_max_112_65408':int((a[:,valid]>70*K).sum()),
    'denominator':int(a[:,valid].size)} for name,a in pred.items()}

# Case timelines include actual future only for retrospective explanation.
chosen=json.loads((ROOT/'results'/'demo_cases.json').read_text(encoding='utf8'))
selected=r['selected_by_validation']
worst_flat=np.where(valid,np.abs(errors['gcn_gru'][[42,43,44].index(selected['gcn_gru'])]),-1).argmax()
wi,wj=np.unravel_index(worst_flat,valid.shape)
chosen.append({'name':'Maximum absolute error of deployed checkpoint','node':int(wj),'time':str(d['timestamps'][ends[wi]])})
out['cases']=[]
for case in chosen:
    j=case['node']; t=int(np.flatnonzero(d['timestamps']==case['time'])[0]); i=int(np.flatnonzero(ends==t)[0])
    neighbors=np.flatnonzero((d['adj'][j]>0)&(np.arange(y.shape[1])!=j))
    timeline=[]
    for k in range(max(0,t-11),min(len(raw),t+7)):
        nv=raw[k,neighbors][vm[k,neighbors]]*K
        timeline.append({'time':str(d['timestamps'][k]),'relative_minutes':int((k-t)*5),
          'own_raw_kmh':float(raw[k,j]*K),'own_valid':bool(vm[k,j]),
          'neighbor_median_observed_kmh':float(np.median(nv)) if len(nv) else None,
          'neighbor_observed':len(nv),'neighbor_under30':int((nv<30).sum())})
    out['cases'].append({'name':case['name'],'sensor':str(d['sensor_ids'][j]),'node':j,'time':case['time'],
       'current_kmh':float(current[i,j]),'target_kmh':float(y[i,j]),'own_history_missing_fraction':float(missing[i,j]),
       'neighbors':len(neighbors),'selected_seeds':selected,'predictions_deployed':{n:float(a[0 if n=='persistence' else [42,43,44].index(selected[n]),i,j]) for n,a in pred.items()},'timeline':timeline})
    observed_indices=np.flatnonzero(vm[:t+1,j])
    previous=int(observed_indices[-1]) if len(observed_indices) else None
    out['cases'][-1]['last_observed_time']=str(d['timestamps'][previous]) if previous is not None else None
    out['cases'][-1]['staleness_minutes']=(t-previous)*5 if previous is not None else -1

# Compare both versions on exactly the same v2 origins and targets.
oldpath=ROOT/'history/v1_35epochs/results/predictions.npz'
if oldpath.exists():
    old=np.load(oldpath); ids=np.searchsorted(old['ends'],ends)
    assert np.array_equal(old['ends'][ids],ends)
    assert np.array_equal(old['valid'][ids],valid)
    comparisons=[]
    for name in ['persistence','gru','gcn_gru']:
        keys=[name] if name=='persistence' else [f'{name}_{seed}' for seed in [42,43,44]]
        old_mae=float(np.mean([np.abs((old[k][ids].astype(np.float64)*K-y)[valid]).mean() for k in keys]))
        new_mae=out['groups']['all']['models'][name]['mae']
        comparisons.append({'model':name,'v1_mae_same_targets':old_mae,'v2_mae_same_targets':new_mae,'relative_reduction_percent':(old_mae-new_mae)/old_mae*100})
    out['v1_comparison']={'valid_targets':int(valid.sum()),'rows':comparisons,'caution':'Several changes together: budget, full validation, scheduler, temporal boundary. No causal attribution to longer training alone.'}

for name,rows in [('by_day',perday),('by_sensor',sensor)]:
    with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (OUT/'by_regime.csv').open('w',newline='',encoding='utf-8-sig') as f:
    rows=[{'regime':name,'n':g['n'],'fraction':g.get('fraction'), 'model':model,**v} for name,g in out['groups'].items() for model,v in g.get('models',{}).items()]
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'diagnostics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['cases','groups']},ensure_ascii=False,indent=2))
print('GROUPS')
for name,g in out['groups'].items():print(name,g['n'],round(g.get('fraction',0)*100,3),{n:round(v['mae'],4) for n,v in g.get('models',{}).items()})
