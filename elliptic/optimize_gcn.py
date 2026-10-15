"""Validation-only GCN ablations; test evaluation is a separate, explicit stage.

The original test was already reported. Any subsequent test scores are a
retrospective reevaluation, NOT an untouched independent confirmation.
"""
from pathlib import Path
import argparse, copy, hashlib, json, random, shutil, time
import numpy as np
import joblib
import torch
from torch import nn
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import QuantileTransformer
from train import adjacency, score, choose_threshold

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'optimization'
CONFIGS = {
    'long': dict(hidden=64, dropout=.2, lr=.003, weight_decay=.0005, pos_weight='ratio', clip=None, epochs=1500, patience=150),
    'moderate_weight': dict(hidden=64, dropout=.2, lr=.003, weight_decay=.0005, pos_weight=7/3, clip=None, epochs=1500, patience=150),
    'paper_inspired': dict(hidden=100, dropout=.2, lr=.001, weight_decay=.0005, pos_weight=7/3, clip=None, epochs=1500, patience=150),
    'clipped': dict(hidden=64, dropout=.2, lr=.003, weight_decay=.0005, pos_weight=7/3, clip=5., epochs=1500, patience=150),
    'quantile': dict(hidden=64, dropout=.2, lr=.003, weight_decay=.0005, pos_weight=7/3, clip=None, transform='quantile', epochs=1500, patience=150),
}
_TRANSFORM_CACHE={}

def neural_features(data, transform=None, include_test=False):
    if transform!='quantile':return data['x'][:,:93]
    key=('quantile',include_test)
    if key in _TRANSFORM_CACHE:return _TRANSFORM_CACHE[key]
    x=data['x'][:,:93];split=data['split'];train=x[split==0]
    fingerprint=hashlib.sha256(train.tobytes()).hexdigest()
    path=OUT/'quantile_transform.joblib'
    saved=joblib.load(path) if path.exists() else None
    if saved is None or saved['train_sha256']!=fingerprint:
        transformer=QuantileTransformer(n_quantiles=1000,output_distribution='normal',subsample=None,random_state=0)
        transformer.fit(train)
        saved=dict(transformer=transformer,train_sha256=fingerprint,fit_split='t1-29, all train nodes only')
        joblib.dump(saved,path,compress=3)
    mask=np.ones(len(x),bool) if include_test else split<2
    transformed=np.zeros(x.shape,dtype=np.float32)
    transformed[mask]=saved['transformer'].transform(x[mask]).astype(np.float32)
    _TRANSFORM_CACHE[key]=transformed
    return transformed

class TunedGCN(nn.Module):
    def __init__(self, config, graph=True):
        super().__init__()
        self.graph = graph
        self.fc1 = nn.Linear(93, config['hidden'])
        self.fc2 = nn.Linear(config['hidden'], 1)
        self.skip = nn.Linear(93, 1, bias=False)
        self.drop = nn.Dropout(config['dropout'])
    def forward(self, x, ax, a):
        h = self.drop(torch.relu(self.fc1(ax if self.graph else x)))
        h = torch.sparse.mm(a, h) if self.graph else h
        return (self.fc2(h) + self.skip(x)).squeeze(-1)

def blocks(data, clip, include_test=False, transform=None):
    result=[]
    x,y,split,src,dst=(data[k] for k in ['x','y','split','src','dst'])
    x=neural_features(data,transform,include_test)
    for k in range(3 if include_test else 2):
        ind=np.flatnonzero(split==k)
        rev=np.full(len(y),-1,dtype=np.int64);rev[ind]=np.arange(len(ind))
        em=(split[src]==k)&(split[dst]==k)
        a=adjacency(len(ind),rev[src[em]],rev[dst[em]])
        features=x[ind,:93].copy()
        if clip is not None:features=np.clip(features,-clip,clip)
        xt=torch.from_numpy(features)
        mask=torch.from_numpy(y[ind]>=0)
        result.append(dict(ind=ind,x=xt,ax=torch.sparse.mm(a,xt),a=a,mask=mask,y=torch.from_numpy(y[ind].astype(np.float32))))
    return result

def preserve_baseline():
    dest=OUT/'baseline'
    if dest.exists():return
    dest.mkdir(parents=True)
    for folder in ['results','models']:
        shutil.copytree(ROOT/folder,dest/folder)
    shutil.copy2(ROOT/'train.py',dest/'train.py')
    (OUT/'protocol.json').write_text(json.dumps(dict(
        created=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        reason='Previous 180-epoch GCN still improving on validation; all seed best epochs 179.',
        train='t1-29',validation='t30-34',test='t35-49 (previously inspected; retrospective reevaluation)',
        candidates=CONFIGS,selection='Pilot seed0 validation AP, then repeat promising configurations on seeds1,2. Select by mean validation AP; validation F1 threshold per seed. No candidate test inference in search stage.',
        controls='Preserve original 12 runs. Compare extended budget to identical baseline; compare pos_weight; compare clipping; run graph=False control with final hyperparameters.',
        forbidden='No threshold tuning on test, no changing labels/split, no unknown-as-licit, no selecting best test seed.'
    ),indent=2),encoding='utf-8')

def train_one(data,name,seed,graph=True,force=False):
    config=CONFIGS[name];key=f'{name}_{"gcn" if graph else "mlp"}_{seed}'
    result_path=OUT/f'{key}.json'
    if result_path.exists() and not force:
        old=json.loads(result_path.read_text(encoding='utf-8'));print('cached',key,old['validation'],flush=True);return
    torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
    started=time.perf_counter();bb=blocks(data,config['clip'],transform=config.get('transform'));bt,bv=bb
    model=TunedGCN(config,graph);opt=torch.optim.Adam(model.parameters(),lr=config['lr'],weight_decay=config['weight_decay'])
    pos_weight=config['pos_weight']
    if pos_weight=='ratio':pos_weight=float((bt['y'][bt['mask']]==0).sum()/(bt['y'][bt['mask']]==1).sum())
    criterion=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight))
    best=-1;wait=0;history=[]
    for epoch in range(1,config['epochs']+1):
        model.train();opt.zero_grad()
        logits=model(bt['x'],bt['ax'],bt['a'])
        loss=criterion(logits[bt['mask']],bt['y'][bt['mask']]);loss.backward();opt.step()
        model.eval()
        with torch.no_grad():vp=torch.sigmoid(model(bv['x'],bv['ax'],bv['a']))[bv['mask']].numpy()
        va=float(average_precision_score(bv['y'][bv['mask']].numpy(),vp))
        history.append(dict(epoch=epoch,loss=float(loss.detach()),val_ap=va))
        if va>best+1e-5:best=va;state=copy.deepcopy(model.state_dict());best_epoch=epoch;wait=0
        else:wait+=1
        if epoch%100==0:print(f'{key} ep={epoch} val_AP={va:.5f} best={best:.5f} at={best_epoch}',flush=True)
        if epoch>=200 and wait>=config['patience']:break
    model.load_state_dict(state);model.eval()
    with torch.no_grad():vp=np.round(torch.sigmoid(model(bv['x'],bv['ax'],bv['a']))[bv['mask']].numpy().astype(np.float64),6)
    vy=bv['y'][bv['mask']].numpy();threshold=choose_threshold(vy,vp)
    result=dict(key=key,config_name=name,graph=graph,seed=seed,config=config,torch_threads=torch.get_num_threads(),threshold=threshold,best_epoch=best_epoch,stopped_epoch=epoch,seconds=round(time.perf_counter()-started,2),validation=score(vy,vp,threshold),history=history)
    result_path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    torch.save(dict(state_dict=state,config=config,graph=graph,seed=seed,best_epoch=best_epoch),OUT/f'{key}.pt')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)

def evaluate(data,key):
    selection=json.loads((OUT/'selection.json').read_text(encoding='utf-8'))
    if key not in selection['evaluate_keys']:
        raise ValueError('Freeze a validation-only selection.json before test evaluation.')
    pth=OUT/f'{key}.json';result=json.loads(pth.read_text(encoding='utf-8'));ck=torch.load(OUT/f'{key}.pt',map_location='cpu',weights_only=True)
    torch.set_num_threads(result.get('torch_threads',4))
    model=TunedGCN(ck['config'],ck['graph']);model.load_state_dict(ck['state_dict']);model.eval()
    p=np.zeros(len(data['y']),dtype=np.float64)
    with torch.no_grad():
        for b in blocks(data,ck['config']['clip'],include_test=True,transform=ck['config'].get('transform')):
            p[b['ind']]=np.round(torch.sigmoid(model(b['x'],b['ax'],b['a'])).numpy().astype(np.float64),6)
    y,split=data['y'],data['split'];tm=(split==2)&(y>=0)
    result['test']=score(y[tm],p[tm],result['threshold']);result['test_at_half']=score(y[tm],p[tm],.5)
    result['test_note']='Previously inspected test, reused for retrospective reevaluation; selection used validation only.'
    pth.write_text(json.dumps(result,indent=2),encoding='utf-8');np.savez_compressed(OUT/f'{key}_predictions.npz',probabilities=p)
    print('EVALUATION',key,json.dumps(result['test']),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--configs',nargs='+',choices=list(CONFIGS),default=list(CONFIGS));parser.add_argument('--seeds',nargs='+',type=int,default=[0]);parser.add_argument('--mlp',action='store_true');parser.add_argument('--evaluate',nargs='+');parser.add_argument('--threads',type=int,default=4);parser.add_argument('--force',action='store_true',help='Retrain selected runs, overwriting their optimization checkpoints and metrics')
    args=parser.parse_args();torch.set_num_threads(args.threads);OUT.mkdir(exist_ok=True);preserve_baseline()
    data=np.load(ROOT/'data/prepared.npz')
    if args.evaluate:
        for key in args.evaluate:evaluate(data,key)
    else:
        for name in args.configs:
            for seed in args.seeds:train_one(data,name,seed,not args.mlp,args.force)

if __name__=='__main__':main()
