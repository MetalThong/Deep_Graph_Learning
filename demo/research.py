"""Extended experiment with PyTorch Geometric, fixed protocol and saved checkpoints.

python research.py --epochs 300 --seeds 42 43 44 --split-seeds 2026
Use --split-seeds 2026 2027 2028 for a larger robustness study.
The defaults are intentionally pre-specified, not tuned on the test set.
"""
import argparse
import copy
import platform
import time
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, SAGEConv
import torch_geometric
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from train import ROOT, load_data, measure, save_json


class GraphModel(nn.Module):
    def __init__(self, kind, depth, inputs=1433, hidden=32, outputs=7):
        super().__init__()
        self.kind=kind
        dims=[inputs]+[hidden]*(depth-1)+[outputs]
        self.layers=nn.ModuleList()
        for i in range(depth):
            a,b=dims[i:i+2]
            if kind=='GCN': layer=GCNConv(a,b,cached=False,bias=False)
            elif kind=='SAGE': layer=SAGEConv(a,b,aggr='mean',bias=False)
            elif kind=='GAT':
                layer=GATConv(a,b//4,heads=4,concat=True,dropout=0,bias=False) if i<depth-1 else GATConv(a,b,heads=1,concat=False,dropout=0,bias=False)
            else: layer=nn.Linear(a,b,bias=False)
            self.layers.append(layer)

    def forward(self,x,edge_index):
        for i,layer in enumerate(self.layers):
            x=layer(x) if self.kind=='MLP' else layer(x,edge_index)
            if i<len(self.layers)-1:
                x=F.dropout(F.relu(x),p=.5,training=self.training)
        return x


def split_labels(y,seed):
    rng=np.random.default_rng(seed)
    train=np.concatenate([rng.permutation(np.flatnonzero(y==k))[:20] for k in range(7)])
    rest=rng.permutation(np.setdiff1d(np.arange(len(y)),train))
    return train,rest[:500],rest[500:1500]


def fit(kind,depth,x,edges,y,train,val,seed,epochs):
    torch.manual_seed(seed)
    model=GraphModel(kind,depth,inputs=x.shape[1])
    optimizer=torch.optim.Adam(model.parameters(),lr=.01,weight_decay=.0005)
    best_loss=float('inf');best=None;stale=0;history=[];start=time.perf_counter()
    for epoch in range(1,epochs+1):
        model.train();optimizer.zero_grad()
        logits=model(x,edges);loss=F.cross_entropy(logits[train],y[train])
        loss.backward();optimizer.step()
        model.eval()
        with torch.no_grad():
            pred=model(x,edges)
            vl=float(F.cross_entropy(pred[val],y[val]))
            va=float((pred[val].argmax(1)==y[val]).float().mean())
        history.append({'epoch':epoch,'train_cross_entropy_dropout':float(loss.detach()),'val_loss':vl,'val_accuracy':va})
        if vl<best_loss-1e-6:
            best_loss=vl;best=copy.deepcopy(model.state_dict());best_epoch=epoch;stale=0
        else: stale+=1
        if stale>=60: break
    model.load_state_dict(best);model.eval()
    with torch.no_grad(): pred=model(x,edges).argmax(1).numpy()
    return model,pred,history,best_epoch,time.perf_counter()-start,best_loss


def verify_numpy_equivalence(x,edges):
    """Use saved NumPy weights to verify the GCN convention before comparing models."""
    import json
    w=json.loads((ROOT/'dist'/'weights.json').read_text())
    ref=np.array(json.loads((ROOT/'results'/'reference_logits.json').read_text()))
    model=GraphModel('GCN',2).double().eval()
    with torch.no_grad():
        model.layers[0].lin.weight.copy_(torch.tensor(w['w1'],dtype=torch.float64).T)
        model.layers[1].lin.weight.copy_(torch.tensor(w['w2'],dtype=torch.float64).T)
        actual=model(x.double(),edges).numpy()
    error=float(np.max(np.abs(ref-actual)))
    if error>1e-9: raise AssertionError(f'NumPy/PyG GCN mismatch: {error}')
    return error


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--epochs',type=int,default=300)
    parser.add_argument('--seeds',nargs='+',type=int,default=[42,43,44])
    parser.add_argument('--split-seeds',nargs='+',type=int,default=[2026])
    args=parser.parse_args()
    if args.epochs<1: parser.error('epochs must be positive')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    x,y,undirected,*_=load_data()
    directed=undirected+[(b,a) for a,b in undirected]
    edge_index=torch.tensor(directed,dtype=torch.long).T.contiguous()
    tx=torch.tensor(x.toarray(),dtype=torch.float32);ty=torch.tensor(y,dtype=torch.long)
    parity=verify_numpy_equivalence(torch.tensor(x.toarray(),dtype=torch.float64),edge_index)
    print('NumPy/PyG max logit difference:',parity,flush=True)
    directory=ROOT/'results'/'research';directory.mkdir(parents=True,exist_ok=True)
    configurations=[('MLP',2),('GCN',2),('SAGE',2),('GAT',2),('GCN',1),('GCN',4),('GCN',8)]
    results={'protocol':'Fixed custom stratified transductive split; 140 train / 500 validation / 1000 test / 1068 unused labels; loss only on train; minimum validation loss checkpoint; no test tuning.',
             'config':{'seeds':args.seeds,'split_seeds':args.split_seeds,'epochs':args.epochs,'hidden':32,
                       'lr':.01,'weight_decay':.0005,'hidden_dropout':.5,'patience':60,'gat_heads':4,
                       'gat_attention_dropout':0,'optimizer':'Adam','bias':False},
             'environment':{'python':platform.python_version(),'torch':torch.__version__,'pyg':torch_geometric.__version__,
                            'device':'CPU','threads':1},
             'numpy_pyg_max_logit_error':parity,'runs':[]}
    for split_seed in args.split_seeds:
        train,val,test=split_labels(y,split_seed)
        save_json(directory/f'split_{split_seed}.json',{'train':train.tolist(),'validation':val.tolist(),'test':test.tolist()})
        baseline=LogisticRegression(C=1000,max_iter=2000,random_state=42)
        start=time.perf_counter();baseline.fit(x[train],y[train]);pred=baseline.predict(x)
        results['runs'].append({'model':'Logistic Regression','seed':42,'split_seed':split_seed,
                                'parameters':int(baseline.coef_.size+baseline.intercept_.size),
                                'seconds':time.perf_counter()-start,**measure(y,pred,test)})
        for kind,depth in configurations:
            label=f'{kind}-{depth}' if kind!='SAGE' else 'GraphSAGE-2'
            for seed in args.seeds:
                model,pred,history,best_epoch,secs,vl=fit(kind,depth,tx,edge_index,ty,train,val,seed,args.epochs)
                run={'model':label,'seed':seed,'split_seed':split_seed,'best_epoch':best_epoch,
                     'val_loss':vl,'parameters':sum(p.numel() for p in model.parameters()),'seconds':secs,
                     **measure(y,pred,test)}
                results['runs'].append(run)
                prefix=f'{label}_split{split_seed}_seed{seed}'
                torch.save({'state_dict':model.state_dict(),'kind':kind,'depth':depth,'seed':seed,'split_seed':split_seed,
                            'best_epoch':best_epoch,'config':results['config']},directory/(prefix+'.pt'))
                save_json(directory/(prefix+'_history.json'),history)
                print(label,split_seed,seed,'accuracy',round(run['accuracy'],4),'f1',round(run['macro_f1'],4),'epoch',best_epoch,'seconds',round(secs,1),flush=True)
                save_json(directory/'progress.json',results)
    results['summary']=[]
    for name in dict.fromkeys(r['model'] for r in results['runs']):
        runs=[r for r in results['runs'] if r['model']==name]
        results['summary'].append({'model':name,'runs':len(runs),'accuracy_mean':float(np.mean([r['accuracy'] for r in runs])),
            'accuracy_std':float(np.std([r['accuracy'] for r in runs])),
            'macro_f1_mean':float(np.mean([r['macro_f1'] for r in runs])),
            'seconds_mean':float(np.mean([r['seconds'] for r in runs])),'parameters':runs[0]['parameters']})
    save_json(directory/'metrics.json',results)
    save_json(ROOT/'dist'/'research.json',results)
    print('Research complete:',len(results['runs']),'runs.',flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1): main()
