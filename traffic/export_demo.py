"""Export small browser checkpoints and the chronological test replay (no retraining)."""
import json, time
from pathlib import Path
import numpy as np
import torch
from train import ROOT, Data, load_model, predict, KMH

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf8')

def main():
    torch.set_num_threads(4)
    data=Data(); d=data.d; out=ROOT/'dist'; out.mkdir(exist_ok=True)
    metrics=json.loads((ROOT/'results'/'metrics.json').read_text())
    manifest=json.loads((ROOT/'results'/'data_manifest.json').read_text())
    p=np.load(ROOT/'results'/'predictions.npz')
    models={}; checkpoints={}
    for name,seed in metrics['selected_by_validation'].items():
        model,ck=load_model(name,seed); checkpoints[name]=model
        assert ck['run_id']==metrics['run_id'],'Checkpoint and metrics revisions differ'
        models[name]={'run_id':ck['run_id'],'seed':seed,'spatial':ck['spatial'],'hidden':ck['hidden'],
                      'weights':{k:v.numpy().tolist() for k,v in model.state_dict().items()}}
    first=int(d['test'][0]-11)
    speed=d['filled'][first:].astype('<f4'); mask=d['valid'][first:].astype('uint8')
    speed.tofile(out/'speeds.f32'); mask.tofile(out/'observed.u8')
    d['age_minutes'][first:].astype('<i4').tofile(out/'age.i32')
    d['calendar'][first:].astype('<f4').tofile(out/'calendar.f32')
    nodes=[{'id':str(i),'lat':float(c[0]),'lon':float(c[1])} for i,c in zip(d['sensor_ids'],d['coords'])]
    edges=[]; rows=[]
    for i in range(data.n):
        rows.append([[int(j),float(d['norm'][i,j])] for j in np.flatnonzero(d['norm'][i])])
        for j in range(i+1,data.n):
            if d['adj'][i,j]>0: edges.append([i,j,float(d['adj'][i,j])])
    g=p[f'gcn_gru_{models["gcn_gru"]["seed"]}']; b=p[f'gru_{models["gru"]["seed"]}']; y=p['actual']
    # Freeze the v1 episodes before v2 results; never search for new favourable cases.
    episodes=[('Phục hồi tốc độ','717458','2012-06-06 18:35:00'),
              ('Tình huống khó','717573','2012-06-15 14:50:00'),
              ('Dữ liệu quá cũ','774067','2012-06-09 13:45:00')]
    cases=[]
    for name,sensor,timestamp in episodes:
        n=int(np.flatnonzero(d['sensor_ids'].astype(str)==sensor)[0]);end=int(np.flatnonzero(d['timestamps']==timestamp)[0]);k=int(np.flatnonzero(d['test']==end)[0])
        cases.append({'name':name,'origin':end-first,'node':n,'sensor_id':sensor,
            'time':str(d['timestamps'][end]),'target_time':str(d['timestamps'][end+3]),
            'age_minutes':int(d['age_minutes'][end,n]),
            'actual_kmh':float(y[k,n]*KMH),'gcn_kmh':float(g[k,n]*KMH),'gru_kmh':float(b[k,n]*KMH),
            'persistence_kmh':float(p['persistence'][k,n]*KMH)})
    refs=[]
    for end in [int(d['test'][0]),int(d['test'][len(d['test'])//2]),*[first+c['origin'] for c in cases]]:
        item={'origin':end-first,'prediction':{}}
        for name,model in checkpoints.items():
            item['prediction'][name]=predict(model,data,np.array([end]),name=='gcn_gru')[0].tolist()
        item['prediction']['gcn_identity']=predict(checkpoints['gcn_gru'],data,np.array([end]),False)[0].tolist()
        refs.append(item)
    # Measure Python forward passes including batch gathering, independent of training.
    sample=np.array([int(d['test'][100])]); times=[]
    for _ in range(25):
        t=time.perf_counter(); predict(checkpoints['gcn_gru'],data,sample,True)
        times.append((time.perf_counter()-t)*1000)
    report={'summary':metrics['summary'],'seeds':metrics['seeds'],'selected':metrics['selected_by_validation'],
            'runs':[{k:v for k,v in r.items() if k!='history'} for r in metrics['runs']],
            'manifest':manifest,'protocol':metrics['protocol'],'cases':cases,
            'python_inference_ms_median':float(np.median(times[5:])),
            'example_selection':'Three historical episodes selected during v1 analysis and frozen before v2 fitting; not representative accuracy claims.',
            'run_id':metrics['run_id'],'interpretation':metrics['interpretation']}
    meta={'run_id':metrics['run_id'],'nodes':nodes,'edges':edges,'rows':rows,'first_source_index':first,'steps':len(speed),
          'timestamps':d['timestamps'][first:].tolist(),'origin_min':11,'origin_max':len(speed)-4,
          'mean':data.mean,'std':data.std,'kmh':KMH,'cases':cases}
    write_json(out/'meta.json',meta); write_json(out/'models.json',models); write_json(out/'report.json',report)
    write_json(ROOT/'results'/'browser_reference.json',refs)
    write_json(ROOT/'results'/'demo_cases.json',cases)
    print(json.dumps({'files':[(x.name,x.stat().st_size) for x in out.iterdir()], 'cases':cases,
                      'inference_ms':report['python_inference_ms_median']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
