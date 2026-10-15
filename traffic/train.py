"""Compact spatial graph convolution + GRU, plus a parameter-matched identity-graph baseline.

Training samples random (forecast origin, sensor) windows. Fixed graph aggregation
is precomputed; all learned spatial/temporal weights are trained jointly.
No test metric is computed until all checkpoints have been selected on validation.
"""
from pathlib import Path
import argparse, json, time, copy, random, platform
import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parent
KMH=1.609344
RUN_ID='v2_160epochs_fullval'

class ForecastNet(nn.Module):
    def __init__(self, spatial=8, hidden=16):
        super().__init__()
        self.spatial=nn.Linear(4,spatial)
        self.gru=nn.GRU(spatial+4,hidden,batch_first=True)
        self.head=nn.Linear(hidden,1)
    def forward(self,x,calendar):
        z=torch.relu(self.spatial(x))
        sequence=torch.cat([z,calendar],-1)
        _,h=self.gru(sequence)
        return x[:,-1,0]+self.head(h[-1]).squeeze(-1)

class Data:
    def __init__(self):
        d=np.load(ROOT/'data'/'prepared.npz')
        self.d=d
        self.node=torch.from_numpy(d['node'])
        self.neighbor=torch.from_numpy(d['neighbor'])
        self.calendar=torch.from_numpy(d['calendar'])
        self.raw=d['raw']; self.valid=d['valid']
        self.mean=float(d['mean']); self.std=float(d['std'])
        self.target=torch.from_numpy((self.raw-self.mean)/self.std)
        self.mask=torch.from_numpy(self.valid)
        self.n=self.raw.shape[1]
    def batch(self,ends,nodes,graph):
        ts=torch.as_tensor(ends)[:,None]+torch.arange(-11,1)[None,:]
        ns=torch.as_tensor(nodes)[:,None]
        own=self.node[ts,ns]
        near=self.neighbor[ts,ns] if graph else own
        x=torch.cat([own,near],-1)
        cal=self.calendar[ts]
        t=torch.as_tensor(ends)+3; n=torch.as_tensor(nodes)
        return x,cal,self.target[t,n],self.mask[t,n]

@torch.inference_mode()
def predict(model,data,ends,graph,batch=4096):
    model.eval(); out=np.empty((len(ends),data.n),dtype=np.float32)
    flat=out.reshape(-1)
    for start in range(0,len(flat),batch):
        ids=np.arange(start,min(start+batch,len(flat)))
        x,c,_,_=data.batch(ends[ids//data.n],ids%data.n,graph)
        flat[start:start+len(ids)]=model(x,c).numpy()*data.std+data.mean
    return out

def score(pred,y,valid):
    err=(pred[valid]-y[valid]).astype(np.float64)*KMH
    slow=valid & (y<30/KMH)
    return {'mae_kmh':float(np.abs(err).mean()),'rmse_kmh':float(np.sqrt((err**2).mean())),
            'valid_targets':int(valid.sum()),'slow_mae_kmh':float(np.abs((pred-y)[slow]).mean()*KMH) if slow.any() else None,
            'slow_targets':int(slow.sum())}

def fit(data,graph,seed,args):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    rng=np.random.default_rng(seed)
    model=ForecastNet(args.spatial,args.hidden)
    opt=torch.optim.Adam(model.parameters(),lr=args.lr,weight_decay=1e-5)
    scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(opt,mode='min',factor=.5,
              patience=6,threshold=1e-4,threshold_mode='abs',min_lr=1e-5)
    train_ends=data.d['train']; val_ends=data.d['val'][::args.val_stride]
    best=float('inf'); patience=0; history=[]; best_state=None; best_epoch=0
    began=time.perf_counter(); name='gcn_gru' if graph else 'gru'
    for epoch in range(1,args.epochs+1):
        model.train(); losses=[]
        for _ in range(args.samples//args.batch):
            ends=rng.choice(train_ends,args.batch); nodes=rng.integers(0,data.n,args.batch)
            x,c,y,m=data.batch(ends,nodes,graph)
            if not m.any(): continue
            opt.zero_grad(); p=model(x,c)
            loss=(p[m]-y[m]).abs().mean()
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),5.); opt.step()
            losses.append(float(loss.detach())*data.std*KMH)
        pred=predict(model,data,val_ends,graph)
        metrics=score(pred,data.raw[val_ends+3],data.valid[val_ends+3])
        value=metrics['mae_kmh']; history.append({'epoch':epoch,'train_sample_mae_kmh':float(np.mean(losses)), 'val_mae_kmh':value,'learning_rate':opt.param_groups[0]['lr']})
        if value<best-1e-5:
            best=value; best_state=copy.deepcopy(model.state_dict()); best_epoch=epoch; patience=0
        else: patience+=1
        scheduler.step(value)
        print(json.dumps({'model':name,'seed':seed,**history[-1],'elapsed_s':round(time.perf_counter()-began,1)}),flush=True)
        if patience>=args.patience: break
    elapsed=time.perf_counter()-began
    model.load_state_dict(best_state)
    checkpoint={'run_id':RUN_ID,'state_dict':best_state,'graph':graph,'seed':seed,'spatial':args.spatial,'hidden':args.hidden,
                'best_epoch':best_epoch,'val_mae_kmh':best,'config':vars(args)}
    torch.save(checkpoint,ROOT/'results'/f'{name}_{seed}.pt')
    result={'run_id':RUN_ID,'model':name,'seed':seed,'best_epoch':best_epoch,'val_mae_kmh':best,'fit_seconds':elapsed,
            'epochs_run':len(history),'stop_reason':'patience' if patience>=args.patience else 'epoch_budget',
            'config':vars(args),'scheduler':{'factor':.5,'patience':6,'min_lr':1e-5,'threshold':1e-4},
            'parameters':sum(p.numel() for p in model.parameters()),'history':history}
    (ROOT/'results'/f'{name}_{seed}.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result

def load_model(name,seed):
    ck=torch.load(ROOT/'results'/f'{name}_{seed}.pt',map_location='cpu',weights_only=True)
    model=ForecastNet(ck['spatial'],ck['hidden']); model.load_state_dict(ck['state_dict']); model.eval()
    return model,ck

def evaluate(data,seeds):
    ends=data.d['test']; y=data.raw[ends+3]; valid=data.valid[ends+3]
    persistence=data.d['filled'][ends]
    runs=[{'model':'persistence','seed':None,**score(persistence,y,valid)}]
    saved={'ends':ends,'actual':y,'valid':valid,'persistence':persistence}
    selected={}
    for name in ['gru','gcn_gru']:
        rows=[]
        for seed in seeds:
            row=json.loads((ROOT/'results'/f'{name}_{seed}.json').read_text())
            model,ck=load_model(name,seed)
            assert ck['run_id']==RUN_ID and row['run_id']==RUN_ID,'Cannot mix training revisions'
            pred=predict(model,data,ends,name=='gcn_gru')
            row.update(score(pred,y,valid)); runs.append(row); rows.append(row)
            saved[f'{name}_{seed}']=pred
            print(json.dumps({k:v for k,v in row.items() if k!='history'}),flush=True)
        # Deployment checkpoint uses validation only, never test rank.
        selected[name]=min(rows,key=lambda r:r['val_mae_kmh'])['seed']
    summary=[]
    for name in ['persistence','gru','gcn_gru']:
        rows=[r for r in runs if r['model']==name]
        summary.append({'model':name,'runs':len(rows),**{key:float(np.mean([r[key] for r in rows])) for key in ['mae_kmh','rmse_kmh','slow_mae_kmh']},
                        'mae_std_kmh':float(np.std([r['mae_kmh'] for r in rows],ddof=1)) if len(rows)>1 else 0.})
    output={'run_id':RUN_ID,'protocol':'chronological 70/10/20 by target timestamp, two-target gap at validation/test start; 12 inputs, direct +3 steps; zero targets masked; km/h metrics; every validation/test origin',
            'interpretation':'Version 2 follows inspection of version 1 test results; exploratory iteration, not a new untouched test benchmark.',
            'environment':{'python':platform.python_version(),'torch':torch.__version__,'device':'cpu','threads':torch.get_num_threads()},
            'seeds':seeds,'selected_by_validation':selected,'summary':summary,'runs':runs}
    (ROOT/'results'/'metrics.json').write_text(json.dumps(output,indent=2),encoding='utf8')
    np.savez_compressed(ROOT/'results'/'predictions.npz',**saved)
    print(json.dumps({'summary':summary,'selected':selected},indent=2),flush=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--epochs',type=int,default=160); ap.add_argument('--patience',type=int,default=20)
    ap.add_argument('--samples',type=int,default=32768); ap.add_argument('--batch',type=int,default=512)
    ap.add_argument('--hidden',type=int,default=16); ap.add_argument('--spatial',type=int,default=8)
    ap.add_argument('--lr',type=float,default=.003); ap.add_argument('--threads',type=int,default=2)
    ap.add_argument('--val-stride',type=int,default=1); ap.add_argument('--seeds',type=int,nargs='+',default=[42,43,44])
    ap.add_argument('--models',nargs='+',default=['gru','gcn_gru']); ap.add_argument('--evaluate-only',action='store_true')
    ap.add_argument('--no-evaluate',action='store_true')
    args=ap.parse_args(); torch.set_num_threads(args.threads); data=Data()
    if not args.evaluate_only:
        for name in args.models:
            for seed in args.seeds: fit(data,name=='gcn_gru',seed,args)
    if not args.no_evaluate and all((ROOT/'results'/f'{name}_{seed}.pt').exists() for name in ['gru','gcn_gru'] for seed in args.seeds):
        evaluate(data,args.seeds)

if __name__=='__main__':main()
