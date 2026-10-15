"""Export measured research results to CSV and slide-ready PNG/SVG figures."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from train import ROOT

report=json.loads((ROOT/'results/research/metrics.json').read_text(encoding='utf-8'))
out=ROOT/'results/figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
rows=report['summary']
with (ROOT/'results/research/summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
with (ROOT/'results/research/runs.csv').open('w',newline='',encoding='utf-8-sig') as f:
    keys=['model','split_seed','seed','accuracy','macro_f1','parameters','seconds','best_epoch','val_loss']
    writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(report['runs'])
chosen=['Logistic Regression','MLP-2','GCN-2','GraphSAGE-2','GAT-2']
selected=[next(r for r in rows if r['model']==name) for name in chosen]
fig,ax=plt.subplots(figsize=(10,5.8))
fig.subplots_adjust(left=.09,right=.98,top=.9,bottom=.21)
x=np.arange(len(chosen));means=np.array([r['accuracy_mean'] for r in selected])*100;std=np.array([r['accuracy_std'] for r in selected])*100
ax.bar(x,means,yerr=std,capsize=5,color=['#8b9992','#779f9a','#007e71','#4993aa','#cb7855'],width=.64)
for i,(mean,sd) in enumerate(zip(means,std)):ax.text(i,mean+sd+1.6,f'{mean:.2f}%',ha='center',fontsize=11)
ax.set(ylim=(0,100),ylabel='Test accuracy (%)',xticks=x,xticklabels=['Logistic\nRegression','MLP','GCN','GraphSAGE','GAT'],title='Cora: architecture comparison on fixed experimental protocol')
ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.text(.09,.045,'3 label splits; 3 initializations per neural model.\nError bars: descriptive population std, not a confidence interval.',fontsize=8)
for ext in ['png','svg']:fig.savefig(out/f'architecture_comparison.{ext}',dpi=220,bbox_inches='tight')
plt.close(fig)
selected=[next(r for r in rows if r['model']==f'GCN-{d}') for d in [1,2,4,8]]
fig,ax=plt.subplots(figsize=(9,5.5))
fig.subplots_adjust(left=.1,right=.98,top=.9,bottom=.23)
x=np.arange(4);means=np.array([r['accuracy_mean'] for r in selected])*100;std=np.array([r['accuracy_std'] for r in selected])*100
ax.errorbar(x,means,yerr=std,fmt='o-',color='#007e71',linewidth=2,capsize=6,markersize=8)
for i,m in enumerate(means):ax.text(i,m+std[i]+4,f'{m:.2f}%',ha='center')
ax.set(xticks=x,xticklabels=['1','2','4','8'],xlabel='Number of GCN layers',ylabel='Test accuracy (%)',ylim=(0,100),title='Depth ablation: deeper is not automatically better')
ax.grid(alpha=.2)
fig.text(.1,.035,'Same optimization settings and hidden width 32; parameter counts differ.\nAccuracy alone does not identify the cause of degradation.',fontsize=8)
for ext in ['png','svg']:fig.savefig(out/f'gcn_depth.{ext}',dpi=220,bbox_inches='tight')
plt.close(fig)
assert len(report['runs'])==len(report['config']['split_seeds'])*(1+7*len(report['config']['seeds']))
assert all(np.isfinite(r['accuracy']) and np.isfinite(r['macro_f1']) for r in report['runs'])
print(json.dumps(rows,indent=2))
print('Exported figures and CSV; run coverage verified:',len(report['runs']))
