"""Reproducible Cora experiment: Logistic Regression, MLP, and GCN.

Run: python train.py --epochs 300 --seeds 42 43 44
GCN forward/backward/Adam are explicit NumPy/SciPy, following the course's
mathematics -> implementation approach. No labels enter message passing.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time
import urllib.request

import numpy as np
import scipy.sparse as sp
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
SOURCE = "https://linqs-data.soe.ucsc.edu/public/lbc/cora.tgz"


def load_data():
    cache = ROOT / "data" / "cora.tgz"
    cache.parent.mkdir(exist_ok=True)
    if not cache.exists():
        with urllib.request.urlopen(SOURCE, timeout=90) as response:
            raw = response.read()
        cache.write_bytes(raw)
    raw = cache.read_bytes()
    # Read only the two named text files; do not extract arbitrary archive paths.
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        content = archive.extractfile("cora/cora.content").read().decode().splitlines()
        citations = archive.extractfile("cora/cora.cites").read().decode().splitlines()
    rows = [line.split() for line in content]
    rows.sort(key=lambda row: int(row[0]))
    ids = [row[0] for row in rows]
    index = {paper: i for i, paper in enumerate(ids)}
    classes = sorted({row[-1] for row in rows})
    y = np.array([classes.index(row[-1]) for row in rows], dtype=np.int64)
    features = [[j for j, value in enumerate(row[1:-1]) if value == "1"] for row in rows]
    r, c = [], []
    for i, values in enumerate(features):
        r.extend([i] * len(values)); c.extend(values)
    x = sp.csr_matrix((np.ones(len(r), dtype=np.float64), (r, c)), shape=(len(rows), len(rows[0])-2))
    x = sp.diags(1 / np.maximum(np.asarray(x.sum(1)).ravel(), 1)) @ x
    edges = sorted({tuple(sorted((index[a], index[b]))) for a, b in map(str.split, citations)
                    if a in index and b in index and a != b})
    # Fixed custom split, NOT Planetoid's public split. Hold constant across models.
    rng = np.random.default_rng(2026)
    train = np.concatenate([rng.permutation(np.flatnonzero(y == k))[:20] for k in range(len(classes))])
    rest = rng.permutation(np.setdiff1d(np.arange(len(y)), train))
    val, test = rest[:500], rest[500:1500]
    return x.tocsr(), y, edges, train, val, test, ids, classes, features, hashlib.sha256(raw).hexdigest()


def adjacency(n, edges):
    r, c = list(range(n)), list(range(n))
    for u, v in edges:
        r.extend([u, v]); c.extend([v, u])
    a = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(n, n))
    d = sp.diags(1 / np.sqrt(np.asarray(a.sum(1)).ravel()))
    return (d @ a @ d).tocsr()


def softmax(logits):
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


def forward(b, a, w1, w2):
    # b = A_hat @ X, cached because A_hat and X are fixed during training.
    return (a @ np.maximum(b @ w1, 0)) @ w2


def loss_grads(b, a, w1, w2, y, train, decay, rng=None):
    z = b @ w1
    h = np.maximum(z, 0)
    drop = (rng.random(h.shape) >= .5) * 2.0 if rng is not None else np.ones_like(h)
    u = a @ (h * drop)
    logits = u @ w2
    p = softmax(logits)
    loss = -np.log(np.maximum(p[train, y[train]], 1e-15)).mean()
    loss += .5 * decay * (np.square(w1).sum() + np.square(w2).sum())
    dl = np.zeros_like(logits)
    dl[train] = p[train]
    dl[train, y[train]] -= 1
    dl /= len(train)
    dw2 = u.T @ dl + decay * w2
    dz = (a.T @ (dl @ w2.T)) * drop * (z > 0)
    dw1 = b.T @ dz + decay * w1
    return float(loss), (np.asarray(dw1), np.asarray(dw2))


def fit(x, a, y, train, val, seed, epochs, hidden=32):
    rng = np.random.default_rng(seed)
    weights = [rng.normal(0, np.sqrt(2/x.shape[1]), (x.shape[1], hidden)),
               rng.normal(0, np.sqrt(2/hidden), (hidden, int(y.max())+1))]
    m, v = [np.zeros_like(w) for w in weights], [np.zeros_like(w) for w in weights]
    b = (a @ x).tocsr()
    history, best, best_loss, stale = [], None, float("inf"), 0
    start = time.perf_counter()
    for epoch in range(1, epochs + 1):
        loss, grads = loss_grads(b, a, *weights, y, train, .0005, rng)
        for j, grad in enumerate(grads):
            m[j] = .9*m[j] + .1*grad
            v[j] = .999*v[j] + .001*grad**2
            weights[j] -= .01*(m[j]/(1-.9**epoch))/(np.sqrt(v[j]/(1-.999**epoch))+1e-8)
        p = softmax(forward(b, a, *weights))
        val_loss = float(-np.log(np.maximum(p[val, y[val]], 1e-15)).mean())
        history.append({"epoch":epoch, "train_loss_dropout":loss, "val_loss":val_loss,
                        "train_accuracy":float(np.mean(p[train].argmax(1)==y[train])),
                        "val_accuracy":float(np.mean(p[val].argmax(1)==y[val]))})
        if val_loss < best_loss - 1e-6:
            best_loss, best, best_epoch, stale = val_loss, [w.copy() for w in weights], epoch, 0
        else:
            stale += 1
        if stale >= 60:
            break
    return best, history, best_epoch, time.perf_counter()-start


def measure(y, pred, test):
    return {"accuracy":float(accuracy_score(y[test], pred[test])),
            "macro_f1":float(f1_score(y[test], pred[test], average="macro", zero_division=0)),
            "confusion_matrix":confusion_matrix(y[test], pred[test], labels=np.arange(7)).tolist()}


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42,43,44])
    args = parser.parse_args()
    if args.epochs < 1 or not args.seeds: parser.error("Need positive epochs and at least one seed")
    x,y,edges,train,val,test,ids,classes,features,sha = load_data()
    (ROOT/"dist").mkdir(exist_ok=True)
    (ROOT/"results").mkdir(exist_ok=True)
    a = adjacency(len(y),edges)
    identity = sp.eye(len(y),format="csr")
    split = np.full(len(y), "unlabelled", dtype=object)
    for name, indices in [("train",train),("validation",val),("test",test)]: split[indices]=name
    report = {"dataset":"Cora", "source":SOURCE, "source_sha256":sha,
        "n":len(y), "features":x.shape[1], "edges_undirected":len(edges), "classes":classes,
        "split":{"method":"custom stratified fixed split; sorted numeric paper IDs; NumPy default_rng(2026)",
                 "seed":2026,"train":len(train),"validation":len(val),"test":len(test),
                 "unlabelled":int(np.sum(split=="unlabelled")),"is_planetoid_public":False},
        "protocol":"Transductive: all X and A visible; only train labels enter loss. Validation loss selects checkpoint. Test is evaluated after selection. All models share the split.",
        "config":{"hidden":32,"max_epochs":args.epochs,"patience":60,"learning_rate":.01,
                  "weight_decay":.0005,"hidden_dropout":.5,"optimizer":"Adam","seeds":args.seeds},
        "runs":[]}
    start=time.perf_counter()
    lr=LogisticRegression(C=1000,max_iter=2000,random_state=42)
    lr.fit(x[train],y[train]); pred_lr=lr.predict(x)
    report["runs"].append({"model":"Logistic Regression","seed":42,"seconds":time.perf_counter()-start,
                           **measure(y,pred_lr,test)})
    for model in ["MLP", "GCN"]:
        adj = identity if model=="MLP" else a
        for seed in args.seeds:
            weights, history, best_epoch, secs=fit(x,adj,y,train,val,seed,args.epochs)
            logits=forward((adj@x).tocsr(),adj,*weights)
            metrics=measure(y,logits.argmax(1),test)
            report["runs"].append({"model":model,"seed":seed,"best_epoch":best_epoch,"seconds":secs,**metrics})
            save_json(ROOT/"results"/f"{model.lower()}_{seed}_history.json",history)
            print(model,seed,"best_epoch",best_epoch,"accuracy",round(metrics["accuracy"],4),
                  "macro_f1",round(metrics["macro_f1"],4),"seconds",round(secs,2),flush=True)
            # Fixed first seed for the demo; do not pick the best seed using test labels.
            if seed==args.seeds[0]:
                if model=="GCN":
                    save_json(ROOT/"dist"/"weights.json",{"w1":weights[0].tolist(),"w2":weights[1].tolist(),"seed":seed})
                    save_json(ROOT/"dist"/"history.json",history)
                    save_json(ROOT/"results"/"reference_logits.json",logits.tolist())
                    selected_gcn=logits.argmax(1)
                else:
                    selected_mlp=logits.argmax(1)
    for model in ["Logistic Regression","MLP","GCN"]:
        runs=[r for r in report["runs"] if r["model"]==model]
        report.setdefault("summary",[]).append({"model":model,"runs":len(runs),
            "accuracy_mean":float(np.mean([r["accuracy"] for r in runs])),
            "accuracy_std":float(np.std([r["accuracy"] for r in runs])),
            "macro_f1_mean":float(np.mean([r["macro_f1"] for r in runs]))})
    # Predetermined categories for presentation. These are illustrative cases, not a new metric.
    candidates={"gcn_correct_mlp_wrong":test[(selected_gcn[test]==y[test])&(selected_mlp[test]!=y[test])],
                "gcn_wrong":test[selected_gcn[test]!=y[test]], "both_correct":test[(selected_gcn[test]==y[test])&(selected_mlp[test]==y[test])]}
    examples={k:int(v[0]) if len(v) else int(test[0]) for k,v in candidates.items()}
    save_json(ROOT/"dist"/"data.json",{"ids":ids,"classes":classes,"features":features,"edges":edges,
             "labels":y.tolist(),"split":split.tolist(),"mlp":selected_mlp.tolist(),"lr":pred_lr.tolist(),"examples":examples})
    save_json(ROOT/"dist"/"report.json",report)
    save_json(ROOT/"results"/"metrics.json",report)
    save_json(ROOT/"results"/"split.json",{"train":train.tolist(),"validation":val.tolist(),"test":test.tolist()})
    print(json.dumps(report["summary"],indent=2),flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
