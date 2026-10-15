"""Download the original Elliptic benchmark and build audited, chronological splits."""
from pathlib import Path
import hashlib, json, zipfile
import numpy as np
import pandas as pd
import requests
from sklearn.preprocessing import StandardScaler
import joblib

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
SOURCE = 'https://www.kaggle.com/api/v1/datasets/download/ellipticco/elliptic-data-set'

def main():
    DATA.mkdir(exist_ok=True)
    raw = DATA / 'elliptic_bitcoin_dataset'
    if not (raw / 'elliptic_txs_features.csv').exists():
        r = requests.get(SOURCE, timeout=180); r.raise_for_status()
        (DATA / 'elliptic.zip').write_bytes(r.content)
        with zipfile.ZipFile(DATA / 'elliptic.zip') as z:
            for name in z.namelist():
                if not (DATA / name).resolve().is_relative_to(DATA.resolve()):
                    raise ValueError('Unsafe archive path')
            z.extractall(DATA)
    f = pd.read_csv(raw / 'elliptic_txs_features.csv', header=None)
    c = pd.read_csv(raw / 'elliptic_txs_classes.csv', dtype={'class':str})
    e = pd.read_csv(raw / 'elliptic_txs_edgelist.csv')
    ids = f.iloc[:,0].to_numpy(np.int64)
    times = f.iloc[:,1].to_numpy(np.int16)
    x = f.iloc[:,2:].to_numpy(np.float32) # 93 local + 72 aggregated; exclude timestep
    assert x.shape == (203769,165) and len(np.unique(ids)) == len(ids)
    assert np.isfinite(x).all()
    lookup = pd.Series(np.arange(len(ids)), index=ids)
    src = e.iloc[:,0].map(lookup).to_numpy(np.int64)
    dst = e.iloc[:,1].map(lookup).to_numpy(np.int64)
    y = c.set_index('txId')['class'].reindex(ids).map({'1':1,'2':0,'unknown':-1}).to_numpy(np.int8)
    assert not np.any(times[src] != times[dst]), 'Unexpected cross-time edges'
    split = np.where(times<=29,0,np.where(times<=34,1,2)).astype(np.int8)
    scaler = StandardScaler().fit(x[split==0])
    x = scaler.transform(x).astype(np.float32)
    (ROOT/'models').mkdir(exist_ok=True); (ROOT/'results').mkdir(exist_ok=True)
    joblib.dump(scaler, ROOT/'models/scaler.joblib')
    np.savez_compressed(DATA/'prepared.npz',ids=ids,times=times,x=x,y=y,src=src,dst=dst,split=split)
    summary = {'source':SOURCE,'paper':'https://arxiv.org/abs/1908.02591','nodes':len(ids),'edges':len(src),'time_steps':49,'features':{'local':93,'aggregated':72,'excluded':'timestep'},'labels':{'illicit':int((y==1).sum()),'licit':int((y==0).sum()),'unknown':int((y<0).sum())},'splits':{},'sha256':{},'protocol':'Train t1-29, validation t30-34, test t35-49. No labels as features. Unknown nodes are context only; never negative labels. StandardScaler fitted to train nodes only. Features are the provider-supplied anonymized benchmark values; original raw amounts cannot be recovered.'}
    for k,name in enumerate(['train','validation','test']):
        mask=split==k
        summary['splits'][name]={'nodes':int(mask.sum()),'known':int((mask&(y>=0)).sum()),'illicit':int((mask&(y==1)).sum()),'licit':int((mask&(y==0)).sum()),'unknown':int((mask&(y<0)).sum()),'start':int(times[mask].min()),'end':int(times[mask].max())}
    for p in raw.glob('*.csv'): summary['sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT/'results/data_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__': main()
