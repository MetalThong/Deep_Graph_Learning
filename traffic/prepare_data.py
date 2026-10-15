"""Fetch the authors' METR-LA release and prepare a causal, chronological experiment."""
from pathlib import Path
import hashlib, json, pickle, urllib.request
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
SOURCES = {
    'metr-la.h5': 'https://drive.google.com/uc?id=1pAGRfzMx6K9WWsfDcD1NMbIif0T0saFC',
    'adj_mx.pkl': 'https://raw.githubusercontent.com/liyaguang/DCRNN/master/data/sensor_graph/adj_mx.pkl',
    'graph_sensor_locations.csv': 'https://raw.githubusercontent.com/liyaguang/DCRNN/master/data/sensor_graph/graph_sensor_locations.csv',
    'DCRNN_LICENSE': 'https://raw.githubusercontent.com/liyaguang/DCRNN/master/LICENSE',
}

def download():
    DATA.mkdir(exist_ok=True)
    for name, url in SOURCES.items():
        if (DATA / name).exists():
            continue
        if name.endswith('.h5'):
            import gdown
            gdown.download(url, str(DATA / name), quiet=False)
        else:
            urllib.request.urlretrieve(url, DATA / name)

def prepare():
    download()
    df = pd.read_hdf(DATA / 'metr-la.h5')
    sensor_ids, _, directed = pickle.load(open(DATA / 'adj_mx.pkl', 'rb'), encoding='latin1')
    assert list(map(str, df.columns)) == list(map(str, sensor_ids))
    assert (np.diff(df.index.asi8) == 300 * 10**9).all()
    raw = df.to_numpy(dtype=np.float32)
    valid = np.isfinite(raw) & (raw > 0)  # DCRNN benchmark masks zero targets.
    nt, nn = raw.shape
    train_end, val_end = int(nt * .7), int(nt * .8)
    observed_train = raw[:train_end][valid[:train_end]]
    mean, std = float(observed_train.mean()), float(observed_train.std())
    medians = np.nanmedian(np.where(valid[:train_end], raw[:train_end], np.nan), axis=0)
    clean = np.where(valid, raw, np.nan)
    # Forward fill only. Never backfill from future observations.
    filled = pd.DataFrame(clean).ffill().fillna(dict(enumerate(medians))).to_numpy(dtype=np.float32)
    node = np.stack([(filled - mean) / std, valid.astype(np.float32)], axis=-1)
    # Symmetrize the published distance graph; this deliberately drops direction.
    adj = np.maximum(directed, directed.T).astype(np.float32)
    np.fill_diagonal(adj, 1.)
    degree = adj.sum(1)
    norm = adj / np.sqrt(degree[:, None] * degree[None, :])
    neighbor = np.einsum('ij,tjf->tif', norm, node, optimize=True)
    mins = df.index.hour.to_numpy() * 60 + df.index.minute.to_numpy()
    dow = df.index.dayofweek.to_numpy()
    calendar = np.stack([np.sin(2*np.pi*mins/1440), np.cos(2*np.pi*mins/1440),
                         np.sin(2*np.pi*dow/7), np.cos(2*np.pi*dow/7)], -1).astype(np.float32)
    ends = np.arange(11, nt - 3, dtype=np.int64)
    target = ends + 3
    # At the first evaluation origin, all labels used before it must be available.
    # +15 minute forecast: skip two target timestamps at each boundary.
    split = {'train': ends[target < train_end],
             'val': ends[(target >= train_end + 2) & (target < val_end)],
             'test': ends[target >= val_end + 2]}
    last_seen=np.full(nn,-1,dtype=np.int32)
    age_minutes=np.empty((nt,nn),dtype=np.int32)
    for t in range(nt):
        last_seen[valid[t]]=t
        age_minutes[t]=np.where(last_seen>=0,(t-last_seen)*5,-1)
    locations = pd.read_csv(DATA / 'graph_sensor_locations.csv').set_index('sensor_id')
    coords = locations.loc[list(map(int, sensor_ids)), ['latitude','longitude']].to_numpy()
    np.savez_compressed(DATA / 'prepared.npz', raw=raw, valid=valid, filled=filled,
                        node=node, neighbor=neighbor, calendar=calendar, adj=adj, norm=norm,
                        timestamps=df.index.astype(str).to_numpy(dtype='U19'),
                        sensor_ids=np.array(sensor_ids), coords=coords, mean=mean, std=std,
                        age_minutes=age_minutes, **split)
    meta = {'dataset':'METR-LA', 'nodes':nn, 'timestamps':nt,
            'start':str(df.index[0]), 'end':str(df.index[-1]), 'interval_minutes':5,
            'raw_unit':'mph', 'display_unit':'km/h', 'mph_to_kmh':1.609344,
            'missing_fraction':float((~valid).mean()), 'mean_train_mph':mean, 'std_train_mph':std,
            'train_end_index':train_end, 'val_end_index':val_end,
            'directed_edges_without_self':int(np.count_nonzero(directed)-np.count_nonzero(np.diag(directed))),
            'undirected_edges_without_self':int((np.count_nonzero(adj)-nn)//2),
            'input_steps':12, 'horizon_steps':3,
            'splits':{k:{'windows':len(v),'target_start':str(df.index[v[0]+3]),
                         'target_end':str(df.index[v[-1]+3])} for k,v in split.items()},
            'preprocessing':'Zero/non-finite = missing; causal forward fill with train-only node-median fallback; global train-only observed mean/std; target zeros masked.',
            'boundary_gap':'Two target timestamps excluded at each validation/test start, so the first origin is at or after the preceding final label timestamp.',
            'freshness':'Age in minutes since last observed raw value, computed from complete past before replay slicing; -1 means no earlier observation. Informational warning only; not a calibrated confidence score or a model input.',
            'graph':'max(A,A.T), diagonal=1, symmetric degree normalization; no road direction in this compact model.',
            'sources':SOURCES,
            'sha256':{name:hashlib.sha256((DATA/name).read_bytes()).hexdigest() for name in SOURCES}}
    (ROOT/'results'/'data_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    return meta

if __name__ == '__main__':
    prepare()
