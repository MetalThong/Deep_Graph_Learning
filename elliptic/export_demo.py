"""Export real test snapshots and seed-0 neural weights for browser inference."""
from pathlib import Path
import json
import numpy as np
import torch
from sklearn.metrics import precision_recall_curve

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'site/dist/data'
NAMES={'rf_local':'Random Forest · 93 đặc trưng','rf_all':'Random Forest · 165 đặc trưng','mlp':'MLP · 93 đặc trưng','gcn':'GCN + skip · 93 đặc trưng'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=np.load(ROOT/'data/prepared.npz');ids=d['ids'];y=d['y'];ts=d['times'];x=d['x'];src=d['src'];dst=d['dst']
    metrics=json.loads((ROOT/'results/metrics.json').read_text(encoding='utf-8'));summary=json.loads((ROOT/'results/data_summary.json').read_text(encoding='utf-8'))
    pred={m:np.load(ROOT/f'results/{m}_0_predictions.npz')['probabilities'] for m in NAMES}
    runs={r['model']:r for r in metrics['runs'] if r['seed']==0}
    from optimize_gcn import neural_features
    transform=runs['gcn'].get('config',{}).get('transform')
    assert transform==runs['mlp'].get('config',{}).get('transform')
    neural_x=neural_features(d,transform,include_test=True)
    weights={}
    for m in ['mlp','gcn']:
        ck=torch.load(ROOT/f'models/{m}_0.pt',map_location='cpu',weights_only=True)
        weights[m]={k:v.numpy().tolist() for k,v in ck['state_dict'].items()}
        weights[m]['__preprocess']={'clip':ck.get('config',{}).get('clip')}
    (OUT/'weights.json').write_text(json.dumps(weights,separators=(',',':')),encoding='utf-8')
    test=ts>=35; known=test&(y>=0)
    g=pred['gcn']>=runs['gcn']['threshold'];rf=pred['rf_all']>=runs['rf_all']['threshold']
    disagreement=known&(y==1)&g&~rf
    disagreement_note='Ví dụ GCN cảnh báo đúng một mẫu illicit mà RF all bỏ sót. Chọn sau đánh giá để minh họa, không đại diện toàn bộ test.'
    if not disagreement.any():
        disagreement=known&(g!=rf)
        disagreement_note='GCN và RF all đưa ra quyết định khác nhau. Đây là ví dụ chọn sau đánh giá.'
    degree=np.bincount(np.r_[src,dst],minlength=len(ids))
    cases=[]
    conditions=[('detected','Phát hiện đúng',known&(y==1)&g,'Đã chọn sau đánh giá để minh họa một giao dịch illicit được GCN cảnh báo.'),('false_alarm','Cảnh báo nhầm',known&(y==0)&g,'GCN cảnh báo nhưng nhãn tham chiếu là licit. Quan sát mạng không đủ để kết luận vi phạm.'),('missed','Bỏ sót',known&(y==1)&~g,'Nhãn tham chiếu là illicit nhưng GCN không phát cảnh báo ở ngưỡng đã chọn.'),('disagree','Hai mô hình khác nhau',disagreement,disagreement_note),('unknown','Chưa có nhãn',test&(y<0)&g,'Có điểm mô hình nhưng không có nhãn tham chiếu để xác nhận đúng hay sai.')]
    for key,title,mask,description in conditions:
        ix=np.flatnonzero(mask&(degree>=2)&(degree<=12))
        if not len(ix):ix=np.flatnonzero(mask)
        if len(ix):
            # Select interpretable-size neighborhoods, not representative performance estimates.
            i=int(ix[np.argmin(abs(degree[ix]-5))])
            cases.append(dict(key=key,title=title,id=int(ids[i]),step=int(ts[i]),description=description,label=int(y[i]),scores={m:float(p[i]) for m,p in pred.items()}))
    snapshots=[]
    for step in range(35,50):
        ind=np.flatnonzero(ts==step);rev=np.full(len(ids),-1,np.int64);rev[ind]=np.arange(len(ind));em=ts[src]==step
        payload={'step':step,'ids':ids[ind].tolist(),'labels':y[ind].tolist(),'src':rev[src[em]].tolist(),'dst':rev[dst[em]].tolist(),'scores':{m:[round(float(v),8) for v in p[ind]] for m,p in pred.items()},'feature_file':f'snapshot-{step}.bin','feature_columns':93}
        payload['feature_transform']=transform or 'standard_scaler'
        neural_x[ind,:93].astype('<f4').tofile(OUT/f'snapshot-{step}.bin')
        (OUT/f'snapshot-{step}.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
        snapshots.append({'step':step,'nodes':len(ind),'known':int((y[ind]>=0).sum())})
    perstep=[]
    for t in range(35,50):
        mask=(ts==t)&(y>=0)
        if not mask.any():continue
        for m in NAMES:
            from train import score
            perstep.append({'step':t,'model':m,**score(y[mask],pred[m][mask],runs[m]['threshold'])})
    export={'names':NAMES,'data_summary':summary,'summary':metrics['summary'],'runs':runs,'snapshots':snapshots,'cases':cases,'per_step':perstep,'protocol':metrics['protocol'],'test_scores':{'labels':y[known].tolist(),'scores':{m:np.round(p[known],8).tolist() for m,p in pred.items()}},'primary_seed':0,'sources':[{'title':'Elliptic dataset','url':'https://www.kaggle.com/datasets/ellipticco/elliptic-data-set'},{'title':'Weber et al. (2019)','url':'https://arxiv.org/abs/1908.02591'}]}
    if (ROOT/'optimization/report.json').exists():
        report=json.loads((ROOT/'optimization/report.json').read_text(encoding='utf-8'))
        export['optimization']={k:report[k] for k in ['selection','summary','test_reuse_disclosure']}
    (OUT/'manifest.json').write_text(json.dumps(export,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (ROOT/'results/demo_cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Exported',len(snapshots),'snapshots,',len(cases),'cases, seed0 models',flush=True)

if __name__=='__main__':main()
