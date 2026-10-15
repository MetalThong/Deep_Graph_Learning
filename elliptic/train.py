"""Reproducible RF/MLP/GCN comparison. Test is never used for model selection."""
from pathlib import Path
import argparse, copy, json, platform, random, time
import joblib
import numpy as np
import scipy.sparse as sp
import torch
from torch import nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

ROOT=Path(__file__).resolve().parent
MODELS=['rf_local','rf_all','mlp','gcn']

def score(y,p,threshold):
    pred=p>=threshold
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)),ap=float(average_precision_score(y,p)),roc_auc=float(roc_auc_score(y,p)),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp))

def choose_threshold(y,p):
    precision,recall,t=precision_recall_curve(y,p)
    f=2*precision[:-1]*recall[:-1]/np.maximum(precision[:-1]+recall[:-1],1e-12)
    return float(t[np.argmax(f)])

def adjacency(n,src,dst):
    a=sp.coo_matrix((np.ones(len(src)*2),(np.r_[src,dst],np.r_[dst,src])),shape=(n,n)).tocsr()
    a.data[:]=1; a.setdiag(1)
    inv=1/np.sqrt(np.asarray(a.sum(axis=1)).ravel())
    a=(sp.diags(inv)@a@sp.diags(inv)).tocoo()
    return torch.sparse_coo_tensor(np.vstack([a.row,a.col]),a.data.astype(np.float32),(n,n)).coalesce()

class Classifier(nn.Module):
    def __init__(self,graph=False,hidden=64):
        super().__init__(); self.graph=graph
        self.fc1=nn.Linear(93,hidden); self.fc2=nn.Linear(hidden,1); self.skip=nn.Linear(93,1,bias=False)
        self.drop=nn.Dropout(.2)
    def forward(self,x,ax,a):
        h=self.drop(torch.relu(self.fc1(ax if self.graph else x)))
        h=torch.sparse.mm(a,h) if self.graph else h
        return (self.fc2(h)+self.skip(x)).squeeze(-1)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',nargs='+',type=int,default=[0,1,2]);ap.add_argument('--models',nargs='+',default=MODELS,choices=MODELS);ap.add_argument('--epochs',type=int,default=180);ap.add_argument('--threads',type=int,default=4);ap.add_argument('--force',action='store_true',help='Retrain and overwrite selected saved runs');args=ap.parse_args()
    torch.set_num_threads(args.threads)
    d=np.load(ROOT/'data/prepared.npz'); x=d['x']; y=d['y']; split=d['split']; src=d['src']; dst=d['dst']
    blocks=[]
    for k in range(3):
        ind=np.flatnonzero(split==k); rev=np.full(len(y),-1,dtype=np.int64);rev[ind]=np.arange(len(ind)); em=(split[src]==k)&(split[dst]==k)
        a=adjacency(len(ind),rev[src[em]],rev[dst[em]])
        xt=torch.from_numpy(x[ind,:93].copy());mask=torch.from_numpy(y[ind]>=0)
        blocks.append(dict(ind=ind,x=xt,ax=torch.sparse.mm(a,xt),a=a,mask=mask,y=torch.from_numpy(y[ind].astype(np.float32))))
    runs=[]
    for name in args.models:
      for seed in args.seeds:
        file=ROOT/f'results/{name}_{seed}.json'
        if file.exists() and not args.force:
            runs.append(json.loads(file.read_text(encoding='utf-8')));print('cached',name,seed,flush=True);continue
        started=time.perf_counter();random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
        trainmask=(split==0)&(y>=0);vm=(split==1)&(y>=0);tm=(split==2)&(y>=0)
        best_epoch=None;history=[]
        if name.startswith('rf'):
            dims=93 if name=='rf_local' else 165
            model=RandomForestClassifier(n_estimators=200,min_samples_leaf=2,max_features='sqrt',class_weight='balanced_subsample',random_state=seed,n_jobs=args.threads)
            model.fit(x[trainmask,:dims],y[trainmask]);p=model.predict_proba(x[:,:dims])[:,1]
            joblib.dump(model,ROOT/f'models/{name}_{seed}.joblib',compress=3)
        else:
            model=Classifier(graph=name=='gcn'); opt=torch.optim.Adam(model.parameters(),lr=.003,weight_decay=5e-4)
            pos=float(((split==0)&(y==1)).sum());neg=float(((split==0)&(y==0)).sum())
            loss_fn=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg/pos))
            best=-1;wait=0;bt=blocks[0];bv=blocks[1]
            for epoch in range(1,args.epochs+1):
                model.train();opt.zero_grad();logits=model(bt['x'],bt['ax'],bt['a']);loss=loss_fn(logits[bt['mask']],bt['y'][bt['mask']]);loss.backward();opt.step()
                model.eval()
                with torch.no_grad(): vp=torch.sigmoid(model(bv['x'],bv['ax'],bv['a']))[bv['mask']].numpy()
                va=float(average_precision_score(y[vm],vp));history.append({'epoch':epoch,'loss':float(loss.detach()),'val_ap':va})
                if va>best+1e-5: best=va;state=copy.deepcopy(model.state_dict());best_epoch=epoch;wait=0
                else: wait+=1
                if epoch%20==0:print(f'{name} seed={seed} epoch={epoch} val_AP={va:.4f} best={best:.4f}',flush=True)
                if epoch>=40 and wait>=30:break
            model.load_state_dict(state);model.eval();p=np.zeros(len(y),np.float32)
            with torch.no_grad():
                for b in blocks:p[b['ind']]=torch.sigmoid(model(b['x'],b['ax'],b['a'])).numpy()
            torch.save({'state_dict':state,'graph':name=='gcn','hidden':64,'seed':seed,'best_epoch':best_epoch},ROOT/f'models/{name}_{seed}.pt')
        p=np.round(p.astype(np.float64),6) # stable ties across multithreaded RF prediction
        threshold=choose_threshold(y[vm],p[vm])
        result=dict(model=name,seed=seed,threshold=threshold,best_epoch=best_epoch,seconds=round(time.perf_counter()-started,2),validation=score(y[vm],p[vm],threshold),test=score(y[tm],p[tm],threshold),test_at_half=score(y[tm],p[tm],.5),history=history)
        file.write_text(json.dumps(result,indent=2),encoding='utf-8');np.savez_compressed(ROOT/f'results/{name}_{seed}_predictions.npz',probabilities=p)
        runs.append(result); print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)
    allruns=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'results').glob('*_[012].json')]
    summary=[]
    for name in MODELS:
        rr=[r for r in allruns if r['model']==name]
        if not rr:continue
        out=dict(model=name,n=len(rr),seeds=[r['seed'] for r in rr])
        for key in ['precision','recall','f1','ap','roc_auc']:
            vals=[r['test'][key] for r in rr];out[key]=float(np.mean(vals));out[key+'_std']=float(np.std(vals,ddof=1)) if len(vals)>1 else 0
        summary.append(out)
    result=dict(environment={'python':platform.python_version(),'torch':torch.__version__,'device':'cpu','threads':args.threads},protocol={'train':'1-29','validation':'30-34','test':'35-49','selection':'Early stopping on validation average precision. Threshold maximizing validation F1. Test untouched until final evaluation.','graph':'Undirected binary edges + self loops, symmetric degree normalization. Direction retained in UI.','features':'93 local numeric features, timestep excluded. RF-all additionally uses 72 provider aggregates.','limitations':'Historical snapshot classification. Edges can include downstream transactions already observed in snapshot; not real-time pre-confirmation detection. Features are anonymized and supplied preprocessed by provider.','neural':'64 hidden units, dropout 0.2, Adam lr .003, weight decay .0005, weighted BCE, at most 180 epochs, patience30. MLP has identical layers and skip connection but adjacency replaced by identity.','rf':'200 trees, min_samples_leaf2, balanced_subsample, sqrt features'},summary=summary,runs=[{k:v for k,v in r.items() if k!='history'} for r in allruns])
    (ROOT/'results/metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('SUMMARY',json.dumps(summary),flush=True)

if __name__=='__main__':main()
